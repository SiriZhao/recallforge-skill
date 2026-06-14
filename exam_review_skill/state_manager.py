from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any

from .models import StudentState


def read_json(path: Path, default: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default
    return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_student_state(path: Path | None, course_name: str = "课程", target_score: int = 80, exam_date: str | None = None, daily_hours: float = 4) -> StudentState:
    data = read_json(path, {}) if path else {}
    if data:
        return StudentState(**{**data, "last_updated": date.today().isoformat()})
    return StudentState(course_name=course_name, target_score=target_score, exam_date=exam_date, daily_hours=daily_hours)


def save_student_state(path: Path, state: StudentState) -> None:
    state.last_updated = date.today().isoformat()
    write_json(path, asdict(state))


def update_history(state: StudentState, event: str, detail: dict | None = None) -> None:
    state.review_history.append({"date": date.today().isoformat(), "event": event, "detail": detail or {}})
