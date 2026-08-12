from __future__ import annotations

from pathlib import Path

import pytest

from exam_review_skill.planner.orchestrator import generate_daily_plan_v4, render_plan_v4
from exam_review_skill.state import course as course_mod
from exam_review_skill.state import workspace as workspace_mod
from exam_review_skill.student.sessions import AnswerResult, record_answer
from exam_review_skill.student.store import load_student_model, save_student_model

from planner_fixtures import build_scenario_workspace


def test_scenario_a_four_courses_not_simple_average(tmp_path: Path):
    """Scenario A: 4 courses, exams within 7 days. Near-exam courses must get more
    time than far courses - never a mechanical 3h/3h split."""
    root = build_scenario_workspace(tmp_path / "ws")
    plan = generate_daily_plan_v4(root, "2026-06-18")
    alloc = plan.allocation
    # probability (exam in 1d) + organic (2d) > botany (8d)
    assert alloc["probability"] > alloc["botany"]
    assert alloc["organic-chemistry"] > alloc["botany"]
    # not equal shares
    values = sorted(alloc.values())
    assert values[-1] > values[0] + 0.2
    # all 4 courses present (anti-starvation)
    assert set(alloc) == {"probability", "organic-chemistry", "botany", "calculus"}
    # topic-level blocks exist
    assert plan.blocks
    assert all(b.topic_name for b in plan.blocks)


def test_scenario_a_anti_starvation_maintenance(tmp_path: Path):
    """Even the far course (botany, 8 days out) keeps a minimum maintenance block."""
    root = build_scenario_workspace(tmp_path / "ws")
    plan = generate_daily_plan_v4(root, "2026-06-18")
    assert plan.allocation["botany"] >= 0.4
    assert any(b.course_id == "botany" for b in plan.blocks)
    assert any("maintenance" in note or "spaced review" in note for note in plan.notes)


def test_scenario_b_two_exams_same_day(tmp_path: Path):
    """Scenario B: two courses exam on the same day - both become urgent."""
    root = build_scenario_workspace(
        tmp_path / "ws",
        exam_dates={"probability": "2026-06-20", "organic-chemistry": "2026-06-20"},
    )
    plan = generate_daily_plan_v4(root, "2026-06-18")
    assert plan.allocation["probability"] > plan.allocation["botany"]
    assert plan.allocation["organic-chemistry"] > plan.allocation["botany"]
    # both urgent courses get a meaningful share (not starved by each other)
    assert plan.allocation["probability"] >= 1.0
    assert plan.allocation["organic-chemistry"] >= 1.0


def test_scenario_c_exam_moved_up_replans(tmp_path: Path):
    """Scenario C: an exam is moved earlier - the scheduler must re-prioritize."""
    root = build_scenario_workspace(tmp_path / "ws")
    # botany exam moved from 06-26 to 06-19 (tomorrow)
    plan = generate_daily_plan_v4(root, "2026-06-18", exam_date_changes={"botany": "2026-06-19"})
    assert any("botany exam date" in a for a in plan.overrides_applied)
    # botany now urgent: its allocation must jump above the far-courses baseline
    baseline = generate_daily_plan_v4(root, "2026-06-18")
    assert plan.allocation["botany"] > baseline.allocation["botany"] + 0.3


def test_scenario_d_lagging_course_gets_boosted(tmp_path: Path):
    """Scenario D: a course badly behind (no mastery data + low estimated score)
    gets a bigger share via target gap and score-gain opportunity."""
    root = build_scenario_workspace(
        tmp_path / "ws",
        exam_dates={"calculus": "2026-06-20"},
    )
    # mark calculus badly behind: low estimated score
    course_path = course_mod.course_dir(root, "calculus")
    course_mod.update_manifest(course_path, current_estimated_score=30)
    plan = generate_daily_plan_v4(root, "2026-06-18")
    # calculus (target 60, current 30, gap 0.30) must outrank botany (target 70, no gap data)
    assert plan.allocation["calculus"] > plan.allocation["botany"]


def test_scenario_e_mixed_chinese_english(tmp_path: Path):
    """Scenario E: mixed zh/en courses - both render in their own course plan."""
    root = build_scenario_workspace(tmp_path / "ws")
    # add an English-only course
    workspace_mod.add_course_to_workspace(
        root, course_id="linear-algebra", course_name="Linear Algebra",
        exam_date="2026-06-25", target_score=75,
    )
    course_path = course_mod.course_dir(root, "linear-algebra")
    from exam_review_skill.i18n import TerminologyMap

    tm = TerminologyMap(course_id="linear-algebra")
    tm.add("matrix", zh="矩阵", en="matrix")
    tm.add("eigenvalue", zh="特征值", en="eigenvalue")
    course_mod._write_json(course_path / "terminology_map.json", tm.to_state())
    from planner_fixtures import _evidence_record

    records = [
        _evidence_record("linear-algebra", 0, "矩阵", "matrix"),
        _evidence_record("linear-algebra", 1, "特征值", "eigenvalue"),
    ]
    course_mod._write_json(
        course_path / "evidence_store.json",
        {"course_id": "linear-algebra", "documents": {}, "records": records, "updated_at": ""},
    )
    from exam_review_skill.knowledge.build import build_course_intelligence

    build_course_intelligence(root, "linear-algebra", days_to_exam=6)
    plan = generate_daily_plan_v4(root, "2026-06-18")
    assert "linear-algebra" in plan.allocation
    text_zh = render_plan_v4(plan, "zh-CN")
    assert "全局每日计划" in text_zh
    assert any(b.course_id == "linear-algebra" and b.topic_name for b in plan.blocks)


def test_mastery_data_shapes_plan_kinds(tmp_path: Path):
    """Once real answers are recorded, the course plan reflects mastery:
    weak/unknown -> practice/study; proficient -> maintenance."""
    root = build_scenario_workspace(tmp_path / "ws")
    model = load_student_model(root, "probability")
    record_answer(
        model,
        AnswerResult(topic_id="central_limit_theorem", correct=False, difficulty=3, mistake_type="calculation_error"),
        today="2026-06-17",
    )
    save_student_model(root, "probability", model)
    plan = generate_daily_plan_v4(root, "2026-06-18")
    prob_blocks = [b for b in plan.blocks if b.course_id == "probability"]
    assert prob_blocks
    # CLT is weak/unknown -> not a 'maintenance' block
    clt_blocks = [b for b in prob_blocks if b.topic_id == "central_limit_theorem"]
    assert clt_blocks
    assert clt_blocks[0].kind in ("study", "practice", "cram")


def test_hours_override_and_skip(tmp_path: Path):
    """User override (skip course + change hours) wins over the planner."""
    root = build_scenario_workspace(tmp_path / "ws")
    plan = generate_daily_plan_v4(
        root, "2026-06-18",
        total_hours_override=3.0,
        skip_courses=["botany"],
    )
    assert plan.total_hours == pytest.approx(3.0)
    assert "botany" not in plan.allocation
    assert "botany" not in {b.course_id for b in plan.blocks}
