from __future__ import annotations

import json
from pathlib import Path

from exam_review_skill.i18n import TerminologyMap
from exam_review_skill.i18n.locales import get_catalog
from exam_review_skill.orchestrator.scheduler import generate_daily_plan, render_plan
from exam_review_skill.state import course as course_mod
from exam_review_skill.state import workspace as workspace_mod


def test_zh_course_manifest_and_plan(tmp_path: Path):
    root = tmp_path / "ws"
    workspace_mod.create_workspace(root, user_locale="zh-CN", daily_total_hours=5.0)
    workspace_mod.add_course_to_workspace(
        root,
        course_id="probability",
        course_name="概率论",
        course_name_localized={"zh-CN": "概率论", "en-US": "Probability"},
        source_languages=["zh-CN"],
        exam_date="2026-06-20",
        target_score=85,
    )
    manifest = course_mod.load_manifest(course_mod.course_dir(root, "probability"))
    assert manifest.course_name == "概率论"
    assert manifest.course_name_localized["en-US"] == "Probability"
    assert manifest.source_languages == ["zh-CN"]
    assert manifest.exam_date == "2026-06-20"
    assert manifest.target_score == 85

    plan = generate_daily_plan(root, "2026-06-18")
    text = render_plan(plan, "zh-CN")
    assert "全局每日计划" in text
    assert "距离考试" in text


def test_zh_terminology_localization(tmp_path: Path):
    root = tmp_path / "ws"
    workspace_mod.create_workspace(root, user_locale="zh-CN")
    workspace_mod.add_course_to_workspace(root, course_id="probability", course_name="概率论")
    cdir = course_mod.course_dir(root, "probability")
    data = course_mod.load_course_json(cdir, "terminology_map.json", {}) or {}
    term_map = TerminologyMap.from_state(data)
    term_map.add("conditional_probability", zh="条件概率", en="conditional probability")
    course_mod._write_json(cdir / "terminology_map.json", term_map.to_state())
    reloaded = TerminologyMap.from_state(
        json.loads((cdir / "terminology_map.json").read_text(encoding="utf-8"))
    )
    assert reloaded.localize("conditional_probability", "zh-CN") == "条件概率"
    assert reloaded.localize("条件概率", "en-US") == "conditional probability"


def test_zh_catalog_keys_present():
    catalog = get_catalog("zh-CN")
    for key in ("plan.block.why", "plan.block.done", "workspace.course.added"):
        assert key in catalog
