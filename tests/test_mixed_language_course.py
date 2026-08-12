from __future__ import annotations

import json
from pathlib import Path

from exam_review_skill.i18n import TerminologyMap, normalize_topic
from exam_review_skill.state import course as course_mod
from exam_review_skill.state import workspace as workspace_mod


def _term_map():
    tm = TerminologyMap(course_id="probability")
    tm.add("bayes_theorem", zh="贝叶斯公式", en="Bayes' theorem", aliases=["Bayes公式", "贝叶斯定理"])
    tm.add("conditional_probability", zh="条件概率", en="conditional probability")
    tm.add("random_variable", zh="随机变量", en="random variable")
    return tm


def test_mixed_language_topics_normalize_to_one_key():
    tm = _term_map()
    for spelling in ["Bayes' theorem", "Bayes theorem", "贝叶斯公式", "Bayes公式", "贝叶斯定理"]:
        key, matched = normalize_topic(spelling, tm)
        assert key == "bayes_theorem"
        assert matched is True
    assert normalize_topic("条件概率", tm) == ("conditional_probability", True)
    assert normalize_topic("random variable", tm) == ("random_variable", True)
    assert normalize_topic("随机变量", tm) == ("random_variable", True)


def test_unmatched_topic_is_not_silently_merged():
    tm = _term_map()
    key, matched = normalize_topic("大数定律", tm)
    assert matched is False
    assert key == "大数定律"  # normalized but never merged into a wrong concept


def test_mixed_source_language_course_supported(tmp_path: Path):
    root = tmp_path / "ws"
    workspace_mod.create_workspace(root, user_locale="zh-CN")
    workspace_mod.add_course_to_workspace(
        root,
        course_id="probability",
        course_name="概率论 / Probability",
        course_name_localized={"zh-CN": "概率论", "en-US": "Probability"},
        source_languages=["zh-CN", "en-US"],  # Chinese PPT + English textbook
        exam_date="2026-06-20",
    )
    manifest = course_mod.load_manifest(course_mod.course_dir(root, "probability"))
    assert manifest.source_languages == ["zh-CN", "en-US"]
    cdir = course_mod.course_dir(root, "probability")
    tm = TerminologyMap(course_id="probability")
    tm.add("bayes_theorem", zh="贝叶斯公式", en="Bayes' theorem", aliases=["Bayes公式"])
    course_mod._write_json(cdir / "terminology_map.json", tm.to_state())
    reloaded = TerminologyMap.from_state(
        json.loads((cdir / "terminology_map.json").read_text(encoding="utf-8"))
    )
    assert reloaded.canonical_key("Bayes' theorem") == "bayes_theorem"
    assert reloaded.canonical_key("贝叶斯公式") == "bayes_theorem"
