from __future__ import annotations

from pathlib import Path

import pytest

from recallforge.models import ReplanEvent
from recallforge.planner.events import record_replan_event
from recallforge.planner.nl import parse_command
from recallforge.planner.orchestrator import generate_daily_plan_v4
from recallforge.state import course as course_mod
from recallforge.state import workspace as workspace_mod

from planner_fixtures import build_scenario_workspace


def test_exam_reschedule_event_updates_calendar(tmp_path: Path):
    root = build_scenario_workspace(tmp_path / "ws")
    record_replan_event(
        root,
        ReplanEvent(event_type="exam_rescheduled", course_id="botany", detail={"new_date": "2026-06-21"}),
    )
    calendar = workspace_mod.load_exam_calendar(root)
    entry = next(e for e in calendar.entries if e.course_id == "botany")
    assert entry.exam_date == "2026-06-21"
    manifest = course_mod.load_manifest(course_mod.course_dir(root, "botany"))
    assert manifest.exam_date == "2026-06-21"
    # event log persisted
    assert (root / "replan_events.jsonl").exists()


def test_course_completed_releases_time(tmp_path: Path):
    """Exam day: course completed -> its future time is released to other courses."""
    root = build_scenario_workspace(tmp_path / "ws")
    before = generate_daily_plan_v4(root, "2026-06-18")
    record_replan_event(root, ReplanEvent(event_type="course_completed", course_id="calculus"))
    manifest = course_mod.load_manifest(course_mod.course_dir(root, "calculus"))
    assert manifest.status == "completed"
    after = generate_daily_plan_v4(root, "2026-06-18")
    assert "calculus" not in after.allocation
    assert "calculus" not in {b.course_id for b in after.blocks}
    # freed time redistributed to remaining courses
    assert after.allocation["botany"] > before.allocation["botany"]


def test_target_and_hours_events(tmp_path: Path):
    root = build_scenario_workspace(tmp_path / "ws")
    record_replan_event(
        root,
        ReplanEvent(event_type="target_changed", course_id="calculus", detail={"target_score": 60}),
    )
    manifest = course_mod.load_manifest(course_mod.course_dir(root, "calculus"))
    assert manifest.target_score == 60
    record_replan_event(
        root,
        ReplanEvent(event_type="hours_changed", detail={"daily_total_hours": 4.0}),
    )
    state = workspace_mod.load_workspace_state(root)
    assert state.daily_total_hours == 4.0


def test_invalid_event_rejected(tmp_path: Path):
    root = build_scenario_workspace(tmp_path / "ws")
    with pytest.raises(ValueError):
        record_replan_event(root, ReplanEvent(event_type="bogus_event"))


def test_nl_zh_commands():
    assert parse_command("今天不想学植物学").action == "skip"
    assert parse_command("今天不想学植物学").course_id == "botany"
    c = parse_command("微积分只求及格")
    assert c.action == "change_target" and c.course_id == "calculus" and c.value == 60
    c = parse_command("明天只有3小时")
    assert c.action == "change_hours" and c.value == 3.0
    c = parse_command("有机化学考试提前了")
    assert c.action == "schedule" and c.course_id == "organic-chemistry"
    assert parse_command("今天学什么").action == "none"


def test_nl_en_commands():
    c = parse_command("I don't want to study botany today")
    assert c.action == "skip" and c.course_id == "botany"
    c = parse_command("skip organic chemistry")
    assert c.action == "skip" and c.course_id == "organic-chemistry"
    c = parse_command("I only need to pass calculus")
    assert c.action == "change_target" and c.course_id == "calculus" and c.value == 60
    c = parse_command("I only have three hours tomorrow")
    assert c.action == "change_hours" and c.value == 3.0
    c = parse_command("My probability exam moved up")
    assert c.action == "schedule" and c.course_id == "probability"
    assert parse_command("What should I study today?").action == "none"
