"""Build RecallForge release artifacts in dist/:
  - recallforge-skill-v2.0.0.zip           (source distribution)
  - recallforge-skill-v2.0.0.tar.gz
  - SHA256SUMS.txt                          (combined checksums)

Only release-needed content is included. Excluded: .git, caches, __pycache__,
test outputs, .env / private keys / API keys, local user course data, and the
obsolete v0 generated artifacts in examples/output.

Usage: python scripts/build_release.py
"""

from __future__ import annotations

import hashlib
import tarfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION = "2.0.0"
DIST = ROOT / "dist"
ZIP_OUT = DIST / f"recallforge-skill-v{VERSION}.zip"
TAR_OUT = DIST / f"recallforge-skill-v{VERSION}.tar.gz"

EXCLUDE_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "venv",
    ".codex",
    ".agents",
    ".test-tmp",
    "node_modules",
    "dist",
    "build",
}
EXCLUDE_FILES = {
    ".env",
    ".env.local",
    "*.key",
    "*.pem",
    "*.p12",
    ".DS_Store",
    "*.egg-info",
}


def _excluded(rel: str) -> bool:
    parts = rel.split("/")
    if any(part in EXCLUDE_DIRS for part in parts):
        return True
    name = parts[-1]
    # a directory named like "*.egg-info" (e.g. recallforge.egg-info)
    if any(part.endswith(".egg-info") for part in parts):
        return True
    for pattern in EXCLUDE_FILES:
        if pattern.startswith("*") and name.endswith(pattern[1:]):
            return True
        if name == pattern:
            return True
    # never ship local user course data or generated v0 artifacts
    if rel.startswith("examples/output/") and name != ".gitkeep":
        return True
    if name == "tmp_example":
        return True
    return False


def main() -> None:
    DIST.mkdir(exist_ok=True)
    _build_zip()
    _build_tarball()
    _write_checksums()
    print("Release artifacts written to", DIST)


def _build_zip() -> None:
    if ZIP_OUT.exists():
        ZIP_OUT.unlink()

    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT).as_posix()
        if _excluded(rel):
            continue
        files.append(path)
    files.sort(key=lambda p: p.relative_to(ROOT).as_posix())

    with zipfile.ZipFile(ZIP_OUT, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in files:
            rel = path.relative_to(ROOT).as_posix()
            zf.write(path, rel)

    print(f"Wrote {ZIP_OUT}")
    print(f"  {len(files)} files, {ZIP_OUT.stat().st_size} bytes")


def _build_tarball() -> None:
    if TAR_OUT.exists():
        TAR_OUT.unlink()
    with tarfile.open(TAR_OUT, "w:gz") as tf:
        for path in sorted(ROOT.rglob("*")):
            if path.is_file():
                rel = path.relative_to(ROOT).as_posix()
                if not _excluded(rel):
                    tf.add(path, arcname=rel)
    print(f"Wrote {TAR_OUT}")


def _write_checksums() -> None:
    lines = []
    for path in sorted(DIST.glob(f"*{VERSION}*")):
        if path.suffix == ".sha256" or path.name == "SHA256SUMS.txt":
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.name}")
    (DIST / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Wrote SHA256SUMS.txt")


if __name__ == "__main__":
    main()
