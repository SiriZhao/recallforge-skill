from __future__ import annotations

import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest


DIST = Path(__file__).resolve().parent.parent / "dist"


def _latest_skill_zip() -> Path | None:
    candidates = sorted(DIST.glob("recallforge-skill-v*.zip"))
    return candidates[-1] if candidates else None


def _latest_plugin_zip() -> Path | None:
    candidates = sorted(DIST.glob("recallforge-plugin-v*.zip"))
    return candidates[-1] if candidates else None


@pytest.fixture(scope="module")
def packages():
    skill = _latest_skill_zip()
    plugin = _latest_plugin_zip()
    if skill is None or plugin is None:
        pytest.skip("release artifacts not built")
    return skill, plugin


def test_clean_room_skill_zip_install(packages, tmp_path: Path):
    skill, _ = packages
    extracted = tmp_path / "extract"
    with zipfile.ZipFile(skill) as zf:
        zf.extractall(extracted)
    assert (extracted / "recallforge" / "SKILL.md").is_file()
    assert not (extracted / "recallforge" / "recallforge").exists()

    target = tmp_path / "installed"
    script = extracted / "scripts" / ("install.ps1" if os.name == "nt" else "install.sh")
    if os.name == "nt":
        command = [
            "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-File", str(script), "-Target", str(target),
        ]
    else:
        command = ["bash", str(script), "--target", str(target)]
    subprocess.run(command, check=True, capture_output=True, text=True, timeout=120)

    for relative in (
        "SKILL.md",
        "agents/openai.yaml",
        "references/material-intelligence.md",
        "references/review-methodology.md",
        "assets/self-test/mini-course.md",
        "assets/self-test/multimodal/probability-slide.svg",
    ):
        assert (target / relative).is_file(), relative


def test_clean_room_plugin_zip_structure(packages, tmp_path: Path):
    _, plugin = packages
    extracted = tmp_path / "plugin"
    with zipfile.ZipFile(plugin) as zf:
        zf.extractall(extracted)
    manifest_path = extracted / ".codex-plugin" / "plugin.json"
    skill_path = extracted / "skills" / "recallforge" / "SKILL.md"
    assert manifest_path.is_file()
    assert skill_path.is_file()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["name"] == "recallforge-plugin"
    assert (extracted / "assets" / "recallforge-mark.svg").is_file()
    assert (extracted / "assets" / "recallforge-banner.svg").is_file()
    assert (extracted / "skills" / "recallforge" / "references" / "material-intelligence.md").is_file()
