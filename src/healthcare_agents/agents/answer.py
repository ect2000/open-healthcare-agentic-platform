"""Answer Agent: Synthesizes evidence-grounded final answers using Gemma 4."""

from __future__ import annotations

from typing import Any

from healthcare_agents.models.base import BaseModelAdapter
from healthcare_agents.workflows.state import HealthcareWorkflowState

ANSWER_SYSTEM_PROMPT = """You are a grounded healthcare discovery assistant.
Synthesize an evidence-backed answer strictly from the supplied provider
candidates and clinical evidence records.

CRITICAL RULES:
1. ONLY refer to clinicians, facilities, and research findings that appear in the supplied data.
2. Disclose that provider results are from demonstration test fixtures.
3. Include explicit citation references from the sources provided.
4. Do not speculate or invent clinical recommendations outside the evidence.
5. Provide a clear, respectful, and well-structured clinical summary.
"""


def format_context(state: HealthcareWorkflowState) -> str:
    """Format validated records into a prompt context block."""
    providers = state.get("provider_candidates", [])
    clinical_evidence = state.get("clinical_evidence", [])
    patient_education = state.get("patient_education_evidence", [])
    validation = state.get("validation_results", {})

    lines: list[str] = [
        f"USER QUERY: {state.get('original_query', '')}",
        "\n--- VALIDATED PROVIDER CANDIDATES (SYNTHETIC FIXTURES) ---",
    ]

    if providers:
        for p in providers:
            lines.append(
                f"- {p.name} | Specialty: {p.specialty} | Facility: {p.facility_name} "
                f"| Location: {p.city}, {p.state} | Source: {p.source} (NPI: {p.npi})"
            )
    else:
        lines.append("(No provider candidates retrieved)")

    lines.append("\n--- RESEARCH & CLINICAL EVIDENCE ---")
    if clinical_evidence:
        for e in clinical_evidence:
            lines.append(f"- [{e.source}: {e.citation_ref}] {e.title} ({e.year}): {e.summary}")
    else:
        lines.append("(No clinical studies retrieved)")

    lines.append("\n--- PATIENT EDUCATION EVIDENCE ---")
    if patient_education:
        for e in patient_education:
            lines.append(f"- [{e.source}: {e.citation_ref}] {e.title} ({e.year}): {e.summary}")
    else:
        lines.append("(No patient education topics retrieved)")

    if validation.get("unsupported_claims"):
        lines.append("\n--- VALIDATION WARNINGS ---")
        for claim in validation["unsupported_claims"]:
            lines.append(f"WARNING: {claim}")

    return "\n".join(lines)


def synthesize_answer(
    state: HealthcareWorkflowState,
    model_adapter: BaseModelAdapter | None = None,
) -> dict[str, Any]:
    """Execute answer synthesis using Gemma 4 model adapter or structured deterministic fallback."""
    context = format_context(state)
    metadata = dict(state.get("execution_metadata", {}))
    errors = list(state.get("errors", []))

    final_answer: str = ""

    if model_adapter is not None:
        try:
            prompt = (
                f"Based strictly on the following validated records, summarize findings:\n\n"
                f"{context}\n\n"
                f"Summarize available providers, cite clinical evidence, and state that "
                f"records are demonstration fixtures."
            )
            response = model_adapter.generate(
                prompt=prompt,
                system_instruction=ANSWER_SYSTEM_PROMPT,
                temperature=0.2,
            )
            final_answer = response.content.strip()
            metadata["answer_tokens"] = response.usage.total_tokens if response.usage else None
        except Exception as err:
            errors.append(f"Answer synthesis model invocation warning: {err}")

    # Deterministic fallback synthesis if model call was unavailable
    if not final_answer:
        providers = state.get("provider_candidates", [])
        evidence = state.get("clinical_evidence", []) + state.get("patient_education_evidence", [])

        summary_parts: list[str] = [
            f'**Healthcare Discovery Summary for:** *"{state.get("original_query", "")}"*\n',
            "### Recommended Provider Candidates (Demonstration Test Data)",
        ]

        if providers:
            for p in providers:
                summary_parts.append(
                    f"- **{p.name}** ({p.specialty})\n"
                    f"  - Facility: {p.facility_name} ({p.city}, {p.state})\n"
                    f"  - Source Provenance: {p.source} (NPI: `{p.npi}`)"
                )
        else:
            summary_parts.append("- No matching providers found in demonstration fixtures.")

        summary_parts.append("\n### Supporting Evidence & Clinical Literature")
        if evidence:
            for e in evidence:
                summary_parts.append(
                    f"- **{e.title}** ({e.year})\n  - {e.summary}\n  - Citation: `{e.citation_ref}`"
                )
        else:
            summary_parts.append("- No relevant clinical evidence records retrieved.")

        summary_parts.append(
            "\n*Notice: All provider and evidence records displayed above are "
            "synthetic test fixtures. Always consult a licensed medical clinician for advice.*"
        )
        final_answer = "\n".join(summary_parts)

    metadata["answer_completed"] = True
    return {
        "final_answer": final_answer,
        "execution_metadata": metadata,
        "errors": errors,
    }
