from __future__ import annotations

from datetime import date, datetime

from ..models import ExamCalendar, ExamCalendarEntry

VALID_STATUSES = ("scheduled", "completed", "canceled")


def upsert_entry(
    calendar: ExamCalendar,
    *,
    course_id: str,
    exam_date: str | None = None,
    exam_time: str | None = None,
    status: str = "scheduled",
    weight: float = 1.0,
    note: str | None = None,
) -> ExamCalendarEntry:
    """Add or replace the active entry for a course.

    Supports: no exam date (exam_date=None), two exams on the same day (two courses
    or two entries), consecutive multi-day exams, and completed exams (kept as
    history while a new active entry may replace them).
    """
    if status not in VALID_STATUSES:
        raise ValueError(f"invalid exam status {status!r}; expected {VALID_STATUSES}")
    if exam_date is not None:
        datetime.fromisoformat(exam_date)  # validates ISO date; raises on garbage
    entry = ExamCalendarEntry(
        course_id=course_id,
        exam_date=exam_date,
        exam_time=exam_time,
        status=status,
        weight=weight,
        note=note,
    )
    # replace only the active (scheduled/canceled) entry for this course; keep completed history
    kept = [e for e in calendar.entries if e.course_id != course_id or e.status == "completed"]
    calendar.entries = kept + [entry]
    return entry


def remove_entry(calendar: ExamCalendar, course_id: str) -> None:
    calendar.entries = [e for e in calendar.entries if e.course_id != course_id]


def mark_completed(calendar: ExamCalendar, course_id: str) -> None:
    for entry in calendar.entries:
        if entry.course_id == course_id and entry.status != "completed":
            entry.status = "completed"


def active_entries(calendar: ExamCalendar) -> list[ExamCalendarEntry]:
    return [e for e in calendar.entries if e.status != "completed"]


def days_to_exam(entry: ExamCalendarEntry, today: date | None = None) -> int | None:
    """Days from `today` until the exam. None when there is no exam date or the
    exam is completed. Two exams on the same day naturally both yield 0."""
    if entry.exam_date is None or entry.status == "completed":
        return None
    today = today or date.today()
    try:
        exam = datetime.fromisoformat(entry.exam_date).date()
    except (TypeError, ValueError):
        return None
    return max(0, (exam - today).days)


def days_between(exam_date: str, today: date) -> int | None:
    try:
        exam = datetime.fromisoformat(exam_date).date()
    except (TypeError, ValueError):
        return None
    return max(0, (exam - today).days)
