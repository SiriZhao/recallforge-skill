from __future__ import annotations

from pathlib import Path

from recallforge.i18n import TerminologyMap
from recallforge.knowledge.build import build_course_intelligence
from recallforge.knowledge.graph import build_knowledge_edges
from recallforge.knowledge.topic import build_topics
from recallforge.state import course as course_mod
from recallforge.state import workspace as workspace_mod


def _make_course(root: Path, course_id: str = "probability") -> Path:
    workspace_mod.create_workspace(root, user_locale="zh-CN", daily_total_hours=6.0)
    workspace_mod.add_course_to_workspace(
        root, course_id=course_id, course_name="概率论", exam_date="2026-06-20", target_score=85
    )
    return root


def _term_map(course_id: str = "probability") -> TerminologyMap:
    tm = TerminologyMap(course_id=course_id)
    tm.add("central_limit_theorem", zh="中心极限定理", en="Central Limit Theorem", aliases=["CLT", "中心极限"])
    tm.add("conditional_probability", zh="条件概率", en="conditional probability")
    tm.add("normal_distribution", zh="正态分布", en="normal distribution")
    return tm


def _evidence_records() -> list[dict]:
    return [
        {
            "evidence_id": "EV-AAA1", "course_id": "probability", "source_file": "lecture_03.pdf",
            "document_type": "pdf", "page_or_slide": "5", "heading": "第五章 中心极限定理",
            "source_language": "zh-CN", "extraction_method": "native_text", "confidence": 0.85,
            "evidence_weight": 1.0, "synthetic": False, "created_at": "2026-06-01T00:00:00+08:00",
            "content": {
                "text": "中心极限定理是指大量独立随机变量之和近似服从正态分布。"
                        "老师强调这是必考重点。易错：混淆CLT的条件。",
                "formula_signals": [],
            },
        },
        {
            "evidence_id": "EV-BBB2", "course_id": "probability", "source_file": "textbook_en.pdf",
            "document_type": "pdf", "page_or_slide": "12", "heading": "Chapter 12",
            "source_language": "en-US", "extraction_method": "native_text", "confidence": 0.9,
            "evidence_weight": 1.0, "synthetic": False, "created_at": "2026-06-02T00:00:00+08:00",
            "content": {
                "text": "Central Limit Theorem is defined as the sum of independent random "
                        "variables approaching a normal distribution. "
                        "Prerequisite: normal distribution.",
                "formula_signals": ["math-tokens"],
            },
        },
        {
            "evidence_id": "EV-CCC3", "course_id": "probability", "source_file": "past_exam_2024.pdf",
            "document_type": "pdf", "page_or_slide": "1", "heading": "期末试卷",
            "source_language": "zh-CN", "extraction_method": "multimodal", "confidence": 0.8,
            "evidence_weight": 2.0, "synthetic": False, "created_at": "2026-06-03T00:00:00+08:00",
            "content": {
                "text": "", "formula_signals": [],
                "exam_structure": [
                    {"question_number": "1", "body": "中心极限定理计算", "question_type": "calculation", "score": "15"},
                    {"question_number": "2", "body": "条件概率简答", "question_type": "short answer", "score": "10"},
                ],
            },
        },
    ]


def test_cross_language_topic_fusion(tmp_path: Path):
    """CLT / Central Limit Theorem / 中心极限定理 must fuse into ONE topic with
    aliases and fusion confidence, without inventing separate topics."""
    root = _make_course(tmp_path / "ws")
    course_path = course_mod.course_dir(root, "probability")
    tm = _term_map()
    course_mod._write_json(course_path / "terminology_map.json", tm.to_state())

    topics = build_topics(_evidence_records(), tm, "probability")
    clt = [t for t in topics if t.topic_id == "central_limit_theorem"]
    assert len(clt) == 1, "cross-language aliases must fuse into one topic"
    topic = clt[0]
    assert topic.localized_names.get("zh-CN") == "中心极限定理"
    assert topic.localized_names.get("en-US") == "Central Limit Theorem"
    assert "CLT" in topic.aliases or "CLT" in topic.localized_names.values() or "CLT" in {
        a for a in topic.aliases
    }
    assert topic.fusion_confidence > 0.6, "multiple languages/sources raise fusion confidence"
    # evidence from lecture (zh), textbook (en), and past exam all attached
    assert len(topic.evidence) == 3
    assert topic.teacher_emphasis == "observed"


