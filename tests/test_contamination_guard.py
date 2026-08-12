from __future__ import annotations

from pathlib import Path

import pytest

from exam_review_skill.models import CourseWrongbook, GlobalStudyPlan, PlanBlock
from exam_review_skill.state import course as course_mod
from exam_review_skill.state import workspace as workspace_mod
from exam_review_skill.state.isolation import (
    StateContaminationError,
    find_mock_markers,
    reject_mock_content,
)


def test_marker_detection():
    data = {
        "course_id": "botany",
        "entries": [
            {"question_id": "Q1", "user_answer": "示例：未作答", "trap_type": "概念不清"},
        ],
    }
    hits = find_mock_markers(data)
    assert hits
    with pytest.raises(StateContaminationError):
        reject_mock_content(data, where="wrongbook.json")


def test_mock_provider_marker_rejected():
    data = {"course_id": "x", "provider": "mock", "notes": ["Mock provider 生成的规则题"]}
    with pytest.raises(StateContaminationError):
        reject_mock_content(data, where="student_state.json")


def test_fabricated_wrongbook_entry_cannot_be_written(tmp_path: Path):
    root = tmp_path / "ws"
    workspace_mod.create_workspace(root)
    workspace_mod.add_course_to_workspace(root, course_id="botany", course_name="植物学")
    cdir = course_mod.course_dir(root, "botany")
    fabricated = CourseWrongbook(
        course_id="botany",
        entries=[{"question_id": "Q1", "user_answer": "示例：未作答"}],
    )
    from dataclasses import asdict

    with pytest.raises(StateContaminationError):
        reject_mock_content(asdict(fabricated), where="wrongbook.json")


def test_clean_state_writes_are_allowed(tmp_path: Path):
    root = tmp_path / "ws"
    workspace_mod.create_workspace(root)
    workspace_mod.add_course_to_workspace(root, course_id="botany", course_name="植物学")
    # a genuinely clean (empty) wrongbook is fine
    cdir = course_mod.course_dir(root, "botany")
    clean = CourseWrongbook(course_id="botany", entries=[])
    from dataclasses import asdict

    course_mod._write_json(cdir / "wrongbook.json", asdict(clean))
    assert find_mock_markers(asdict(clean)) == []


def test_global_plan_rejects_mock_rationale(tmp_path: Path):
    root = tmp_path / "ws"
    workspace_mod.create_workspace(root)
    bad_plan = GlobalStudyPlan(
        workspace_id="WS-X",
        date="2026-06-18",
        total_hours=6.0,
        blocks=[PlanBlock("B001", "botany", "09:00", "10:00", "study",
                          why="Mock provider 生成的规则题", risk="r", goal="g", done_when="d")],
    )
    from dataclasses import asdict

    with pytest.raises(StateContaminationError):
        reject_mock_content(asdict(bad_plan), where="global_study_plan.json")
