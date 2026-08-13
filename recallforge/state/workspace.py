from __future__ import annotations

import json
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any

from ..models import (
    DayOverride,
    ExamCalendar,
    ExamCalendarEntry,
    GlobalStudyPlan,
    PlanBlock,
    WorkspaceState,
    _now_iso,
)
from .isolation import reject_mock_content

WORKSPACE_FILES = (
    "workspace_state.json",
    "exam_calendar.json",
    "global_study_plan.json",
    "overrides.json",
)
COURSES_DIR = "courses"


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


def create_workspace(
    root: Path,
    *,
    user_locale: str = "zh-CN",
    content_language: str = "auto",
    output_language: str | None = None,
    daily_total_hours: float = 6.0,
) -> WorkspaceState:
    """Create a workspace with an empty exam calendar and override store.
    Raises FileExistsError if already initialized (never silently overwrites)."""
    root = Path(root)
    if (root / "workspace_state.json").exists():
        raise FileExistsError(f"workspace already initialized at {root}")
    state = WorkspaceState(
        workspace_id=f"WS-{uuid.uuid4().hex[:12].upper()}",
        user_locale=user_locale,
        content_language=content_language,
        output_language=output_language or user_locale,
        daily_total_hours=daily_total_hours,
    )
    _write_json(root / "workspace_state.json", asdict(state))
    _write_json(root / "exam_calendar.json", asdict(ExamCalendar(workspace_id=state.workspace_id)))
    _write_json(
        root / "global_study_plan.json",
        asdict(GlobalStudyPlan(workspace_id=state.workspace_id, date="", total_hours=0.0)),
    )
    _write_json(
        root / "overrides.json",
        {"workspace_id": state.workspace_id, "overrides": [], "updated_at": _now_iso()},
    )
    return state


def load_workspace_state(root: Path) -> WorkspaceState:
    data = _read_json(root / "workspace_state.json", {})
    if not data:
        raise FileNotFoundError(f"no workspace at {root} (run 'workspace init' first)")
    return WorkspaceState(**data)


def save_workspace_state(root: Path, state: WorkspaceState) -> None:
    state.updated_at = _now_iso()
    _write_json(root / "workspace_state.json", asdict(state))


def load_exam_calendar(root: Path) -> ExamCalendar:
    data = _read_json(root / "exam_calendar.json", {})
    entries = [ExamCalendarEntry(**e) for e in data.get("entries", [])]
    return ExamCalendar(
        workspace_id=data.get("workspace_id", ""),
        entries=entries,
        updated_at=data.get("updated_at", _now_iso()),
    )


def save_exam_calendar(root: Path, calendar: ExamCalendar) -> None:
    calendar.updated_at = _now_iso()
    _write_json(root / "exam_calendar.json", asdict(calendar))


def load_global_plan(root: Path, plan_date: str) -> GlobalStudyPlan | None:
    data = _read_json(root / "global_study_plan.json", None)
    if not data or data.get("date") != plan_date:
        return None
    return GlobalStudyPlan(
        workspace_id=data.get("workspace_id", ""),
        date=data.get("date", plan_date),
        total_hours=data.get("total_hours", 0.0),
        blocks=[PlanBlock(**b) for b in data.get("blocks", [])],
        allocation=data.get("allocation", {}),
        notes=data.get("notes", []),
        overrides_applied=data.get("overrides_applied", []),
        generated_at=data.get("generated_at", _now_iso()),
    )


def save_global_plan(root: Path, plan: GlobalStudyPlan) -> None:
    _write_json(root / "global_study_plan.json", asdict(plan))


def load_overrides(root: Path) -> list[DayOverride]:
    data = _read_json(root / "overrides.json", {})
    return [DayOverride(**o) for o in data.get("overrides", [])]


def save_overrides(root: Path, overrides: list[DayOverride]) -> None:
    state = load_workspace_state(root)
    _write_json(
        root / "overrides.json",
        {
            "workspace_id": state.workspace_id,
            "overrides": [asdict(o) for o in overrides],
            "updated_at": _now_iso(),
        },
    )


def upsert_override(root: Path, override: DayOverride) -> list[DayOverride]:
    overrides = [o for o in load_overrides(root) if o.date != override.date]
    overrides.append(override)
    save_overrides(root, overrides)
    return overrides


def override_for(root: Path, plan_date: str) -> DayOverride | None:
    for o in load_overrides(root):
        if o.date == plan_date:
            return o
    return None


def add_course_to_workspace(
    root: Path,
    *,
    course_id: str,
    course_name: str,
    **manifest_kwargs,
) -> Path:
    from .course import create_course

    state = load_workspace_state(root)
    if course_id in state.courses:
        raise ValueError(f"course already exists: {course_id}")
    course_path = create_course(
        root, course_id=course_id, course_name=course_name, **manifest_kwargs
    )
    state.courses.append(course_id)
    state.courses.sort()
    save_workspace_state(root, state)
    return course_path


def list_courses(root: Path) -> list[str]:
    return list(load_workspace_state(root).courses)
