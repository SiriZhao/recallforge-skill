from __future__ import annotations

from datetime import date, timedelta

from ..models import RetrySchedule, StudentModel
from .diagnosis import DIAGNOSIS_TAXONOMY


SEVERITY_BY_DIAGNOSIS = {
    "prerequisite_gap": 3,
    "concept_gap": 3,
    "formula_recall": 2,
    "condition_misread": 2,
    "calculation_error": 2,
    "algebra_error": 2,
    "sign_error": 2,
    "unit_error": 2,
    "reasoning_jump": 2,
    "question_misread": 1,
    "method_selection": 2,
    "memory_failure": 1,
    "careless_error": 1,
    "unknown": 2,
}


def schedule_retry(
    *,
    topic_id: str,
    diagnosis: str,
    repeat_count: int = 0,
    mastery: str | None = None,
    days_to_exam: int | None = None,
    today: date | None = None,
) -> RetrySchedule:
    """Schedule the next review for a wrong topic.

    Factors: mistake type (severity), repeat count (repeated errors sooner),
    mastery (near-proficient spaces out), exam proximity (urgent exams pull in).
    """
    today = today or date.today()
    severity = SEVERITY_BY_DIAGNOSIS.get(diagnosis, 2)
    interval = {3: 1, 2: 2, 1: 3}.get(severity, 2)
    if repeat_count >= 2:
        interval = 1  # repeated errors: retry tomorrow
    if mastery == "proficient":
        interval = max(interval, 3)
    if days_to_exam is not None and days_to_exam <= 3:
        interval = min(interval, 1)  # exam-close: retry immediately

    priority = "S" if severity == 3 else "A" if severity == 2 else "B"
    reason = (
        f"diagnosis={diagnosis} (severity {severity}), repeats={repeat_count}, "
        f"mastery={mastery}, days_to_exam={days_to_exam}"
    )
    return RetrySchedule(
        topic_id=topic_id,
        next_review_days=interval,
        next_review_date=(today + timedelta(days=interval)).isoformat(),
        reason=reason,
        priority=priority,
    )
