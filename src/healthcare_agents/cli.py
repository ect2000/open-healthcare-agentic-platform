"""Command Line Interface for healthcare-agents."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from healthcare_agents import __version__
from healthcare_agents.config import ConfigurationError, get_settings
from healthcare_agents.models import (
    ModelError,
    ModelNotFoundError,
    ModelTimeoutError,
    ModelUnavailableError,
    OllamaAdapter,
    get_model_adapter,
)
from healthcare_agents.workflows import run_healthcare_workflow


def build_parser() -> argparse.ArgumentParser:
    """Construct argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="healthcare-agents",
        description="Vendor-neutral healthcare agentic AI platform CLI.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show program's version number and exit.",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # health / status command
    health_parser = subparsers.add_parser(
        "health",
        aliases=["status"],
        help="Check configuration and system status.",
    )
    health_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show full configuration details.",
    )

    # model command hierarchy
    model_parser = subparsers.add_parser(
        "model",
        help="Model management and inference commands.",
    )
    model_subparsers = model_parser.add_subparsers(dest="model_command", help="Model subcommands")

    # healthcare-agents model status
    model_subparsers.add_parser(
        "status",
        help="Check local model availability and service health.",
    )

    # healthcare-agents model chat
    chat_parser = model_subparsers.add_parser(
        "chat",
        help="Execute chat inference with the local model.",
    )
    chat_parser.add_argument(
        "--prompt",
        "-p",
        required=True,
        help="Prompt text for the model.",
    )
    chat_parser.add_argument(
        "--stream",
        "-s",
        action="store_true",
        help="Stream response tokens in real-time.",
    )
    chat_parser.add_argument(
        "--system",
        help="Optional system instruction for the model.",
    )

    # healthcare-agents search command (Milestone M3)
    search_parser = subparsers.add_parser(
        "search",
        help="Run multi-agent healthcare discovery workflow with LangGraph.",
    )
    search_parser.add_argument(
        "--query",
        "-q",
        required=True,
        help="Healthcare search query (e.g., 'Find pediatric dentists in Houston').",
    )
    search_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Display detailed agent planning, retrieval, and validation stages.",
    )

    return parser


def handle_health(verbose: bool = False) -> int:
    """Execute health / status verification."""
    try:
        settings = get_settings()
    except ConfigurationError as err:
        sys.stderr.write(f"Configuration error: {err}\n")
        return 1

    sys.stdout.write("Status: healthy\n")
    sys.stdout.write(f"Environment: {settings.environment}\n")
    sys.stdout.write(f"Log Level: {settings.log_level}\n")
    sys.stdout.write(f"Configured Model Provider: {settings.model_provider}\n")

    if verbose:
        sys.stdout.write(f"App Name: {settings.app_name}\n")
        sys.stdout.write(f"Configured Model: {settings.model_name}\n")
        sys.stdout.write(f"Ollama URL: {settings.ollama_base_url}\n")
        sys.stdout.write(f"Model Timeout: {settings.model_timeout_seconds}s\n")

    return 0


def handle_model_status() -> int:
    """Execute model status inspection."""
    try:
        settings = get_settings()
    except ConfigurationError as err:
        sys.stderr.write(f"Configuration error: {err}\n")
        return 1

    sys.stdout.write("=== Model Service Status ===\n")
    sys.stdout.write(f"Provider: {settings.model_provider}\n")
    sys.stdout.write(f"Model: {settings.model_name}\n")
    sys.stdout.write(f"Endpoint: {settings.ollama_base_url}\n")

    adapter = get_model_adapter(
        provider=settings.model_provider,
        base_url=settings.ollama_base_url,
        model_name=settings.model_name,
        timeout_seconds=settings.model_timeout_seconds,
    )

    if isinstance(adapter, OllamaAdapter):
        service_ok = adapter.check_service_health()
        if not service_ok:
            sys.stderr.write(
                f"Error: Ollama service is unavailable at {settings.ollama_base_url}. "
                "Ensure Ollama is running (`ollama serve`).\n"
            )
            return 1

        sys.stdout.write("Service Status: reachable\n")
        try:
            available_models = adapter.list_models()
        except ModelUnavailableError as err:
            sys.stderr.write(f"Error checking models: {err}\n")
            return 1

        is_installed = (
            settings.model_name in available_models
            or f"{settings.model_name}:latest" in available_models
        )
        if is_installed:
            sys.stdout.write(f"Model Availability: installed ({settings.model_name})\n")
            return 0

        sys.stderr.write(
            f"Model Availability: NOT installed. Target model '{settings.model_name}' "
            f"was not found on Ollama.\n"
            f"Installed models: {', '.join(available_models) if available_models else 'none'}\n"
            f"Run: ollama pull {settings.model_name}\n"
        )
        return 1

    is_avail = adapter.is_available()
    sys.stdout.write(f"Model Availability: {'ready' if is_avail else 'not ready'}\n")
    return 0 if is_avail else 1


