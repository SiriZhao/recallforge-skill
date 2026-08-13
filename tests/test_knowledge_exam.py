from __future__ import annotations

import json
from pathlib import Path

from recallforge.i18n import TerminologyMap
from recallforge.knowledge.build import build_course_intelligence
from recallforge.knowledge.exam import (
    build_exam_points,
    build_past_exam_sets,
    evidence_weight_for,
)
from recallforge.knowledge.teacher import build_teacher_style
from recallforge.knowledge.topic import build_topics
from recallforge.state import course as course_mod
from recallforge.state import workspace as workspace_mod


def _term_map() -> TerminologyMap:
    tm = TerminologyMap(course_id="probability")
    tm.add("central_limit_theorem", zh="中心极限定理", en="Central Limit Theorem", aliases=["CLT"])
    tm.add("conditional_probability", zh="条件概率", en="conditional probability")
    tm.add("normal_distribution", zh="正态分布", en="normal distribution")
    return tm


def _records() -> list[dict]:
    return [
        {
            "evidence_id": "EV-AAA1", "course_id": "probability", "source_file": "lecture_03.pdf",
            "document_type": "pdf", "page_or_slide": "5", "heading": "第五章",
            "source_language": "zh-CN", "extraction_method": "native_text", "confidence": 0.85,
            "evidence_weight": 1.0, "synthetic": False, "created_at": "2026-06-01T00:00:00+08:00",
            "content": {"text": "中心极限定理是指大量独立随机变量之和近似服从正态分布。老师强调这是必考重点。", "formula_signals": []},
        },
        {
            "evidence_id": "EV-BBB2", "course_id": "probability", "source_file": "textbook_en.pdf",
            "document_type": "pdf", "page_or_slide": "12", "heading": "Chapter 12",
            "source_language": "en-US", "extraction_method": "native_text", "confidence": 0.9,
            "evidence_weight": 1.0, "synthetic": False, "created_at": "2026-06-02T00:00:00+08:00",
            "content": {"text": "Central Limit Theorem is defined as the sum of independent random variables. Prerequisite: normal distribution.", "formula_signals": []},
        },
        {
            "evidence_id": "EV-CCC3", "course_id": "probability", "source_file": "past_exam_2024.pdf",
            "document_type": "pdf", "page_or_slide": "1", "heading": "期末试卷",
            "source_language": "zh-CN", "extraction_method": "multimodal", "confidence": 0.8,
            "evidence_weight": 2.0, "synthetic": False, "created_at": "2026-06-03T00:00:00+08:00",
            "content": {"text": "", "formula_signals": [], "exam_structure": [
                {"question_number": "1", "body": "中心极限定理计算", "question_type": "calculation", "score": "15"},
                {"question_number": "2", "body": "条件概率简答", "question_type": "short answer", "score": "10"},
            ]},
        },
        {
            "evidence_id": "EV-DDD4", "course_id": "probability", "source_file": "past_exam_2023.pdf",
            "document_type": "pdf", "page_or_slide": "1", "heading": "期末试卷",
            "source_language": "zh-CN", "extraction_method": "multimodal", "confidence": 0.8,
            "evidence_weight": 2.0, "synthetic": False, "created_at": "2026-05-01T00:00:00+08:00",
            "content": {"text": "", "formula_signals": [], "exam_structure": [
                {"question_number": "1", "body": "中心极限定理选择", "question_type": "multiple choice", "score": "5"},
                {"question_number": "2", "body": "中心极限定理综合", "question_type": "essay", "score": "20"},
            ]},
        },
    ]


def test_past_exam_sets_modeled_per_file(tmp_path: Path):
    tm = _term_map()
    sets = build_past_exam_sets(_records(), tm)
    assert len(sets) == 2  # one per exam file
    by_file = {s.source_file: s for s in sets}
    assert by_file["past_exam_2024.pdf"].year == "2024"
    assert by_file["past_exam_2023.pdf"].year == "2023"
    q1 = by_file["past_exam_2024.pdf"].questions[0]
    assert q1.question_number == "1"
    assert q1.question_type == "calculation"
    assert q1.score == "15"
    assert q1.topics == ["central_limit_theorem"]
    assert q1.evidence_ref == "EV-CCC3"


