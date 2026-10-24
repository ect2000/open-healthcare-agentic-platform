"""Validation Component: Deterministic verification of retrieved data and provenance."""

from __future__ import annotations

from typing import Any

from healthcare_agents.workflows.state import (
    HealthcareWorkflowState,
    ValidationResults,
)


def validate_records(state: HealthcareWorkflowState) -> dict[str, Any]:
    """Perform deterministic checks on retrieved candidate providers and evidence."""
    providers = state.get("provider_candidates", [])
    clinical_evidence = state.get("clinical_evidence", [])
    patient_education = state.get("patient_education_evidence", [])
    metadata = dict(state.get("execution_metadata", {}))

    unsupported_claims: list[str] = []
    missing_fields: list[str] = []
    notes: list[str] = []

    # 1. Duplicate detection and NPI format validation
    seen_npis: set[str] = set()
    duplicates_count = 0
    for p in providers:
        if not p.npi:
            missing_fields.append(f"Provider {p.provider_id} missing NPI")
        else:
            if not (p.npi.isdigit() and len(p.npi) == 10):
                unsupported_claims.append(
                    f"Provider {p.name} has invalid NPI format '{p.npi}' (expected 10 digits)."
                )
            if p.npi in seen_npis:
                duplicates_count += 1
                notes.append(f"Duplicate provider detected: NPI {p.npi}")
            else:
                seen_npis.add(p.npi)

        if not p.name or p.name.strip() == "":
            missing_fields.append(f"Provider {p.provider_id} missing name")
        if not p.specialty or p.specialty.strip() == "":
            missing_fields.append(f"Provider {p.provider_id} missing specialty")

    # 2. Evidence validation (PMID format, URL, duplicates, metadata)
    all_evidence = clinical_evidence + patient_education
    seen_evidence_ids: set[str] = set()
    seen_pmids: set[str] = set()
    duplicate_evidence_count = 0

    for e in all_evidence:
        if not e.citation_ref:
            missing_fields.append(f"Evidence {e.record_id} missing citation reference")
        if not e.title or e.title.strip() == "":
            missing_fields.append(f"Evidence {e.record_id} missing article title")

        # Validate PMID format if pmid present or citation_ref starts with PMID:
        pmid_to_check = e.pmid
        if not pmid_to_check and e.citation_ref.startswith("PMID:"):
            pmid_to_check = e.citation_ref.split(":", 1)[1].strip()

        if pmid_to_check:
            # Allow DEMO- prefix only for synthetic fixtures
            if e.is_synthetic:
                is_pmid_format_valid = pmid_to_check.replace("DEMO-", "").isdigit()
            else:
                is_pmid_format_valid = pmid_to_check.isdigit()

            if not is_pmid_format_valid:
                unsupported_claims.append(
                    f"Evidence record {e.record_id} has invalid PMID format '{pmid_to_check}'."
                )

            if pmid_to_check in seen_pmids:
                duplicate_evidence_count += 1
                notes.append(f"Duplicate PubMed article detected: PMID {pmid_to_check}")
            else:
                seen_pmids.add(pmid_to_check)

        # Validate publication URL if provided
        if e.pubmed_url and not e.pubmed_url.startswith("https://pubmed.ncbi.nlm.nih.gov/"):
            unsupported_claims.append(
                f"Evidence record {e.record_id} has invalid PubMed URL '{e.pubmed_url}'."
            )

        # Validate official MedlinePlus URL if provided
        if e.official_url and not (
            e.official_url.startswith("https://medlineplus.gov/")
            or e.official_url.startswith("https://medlineplus.gov/spanish/")
        ):
            unsupported_claims.append(
                f"Patient education record {e.record_id} has "
                f"non-official MedlinePlus URL '{e.official_url}'."
            )

        if e.record_id in seen_evidence_ids:
            notes.append(f"Duplicate evidence record: {e.record_id}")
        else:
            seen_evidence_ids.add(e.record_id)

    # 3. Source provenance check & Clinical Independence Guardrail
    provenance_verified = True
    for p in providers:
        if not p.source:
            provenance_verified = False
            unsupported_claims.append(f"Provider {p.name} has no verifiable source provenance.")

    for e in all_evidence:
        if not e.source:
            provenance_verified = False
            unsupported_claims.append(f"Evidence {e.title} has no verifiable source provenance.")

    # Guardrail: Patient education resources must not be cited as original scientific research
    # or provider qualifications.
    if patient_education:
        notes.append(
            "Patient education resources from MedlinePlus provide consumer health context; "
            "they are not primary biomedical research publications or clinician credentials."
        )

    # 4. CMS Quality Records validation and NPI match verification
    cms_quality = state.get("cms_quality", [])
    unmatched_cms = state.get("unmatched_cms_records", [])

    provider_npis = {p.npi for p in providers if p.npi}
    for q in cms_quality:
        if not q.source:
            provenance_verified = False
            unsupported_claims.append(
                f"CMS quality record {q.record_id} has no verifiable source provenance."
            )
        if q.npi and q.npi not in provider_npis:
            unsupported_claims.append(
                f"CMS quality record {q.record_id} refers to NPI {q.npi} "
                "not among candidate providers."
            )

    if unmatched_cms:
        notes.append(
            f"Preserved {len(unmatched_cms)} unmatched CMS record(s) "
            "separately without linking to providers."
        )

    # Guardrail: Clinical research articles establish general biomedical literature existence,
    # and must never be asserted as direct evidence of an individual clinician's qualifications,
    # experience, or clinical outcomes.
    if clinical_evidence and providers:
        notes.append(
            "Biomedical research studies establish literature context only; they do not attest "
            "to specific individual provider clinical competence, board certification, or outcomes."
        )

    # Guardrail: CMS Provider Data quality scores (e.g. MIPS or Hospital star ratings) apply only
    # to participating clinicians/facilities and must never be extrapolated to other providers.
    # Missing CMS quality data indicates absence of public program reporting, NOT low quality.
    notes.append(
        "Absence of CMS quality measures for a provider indicates lack of public program "
        "participation or dataset coverage (common in dentistry and non-Medicare specialties), "
        "not poor clinical quality."
    )

    # 5. Provenance registry and citation verification
    unified_items = state.get("unified_evidence", [])
    if unified_items:
        from healthcare_agents.evidence.provenance import verify_citation_integrity

        # Join text representation of candidate facts to test citation integrity
        full_text_sample = " ".join([p.name for p in providers] + [e.title for e in all_evidence])
        citation_check = verify_citation_integrity(full_text_sample, unified_items)
        if not citation_check.is_valid:
            for uncited in citation_check.unresolved_citations:
                unsupported_claims.append(f"Citation [{uncited}] not found in retrieved evidence.")
            for boundary in citation_check.boundary_violations:
                unsupported_claims.append(f"Citation boundary violation: {boundary}")
            for dup in citation_check.duplicate_citation_ids:
                notes.append(f"Duplicate citation ID detected: {dup}")
            for url_err in citation_check.url_mismatches:
                unsupported_claims.append(f"URL domain mismatch: {url_err}")

    # 6. Check for missing evidence
    if not providers and not all_evidence:
        notes.append("No provider or clinical evidence records retrieved.")

    is_valid = len(missing_fields) == 0 and provenance_verified and len(unsupported_claims) == 0

    validation: ValidationResults = {
        "is_valid": is_valid,
        "duplicate_providers_found": duplicates_count,
        "unsupported_claims": unsupported_claims,
        "missing_evidence_fields": missing_fields,
        "provenance_verified": provenance_verified,
        "notes": notes,
    }

    metadata["validation_completed"] = True
    metadata["validation_is_valid"] = is_valid

    return {
        "validation_results": validation,
        "unsupported_claims": unsupported_claims,
        "execution_metadata": metadata,
    }