def test_no_false_merging_of_different_concepts(tmp_path: Path):
    """Different concepts (CLT vs conditional probability) must NOT merge; each
    recognized concept becomes its own topic; no generic heading/chapter garbage."""
    root = _make_course(tmp_path / "ws")
    course_path = course_mod.course_dir(root, "probability")
    tm = _term_map()
    course_mod._write_json(course_path / "terminology_map.json", tm.to_state())

    topics = build_topics(_evidence_records(), tm, "probability")
    ids = {t.topic_id for t in topics}
    assert "central_limit_theorem" in ids
    assert "conditional_probability" in ids
    assert "normal_distribution" in ids  # also mentioned in evidence, a real concept
    assert len(ids) == 3, "only real recognized concepts, no generic heading/chapter garbage"
    assert not any("第五章" in t.topic_id for t in topics)
    assert not any("chapter" in t.topic_id for t in topics)
    assert not any("期末" in t.topic_id for t in topics)


def test_citation_preservation(tmp_path: Path):
    """Every topic field must carry evidence_refs to real evidence ids."""
    root = _make_course(tmp_path / "ws")
    course_path = course_mod.course_dir(root, "probability")
    tm = _term_map()
    course_mod._write_json(course_path / "terminology_map.json", tm.to_state())
    topics = build_topics(_evidence_records(), tm, "probability")
    clt = next(t for t in topics if t.topic_id == "central_limit_theorem")
    assert clt.evidence == ["EV-AAA1", "EV-BBB2", "EV-CCC3"]
    assert all(d.evidence_refs for d in clt.definitions)
    assert all(f.evidence_refs for f in clt.formulas)
    assert all(m.evidence_refs for m in clt.common_mistakes)
    # definition text is a verbatim substring of source evidence (hallucination guard)
    source_text = _evidence_records()[0]["content"]["text"]
    assert clt.definitions[0].text in source_text


def test_formula_evidence_preserved(tmp_path: Path):
    root = _make_course(tmp_path / "ws")
    course_path = course_mod.course_dir(root, "probability")
    tm = _term_map()
    course_mod._write_json(course_path / "terminology_map.json", tm.to_state())
    records = _evidence_records()
    records[0]["content"]["text"] += "\nc1 * V1 = c2 * V2"
    records[0]["content"]["formula_signals"] = ["math-tokens"]
    topics = build_topics(records, tm, "probability")
    clt = next(t for t in topics if t.topic_id == "central_limit_theorem")
    assert any("c1 * V1 = c2 * V2" in f.text for f in clt.formulas)


def test_prerequisite_edge_is_real_and_evidence_backed(tmp_path: Path):
    """prerequisite edges must come from explicit text evidence, not adjacency."""
    root = _make_course(tmp_path / "ws")
    course_path = course_mod.course_dir(root, "probability")
    tm = _term_map()
    course_mod._write_json(course_path / "terminology_map.json", tm.to_state())
    topics = build_topics(_evidence_records(), tm, "probability")
    edges = build_knowledge_edges(topics, _evidence_records(), tm)
    prereq = [e for e in edges if e.relation == "prerequisite"]
    assert prereq, "Prerequisite: normal distribution must create a real prerequisite edge"
    edge = prereq[0]
    assert edge.source == "normal_distribution"
    assert edge.target == "central_limit_theorem"
    assert edge.evidence_refs == ["EV-BBB2"]


def test_knowledge_edges_relations(tmp_path: Path):
    root = _make_course(tmp_path / "ws")
    course_path = course_mod.course_dir(root, "probability")
    tm = _term_map()
    course_mod._write_json(course_path / "terminology_map.json", tm.to_state())
    topics = build_topics(_evidence_records(), tm, "probability")
    edges = build_knowledge_edges(topics, _evidence_records(), tm)
    relations = {e.relation for e in edges}
    assert "prerequisite" in relations
    assert "related_to" in relations  # lecture text mentions both CLT and normal distribution


def test_build_course_intelligence_persists_all_state(tmp_path: Path):
    root = _make_course(tmp_path / "ws")
    course_path = course_mod.course_dir(root, "probability")
    tm = _term_map()
    course_mod._write_json(course_path / "terminology_map.json", tm.to_state())
    course_mod._write_json(
        course_path / "evidence_store.json",
        {"course_id": "probability", "documents": {}, "records": _evidence_records(), "updated_at": ""},
    )
    result = build_course_intelligence(root, "probability", days_to_exam=3, unresolved_pages=["scan.pdf:1"])
    assert len(result.topics) == 3  # CLT + conditional probability + normal distribution
    assert len(result.exam_points) == 3
    assert (course_path / "knowledge_graph.json").exists()
    assert (course_path / "exam_model.json").exists()
    assert (course_path / "risk_radar.json").exists()
    assert (course_path / "conflicts.json").exists()
    assert (course_path / "coverage_report.json").exists()
    assert result.coverage.unresolved_documents == ["scan.pdf:1"]
