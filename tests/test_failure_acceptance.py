from __future__ import annotations

import json
from pathlib import Path

import pytest

from exam_review_skill.i18n import TerminologyMap
from exam_review_skill.ingestion.pipeline import ingest_file
from exam_review_skill.ingestion.types import IngestOptions
from exam_review_skill.knowledge.build import build_course_intelligence
from exam_review_skill.planner.orchestrator import generate_daily_plan_v4
from exam_review_skill.reporting.dashboard import build_dashboard
from exam_review_skill.state import course as course_mod
from exam_review_skill.state import workspace as workspace_mod
from exam_review_skill.student.store import load_student_model


def _make_course(root: Path, course_id: str = "p", **manifest) -> Path:
    workspace_mod.create_workspace(root, user_locale="zh-CN", daily_total_hours=6)
    workspace_mod.add_course_to_workspace(root, course_id=course_id, course_name="概率论", **manifest)
    course_path = course_mod.course_dir(root, course_id)
    tm = TerminologyMap(course_id=course_id)
    tm.add("clt", zh="中心极限定理", en="CLT")
    course_mod._write_json(course_path / "terminology_map.json", tm.to_state())
    return root


def test_broken_pdf_graceful(tmp_path: Path):
    """A broken PDF must be recorded as unresolved, not crash the pipeline."""
    root = _make_course(tmp_path / "ws")
    broken = tmp_path / "broken.pdf"
    broken.write_bytes(b"%PDF-1.4 not a real pdf \x00\x01" * 10)
    result = ingest_file(root, "p", broken, options=IngestOptions())
    assert result.documents_seen == ["broken.pdf"]
    assert result.warnings, "must record a warning"
    # pipeline continues; no fake evidence
    assert result.evidence_added == []


def test_missing_answer_key_graceful(tmp_path: Path):
    """No answer key -> coverage report says so; everything else still works."""
    root = _make_course(tmp_path / "ws")
    mat = tmp_path / "notes.txt"
    mat.write_text("中心极限定理（CLT）是指大量独立随机变量之和近似服从正态分布。", encoding="utf-8")
    ingest_file(root, "p", mat, options=IngestOptions())
    result = build_course_intelligence(root, "p")
    assert result.coverage.answer_coverage["answer_sources"] == 0
    assert "insufficient" in result.coverage.verdict
    assert result.topics, "topics still built without answer keys"


def test_multimodal_provider_failure_graceful(tmp_path: Path):
    """Unconfigured multimodal provider -> scanned page is unresolved, never faked."""
    root = _make_course(tmp_path / "ws")
    from ingestion_fixtures import make_scanned_pdf
    scanned = make_scanned_pdf(tmp_path / "scan.pdf")
    result = ingest_file(root, "p", scanned, options=IngestOptions(provider_name="openai"))
    assert result.evidence_added == []
    assert result.unresolved_pages
    assert any("provider" in w.lower() for w in result.warnings)


def test_ocr_unavailable_graceful(tmp_path: Path):
    """OCR disabled by default -> page unresolved with a clear warning."""
    root = _make_course(tmp_path / "ws")
    from ingestion_fixtures import make_scanned_pdf
    scanned = make_scanned_pdf(tmp_path / "scan.pdf")
    result = ingest_file(root, "p", scanned, options=IngestOptions())
    assert result.evidence_added == []
    assert result.unresolved_pages
    assert any("OCR" in w or "ocr" in w for w in result.warnings)


def test_missing_exam_date_graceful(tmp_path: Path):
    """No exam date -> planner treats the course as maintenance (never crashes)."""
    root = _make_course(tmp_path / "ws", exam_date=None)
    mat = tmp_path / "notes.txt"
    mat.write_text("中心极限定理（CLT）是指大量独立随机变量之和近似服从正态分布。", encoding="utf-8")
    ingest_file(root, "p", mat, options=IngestOptions())
    build_course_intelligence(root, "p")
    plan = generate_daily_plan_v4(root, "2026-06-18")
    assert plan.blocks or not plan.allocation  # never crashes


def test_no_past_exams_graceful(tmp_path: Path):
    """No past exams -> exam model still builds; past-exam coverage = 0."""
    root = _make_course(tmp_path / "ws")
    mat = tmp_path / "notes.txt"
    mat.write_text("中心极限定理（CLT）是指大量独立随机变量之和近似服从正态分布。", encoding="utf-8")
    ingest_file(root, "p", mat, options=IngestOptions())
    result = build_course_intelligence(root, "p")
    assert result.past_exam_sets == []
    assert result.coverage.past_exam_coverage["exam_sets"] == 0
    assert result.exam_points, "exam points built from teacher emphasis even without past exams"


def test_no_student_history_graceful(tmp_path: Path):
    """No answer history -> mastery stays unknown; readiness is Unknown, not 0."""
    root = _make_course(tmp_path / "ws")
    mat = tmp_path / "notes.txt"
    mat.write_text("中心极限定理（CLT）是指大量独立随机变量之和近似服从正态分布。", encoding="utf-8")
    ingest_file(root, "p", mat, options=IngestOptions())
    build_course_intelligence(root, "p")
    model = load_student_model(root, "p")
    assert model.topics == {}  # no fabricated topics
    dash = build_dashboard(root, plan=generate_daily_plan_v4(root, "2026-06-18"), plan_date="2026-06-18")
    assert "Unknown / Insufficient evidence" in dash


def test_conflicting_sources_graceful(tmp_path: Path):
    """Conflicting definitions -> conflict recorded, not silently overwritten."""
    root = _make_course(tmp_path / "ws")
    a = tmp_path / "note_a.txt"
    a.write_text("中心极限定理是指样本均值近似服从正态分布。", encoding="utf-8")
    b = tmp_path / "note_b.txt"
    b.write_text("中心极限定理是指任意分布都严格等于正态分布。", encoding="utf-8")
    ingest_file(root, "p", a, options=IngestOptions())
    ingest_file(root, "p", b, options=IngestOptions())
    result = build_course_intelligence(root, "p")
    assert result.conflicts, "conflicting definitions must be detected"
    assert result.conflicts[0].resolved is False


def test_corrupted_state_graceful(tmp_path: Path):
    """Corrupted JSON state -> loaders fall back to defaults, never crash."""
    root = _make_course(tmp_path / "ws")
    course_path = course_mod.course_dir(root, "p")
    (course_path / "student_state.json").write_text("{corrupted!!!", encoding="utf-8")
    (course_path / "knowledge_graph.json").write_text("not json", encoding="utf-8")
    model = load_student_model(root, "p")
    assert model.course_id == "p"
    # build still works with the corrupted files
    result = build_course_intelligence(root, "p")
    assert result.topics == [] or result.topics


def test_unknown_locale_graceful(tmp_path: Path):
    """An unsupported locale fails closed to the fallback locale instead of crashing."""
    from exam_review_skill.i18n.locales import t

    root = _make_course(tmp_path / "ws")
    # unknown locale -> language-level fallback to zh-CN
    text = t("zh-TW", "plan.title", date="2026-06-18", hours="6")
    assert "全局每日计划" in text
    # totally unknown -> en-US fallback
    text2 = t("xx-XX", "plan.title", date="2026-06-18", hours="6")
    assert "Global daily plan" in text2
    # dashboard renders without crashing under an unknown locale
    dash = build_dashboard(root, plan=None, plan_date="2026-06-18", locale="xx-XX")
    assert isinstance(dash, str)
