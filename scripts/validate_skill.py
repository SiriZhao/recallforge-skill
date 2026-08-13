"""Validate RecallForge's host-installable skill and plugin package."""
from __future__ import annotations
import json, re, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skill" / "recallforge"
VERSION = "2.2.0"
REQUIRED = ["SKILL.md", "agents/openai.yaml", "references/review-methodology.md", "references/active-recall.md", "references/exam-simulation.md", "references/material-intelligence.md", "assets/self-test/mini-course.md", "assets/self-test/multimodal/probability-slide.svg"]

def check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"validation failed: {message}")

def main() -> None:
    for item in REQUIRED: check((SKILL / item).is_file(), f"missing skill/{item}")
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    check(text.startswith("---\n"), "SKILL.md frontmatter missing")
    check(re.search(r"^name: recallforge$", text, re.M) is not None, "skill name must be recallforge")
    check("description:" in text and "self-test" in text, "description or self-test missing")
    check("multimodal-test" in text and "inspect-materials" in text, "material modes missing")
    check(not re.search(r"[A-Za-z]:\\|/Users/|/home/", text), "absolute path in skill")
    plugin = ROOT / "recallforge-plugin"
    manifest = json.loads((plugin / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
    check(manifest["version"] == VERSION, "plugin version mismatch")
    check((plugin / "skills/recallforge/SKILL.md").is_file(), "plugin skill missing")
    check((plugin / "skills/recallforge/references/material-intelligence.md").is_file(), "plugin material reference missing")
    candidate_versions = {
        re.search(r'^version = "([^"]+)"', (ROOT / "pyproject.toml").read_text(encoding="utf-8"), re.M).group(1),
        manifest["version"],
    }
    check(all(value.startswith("2.2.0") for value in candidate_versions), "candidate version mismatch")
    for package in (ROOT / "dist").glob("recallforge-*-v*.zip"):
        with zipfile.ZipFile(package) as zf:
            names = set(zf.namelist())
        if "plugin" in package.name: check(".codex-plugin/plugin.json" in names and "skills/recallforge/SKILL.md" in names, "plugin archive structure")
        else: check("recallforge/SKILL.md" in names, "skill archive structure")
    print("RecallForge skill validation passed")

if __name__ == "__main__": main()
