from __future__ import annotations

import json
from pathlib import Path

from exam_review_skill.i18n import TerminologyMap
from exam_review_skill.knowledge.build import build_course_intelligence
from exam_review_skill.knowledge.conflict import detect_conflicts
from exam_review_skill.knowledge.risk import build_risk_radar
from exam_review_skill.knowledge.topic import build_topics
from exam_review_skill.models import ExamPointModel
from exam_review_skill.state import course as course_mod
from exam_review_skill.state import workspace as workspace_mod


def _term_map() -> TerminologyMap:
    tm = TerminologyMap(course_id="probability")
    tm.add("central_limit_theorem", zh="中心极限定理", en="Central Limit Theorem")
    tm.add("conditional_probability", zh="条件概率", en="conditional probability")
    tm.add("normal_distribution", zh="正态分布", en="normal distribution")
    return tm


def test_risk_radar_explainable_priority(tmp_path: Path):
    points = [
        ExamPointModel(
            exam_point_id="EP1", topic_id="a", topic_name="A",
            importance=5, likelihood_estimate=0.9, evidence=["e1", "e2", "e3", "e4"],
            past_exam_frequency=4, teacher_emphasis="observed", learning_cost=1.0,
        ),
        ExamPointModel(
            exam_point_id="EP2", topic_id="b", topic_name="B",
            importance=1, likelihood_estimate=0.05, evidence=["e1"],
            past_exam_frequency=0, teacher_emphasis="unknown", learning_cost=1.0,
        ),
    ]
    ranked = build_risk_radar(points, mastery={"a": {"level": "unknown"}}, days_to_exam=1)
    by_id = {p.exam_point_id: p for p in ranked}
    assert by_id["EP1"].priority == "S"
    assert by_id["EP2"].priority == "C"
    assert len(by_id["EP1"].priority_rationale) >= 3
    # rationale must contain the actual numbers, not just a label
    assert any("score=" in r for r in by_id["EP1"].priority_rationale)
    assert any("likelihood" in r for r in by_id["EP1"].priority_rationale)
    # S is sorted first
    assert ranked[0].exam_point_id == "EP1"


def test_risk_radar_urgency_effect(tmp_path: Path):
    def make(gap_level: str):
        return [ExamPointModel(
            exam_point_id="EP", topic_id="t", topic_name="T",
            importance=4, likelihood_estimate=0.5, evidence=["e1"],
            past_exam_frequency=1, teacher_emphasis="inferred", learning_cost=1.0,
        )]

    far = build_risk_radar(make("unknown"), mastery={"t": {"level": "unknown"}}, days_to_exam=30)
    near = build_risk_radar(make("unknown"), mastery={"t": {"level": "unknown"}}, days_to_exam=1)
    rank = {"S": 0, "A": 1, "B": 2, "C": 3}
    assert rank[near[0].priority] <= rank[far[0].priority]  # urgency pushes the same item up


def test_conflict_detected_not_silently_overwritten(tmp_path: Path):
    root = tmp_path / "ws"
    workspace_mod.create_workspace(root)
    workspace_mod.add_course_to_workspace(root, course_id="probability", course_name="概率论")
    course_path = course_mod.course_dir(root, "probability")
    tm = _term_map()
    course_mod._write_json(course_path / "terminology_map.json", tm.to_state())
    records = [
        {
            "evidence_id": "EV-A", "course_id": "probability", "source_file": "lecture_03.pdf",
            "document_type": "pdf", "page_or_slide": "1", "heading": "第五章",
            "source_language": "zh-CN", "extraction_method": "native_text", "confidence": 0.85,
            "evidence_weight": 1.0, "synthetic": False, "created_at": "2026-06-01T00:00:00+08:00",
            "content": {"text": "中心极限定理是指样本均值近似服从正态分布。", "formula_signals": []},
        },
        {
            "evidence_id": "EV-B", "course_id": "probability", "source_file": "textbook_en.pdf",
            "document_type": "pdf", "page_or_slide": "1", "heading": "Chapter 12",
            "source_language": "en-US", "extraction_method": "native_text", "confidence": 0.9,
            "evidence_weight": 1.0, "synthetic": False, "created_at": "2026-06-02T00:00:00+08:00",
            "content": {"text": "Central Limit Theorem is defined as the sum of independent random variables. Prerequisite: normal distribution.", "formula_signals": []},
        },
    ]
    course_mod._write_json(
        course_path / "evidence_store.json",
        {"course_id": "probability", "documents": {}, "records": records, "updated_at": ""},
    )
    result = build_course_intelligence(root, "probability")
    assert len(result.conflicts) >= 1
    conflict = result.conflicts[0]
    assert conflict.resolved is False  # never silently resolved
    assert len(conflict.alternatives) == 2
    assert conflict.chosen is not None
    assert "user confirmation" in conflict.resolution_reason
    # persisted too
    conflicts_file = json.loads((course_path / "conflicts.json").read_text(encoding="utf-8"))
    assert conflicts_file["conflicts"]


def test_same_language_contradiction_flags_real_conflict(tmp_path: Path):
    tm = _term_map()
    topics = build_topics(
        [
            {
                "evidence_id": "EV-X", "course_id": "p", "source_file": "note_a.pdf",
                "document_type": "pdf", "page_or_slide": "1", "heading": "",
                "source_language": "zh-CN", "extraction_method": "native_text", "confidence": 0.8,
                "evidence_weight": 1.0, "synthetic": False, "created_at": "2026-06-01T00:00:00+08:00",
                "content": {"text": "中心极限定理是指样本均值近似服从正态分布。", "formula_signals": []},
            },
            {
                "evidence_id": "EV-Y", "course_id": "p", "source_file": "note_b.pdf",
                "document_type": "pdf", "page_or_slide": "1", "heading": "",
                "source_language": "zh-CN", "extraction_method": "native_text", "confidence": 0.8,
                "evidence_weight": 1.0, "synthetic": False, "created_at": "2026-06-03T00:00:00+08:00",
                "content": {"text": "中心极限定理是指任意分布都严格等于正态分布。", "formula_signals": []},
            },
        ],
        tm, "p",
    )
    conflicts = detect_conflicts(topics, [
        {
            "evidence_id": "EV-X", "course_id": "p", "source_file": "note_a.pdf",
            "document_type": "pdf", "page_or_slide": "1", "heading": "",
            "source_language": "zh-CN", "extraction_method": "native_text", "confidence": 0.8,
            "evidence_weight": 1.0, "synthetic": False, "created_at": "2026-06-01T00:00:00+08:00",
            "content": {"text": "中心极限定理是指样本均值近似服从正态分布。", "formula_signals": []},
        },
        {
            "evidence_id": "EV-Y", "course_id": "p", "source_file": "note_b.pdf",
            "document_type": "pdf", "page_or_slide": "1", "heading": "",
            "source_language": "zh-CN", "extraction_method": "native_text", "confidence": 0.8,
            "evidence_weight": 1.0, "synthetic": False, "created_at": "2026-06-03T00:00:00+08:00",
            "content": {"text": "中心极限定理是指任意分布都严格等于正态分布。", "formula_signals": []},
        },
    ], tm)
    clt_conflicts = [c for c in conflicts if c.topic_id == "central_limit_theorem"]
    assert len(clt_conflicts) == 1
    assert "user confirmation" in clt_conflicts[0].resolution_reason


def test_coverage_report_verdict(tmp_path: Path):
    root = tmp_path / "ws"
    workspace_mod.create_workspace(root)
    workspace_mod.add_course_to_workspace(root, course_id="probability", course_name="概率论")
    course_path = course_mod.course_dir(root, "probability")
    tm = _term_map()
    course_mod._write_json(course_path / "terminology_map.json", tm.to_state())
    # empty evidence -> insufficient, never 'adequate' with no proof
    course_mod._write_json(
        course_path / "evidence_store.json",
        {"course_id": "probability", "documents": {}, "records": [], "updated_at": ""},
    )
    result = build_course_intelligence(root, "probability", unresolved_pages=["scan.pdf:1"])
    assert result.coverage.verdict.startswith("insufficient")
    assert result.coverage.unresolved_documents == ["scan.pdf:1"]
    assert result.coverage.material_coverage["evidence_records"] == 0
    assert result.coverage.past_exam_coverage["exam_sets"] == 0
    assert result.coverage.answer_coverage["answer_sources"] == 0


def test_no_hallucination_without_evidence(tmp_path: Path):
    """No evidence -> no topics, no exam points, no fabricated content."""
    root = tmp_path / "ws"
    workspace_mod.create_workspace(root)
    workspace_mod.add_course_to_workspace(root, course_id="probability", course_name="概率论")
    course_path = course_mod.course_dir(root, "probability")
    tm = _term_map()
    course_mod._write_json(course_path / "terminology_map.json", tm.to_state())
    course_mod._write_json(
        course_path / "evidence_store.json",
        {"course_id": "probability", "documents": {}, "records": [], "updated_at": ""},
    )
    result = build_course_intelligence(root, "probability")
    assert result.topics == []
    assert result.exam_points == []
    assert result.teacher_style.tier == "unknown"
    assert result.conflicts == []
