from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import pytest

from recallforge.models import DayOverride, ExamCalendar
from recallforge.orchestrator.calendar import (
    active_entries,
    days_to_exam,
    mark_completed,
    remove_entry,
    upsert_entry,
)
from recallforge.state import course as course_mod
from recallforge.state import workspace as workspace_mod
from recallforge.state.course import COURSE_FILES
from recallforge.state.isolation import (
    StateContaminationError,
    assert_course_isolation,
    reject_mock_content,
)
from recallforge.state.workspace import WORKSPACE_FILES


def _build_workspace(root: Path) -> Path:
    workspace_mod.create_workspace(root, user_locale="zh-CN", daily_total_hours=6.0)
    workspace_mod.add_course_to_workspace(
        root, course_id="probability", course_name="概率论",
        course_name_localized={"zh-CN": "概率论", "en-US": "Probability"},
        source_languages=["zh-CN"], exam_date="2026-06-23", target_score=85,
    )
    workspace_mod.add_course_to_workspace(
        root, course_id="organic-chemistry", course_name="有机化学",
        source_languages=["zh-CN"], exam_date="2026-06-20", target_score=80,
    )
    workspace_mod.add_course_to_workspace(
        root, course_id="botany", course_name="植物学", target_score=70,
    )
    workspace_mod.add_course_to_workspace(
        root, course_id="calculus", course_name="微积分", exam_date="2026-06-21", target_score=60,
    )
    return root


def test_multi_course_workspace_files(tmp_path: Path):
    root = _build_workspace(tmp_path / "ws")
    for filename in WORKSPACE_FILES:
        assert (root / filename).exists(), filename
    assert workspace_mod.list_courses(root) == [
        "botany", "calculus", "organic-chemistry", "probability",
    ]
    state = workspace_mod.load_workspace_state(root)
    assert state.workspace_id.startswith("WS-")
    assert state.daily_total_hours == 6.0
    assert state.user_locale == "zh-CN"


def test_each_course_has_all_isolated_files(tmp_path: Path):
    root = _build_workspace(tmp_path / "ws")
    for cid in workspace_mod.list_courses(root):
        cdir = course_mod.course_dir(root, cid)
        for filename in COURSE_FILES:
            assert (cdir / filename).exists(), f"{cid}/{filename}"
        # every course directory is self-contained
        assert_course_isolation(cdir, course_id=cid)


def test_course_isolation_rejects_foreign_course_id(tmp_path: Path):
    root = _build_workspace(tmp_path / "ws")
    cdir = course_mod.course_dir(root, "botany")
    # tamper: inject a foreign course_id into the knowledge graph
    kg_path = cdir / "knowledge_graph.json"
    data = json.loads(kg_path.read_text(encoding="utf-8"))
    data["course_id"] = "probability"
    kg_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(StateContaminationError):
        assert_course_isolation(cdir, course_id="botany")


def test_workspace_rejects_mock_content_in_state(tmp_path: Path):
    root = _build_workspace(tmp_path / "ws")
    # fabricating a mock-style wrongbook entry must be rejected before persistence
    cdir = course_mod.course_dir(root, "botany")
    with pytest.raises(StateContaminationError):
        reject_mock_content({"course_id": "botany", "user_answer": "示例：未作答"}, where="wrongbook")
    with pytest.raises(StateContaminationError):
        reject_mock_content({"provider": "mock"}, where="student_state")


def test_exam_calendar_edge_cases():
    cal = ExamCalendar(workspace_id="WS-1")
    # no exam date
    upsert_entry(cal, course_id="botany", exam_date=None)
    # two exams on the same day
    upsert_entry(cal, course_id="organic-chemistry", exam_date="2026-06-20", exam_time="09:00")
    upsert_entry(cal, course_id="calculus", exam_date="2026-06-20", exam_time="14:00")
    # consecutive days
    upsert_entry(cal, course_id="probability", exam_date="2026-06-21")
    # completed exam stays as history
    upsert_entry(cal, course_id="probability", exam_date="2026-06-21")
    mark_completed(cal, "probability")
    active = active_entries(cal)
    assert any(e.course_id == "botany" and e.exam_date is None for e in active)
    assert len([e for e in active if e.exam_date == "2026-06-20"]) == 2
    assert all(e.course_id != "probability" for e in active)
    # completed entry is retained in history
    assert any(e.course_id == "probability" and e.status == "completed" for e in cal.entries)
    # days_to_exam
    assert days_to_exam(cal.entries[0]) is None  # no date
    assert days_to_exam(next(e for e in cal.entries if e.course_id == "organic-chemistry")) is not None
    # remove
    remove_entry(cal, "botany")
    assert all(e.course_id != "botany" for e in cal.entries)


def test_duplicate_course_and_bad_id_rejected(tmp_path: Path):
    root = _build_workspace(tmp_path / "ws")
    with pytest.raises(ValueError):
        workspace_mod.add_course_to_workspace(root, course_id="botany", course_name="dup")
    with pytest.raises(ValueError):
        course_mod.create_course(root, course_id="Bad Course!", course_name="x")
