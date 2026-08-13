from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ..state.course import course_dir
from ..state.isolation import StateContaminationError, find_mock_markers
from .types import Evidence, evidence_to_dict

EVIDENCE_FILE = "evidence_store.json"


def _content_hash(evidence: Evidence) -> str:
    payload = json.dumps(
        {
            "course_id": evidence.course_id,
            "source_file": evidence.source_file,
            "page_or_slide": evidence.page_or_slide,
            "extraction_method": evidence.extraction_method,
            "content": evidence.content,
            "question_number": evidence.question_number,
            "heading": evidence.heading,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _file_hash(path: Path) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _load_store(course_path: Path) -> dict:
    path = course_path / EVIDENCE_FILE
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"course_id": "", "documents": {}, "records": [], "updated_at": ""}


def reject_synthetic(records: list[dict], *, where: str) -> None:
    """Fail closed: real state must never contain synthetic (mock/test) records."""
    for i, record in enumerate(records):
        if record.get("synthetic") is True:
            raise StateContaminationError(
                f"{where}[{i}]: synthetic record rejected from real state "
                f"({record.get('evidence_id', '?')})"
            )
        hits = find_mock_markers(record)
        if hits:
            raise StateContaminationError(f"{where}[{i}]: mock markers {hits[:3]}")


def write_evidence(
    workspace_root: Path,
    course_id: str,
    evidence_list: list[Evidence],
    *,
    store_mode: str = "real",
) -> tuple[int, int]:
    """Write evidence to the per-course evidence store with content-hash dedup and
    incremental ingestion (unchanged files are skipped). Returns (added, duplicates).

    store_mode="real" rejects synthetic records (contamination guard).
    store_mode="demo"/"test" is only for fixtures/tests/CI and keeps the synthetic flag.
    """
    course_path = course_dir(workspace_root, course_id)
    if not (course_path / "course_manifest.json").exists():
        raise FileNotFoundError(f"no course {course_id!r} in workspace {workspace_root}")
    store = _load_store(course_path)
    store["course_id"] = course_id
    existing_hashes = {r.get("content_hash") for r in store.get("records", [])}

    serializable = [evidence_to_dict(e) for e in evidence_list]
    if store_mode == "real":
        reject_synthetic(serializable, where=f"evidence_store[{course_id}]")

    added = 0
    duplicates = 0
    for record in serializable:
        if record["content_hash"] in existing_hashes:
            duplicates += 1
            continue
        existing_hashes.add(record["content_hash"])
        store["records"].append(record)
        added += 1

    import datetime

    store["updated_at"] = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    (course_path / EVIDENCE_FILE).write_text(
        json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return added, duplicates


def read_evidence(workspace_root: Path, course_id: str) -> list[dict]:
    course_path = course_dir(workspace_root, course_id)
    return _load_store(course_path).get("records", [])


def load_processed_files(workspace_root: Path, course_id: str) -> dict[str, str]:
    """Map source_file -> content hash of files already ingested (incremental)."""
    course_path = course_dir(workspace_root, course_id)
    return dict(_load_store(course_path).get("documents", {}))


def mark_file_processed(workspace_root: Path, course_id: str, source_file: str, file_hash: str) -> None:
    course_path = course_dir(workspace_root, course_id)
    store = _load_store(course_path)
    store["course_id"] = course_id
    store.setdefault("documents", {})[source_file] = file_hash
    (course_path / EVIDENCE_FILE).write_text(
        json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def current_file_hash(path: Path) -> str:
    return _file_hash(path)
