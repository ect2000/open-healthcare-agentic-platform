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

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
