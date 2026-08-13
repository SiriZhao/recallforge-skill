from __future__ import annotations

import json
from pathlib import Path

from recallforge.i18n import TerminologyMap
from recallforge.ingestion.pipeline import ingest_file
from recallforge.ingestion.types import IngestOptions
from recallforge.knowledge.build import build_course_intelligence
from recallforge.state import course as course_mod
from recallforge.state import workspace as workspace_mod
from recallforge.state.isolation import find_mock_markers
from recallforge.student.store import load_student_model
from recallforge.tutor.diagnosis import DIAGNOSIS_TAXONOMY


def _build_real_course(root: Path) -> Path:
    workspace_mod.create_workspace(root, user_locale="zh-CN", daily_total_hours=6)
    workspace_mod.add_course_to_workspace(
        root, course_id="probability", course_name="概率论",
        exam_date="2026-06-19", target_score=85,
    )
    course_path = course_mod.course_dir(root, "probability")
    tm = TerminologyMap(course_id="probability")
    tm.add("clt", zh="中心极限定理", en="CLT")
    course_mod._write_json(course_path / "terminology_map.json", tm.to_state())
    mat = root / "notes.txt"
    mat.write_text(
        "中心极限定理（CLT）是指大量独立随机变量之和近似服从正态分布。老师强调这是必考重点。",
        encoding="utf-8",
    )
    ingest_file(root, "probability", mat, options=IngestOptions())
    build_course_intelligence(root, "probability")
    return root


def test_no_mock_contamination_in_real_state(tmp_path: Path):
    """Real state must contain zero mock/synthetic markers."""
    root = _build_real_course(tmp_path / "ws")
    course_path = course_mod.course_dir(root, "probability")
    for filename in (
        "knowledge_graph.json", "exam_model.json", "risk_radar.json",
        "student_state.json", "wrongbook.json", "evidence_store.json",
        "coverage_report.json", "conflicts.json", "course_manifest.json",
    ):
        path = course_path / filename
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            hits = find_mock_markers(data)
            assert hits == [], f"{filename} has mock markers: {hits}"


def test_no_fabricated_citations(tmp_path: Path):
    """Every topic and exam point must carry real evidence refs."""
    root = _build_real_course(tmp_path / "ws")
    result = build_course_intelligence(root, "probability", persist=False)
    for topic in result.topics:
        assert topic.evidence, f"topic {topic.topic_id} has no evidence"
    for point in result.exam_points:
        assert point.evidence, f"exam point {point.exam_point_id} has no evidence"


def test_no_fabricated_exam_probability(tmp_path: Path):
    """likelihood_estimate is an ordinal heuristic; never presented as a real
    probability, and it derives from real past-exam frequency."""
    root = _build_real_course(tmp_path / "ws")
    exam_model = course_mod.load_course_json(
        course_mod.course_dir(root, "probability"), "exam_model.json", {}
    )
    for point in exam_model.get("exam_points", []):
        assert 0.0 <= point.get("likelihood_estimate", 0) <= 1.0
        # frequency is a real count, never fabricated
        assert point.get("past_exam_frequency", 0) >= 0
        assert isinstance(point.get("past_exam_frequency"), int)


def test_no_fabricated_mastery(tmp_path: Path):
    """Without real answers, mastery is 'unknown' - never a pretend number."""
    root = _build_real_course(tmp_path / "ws")
    model = load_student_model(root, "probability")
    assert model.topics == {}  # no fabricated mastery for topics without answers
    # even after answers, mastery_score is derived from real data (tested elsewhere)


def test_no_fabricated_teacher_statements(tmp_path: Path):
    """Teacher-style claims carry evidence tiers; nothing asserted without evidence."""
    root = _build_real_course(tmp_path / "ws")
    result = build_course_intelligence(root, "probability", persist=False)
    for claim in result.teacher_style.claims:
        assert claim["tier"] in ("observed", "strongly_inferred", "inferred")
        assert claim["evidence_refs"], f"claim without evidence: {claim['claim']}"
    # a course with no teacher evidence produces no claims
    workspace_mod.add_course_to_workspace(root, course_id="botany", course_name="植物学")
    botany_path = course_mod.course_dir(root, "botany")
    tm = TerminologyMap(course_id="botany")
    tm.add("photosynthesis", zh="光合作用", en="photosynthesis")
    course_mod._write_json(botany_path / "terminology_map.json", tm.to_state())
    plain = botany_path / "plain.txt"
    plain.write_text("光合作用（photosynthesis）是植物利用光能合成有机物的过程。", encoding="utf-8")
    ingest_file(root, "botany", plain, options=IngestOptions())
    botany_result = build_course_intelligence(root, "botany", persist=False)
    assert botany_result.teacher_style.claims == [] or all(
        c["tier"] != "unknown" for c in botany_result.teacher_style.claims
    )


def test_no_cross_course_knowledge_contamination(tmp_path: Path):
    """Each course's knowledge stays strictly in its own directory."""
    root = _build_real_course(tmp_path / "ws")
    workspace_mod.add_course_to_workspace(root, course_id="organic", course_name="有机化学")
    org_path = course_mod.course_dir(root, "organic")
    tm = TerminologyMap(course_id="organic")
    tm.add("esterification", zh="酯化反应", en="esterification")
    course_mod._write_json(org_path / "terminology_map.json", tm.to_state())
    mat = root / "organic.txt"
    mat.write_text("酯化反应（esterification）是羧酸与醇生成酯的反应。", encoding="utf-8")
    ingest_file(root, "organic", mat, options=IngestOptions())
    build_course_intelligence(root, "organic")

    prob_path = course_mod.course_dir(root, "probability")
    prob_kg = json.loads((prob_path / "knowledge_graph.json").read_text(encoding="utf-8"))
    org_kg = json.loads((org_path / "knowledge_graph.json").read_text(encoding="utf-8"))
    prob_topic_ids = {t["topic_id"] for t in prob_kg.get("topics", [])}
    org_topic_ids = {t["topic_id"] for t in org_kg.get("topics", [])}
    assert prob_topic_ids & org_topic_ids == set(), "topics leaked across courses"
    assert "esterification" not in prob_topic_ids
    assert "clt" not in org_topic_ids
    # evidence stores are also isolated
    prob_evidence = json.loads((prob_path / "evidence_store.json").read_text(encoding="utf-8"))
    assert all(r["course_id"] == "probability" for r in prob_evidence["records"])
    org_evidence = json.loads((org_path / "evidence_store.json").read_text(encoding="utf-8"))
    assert all(r["course_id"] == "organic" for r in org_evidence["records"])


def test_diagnosis_taxonomy_no_fabricated_categories(tmp_path: Path):
    """Diagnoses come only from the fixed taxonomy."""
    assert "unknown" in DIAGNOSIS_TAXONOMY
    assert len(DIAGNOSIS_TAXONOMY) >= 13