def handle_model_chat(prompt: str, stream: bool = False, system: str | None = None) -> int:
    """Execute model chat inference."""
    try:
        settings = get_settings()
    except ConfigurationError as err:
        sys.stderr.write(f"Configuration error: {err}\n")
        return 1

    adapter = get_model_adapter(
        provider=settings.model_provider,
        base_url=settings.ollama_base_url,
        model_name=settings.model_name,
        timeout_seconds=settings.model_timeout_seconds,
    )

    try:
        if stream:
            for chunk in adapter.generate_stream(prompt=prompt, system_instruction=system):
                if chunk.content:
                    sys.stdout.write(chunk.content)
                    sys.stdout.flush()
            sys.stdout.write("\n")
            return 0

        response = adapter.generate(prompt=prompt, system_instruction=system)
        sys.stdout.write(f"{response.content}\n")
        return 0

    except ModelUnavailableError as err:
        sys.stderr.write(
            f"Connection Error: {err}\n"
            f"Please verify Ollama is running at {settings.ollama_base_url}.\n"
        )
        return 1
    except ModelNotFoundError as err:
        sys.stderr.write(
            f"Model Not Found: {err}\nPlease install it using: ollama pull {settings.model_name}\n"
        )
        return 1
    except ModelTimeoutError as err:
        sys.stderr.write(f"Timeout Error: {err}\n")
        return 1
    except ModelError as err:
        sys.stderr.write(f"Model Inference Error: {err}\n")
        return 1


