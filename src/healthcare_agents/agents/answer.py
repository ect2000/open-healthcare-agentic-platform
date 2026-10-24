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
        "\n--- VALIDATED PROVIDER CANDIDATES ---",
    ]

    if providers:
        for p in providers:
            prov_type = "DEMO FIXTURE" if p.is_synthetic else "LIVE REGISTRY"
            practice_info = f" | Practice: {p.practice_address}" if p.practice_address else ""
            lines.append(
                f"- [{prov_type}] {p.name} | Specialty: {p.specialty} "
                f"| Location: {p.city}, {p.state}{practice_info} "
                f"| Source: {p.source} (NPI: {p.npi})"
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
            "### Candidate Healthcare Providers",
        ]

        if providers:
            for p in providers:
                status_label = "Demonstration Fixture" if p.is_synthetic else "Live NPPES Registry"
                addr_info = (
                    f"\n  - Practice Address: {p.practice_address}" if p.practice_address else ""
                )
                summary_parts.append(
                    f"- **{p.name}** ({p.specialty}) [{status_label}]\n"
                    f"  - Entity: {p.entity_type} | Location: {p.city}, {p.state}{addr_info}\n"
                    f"  - Source: {p.source} (NPI: `{p.npi}`)"
                )
        else:
            summary_parts.append("- No matching providers found.")

        summary_parts.append("\n### Supporting Evidence & Clinical Literature (Simulated Fixtures)")
        if evidence:
            for e in evidence:
                summary_parts.append(
                    f"- **{e.title}** ({e.year})\n  - {e.summary}\n  - Citation: `{e.citation_ref}`"
                )
        else:
            summary_parts.append("- No relevant clinical evidence records retrieved.")

        has_live = any(not p.is_synthetic for p in providers)
        prov_notice = (
            "Provider records retrieved live from the public CMS NPPES registry."
            if has_live
            else "Provider records are demonstration test fixtures."
        )
        summary_parts.append(
            f"\n*Notice: {prov_notice} Research and patient education evidence remain "
            "simulated demonstration fixtures for M4A. An NPI is an administrative identifier and "
            "not proof of clinical competence, licensing status, or quality. "
            "Always consult a licensed clinician.*"
        )
        final_answer = "\n".join(summary_parts)

    metadata["answer_completed"] = True
    return {
        "final_answer": final_answer,
        "execution_metadata": metadata,
        "errors": errors,
    }
