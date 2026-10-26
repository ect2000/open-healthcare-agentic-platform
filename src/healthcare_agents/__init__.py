"""Healthcare Agents Platform package."""

from importlib.metadata import PackageNotFoundError, version

from healthcare_agents.config import Settings, get_settings

try:
    __version__ = version("open-healthcare-agentic-platform")
except PackageNotFoundError:
    try:
        __version__ = version("healthcare-agents")
    except PackageNotFoundError:
        __version__ = "0.10.1"

__all__ = ["Settings", "__version__", "get_settings"]
