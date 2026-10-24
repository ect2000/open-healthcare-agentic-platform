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

    # Guardrail: Clinical research articles establish general biomedical literature existence,
    # and must never be asserted as direct evidence of an individual clinician's qualifications,
    # experience, or clinical outcomes.
    if clinical_evidence and providers:
        notes.append(
            "Biomedical research studies establish literature context only; they do not attest "
            "to specific individual provider clinical competence, board certification, or outcomes."
        )

    # 4. Check for missing evidence
    if not providers and not all_evidence:
        notes.append("No provider or clinical evidence records retrieved.")

    is_valid = len(missing_fields) == 0 and provenance_verified

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
