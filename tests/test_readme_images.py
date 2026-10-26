"""Automated validation tests for README.md image links and assets."""

import pathlib
import re
import urllib.request

import pytest


def test_all_local_images_exist_in_git() -> None:
    """Verify that every local image asset referenced in docs/images exists on disk."""
    repo_root = pathlib.Path(__file__).parent.parent
    docs_images = repo_root / "docs" / "images"
    assert docs_images.exists() and docs_images.is_dir()

    readme_text = (repo_root / "README.md").read_text()
    # Find all referenced image file basenames (e.g. m08_platform_overview.png)
    image_names = re.findall(r"docs/images/([a-zA-Z0-9_\-]+\.png)", readme_text)
    assert len(image_names) >= 20

    for img_name in set(image_names):
        img_path = docs_images / img_name
        assert img_path.exists(), f"Image asset {img_name} missing from docs/images"


def test_readme_contains_no_relative_image_paths() -> None:
    """Ensure README contains no relative image paths like ![...](docs/images/...)."""
    repo_root = pathlib.Path(__file__).parent.parent
    readme_text = (repo_root / "README.md").read_text()

    # Relative image paths will match !\[...\]\((?!http)
    broken_relative = re.findall(r"!\[.*?\]\((?!https?:\/\/)(docs\/images\/[^\)]+)\)", readme_text)
    assert broken_relative == [], f"Found relative image links in README: {broken_relative}"


@pytest.mark.live
def test_remote_raw_github_image_urls_return_http_200() -> None:
    """Validate that every remote raw GitHub image URL in README returns HTTP 200 and image/png."""
    repo_root = pathlib.Path(__file__).parent.parent
    readme_text = (repo_root / "README.md").read_text()

    raw_urls = re.findall(
        r"!\[.*?\]\((https:\/\/raw\.githubusercontent\.com\/hastimal\/open-healthcare-agentic-platform\/main\/docs\/images\/[^\)]+)\)",
        readme_text,
    )
    assert len(raw_urls) >= 20

    for url in set(raw_urls):
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            assert resp.status == 200, f"URL {url} returned HTTP {resp.status}"
            content_type = resp.headers.get("Content-Type", "")
            assert "image" in content_type, (
                f"URL {url} returned non-image Content-Type: {content_type}"
            )
