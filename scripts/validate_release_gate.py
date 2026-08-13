"""Validate release-gate invariants before publishing RecallForge.

Checks version freeze consistency, host verification evidence, OCR evidence,
and relative Markdown links. Pure validation; performs no mutations.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def fail(message: str) -> None:
    raise SystemExit(f"release gate failed: {message}")


def main() -> None:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    pyproject = re.search(
        r'^version = "([^"]+)"',
        (ROOT / "pyproject.toml").read_text(encoding="utf-8"),
        re.M,
    )
    build = re.search(
        r'VERSION="([^"]+)"',
        (ROOT / "scripts" / "build_release.py").read_text(encoding="utf-8"),
    )
    validate = re.search(
        r'VERSION = "([^"]+)"',
        (ROOT / "scripts" / "validate_skill.py").read_text(encoding="utf-8"),
    )
    plugin = json.loads(
        (ROOT / "recallforge-plugin" / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
    )["version"]
    expected = {"2.2.0"} if version == "2.2.0" else {version}
    found = {
        "VERSION": version,
        "pyproject": pyproject.group(1) if pyproject else None,
        "build_release": build.group(1) if build else None,
        "validate_skill": validate.group(1) if validate else None,
        "plugin": plugin,
    }
    if set(found.values()) != expected:
        fail(f"version freeze mismatch: {found}")
    print("VERSION_FREEZE_OK", found)

    host = json.loads(
        (ROOT / "verification" / "host-verification-template.json").read_text(encoding="utf-8")
    )
    if host.get("verification_method") != "EXTERNAL_MANUAL":
        fail("host verification_method must be EXTERNAL_MANUAL")
    if not host.get("verified_at"):
        fail("host verified_at missing")
    if not host.get("recognition_warnings"):
        fail("host recognition_warnings must not be empty")
    for key in ("text_self_test", "multimodal_test", "functional_test", "material_e2e"):
        if host.get(key) != "PASS":
            fail(f"host {key} must be PASS")
    if host.get("skill_visible") is not True:
        fail("host skill_visible must be true")
    print("HOST_EVIDENCE_OK")

    ocr = json.loads(
        (ROOT / "benchmarks" / "results" / "ocr-windows-reference.json").read_text(encoding="utf-8")
    )
    summary = ocr.get("summary", {})
    for engine in ("tesseract", "rapidocr"):
        if engine not in summary:
            fail(f"OCR summary missing engine {engine}")
        if summary[engine].get("fixtures_with_cer") != 10:
            fail(f"OCR {engine} did not complete 10 fixtures")
        if summary[engine].get("failures") != 0:
            fail(f"OCR {engine} reported failures")
    print("OCR_EVIDENCE_OK")

    broken: list[str] = []
    md_files = [
        path
        for root_dir in (ROOT / "docs", ROOT / "benchmarks")
        for path in root_dir.rglob("*.md")
    ]
    md_files += [ROOT / "README.md", ROOT / "README.zh-CN.md"]
    link_pattern = re.compile(r"\[[^\]]+\]\(([^)#]+)(?:#[^)]+)?\)")
    for file in md_files:
        raw = file.read_text(encoding="utf-8")
        for match in link_pattern.finditer(raw):
            target = match.group(1)
            if target.startswith(("https:", "http:", "mailto:")):
                continue
            if not (file.parent / target).exists():
                broken.append(f"{file.relative_to(ROOT)}: {target}")
    if broken:
        fail("broken markdown links:\n" + "\n".join(broken))
    print("MARKDOWN_LINKS_OK")


if __name__ == "__main__":
    sys.exit(main())
