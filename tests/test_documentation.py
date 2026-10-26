"""Automated documentation, link, and asset validation tests."""

import pathlib
import re
import urllib.request

import pytest


def test_markdown_local_links_exist() -> None:
    """Verify that all relative file links in README.md and docs/ exist on disk."""
    repo_root = pathlib.Path(__file__).parent.parent
    md_files = [
        repo_root / "README.md",
        repo_root / "CONTRIBUTING.md",
        *list((repo_root / "docs").rglob("*.md")),
    ]

    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8")
        # Find markdown links: [text](path)
        # Exclude http/https, mailto, anchor only #
        links = re.findall(r"\[.*?\]\((?!https?:\/\/|mailto:|#)([^\)\s]+)\)", content)
        for link in links:
            # Strip anchors if present
            clean_link = link.split("#")[0]
            if not clean_link or "..." in clean_link:
                continue
            if clean_link.startswith("file://"):
                clean_path_str = clean_link.replace("file://", "")
                if clean_path_str.startswith("/Users/"):
                    target_path = pathlib.Path(clean_path_str)
                else:
                    target_path = (repo_root / clean_path_str.lstrip("/")).resolve()
            else:
                target_path = (md_file.parent / clean_link).resolve()
            assert target_path.exists(), (
                f"Broken relative link '{link}' in {md_file.relative_to(repo_root)}"
            )


def test_readme_and_pypi_image_assets_exist() -> None:
    """Verify that all image references in README.md and docs/pypi/README.md exist locally."""
    repo_root = pathlib.Path(__file__).parent.parent
    docs_images = repo_root / "docs" / "images"

    for file_path in [repo_root / "README.md", repo_root / "docs" / "pypi" / "README.md"]:
        text = file_path.read_text(encoding="utf-8")
        images = re.findall(r"docs/images/([a-zA-Z0-9_\-]+\.(?:png|svg))", text)
        for img in images:
            assert (docs_images / img).exists(), (
                f"Image asset '{img}' referenced in {file_path.name} is missing from docs/images"
            )


def test_no_hardcoded_issue_status_in_readme() -> None:
    """Ensure README.md does not contain hardcoded issue statuses."""
    repo_root = pathlib.Path(__file__).parent.parent
    readme_text = (repo_root / "README.md").read_text(encoding="utf-8")
    assert (
        "Current issue status, discussions, and progress are maintained live on GitHub"
        in readme_text
    )


def test_package_metadata_points_to_pypi_readme() -> None:
    """Verify pyproject.toml points to docs/pypi/README.md for package long_description."""
    repo_root = pathlib.Path(__file__).parent.parent
    pyproject_text = (repo_root / "pyproject.toml").read_text(encoding="utf-8")
    assert 'readme = "docs/pypi/README.md"' in pyproject_text


@pytest.mark.live
def test_all_readme_external_image_urls() -> None:
    """Verify all raw GitHub image URLs in README.md return HTTP 200 and image mime-type."""
    repo_root = pathlib.Path(__file__).parent.parent
    readme_text = (repo_root / "README.md").read_text(encoding="utf-8")
    urls = re.findall(r"!\[.*?\]\((https:\/\/raw\.githubusercontent\.com\/[^\)]+)\)", readme_text)

    for url in set(urls):
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=5) as resp:
            assert resp.status == 200, f"URL {url} returned HTTP {resp.status}"
            ct = resp.headers.get("Content-Type", "")
            assert "image" in ct, f"URL {url} returned non-image content type: {ct}"
