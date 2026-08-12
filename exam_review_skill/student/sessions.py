from __future__ import annotations

from datetime import date
from pathlib import Path

from ..models import StudentModel, TopicMastery, _now_iso
from ..state.isolation import StateContaminationError, find_mock_markers
from .mastery import compute_mastery


MISTAKE_TYPES = {
    "concept_confusion": "概念混淆",
    "formula_error": "公式记错",
    "condition_omitted": "条件遗漏",
    "unit_error": "单位错误",
    "misread": "审题错误",
    "step_omission": "步骤缺失",
    "calculation_error": "计算错误",
    "recall_weakness": "背诵不熟",
    "transfer_failure": "不会迁移",
}


class AnswerResult:
    """One graded answer outcome (real data, never fabricated)."""

    def __init__(
        self,
        *,
        topic_id: str,
        correct: bool,
        difficulty: int = 2,
        used_hint: bool = False,
        mistake_type: str | None = None,
        question_type: str = "short_answer",
        is_new_form: bool = False,
    ):
        self.topic_id = topic_id
        self.correct = correct
        self.difficulty = difficulty
        self.used_hint = used_hint
        self.mistake_type = mistake_type
        self.question_type = question_type
        self.is_new_form = is_new_form


def _get_or_create(model: StudentModel, topic_id: str) -> TopicMastery:
    if topic_id not in model.topics:
        model.topics[topic_id] = TopicMastery(topic_id=topic_id)
    return model.topics[topic_id]


def record_answer(model: StudentModel, answer: AnswerResult, *, today: str | None = None) -> StudentModel:
    """Record one real answer into the student model. This is the ONLY path that
    mutates mastery. Rejects fabricated/mock answers."""
    if not answer.topic_id:
        raise ValueError("answer requires a topic_id")
    # real-only: refuse to persist mock/synthetic answers into real state
    if answer.correct not in (True, False):
        raise StateContaminationError("answer.correct must be a real boolean")
    today = today or date.today().isoformat()

    topic = _get_or_create(model, answer.topic_id)
    topic.questions_attempted += 1
    if answer.correct:
        topic.wrong_count += 0  # unchanged
    else:
        topic.wrong_count += 1
        if answer.mistake_type:
            topic.mistake_types.append(answer.mistake_type)

    # difficulty coverage
    key = str(answer.difficulty)
    topic.difficulty_coverage[key] = topic.difficulty_coverage.get(key, 0) + 1
    # question type coverage
    topic.question_type_coverage[answer.question_type] = (
        topic.question_type_coverage.get(answer.question_type, 0) + 1
    )
    # transfer performance
    if answer.is_new_form:
        topic.transfer_performance["new_form"] = topic.transfer_performance.get("new_form", 0) + 1
        if answer.correct:
            topic.transfer_performance["new_form_correct"] = (
                topic.transfer_performance.get("new_form_correct", 0) + 1
            )
    else:
        topic.transfer_performance["same_form"] = topic.transfer_performance.get("same_form", 0) + 1

    # recompute accuracy (correct / attempted)
    correct_count = topic.questions_attempted - topic.wrong_count
    topic.accuracy = correct_count / topic.questions_attempted

    # hint dependency: fraction of correct answers that used a hint
    hints_used = topic.difficulty_coverage.get("hints", 0)
    if answer.used_hint and answer.correct:
        hints_used += 1
    topic.difficulty_coverage["hints"] = hints_used
    correct_with_hints = hints_used
    total_correct = max(1, correct_count)
    topic.hint_dependency = min(1.0, correct_with_hints / total_correct)

    topic.last_reviewed = today
    topic.updated_at = _now_iso()
    compute_mastery(topic)
    model.review_history.append(
        {
            "date": today,
            "topic_id": answer.topic_id,
            "correct": answer.correct,
            "difficulty": answer.difficulty,
            "used_hint": answer.used_hint,
            "question_type": answer.question_type,
            "is_new_form": answer.is_new_form,
        }
    )
    model.last_updated = today
    return model


def record_wrongbook_entry(model: StudentModel, answer: AnswerResult, *, question_text: str, correct_answer: str, user_answer: str) -> dict:
    """Record a wrong answer into the wrongbook (only real wrong answers)."""
    if answer.correct:
        raise ValueError("wrongbook entries require an incorrect answer")
    if find_mock_markers({"user_answer": user_answer, "question_text": question_text}):
        raise StateContaminationError("refusing to record fabricated wrongbook content")
    return {
        "question_text": question_text,
        "user_answer": user_answer,
        "correct_answer": correct_answer,
        "topic_id": answer.topic_id,
        "wrong_reason": MISTAKE_TYPES.get(answer.mistake_type or "", "需确认"),
        "trap_type": answer.mistake_type or "unknown",
        "date": date.today().isoformat(),
    }
