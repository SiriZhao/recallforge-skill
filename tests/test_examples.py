from __future__ import annotations

import sys
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def examples_root():
    return Path(__file__).resolve().parent.parent / "examples"


def test_examples_common_imports():
    """The shared example helper must import and build a workspace."""
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from examples.examples_common import add_course_with_evidence, make_workspace

    root = make_workspace(Path(__file__).parent / "tmp_example", locale="zh-CN", daily_hours=5)
    add_course_with_evidence(
        root,
        course_id="probability",
        name="概率论",
        exam_date="2026-06-19",
        target_score=85,
        topics=[("central_limit_theorem", "中心极限定理", "Central Limit Theorem")],
    )
    from exam_review_skill.state import course as course_mod
    from exam_review_skill.state import workspace as workspace_mod

    assert "probability" in workspace_mod.list_courses(root)
    kg = course_mod.load_course_json(course_mod.course_dir(root, "probability"), "knowledge_graph.json", {})
    assert kg.get("topics"), "knowledge graph should have topics"
    import shutil

    shutil.rmtree(Path(__file__).parent / "tmp_example", ignore_errors=True)


def test_example_readmes_present(examples_root: Path):
    for name in (
        "chinese-final-exam",
        "english-course",
        "mixed-language-course",
        "four-course-exam-week",
        "24-hour-cram",
    ):
        readme = examples_root / name / "README.md"
        assert readme.exists(), f"missing {name}/README.md"
        content = readme.read_text(encoding="utf-8")
        assert len(content) > 200, f"{name} README too short"
