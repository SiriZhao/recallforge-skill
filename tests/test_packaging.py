from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

import pytest


DIST = Path(__file__).resolve().parent.parent / "dist"
VERSION = "2.0.0"


@pytest.fixture(scope="module")
def release_available() -> bool:
    return (DIST / f"exam-review-skill-v{VERSION}.zip").exists()


def test_release_zip_exists(release_available):
    if not release_available:
        pytest.skip("release artifact not built in this checkout")
    assert (DIST / f"exam-review-skill-v{VERSION}.zip").exists()
    assert (DIST / "SHA256SUMS.txt").exists()


def test_release_zip_clean(release_available):
    if not release_available:
        pytest.skip("release artifact not built in this checkout")
    zip_path = DIST / f"exam-review-skill-v{VERSION}.zip"
    with zipfile.ZipFile(zip_path) as z:
        names = z.namelist()
    forbidden = [
        n for n in names
        if any(x in n for x in (".git/", "__pycache__", ".venv", "dist/", "build/", ".egg-info"))
        or n.endswith((".env", ".key", ".pem", ".p12"))
        or ("examples/output/" in n and not n.endswith(".gitkeep"))
    ]
    assert forbidden == [], f"forbidden entries: {forbidden}"
    # key files present
    for required in ("SKILL.md", "README.md", "CHANGELOG.md", "LICENSE", "pyproject.toml"):
        assert any(n.endswith(required) for n in names), required


def test_release_checksum_matches(release_available):
    if not release_available:
        pytest.skip("release artifact not built in this checkout")
    checksum_file = DIST / "SHA256SUMS.txt"
    lines = checksum_file.read_text(encoding="utf-8").strip().splitlines()
    assert lines, "empty checksum file"
    for line in lines:
        digest, name = line.split("  ")
        path = DIST / name
        assert path.exists(), name
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual == digest, f"{name} checksum mismatch"
