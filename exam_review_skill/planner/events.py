from __future__ import annotations

from pathlib import Path

from ..models import ReplanEvent
from ..state import course as course_mod
from ..state import workspace as workspace_mod


VALID_EVENTS = {
    "quiz_completed",
    "wrong_answer",
    "topic_mastered",
    "new_material",
    "new_past_exam",
    "exam_rescheduled",
    "hours_changed",
    "target_changed",
    "course_completed",
}


def record_replan_event(
    workspace_root: Path,
    event: ReplanEvent,
    *,
    persist: bool = True,
) -> ReplanEvent:
    """Record a dynamic event that should trigger re-planning. Applies immediate
    state effects (e.g. exam reschedule updates the calendar, course_completed
    marks the manifest/course status and releases its future time)."""
    if event.event_type not in VALID_EVENTS:
        raise ValueError(f"unknown replan event: {event.event_type}")

    if event.event_type == "exam_rescheduled" and event.course_id:
        new_date = event.detail.get("new_date")
        if new_date:
            from ..orchestrator.calendar import upsert_entry

            calendar = workspace_mod.load_exam_calendar(workspace_root)
            upsert_entry(calendar, course_id=event.course_id, exam_date=new_date)
            workspace_mod.save_exam_calendar(workspace_root, calendar)
            # also update the manifest so the scheduler sees the change
            course_path = course_mod.course_dir(workspace_root, event.course_id)
            if (course_path / "course_manifest.json").exists():
                course_mod.update_manifest(course_path, exam_date=new_date)

    if event.event_type == "course_completed" and event.course_id:
        course_path = course_mod.course_dir(workspace_root, event.course_id)
        if (course_path / "course_manifest.json").exists():
            course_mod.update_manifest(course_path, status="completed")
        from ..orchestrator.calendar import mark_completed

        calendar = workspace_mod.load_exam_calendar(workspace_root)
        mark_completed(calendar, event.course_id)
        workspace_mod.save_exam_calendar(workspace_root, calendar)

    if event.event_type == "target_changed" and event.course_id:
        score = event.detail.get("target_score")
        if score is not None:
            course_path = course_mod.course_dir(workspace_root, event.course_id)
            if (course_path / "course_manifest.json").exists():
                course_mod.update_manifest(course_path, target_score=int(score))

    if event.event_type == "hours_changed":
        hours = event.detail.get("daily_total_hours")
        if hours is not None:
            state = workspace_mod.load_workspace_state(workspace_root)
            state.daily_total_hours = float(hours)
            workspace_mod.save_workspace_state(workspace_root, state)

    if persist:
        _append_event_log(workspace_root, event)
    return event


def _append_event_log(workspace_root: Path, event: ReplanEvent) -> None:
    from ..models import to_dict

    log_path = workspace_root / "replan_events.jsonl"
    with open(log_path, "a", encoding="utf-8") as handle:
        handle.write(__import__("json").dumps(to_dict(event), ensure_ascii=False) + "\n")
