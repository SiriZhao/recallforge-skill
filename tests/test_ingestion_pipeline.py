from __future__ import annotations

from pathlib import Path

from exam_review_skill.ingestion.evidence import read_evidence
from exam_review_skill.ingestion.pipeline import ingest_file
from exam_review_skill.ingestion.router import route_page
from exam_review_skill.ingestion.types import IngestOptions, NativePage
from exam_review_skill.state import course as course_mod
from exam_review_skill.state import workspace as workspace_mod

from ingestion_fixtures import (
    make_docx,
    make_exam_pdf,
    make_formula_pdf,
    make_mixed_language_pdf,
    make_pptx,
    make_scanned_pdf,
    make_text_pdf,
)


def _workspace_with_course(root: Path, course_id: str = "chem101") -> Path:
    workspace_mod.create_workspace(root, user_locale="zh-CN", daily_total_hours=6.0)
    workspace_mod.add_course_to_workspace(root, course_id=course_id, course_name="Chemistry")
    return root


def _demo_options() -> IngestOptions:
    return IngestOptions(provider_name="synthetic", store_mode="demo")


def test_text_pdf_uses_native_text(tmp_path: Path):
    root = _workspace_with_course(tmp_path / "ws")
    pdf = make_text_pdf(
        tmp_path / "notes.pdf",
        body="Standard solution is a solution of known concentration.\nTitration needs an indicator.",
    )
    result = ingest_file(root, "chem101", pdf, options=IngestOptions())
    assert result.documents_parsed == ["notes.pdf"]
    assert len(result.evidence_added) == 1
    evidence = result.evidence_added[0]
    assert evidence.extraction_method == "native_text"
    assert evidence.source_file == "notes.pdf"
    assert evidence.document_type == "pdf"
    assert evidence.page_or_slide == "1"
    assert "Standard solution" in evidence.content["text"]
    assert evidence.synthetic is False
    assert evidence.confidence >= 0.8


def test_scanned_pdf_without_provider_is_unresolved_not_faked(tmp_path: Path):
    root = _workspace_with_course(tmp_path / "ws")
    pdf = make_scanned_pdf(tmp_path / "scan.pdf")
    result = ingest_file(root, "chem101", pdf, options=IngestOptions())
    # no provider, no OCR -> page must be unresolved, never fabricated
    assert result.evidence_added == []
    assert result.unresolved_pages, "scanned page should be unresolved"
    assert any("no provider" in w for w in result.warnings)
    # and nothing persisted to real state
    assert read_evidence(root, "chem101") == []


def test_scanned_pdf_with_synthetic_provider_demo(tmp_path: Path):
    root = _workspace_with_course(tmp_path / "ws")
    pdf = make_scanned_pdf(tmp_path / "scan.pdf")
    result = ingest_file(root, "chem101", pdf, options=_demo_options())
    assert result.evidence_added
    evidence = result.evidence_added[0]
    assert evidence.extraction_method == "multimodal"
    assert evidence.synthetic is True  # clearly flagged
    records = read_evidence(root, "chem101")
    assert len(records) == 1
    assert records[0]["synthetic"] is True
    assert records[0]["extraction_method"] == "multimodal"


def test_pptx_uses_native_text_boxes(tmp_path: Path):
    root = _workspace_with_course(tmp_path / "ws")
    pptx = make_pptx(tmp_path / "lecture.pptx", slides=2)
    result = ingest_file(root, "chem101", pptx, options=IngestOptions())
    assert len(result.evidence_added) == 2  # one per slide
    first = result.evidence_added[0]
    assert first.extraction_method == "native_text"
    assert first.page_or_slide == "1"
    assert first.heading == "Lecture: Standard Solution"
    assert "Definition and calibration" in first.content["text"]


