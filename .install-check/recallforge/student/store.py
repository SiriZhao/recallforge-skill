from __future__ import annotations

import json
from pathlib import Path

from ..models import StudentModel, TopicMastery, _now_iso
from ..state.course import course_dir
from ..state.isolation import reject_mock_content
from .mastery import sync_mastery_levels


def load_student_model(workspace_root: Path, course_id: str) -> StudentModel:
    """Load the per-course student model. Falls back to the Round-1/3 flat
    `mastery` dict shape when present, upgrading it to the v4 model."""
    course_path = course_dir(workspace_root, course_id)
    path = course_path / "student_state.json"
    data = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            data = {}

    model = StudentModel(course_id=course_id)
    model.student_id = data.get("student_id", "student-default")
    model.diagnostic_completed = bool(data.get("diagnostic_completed", False))
    model.review_history = data.get("review_history", []) or []
    model.weak_points = data.get("weak_points", []) or []
    model.strong_points = data.get("strong_points", []) or []
    model.wrong_patterns = data.get("wrong_patterns", []) or []
    model.last_updated = data.get("last_updated", "")

    # v4 shape: topics: {topic_id: {...}}
    topics = data.get("topics", {}) or {}
    # v1/v3 shape: mastery: {topic_id: {"level": ...}} -> upgrade to v4
    legacy_mastery = data.get("mastery", {}) or {}
    for tid, raw in topics.items():
        if isinstance(raw, dict):
            model.topics[tid] = TopicMastery(**{k: v for k, v in raw.items() if k != "topic_id"}, topic_id=tid)
    for tid, raw in legacy_mastery.items():
        if tid not in model.topics and isinstance(raw, dict):
            level = raw.get("level", "unknown")
            tm = TopicMastery(topic_id=tid, mastery=level if level in ("unknown", "novice", "developing", "proficient") else "unknown")
            tm.questions_attempted = int(raw.get("attempts", 0) or 0)
            tm.accuracy = raw.get("accuracy")
            model.topics[tid] = tm
    return sync_mastery_levels(model)


def save_student_model(workspace_root: Path, course_id: str, model: StudentModel) -> None:
    """Persist the student model. Includes a `mastery` compatibility view so the
    Round-3 risk radar and orchestrator keep working unchanged."""
    model.last_updated = _now_iso()
    state = model.to_state()
    # compatibility view for Round 3 risk radar: mastery[topic_id].level
    state["mastery"] = {
        tid: {"level": tm.mastery, "mastery_score": tm.mastery_score}
        for tid, tm in model.topics.items()
    }
    reject_mock_content(state, where=f"student_state[{course_id}]")
    course_path = course_dir(workspace_root, course_id)
    (course_path / "student_state.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )
