from __future__ import annotations
import hashlib, json, zipfile
from pathlib import Path
import pytest

DIST=Path(__file__).resolve().parent.parent/"dist"; VERSION="2.1.2"
@pytest.fixture(scope="module")
def packages():
    return DIST/f"recallforge-skill-v{VERSION}.zip", DIST/f"recallforge-plugin-v{VERSION}.zip"
def test_skill_archive_layout(packages):
    skill,_=packages
    if not skill.exists(): pytest.skip("release artifact not built")
    with zipfile.ZipFile(skill) as z: names=set(z.namelist())
    assert "recallforge/SKILL.md" in names
    assert "recallforge/agents/openai.yaml" in names
    assert "recallforge/assets/self-test/mini-course.md" in names
    assert "scripts/install.ps1" in names and "scripts/install.sh" in names
    assert not any(n.startswith("recallforge/recallforge/") for n in names)
def test_plugin_archive_layout(packages):
    _,plugin=packages
    if not plugin.exists(): pytest.skip("release artifact not built")
    with zipfile.ZipFile(plugin) as z:
        names=set(z.namelist()); manifest=json.loads(z.read(".codex-plugin/plugin.json"))
    assert "skills/recallforge/SKILL.md" in names
    assert manifest["name"]=="recallforge-plugin" and manifest["version"]==VERSION
def test_checksums(packages):
    checksum=DIST/"SHA256SUMS.txt"
    if not checksum.exists(): pytest.skip("release artifact not built")
    for line in checksum.read_text().splitlines():
        digest,name=line.split("  "); assert hashlib.sha256((DIST/name).read_bytes()).hexdigest()==digest