def handle_search(query: str, verbose: bool = False) -> int:
    """Execute the multi-agent LangGraph healthcare discovery workflow."""
    try:
        settings = get_settings()
    except ConfigurationError as err:
        sys.stderr.write(f"Configuration error: {err}\n")
        return 1

    adapter = get_model_adapter(
        provider=settings.model_provider,
        base_url=settings.ollama_base_url,
        model_name=settings.model_name,
        timeout_seconds=settings.model_timeout_seconds,
    )

    sys.stdout.write("==================================================\n")
    sys.stdout.write("  HEALTHCARE MULTI-AGENT WORKFLOW (LangGraph)     \n")
    sys.stdout.write("==================================================\n")
    sys.stdout.write(f"Query: {query}\n\n")

    try:
        state = run_healthcare_workflow(query=query, model_adapter=adapter)
    except Exception as err:
        sys.stderr.write(f"Workflow execution failure: {err}\n")
        return 1

    plan = state.get("search_plan", {})
    providers = state.get("provider_candidates", [])
    evidence = state.get("clinical_evidence", []) + state.get("patient_education_evidence", [])
    validation = state.get("validation_results", {})
    final_answer = state.get("final_answer", "")

    if verbose:
        sys.stdout.write("--- [Stage 1: Planner Agent] ---\n")
        sys.stdout.write(f"Specialty: {plan.get('specialty') or 'N/A'}\n")
        sys.stdout.write(f"Location:  {plan.get('city') or 'N/A'}, {plan.get('state') or 'N/A'}\n")
        sys.stdout.write(f"Topics:    {', '.join(plan.get('evidence_topics', []))}\n\n")

        retriever_used = state.get("execution_metadata", {}).get(
            "provider_retriever", "ProviderRetriever"
        )
        sys.stdout.write(f"--- [Stage 2: Provider Retrieval ({retriever_used})] ---\n")
        if providers:
            for p in providers:
                status_str = "FIXTURE" if p.is_synthetic else "LIVE NPPES"
                addr = f" | Addr: {p.practice_address}" if p.practice_address else ""
                phone = f" | Phone: {p.telephone}" if p.telephone else ""
                ts = f" | Timestamp: {p.retrieval_timestamp}" if p.retrieval_timestamp else ""
                sys.stdout.write(
                    f"- [{status_str}] {p.name} | {p.specialty} | {p.facility_name} "
                    f"({p.city}, {p.state}) [NPI: {p.npi}]{addr}{phone}{ts}\n"
                )
        else:
            sys.stdout.write("(No provider candidates retrieved)\n")
        sys.stdout.write("\n")

        ev_retriever = state.get("execution_metadata", {}).get(
            "evidence_retriever", "EvidenceRetriever"
        )
        edu_retriever = state.get("execution_metadata", {}).get(
            "patient_education_retriever", "EducationRetriever"
        )
        sys.stdout.write(
            f"--- [Stage 3: Evidence Retrieval ({ev_retriever} / {edu_retriever})] ---\n"
        )
        if evidence:
            for e in evidence:
                if e.is_synthetic:
                    status_str = "FIXTURE"
                elif "MedlinePlus" in e.source:
                    status_str = "LIVE MEDLINEPLUS"
                else:
                    status_str = "LIVE PUBMED"
                url_val = e.official_url or e.pubmed_url
                url_str = f" | URL: {url_val}" if url_val else ""
                auth_str = f" | Authors: {', '.join(e.authors[:2])}" if e.authors else ""
                sys.stdout.write(
                    f"- [{status_str}] {e.title} ({e.year}) [{e.citation_ref}]{auth_str}{url_str}\n"
                )
        else:
            sys.stdout.write("(No clinical or educational evidence records retrieved)\n")
        sys.stdout.write("\n")

        sys.stdout.write("--- [Stage 4: CMS Provider Data & Quality Reporting] ---\n")
        cms_quality = state.get("cms_quality", [])
        unmatched_cms = state.get("unmatched_cms_records", [])
        if cms_quality:
            for q in cms_quality:
                q_status = "FIXTURE" if q.is_synthetic else "LIVE CMS"
                val = f"{q.measure_name}: {q.score}" if q.score else q.measure_name
                sys.stdout.write(
                    f"- [{q_status}] {q.entity_name} [NPI: {q.npi}] | Dataset: {q.dataset_id} "
                    f"({q.dataset_name}) | {val} | URL: {q.source_url}\n"
                )
        else:
            sys.stdout.write(
                "(No CMS quality records available for candidate providers. Note: Specialties like "
                "pediatric dentistry are generally not included in MIPS or Hospital datasets; "
                "this denotes dataset scope, not poor clinical quality.)\n"
            )
        if unmatched_cms:
            sys.stdout.write(
                f"(Preserved {len(unmatched_cms)} unmatched CMS record(s) safely unjoined.)\n"
            )
        sys.stdout.write("\n")

        sys.stdout.write("--- [Stage 5: Evidence Processing & Deterministic Validation] ---\n")
        unified_items = state.get("unified_evidence", [])
        excluded_items = state.get("excluded_evidence", [])
        prov_recs = state.get("provenance_records", [])
        sys.stdout.write(f"Total Normalized Items: {len(unified_items)}\n")
        sys.stdout.write(f"Excluded Items:         {len(excluded_items)}\n")
        sys.stdout.write(f"Provenance Records:     {len(prov_recs)}\n")
        if excluded_items:
            sys.stdout.write("Sample Excluded Items (Relevance/Quality Filtering):\n")
            for ex in excluded_items[:3]:
                reason = ex.relevance.exclusion_reason or "Low topical relevance"
                sys.stdout.write(f"  - [{ex.citation_id}] {ex.title_or_name}: {reason}\n")
        sys.stdout.write("\n")

        valid_str = "VALID" if validation.get("is_valid") else "INVALID"
        sys.stdout.write("--- [Stage 5: Deterministic Validation] ---\n")
        sys.stdout.write(f"Status:             {valid_str}\n")
        sys.stdout.write(f"Duplicates Checked: {validation.get('duplicate_providers_found', 0)}\n")
        sys.stdout.write(f"Provenance OK:      {validation.get('provenance_verified')}\n")
        if validation.get("unsupported_claims"):
            sys.stdout.write(f"Warnings:           {', '.join(validation['unsupported_claims'])}\n")
        sys.stdout.write("\n")

    sys.stdout.write("--- [Stage 6: Synthesized Discovery Result] ---\n")
    sys.stdout.write(f"{final_answer}\n\n")

    citations = state.get("citations", [])
    if citations:
        sys.stdout.write("--- [Citations & Source Provenance] ---\n")
        for c in citations:
            sys.stdout.write(f"- {c}\n")
        sys.stdout.write("\n")

    has_live_prov = any(not p.is_synthetic for p in providers)
    has_live_pubmed = any(not e.is_synthetic for e in evidence if e.source == "PubMed-Live")
    has_live_cms = any(not q.is_synthetic for q in state.get("cms_quality", []))
    has_live_mlp = any(not e.is_synthetic for e in state.get("patient_education_evidence", []))

    if has_live_prov and has_live_pubmed:
        cms_desc = (
            "CMS Provider Data Catalog" if has_live_cms else "CMS Provider Data Catalog evaluated"
        )
        mlp_desc = (
            "Patient education retrieved live from U.S. NLM MedlinePlus Web Service."
            if has_live_mlp
            else "Patient education retrieved from demonstration test fixtures."
        )
        sys.stdout.write(
            f"[Notice: Provider records retrieved live from CMS NPPES Registry API v2.1. "
            f"Biomedical literature retrieved live from NCBI Entrez PubMed. "
            f"Quality measures retrieved live from {cms_desc}. "
            f"{mlp_desc}]\n"
        )
    elif has_live_prov:
        sys.stdout.write(
            "[Notice: Provider records retrieved live from CMS NPPES Registry API v2.1. "
            "Evidence records retrieved from demonstration test fixtures.]\n"
        )
    else:
        sys.stdout.write(
            "[Notice: Data retrieved from synthetic test fixtures for demonstration.]\n"
        )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Main CLI entrypoint."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command in ("health", "status"):
        return handle_health(verbose=getattr(args, "verbose", False))

    if args.command == "model":
        if args.model_command == "status":
            return handle_model_status()
        if args.model_command == "chat":
            return handle_model_chat(
                prompt=args.prompt,
                stream=getattr(args, "stream", False),
                system=getattr(args, "system", None),
            )
        parser.parse_args(["model", "--help"])
        return 0

    if args.command == "search":
        return handle_search(
            query=args.query,
            verbose=getattr(args, "verbose", False),
        )

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
