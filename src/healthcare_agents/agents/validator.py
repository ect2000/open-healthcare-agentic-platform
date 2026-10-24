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

    # 1. Duplicate detection
    seen_npis: set[str] = set()
    duplicates_count = 0
    for p in providers:
        if not p.npi:
            missing_fields.append(f"Provider {p.provider_id} missing NPI")
        elif p.npi in seen_npis:
            duplicates_count += 1
            notes.append(f"Duplicate provider detected: NPI {p.npi}")
        else:
            seen_npis.add(p.npi)

        if not p.name:
            missing_fields.append(f"Provider {p.provider_id} missing name")
        if not p.specialty:
            missing_fields.append(f"Provider {p.provider_id} missing specialty")

    # 2. Evidence validation
    all_evidence = clinical_evidence + patient_education
    seen_evidence_ids: set[str] = set()
    for e in all_evidence:
        if not e.citation_ref:
            missing_fields.append(f"Evidence {e.record_id} missing citation reference")
        if e.record_id in seen_evidence_ids:
            notes.append(f"Duplicate evidence record: {e.record_id}")
        else:
            seen_evidence_ids.add(e.record_id)

    # 3. Source provenance check
    provenance_verified = True
    for p in providers:
        if not p.source:
            provenance_verified = False
            unsupported_claims.append(f"Provider {p.name} has no verifiable source provenance.")

    for e in all_evidence:
        if not e.source:
            provenance_verified = False
            unsupported_claims.append(f"Evidence {e.title} has no verifiable source provenance.")

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
