"""Tests for release tag and SemVer mapping compatibility."""

import re


def extract_semver_from_tag(tag: str) -> str:
    """Extract standard SemVer (X.Y.Z) from milestone release tag (e.g., v0.10.0-m10 -> 0.10.0)."""
    clean_tag = tag.lstrip("v")
    # Match major.minor.patch
    match = re.match(r"^(\d+\.\d+\.\d+)", clean_tag)
    if match:
        return match.group(1)
    return clean_tag


def test_milestone_tag_mapping() -> None:
    """Verify v0.10.0-m10 maps to 0.10.0."""
    assert extract_semver_from_tag("v0.10.0-m10") == "0.10.0"
    assert extract_semver_from_tag("v0.10.1-m10.1") == "0.10.1"
    assert extract_semver_from_tag("v0.9.0-m09") == "0.9.0"
    assert extract_semver_from_tag("0.10.0") == "0.10.0"
    assert extract_semver_from_tag("0.10.1") == "0.10.1"


def test_chart_and_package_version_alignment() -> None:
    """Verify Chart.yaml and pyproject.toml versions align with 0.10.0."""
    import pathlib

    repo_root = pathlib.Path(__file__).parent.parent

    pyproject_text = (repo_root / "pyproject.toml").read_text()
    assert 'version = "0.10.0"' in pyproject_text

    chart_text = (repo_root / "charts" / "open-healthcare" / "Chart.yaml").read_text()
    assert "version: 0.10.0" in chart_text
    assert 'appVersion: "0.10.0"' in chart_text


def test_helm_image_references_match_ghcr() -> None:
    """Verify values.yaml references GHCR repository with appVersion default."""
    import pathlib

    repo_root = pathlib.Path(__file__).parent.parent
    values_text = (repo_root / "charts" / "open-healthcare" / "values.yaml").read_text()
    assert "ghcr.io/hastimal/open-healthcare-api" in values_text
    assert "ghcr.io/hastimal/open-healthcare-ui" in values_text