def test_question_topic_bidirectional_mapping(tmp_path: Path):
    tm = _term_map()
    records = _records()
    course_path = None
    root = tmp_path / "ws"
    workspace_mod.create_workspace(root)
    workspace_mod.add_course_to_workspace(root, course_id="probability", course_name="概率论")
    course_path = course_mod.course_dir(root, "probability")
    course_mod._write_json(course_path / "terminology_map.json", tm.to_state())
    course_mod._write_json(
        course_path / "evidence_store.json",
        {"course_id": "probability", "documents": {}, "records": records, "updated_at": ""},
    )
    result = build_course_intelligence(root, "probability")
    # KnowledgeTopic -> Questions: CLT links to 3 past exam questions
    clt_topic = next(t for t in result.topics if t.topic_id == "central_limit_theorem")
    assert len(clt_topic.past_exam_links) == 3
    # ExamPointModel -> topic_name preserved
    clt_point = next(p for p in result.exam_points if p.topic_id == "central_limit_theorem")
    assert clt_point.past_exam_frequency == 3
    assert clt_point.topic_name == "Central Limit Theorem"


def test_likelihood_heuristic_not_statistical(tmp_path: Path):
    tm = _term_map()
    records = _records()
    topics = build_topics(records, tm, "probability")
    teacher = build_teacher_style("probability", topics, records, tm)
    exam_sets = build_past_exam_sets(records, tm)
    points = build_exam_points(topics, exam_sets, teacher, records, tm)
    clt = next(p for p in points if p.topic_id == "central_limit_theorem")
    # high frequency + teacher emphasis => higher likelihood than a rarely-tested topic
    cond = next(p for p in points if p.topic_id == "conditional_probability")
    assert clt.likelihood_estimate > cond.likelihood_estimate
    assert 0.0 <= clt.likelihood_estimate <= 1.0
    # frequency is a REAL count of past-exam questions
    assert clt.past_exam_frequency == 3


def test_evidence_weight_past_exam_higher_and_overrideable(tmp_path: Path):
    lecture = {"source_file": "lecture_03.pdf"}
    past = {"source_file": "past_exam_2024.pdf"}
    answer = {"source_file": "answer_key.pdf"}
    assert evidence_weight_for(past) > evidence_weight_for(lecture)
    assert evidence_weight_for(answer) >= evidence_weight_for(past)
    # per-course override table (not hard-coded globally)
    weights = {"past_exam": 1.0, "lecture_slide": 3.0}
    assert evidence_weight_for(past, weights) < evidence_weight_for(lecture, weights)


def test_teacher_style_tiers(tmp_path: Path):
    tm = _term_map()
    records = _records()
    topics = build_topics(records, tm, "probability")
    teacher = build_teacher_style("probability", topics, records, tm)
    assert teacher.tier == "observed"
    assert teacher.question_type_frequency.get("calculation", 0) == 1
    assert teacher.question_type_frequency.get("essay", 0) == 1
    claims = {c["claim"] for c in teacher.claims}
    assert "question type distribution" in claims
    # every claim has an evidence tier, never 'unknown' assertions
    assert all(c["tier"] in ("observed", "strongly_inferred", "inferred") for c in teacher.claims)


def test_teacher_style_unknown_when_no_evidence(tmp_path: Path):
    teacher = build_teacher_style("probability", [], [], _term_map())
    assert teacher.tier == "unknown"
    assert teacher.claims == []


def test_exam_model_json_kept_separate(tmp_path: Path):
    root = tmp_path / "ws"
    workspace_mod.create_workspace(root)
    workspace_mod.add_course_to_workspace(root, course_id="probability", course_name="概率论")
    course_path = course_mod.course_dir(root, "probability")
    tm = _term_map()
    course_mod._write_json(course_path / "terminology_map.json", tm.to_state())
    course_mod._write_json(
        course_path / "evidence_store.json",
        {"course_id": "probability", "documents": {}, "records": _records(), "updated_at": ""},
    )
    build_course_intelligence(root, "probability")
    exam_model = json.loads((course_path / "exam_model.json").read_text(encoding="utf-8"))
    assert "exam_points" in exam_model
    assert "past_exam_sets" in exam_model
    assert "teacher_style" in exam_model
    assert "evidence_weights" in exam_model
    assert exam_model["exam_points"][0]["past_exam_frequency"] >= 0
