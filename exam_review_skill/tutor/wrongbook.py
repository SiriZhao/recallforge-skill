from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from ..models import GradingResult, QuizQuestion, StudentModel
from ..state import course as course_mod
from ..state.isolation import StateContaminationError, find_mock_markers
from .diagnosis import diagnose_wrong_answer


def add_wrongbook_entry(
    *,
    workspace_root: Path,
    course_id: str,
    question: QuizQuestion,
    user_answer: str,
    grading: GradingResult,
    diagnosis: object,
    student: StudentModel,
) -> dict:
    """Add a real wrong answer to the wrongbook. The entry records the diagnosis so
    it can drive mastery, risk, planner, future quizzes, and cram."""
    if grading.correct:
        raise ValueError("wrongbook entries require an incorrect answer")
    if find_mock_markers({"user_answer": user_answer, "question_text": question.question_text}):
        raise StateContaminationError("refusing to record fabricated wrongbook content")

    severity = getattr(diagnosis, "severity", 2)
    next_days = _retry_interval(severity, repeat_count=0, mastery=student.topics.get(question.topic_id))
    entry = {
        "question_id": question.question_id,
        "question_text": question.question_text,
        "user_answer": user_answer,
        "correct_answer": question.correct_answer,
        "topic_id": question.topic_id,
        "topic_name": question.topic_name,
        "level": question.level,
        "wrong_reason": getattr(diagnosis, "explanation", ""),
        "diagnosis": getattr(diagnosis, "diagnosis", "unknown"),
        "severity": severity,
        "prerequisite_fix": getattr(diagnosis, "prerequisite_fix", []),
        "next_review_date": (date.today() + timedelta(days=next_days)).isoformat(),
        "retry_count": 0,
        "date": date.today().isoformat(),
        "evidence_refs": list(question.evidence_refs),
    }
    course_path = course_mod.course_dir(workspace_root, course_id)
    wrongbook = course_mod.load_course_json(course_path, "wrongbook.json", {}) or {}
    entries = wrongbook.get("entries", []) or []
    entries.append(entry)
    wrongbook["entries"] = entries
    course_mod._write_json(course_path / "wrongbook.json", wrongbook)
    return entry


def load_wrongbook(workspace_root: Path, course_id: str) -> list[dict]:
    course_path = course_mod.course_dir(workspace_root, course_id)
    data = course_mod.load_course_json(course_path, "wrongbook.json", {}) or {}
    return data.get("entries", []) or []


def _retry_interval(severity: int, repeat_count: int, mastery) -> int:
    """Retry scheduling: mistake severity + repeat count + mastery -> days."""
    base = {1: 1, 2: 2, 3: 3}.get(severity, 2)
    repeat_bonus = min(3, repeat_count)  # repeated errors retry sooner
    interval = max(1, base - repeat_bonus)
    if mastery and mastery.mastery == "proficient":
        interval = max(interval, 3)  # near-mastery topics space further out
    return interval


def update_retry_after_attempt(
    workspace_root: Path,
    course_id: str,
    topic_id: str,
    *,
    correct: bool,
    diagnosis: object | None = None,
) -> list[dict]:
    """Update wrongbook retry scheduling after a re-attempt."""
    entries = load_wrongbook(workspace_root, course_id)
    updated = False
    for entry in entries:
        if entry.get("topic_id") != topic_id:
            continue
        entry["retry_count"] = entry.get("retry_count", 0) + 1
        if correct:
            entry["resolved"] = True
            entry["resolved_date"] = date.today().isoformat()
        else:
            entry["resolved"] = False
            entry["next_review_date"] = (
                date.today() + timedelta(days=_retry_interval(entry.get("severity", 2), entry.get("retry_count", 1), None))
            ).isoformat()
            if diagnosis:
                entry["diagnosis"] = getattr(diagnosis, "diagnosis", entry.get("diagnosis"))
        updated = True
    if updated:
        course_path = course_mod.course_dir(workspace_root, course_id)
        course_mod._write_json(
            course_path / "wrongbook.json",
            {"course_id": course_id, "entries": entries, "updated_at": date.today().isoformat()},
        )
    return entries
