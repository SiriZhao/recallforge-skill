from __future__ import annotations

import json
import re
from dataclasses import asdict
from pathlib import Path
from typing import Any

from ..models import (
    CourseManifest,
    CourseStudentState,
    CourseStudyPlan,
    CourseWrongbook,
    DocumentIndex,
    ExamModel,
    KnowledgeGraph,
    TerminologyMapState,
    _now_iso,
)
from .isolation import reject_mock_content

COURSE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")

COURSE_FILES = (
    "course_manifest.json",
    "document_index.json",
    "knowledge_graph.json",
    "exam_model.json",
    "student_state.json",
    "wrongbook.json",
    "evidence_store.json",
    "risk_radar.json",
    "conflicts.json",
    "coverage_report.json",
    "study_plan.json",
    "sessions.jsonl",
    "terminology_map.json",
)


def validate_course_id(course_id: str) -> None:
    if not COURSE_ID_RE.match(course_id):
        raise ValueError(
            f"invalid course_id {course_id!r}: use lowercase letters, digits, and hyphens"
        )


def course_dir(workspace_root: Path, course_id: str) -> Path:
    return Path(workspace_root) / "courses" / course_id


def _write_json(path: Path, data: Any) -> None:
    reject_mock_content(data, where=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_json(path: Path, default: Any) -> Any:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default
    return default


def create_course(
    workspace_root: Path,
    *,
    course_id: str,
    course_name: str,
    course_name_localized: dict[str, str] | None = None,
    source_languages: list[str] | None = None,
    exam_date: str | None = None,
    exam_time: str | None = None,
    target_score: int = 80,
    current_estimated_score: int | None = None,
    daily_preference: float = 1.0,
    importance_override: float | None = None,
    status: str = "active",
) -> Path:
    """Create a fully isolated course directory with all per-course state files.
    Empty structures are real defaults (no fabricated knowledge content)."""
    validate_course_id(course_id)
    root = course_dir(workspace_root, course_id)
    if (root / "course_manifest.json").exists():
        raise FileExistsError(f"course already exists: {course_id}")
    manifest = CourseManifest(
        course_id=course_id,
        course_name=course_name,
        course_name_localized=course_name_localized or {},
        source_languages=source_languages or [],
        exam_date=exam_date,
        exam_time=exam_time,
        target_score=target_score,
        current_estimated_score=current_estimated_score,
        daily_preference=daily_preference,
        importance_override=importance_override,
        status=status,
    )
    _write_json(root / "course_manifest.json", asdict(manifest))
    _write_json(root / "document_index.json", asdict(DocumentIndex(course_id=course_id)))
    _write_json(
        root / "knowledge_graph.json",
        {"course_id": course_id, "topics": [], "edges": [], "updated_at": _now_iso()},
    )
    _write_json(
        root / "exam_model.json",
        {
            "course_id": course_id,
            "exam_points": [],
            "past_exam_sets": [],
            "teacher_style": {},
            "evidence_weights": {},
            "updated_at": _now_iso(),
        },
    )
    _write_json(
        root / "student_state.json",
        {
            "student_id": "student-default",
            "course_id": course_id,
            "topics": {},
            "weak_points": [],
            "strong_points": [],
            "wrong_patterns": [],
            "review_history": [],
            "diagnostic_completed": False,
            "mastery": {},
            "last_updated": _now_iso(),
        },
    )
    _write_json(root / "wrongbook.json", asdict(CourseWrongbook(course_id=course_id)))
    _write_json(
        root / "evidence_store.json",
        {"course_id": course_id, "documents": {}, "records": [], "updated_at": _now_iso()},
    )
    _write_json(
        root / "risk_radar.json",
        {"course_id": course_id, "items": [], "updated_at": _now_iso()},
    )
    _write_json(
        root / "conflicts.json",
        {"course_id": course_id, "conflicts": [], "updated_at": _now_iso()},
    )
    _write_json(
        root / "coverage_report.json",
        {"course_id": course_id, "verdict": "insufficient", "generated_at": _now_iso()},
    )
    _write_json(root / "study_plan.json", asdict(CourseStudyPlan(course_id=course_id)))
    _write_json(
        root / "terminology_map.json",
        asdict(TerminologyMapState(course_id=course_id)),
    )
    (root / "sessions.jsonl").write_text("", encoding="utf-8")
    return root


def load_manifest(course_path: Path) -> CourseManifest:
    data = _read_json(course_path / "course_manifest.json", {})
    if not data:
        raise FileNotFoundError(f"no course manifest at {course_path}")
    return CourseManifest(**data)


def save_manifest(course_path: Path, manifest: CourseManifest) -> None:
    manifest.updated_at = _now_iso()
    _write_json(course_path / "course_manifest.json", asdict(manifest))


def update_manifest(course_path: Path, **changes) -> CourseManifest:
    manifest = load_manifest(course_path)
    for key, value in changes.items():
        if not hasattr(manifest, key):
            raise ValueError(f"unknown manifest field: {key}")
        setattr(manifest, key, value)
    save_manifest(course_path, manifest)
    return manifest


def load_course_json(course_path: Path, filename: str, default: Any) -> Any:
    return _read_json(course_path / filename, default)
