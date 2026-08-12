from __future__ import annotations

from pathlib import Path

import pytest

from exam_review_skill.models import DayOverride
from exam_review_skill.orchestrator.scheduler import (
    MAX_SHARE,
    MIN_MAINTENANCE_HOURS,
    allocate_hours,
    generate_daily_plan,
    render_plan,
)
from exam_review_skill.state import workspace as workspace_mod


def _build_workspace(root: Path) -> Path:
    workspace_mod.create_workspace(root, user_locale="zh-CN", daily_total_hours=6.0)
    workspace_mod.add_course_to_workspace(
        root, course_id="probability", course_name="概率论",
        source_languages=["zh-CN"], exam_date="2026-06-23", target_score=85,
        current_estimated_score=70,
    )
    workspace_mod.add_course_to_workspace(
        root, course_id="organic-chemistry", course_name="有机化学",
        source_languages=["zh-CN"], exam_date="2026-06-20", target_score=80,
        current_estimated_score=45,
    )
    workspace_mod.add_course_to_workspace(
        root, course_id="botany", course_name="植物学", target_score=70,
        current_estimated_score=70,
    )
    workspace_mod.add_course_to_workspace(
        root, course_id="calculus", course_name="微积分", exam_date="2026-06-21", target_score=60,
        current_estimated_score=55,
    )
    return root


def test_global_plan_includes_all_courses_with_anti_starvation(tmp_path: Path):
    root = _build_workspace(tmp_path / "ws")
    plan = generate_daily_plan(root, "2026-06-18")
    assert set(plan.allocation) == {"probability", "organic-chemistry", "botany", "calculus"}
    # anti-starvation: every active course gets at least the minimum maintenance
    for cid, hours in plan.allocation.items():
        assert hours >= MIN_MAINTENANCE_HOURS - 1e-9, cid
    assert sum(plan.allocation.values()) == pytest.approx(6.0, abs=0.1)


def test_plan_is_not_simple_time_averaging(tmp_path: Path):
    root = _build_workspace(tmp_path / "ws")
    plan = generate_daily_plan(root, "2026-06-18")
    # near-term, higher-target courses must get more than the far/undated ones
    assert plan.allocation["organic-chemistry"] > plan.allocation["botany"] + 0.3
    values = sorted(plan.allocation.values())
    assert values[-1] > values[0] + 0.3  # clearly not equal shares


def test_every_block_has_rationale_fields(tmp_path: Path):
    root = _build_workspace(tmp_path / "ws")
    plan = generate_daily_plan(root, "2026-06-18")
    assert plan.blocks
    for block in plan.blocks:
        assert block.why and block.risk and block.goal and block.done_when
        assert block.start < block.end
    # no overlapping or out-of-order blocks
    prev_end = None
    for block in plan.blocks:
        if prev_end is not None:
            assert block.start >= prev_end
        prev_end = block.end


def test_user_override_skip_and_hours(tmp_path: Path):
    root = _build_workspace(tmp_path / "ws")
    # stored override: skip botany + only 3 hours today
    workspace_mod.upsert_override(
        root,
        DayOverride(
            date="2026-06-18",
            skip_courses=["botany"],
            total_hours=3.0,
            target_scores={"calculus": 60},
            note="今天不想学植物学",
        ),
    )
    plan = generate_daily_plan(root, "2026-06-18")
    assert "botany" not in plan.allocation
    assert "botany" not in {b.course_id for b in plan.blocks}
    assert plan.total_hours == pytest.approx(3.0)
    assert any("calculus" in a and "60" in a for a in plan.overrides_applied)
    assert any("今天不想学植物学" in a for a in plan.overrides_applied)


def test_inline_override_replans(tmp_path: Path):
    root = _build_workspace(tmp_path / "ws")
    plan = generate_daily_plan(
        root, "2026-06-18",
        skip_courses=["organic-chemistry"],
        total_hours_override=2.0,
    )
    assert "organic-chemistry" not in plan.allocation
    assert plan.total_hours == pytest.approx(2.0)
    # remaining courses still keep maintenance (no starvation after a skip)
    assert "botany" in plan.allocation


def test_exam_date_change_replans(tmp_path: Path):
    root = _build_workspace(tmp_path / "ws")
    # organic exam moved up to the plan date -> it becomes the top priority (cram)
    plan = generate_daily_plan(
        root, "2026-06-18",
        exam_date_changes={"organic-chemistry": "2026-06-18"},
    )
    assert any("organic-chemistry" in a and "2026-06-18" in a for a in plan.overrides_applied)
    organic = next(b for b in plan.blocks if b.course_id == "organic-chemistry")
    assert organic.kind == "cram"


def test_render_plan_localized_zh(tmp_path: Path):
    root = _build_workspace(tmp_path / "ws")
    plan = generate_daily_plan(root, "2026-06-18")
    text = render_plan(plan, "zh-CN")
    assert "全局每日计划" in text
    assert "为什么：" in text
    assert "结束标准" in text


def test_allocate_hours_cap(tmp_path: Path):
    root = _build_workspace(tmp_path / "ws")
    from exam_review_skill.orchestrator.scheduler import build_course_signal
    from exam_review_skill.models import CourseManifest

    # single urgent course must not exceed the daily cap (unless cram)
    signal = build_course_signal(
        CourseManifest(course_id="only", course_name="only", target_score=80,
                       current_estimated_score=40, topic_count=10),
        entry_days=1,
        exam_model={},
        student={},
        study_plan={},
        today=__import__("datetime").date(2026, 6, 18),
    )
    allocation, _ = allocate_hours([signal], 6.0, [], None, "zh-CN")
    assert allocation["only"] <= 6.0 * 0.8 + 1e-9  # cram share allowed for exam<=2d
