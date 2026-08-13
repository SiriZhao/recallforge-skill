"""Validate RecallForge's host-installable skill and plugin package."""
from __future__ import annotations
import json, re, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skill" / "recallforge"
VERSION = "2.1.3"
REQUIRED = ["SKILL.md", "agents/openai.yaml", "references/review-methodology.md", "references/active-recall.md", "references/exam-simulation.md", "assets/self-test/mini-course.md"]

def check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"validation failed: {message}")

def main() -> None:
    for item in REQUIRED: check((SKILL / item).is_file(), f"missing skill/{item}")
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    check(text.startswith("---\n"), "SKILL.md frontmatter missing")
    check(re.search(r"^name: recallforge$", text, re.M) is not None, "skill name must be recallforge")
    check("description:" in text and "self-test" in text, "description or self-test missing")
    check(not re.search(r"[A-Za-z]:\\|/Users/|/home/", text), "absolute path in skill")
    plugin = ROOT / "recallforge-plugin"
    manifest = json.loads((plugin / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
    check(manifest["version"] == VERSION, "plugin version mismatch")
    check((plugin / "skills/recallforge/SKILL.md").is_file(), "plugin skill missing")
    for package in (ROOT / "dist").glob("recallforge-*-v*.zip"):
        with zipfile.ZipFile(package) as zf:
            names = set(zf.namelist())
        if "plugin" in package.name: check(".codex-plugin/plugin.json" in names and "skills/recallforge/SKILL.md" in names, "plugin archive structure")
        else: check("recallforge/SKILL.md" in names, "skill archive structure")
    print("RecallForge skill validation passed")

if __name__ == "__main__": main()
