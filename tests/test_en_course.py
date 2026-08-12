from __future__ import annotations

from pathlib import Path

from exam_review_skill.i18n import LanguageProfile
from exam_review_skill.i18n.locales import get_catalog
from exam_review_skill.orchestrator.scheduler import generate_daily_plan, render_plan
from exam_review_skill.state import course as course_mod
from exam_review_skill.state import workspace as workspace_mod


def test_en_course_manifest_and_plan(tmp_path: Path):
    root = tmp_path / "ws"
    workspace_mod.create_workspace(root, user_locale="en-US", daily_total_hours=4.0)
    workspace_mod.add_course_to_workspace(
        root,
        course_id="organic-chemistry",
        course_name="Organic Chemistry",
        source_languages=["en-US"],
        exam_date="2026-06-20",
        target_score=80,
    )
    manifest = course_mod.load_manifest(course_mod.course_dir(root, "organic-chemistry"))
    assert manifest.course_name == "Organic Chemistry"
    assert manifest.source_languages == ["en-US"]

    plan = generate_daily_plan(root, "2026-06-18")
    text = render_plan(plan, "en-US")
    assert "Global daily plan" in text
    assert "days to exam" in text


def test_en_language_profile():
    profile = LanguageProfile(ui_locale="en-US", source_languages=["en-US"], output_language="zh-CN")
    assert profile.validate() == []
    assert profile.describe() == "UI=en-US | Source=en-US | Output=zh-CN | Terminology=both"


def test_en_catalog_keys_present():
    catalog = get_catalog("en-US")
    for key in ("plan.block.why", "plan.block.done", "workspace.course.added"):
        assert key in catalog
