"""Command Line Interface for healthcare-agents."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from healthcare_agents import __version__
from healthcare_agents.config import ConfigurationError, get_settings


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

    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Main CLI entrypoint."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command in ("health", "status"):
        return handle_health(verbose=getattr(args, "verbose", False))

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
