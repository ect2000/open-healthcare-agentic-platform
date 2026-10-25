"""Tests for top-level package imports and exports."""

import healthcare_agents
from healthcare_agents import Settings, __version__, get_settings


def test_package_metadata() -> None:
    """Verify package version is defined and non-empty."""
    assert __version__ == "0.5.0"
    assert healthcare_agents.__version__ == "0.5.0"


def test_package_exports() -> None:
    """Verify primary exports exist."""
    assert Settings is not None
    assert callable(get_settings)