def test_docx_with_table_routes_to_vision_and_degrades_honestly(tmp_path: Path):
    root = _workspace_with_course(tmp_path / "ws")
    docx = make_docx(tmp_path / "notes.docx", with_table=True)
    page = NativePage(page_or_slide="1", raw_text="x", has_text_layer=True, table_signals=True)
    assert route_page(page).method == "vision"
    result = ingest_file(root, "chem101", docx, options=_demo_options())
    # LibreOffice is not installed here -> the visual render is unavailable.
    # The page must be recorded unresolved (never fabricated).
    assert result.evidence_added == []
    assert result.unresolved_pages
    assert any("LibreOffice" in w for w in result.warnings)
    # native text still routes to vision and the store stays empty (no fake content)
    assert read_evidence(root, "chem101") == []


def test_formula_ambiguity_stays_low_confidence(tmp_path: Path):
    root = _workspace_with_course(tmp_path / "ws")
    pdf = make_formula_pdf(tmp_path / "kinetics.pdf", with_ambiguous=True)
    result = ingest_file(root, "chem101", pdf, options=_demo_options())
    assert result.evidence_added
    record = result.evidence_added[0]
    formulas = record.content.get("formulas", [])
    assert formulas, "formula regions must be recorded"
    ambiguous = [f for f in formulas if f["signals"]]
    assert ambiguous, "x_1 / b^2 should be flagged ambiguous"
    for formula in ambiguous:
        assert formula["confidence"] < 0.5, "unconfirmed ambiguous formula must stay low-confidence"


def test_exam_paper_structure_is_preserved(tmp_path: Path):
    root = _workspace_with_course(tmp_path / "ws")
    pdf = make_exam_pdf(tmp_path / "exam.pdf")
    result = ingest_file(root, "chem101", pdf, options=_demo_options())
    assert result.evidence_added
    record = result.evidence_added[0]
    structure = record.content.get("exam_structure", [])
    assert len(structure) >= 3, "exam questions must be parsed, not flattened into a blob"
    q1 = next(q for q in structure if q["question_number"] == "1")
    assert len(q1["options"]) == 4
    assert q1["score"] in ("10", None)
    q2 = next(q for q in structure if q["question_number"] == "2")
    assert "系统误差" in q2["body"]


def test_mixed_language_page_keeps_language_hint(tmp_path: Path):
    root = _workspace_with_course(tmp_path / "ws")
    pdf = make_mixed_language_pdf(tmp_path / "bayes.pdf")
    result = ingest_file(root, "chem101", pdf, options=_demo_options())
    assert result.evidence_added
    record = result.evidence_added[0]
    assert record.source_language in ("mixed", None)
    assert "Bayes" in record.content.get("text_blocks", [{}])[0].get("text", "")


def test_router_decisions():
    native = NativePage(page_or_slide="1", raw_text="plain text", has_text_layer=True)
    assert route_page(native).method == "native_text"
    image_only = NativePage(page_or_slide="1", raw_text="", has_text_layer=False, has_images=True)
    assert route_page(image_only).method == "vision"
    formula = NativePage(page_or_slide="1", raw_text="a = b", has_text_layer=True, formula_signals=["math-tokens"])
    assert route_page(formula).method == "vision"
    exam = NativePage(page_or_slide="1", raw_text="1. question", has_text_layer=True, question_numbers=["1"])
    assert route_page(exam).method == "vision"
    table = NativePage(page_or_slide="1", raw_text="a | b", has_text_layer=True, table_signals=True)
    assert route_page(table).method == "vision"
    empty = NativePage(page_or_slide="1", raw_text="", has_text_layer=False, has_images=False)
    assert route_page(empty).method == "unresolved"


def test_incremental_ingestion_skips_unchanged_file(tmp_path: Path):
    root = _workspace_with_course(tmp_path / "ws")
    txt = tmp_path / "note.txt"
    txt.write_text("First version", encoding="utf-8")
    first = ingest_file(root, "chem101", txt, options=IngestOptions())
    assert len(first.evidence_added) == 1
    second = ingest_file(root, "chem101", txt, options=IngestOptions())
    assert second.evidence_added == []
    assert any("incremental" in w for w in second.warnings)
    # content-hash dedup also prevents duplicates on re-ingest after change
    txt.write_text("Second version", encoding="utf-8")
    third = ingest_file(root, "chem101", txt, options=IngestOptions())
    assert len(third.evidence_added) == 1
    assert read_evidence(root, "chem101")
