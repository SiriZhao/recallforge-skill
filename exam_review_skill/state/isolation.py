from __future__ import annotations

import json
from typing import Any


MOCK_MARKERS = (
    '"provider": "mock"',
    '"provider":"mock"',
    "示例：未作答",
    "Mock provider",
    "mock provider",
    "MockLLMProvider",
    "sandbox_mode",
)


class StateContaminationError(ValueError):
    """Raised when mock/sandbox content or cross-course data would enter real state."""


def find_mock_markers(obj: Any, path: str = "$", hits: list[str] | None = None) -> list[str]:
    """Recursively locate mock/sandbox markers in nested data. Returns hit paths."""
    hits = hits if hits is not None else []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "provider" and isinstance(v, str) and v.strip().lower() in ("mock", "sandbox"):
                hits.append(f"{path}.provider = {v!r}")
            if k == "synthetic" and v is True:
                hits.append(f"{path}.synthetic = true (mock/test record in real state)")
            find_mock_markers(v, f"{path}.{k}", hits)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            find_mock_markers(v, f"{path}[{i}]", hits)
    elif isinstance(obj, str):
        for marker in MOCK_MARKERS:
            if marker in obj:
                hits.append(f"{path} contains {marker!r}")
    return hits


def reject_mock_content(data: Any, *, where: str) -> None:
    """Fail closed: refuse to persist any mock/sandbox content into real state."""
    hits = find_mock_markers(data)
    if hits:
        raise StateContaminationError(f"{where}: mock/sandbox content rejected at {hits[:5]}")


def _load_json(path) -> Any:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def assert_course_isolation(course_path, course_id: str | None = None) -> None:
    """Verify a course directory belongs to exactly one course: the manifest
    course_id must match the directory name and every per-course payload must carry
    the same course_id. Knowledge content is never shared across courses."""
    from .course import load_manifest

    manifest = load_manifest(course_path)
    if course_id is not None and manifest.course_id != course_id:
        raise StateContaminationError(
            f"course dir {course_path}: manifest.course_id={manifest.course_id!r} "
            f"does not match expected {course_id!r}"
        )
    for filename in (
        "document_index.json",
        "knowledge_graph.json",
        "exam_model.json",
        "student_state.json",
        "wrongbook.json",
        "evidence_store.json",
        "terminology_map.json",
    ):
        data = _load_json(course_path / filename)
        if data and data.get("course_id") not in (None, manifest.course_id):
            raise StateContaminationError(
                f"{course_path / filename}: references foreign course_id "
                f"{data.get('course_id')!r}"
            )
