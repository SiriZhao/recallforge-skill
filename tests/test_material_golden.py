from __future__ import annotations

import json
from pathlib import Path

import pymupdf

from recallforge.ingestion.classifier import document_type
from recallforge.ingestion.native_parser import parse_native
from recallforge.ingestion.pipeline import ingest_file
from recallforge.ingestion.types import IngestOptions
from recallforge.state import workspace as workspace_mod

from ingestion_fixtures import (
    make_docx, make_exam_pdf, make_formula_pdf, make_pptx, make_scanned_pdf, make_text_pdf,
)


ROOT = Path(__file__).resolve().parent.parent
GOLDEN = json.loads((ROOT / "tests" / "golden" / "material-golden-cases.json").read_text(encoding="utf-8"))


def _workspace(root: Path) -> Path:
    workspace_mod.create_workspace(root, user_locale="zh-CN")
    workspace_mod.add_course_to_workspace(root, course_id="golden", course_name="Golden")
    return root


def test_golden_file_is_loadable_and_has_required_cases():
    assert set(GOLDEN["cases"]) == {
        "pptx_native", "digital_pdf", "scanned_pdf_no_provider",
        "formula_ambiguity", "past_paper", "docx_table",
    }


def test_golden_pptx_native(tmp_path: Path):
    pptx = make_pptx(tmp_path / "lecture.pptx", slides=2)
    pages = parse_native(pptx, document_type(pptx))
    assert len(pages) == GOLDEN["cases"]["pptx_native"]["expect"]["units"]
    assert [page.source_anchor for page in pages] == GOLDEN["cases"]["pptx_native"]["expect"]["source_anchors"]
    assert all(page.blocks for page in pages)


def test_golden_digital_pdf(tmp_path: Path):
    root = _workspace(tmp_path / "ws")
    pdf = make_text_pdf(
        tmp_path / "digital.pdf",
        body="Standard solution is a solution of known concentration.",
    )
    result = ingest_file(root, "golden", pdf, options=IngestOptions())
    assert result.page_statuses[0].status == "processed"
    assert result.evidence_added[0].extraction_method == "native_text"
    assert result.evidence_added[0].source_anchor.endswith("p. 1")


def test_golden_scanned_pdf_fails_closed_without_provider(tmp_path: Path):
    root = _workspace(tmp_path / "ws")
    pdf = make_scanned_pdf(tmp_path / "scan.pdf")
    result = ingest_file(root, "golden", pdf, options=IngestOptions())
    assert result.evidence_added == []
    assert result.page_statuses[0].status == "failed_with_reason"
    assert result.page_statuses[0].source_anchor.endswith("p. 1")


def test_golden_formula_ambiguity_stays_uncertain(tmp_path: Path):
    from recallforge.ingestion.formula_verify import extract_formula_regions

    pdf = make_formula_pdf(tmp_path / "formula.pdf", with_ambiguous=True)
    page = parse_native(pdf, document_type(pdf))[0]
    candidates = extract_formula_regions(page.raw_text, page.page_or_slide, page.formula_signals)
    ambiguous = [formula for formula in candidates if formula.signals]
    assert ambiguous
    assert all(formula.confidence < 0.5 for formula in ambiguous)


def test_golden_past_paper_keeps_question_structure(tmp_path: Path):
    root = _workspace(tmp_path / "ws")
    pdf = make_exam_pdf(tmp_path / "exam.pdf")
    result = ingest_file(
        root,
        "golden",
        pdf,
        options=IngestOptions(provider_name="synthetic", store_mode="demo"),
    )
    questions = result.evidence_added[0].content.get("exam_structure", [])
    assert len(questions) >= GOLDEN["cases"]["past_paper"]["expect"]["question_count_min"]
    assert questions[0]["options"]
    assert any(q["score"] for q in questions)
    assert any("系统误差" in q["body"] for q in questions)


def test_golden_docx_table_not_flattened(tmp_path: Path):
    docx = make_docx(tmp_path / "notes.docx", with_table=True)
    page = parse_native(docx, document_type(docx))[0]
    table = next(block for block in page.blocks if block["type"] == "table")
    assert table["headers"] == GOLDEN["cases"]["docx_table"]["expect"]["headers"]
    assert len(table["rows"]) == 3


def test_real_scanned_textbook_no_silent_drop(tmp_path: Path):
    """Generate a 12-page image-only textbook and verify every page is accounted for."""
    root = _workspace(tmp_path / "ws")
    pdf_path = tmp_path / "textbook-scan.pdf"
    doc = pymupdf.open()
    for index in range(12):
        page = doc.new_page(width=800, height=1000)
        text = f"Page {index + 1}: scanned textbook fixture"
        import io
        from PIL import Image, ImageDraw
        image = Image.new("RGB", (800, 1000), "white")
        draw = ImageDraw.Draw(image)
        try:
            from PIL import ImageFont
            font = ImageFont.truetype("arial.ttf", 30)
        except Exception:
            font = None
        draw.text((60, 80), text, fill="black", font=font)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        page.insert_image(page.rect, stream=buffer.getvalue())
    doc.save(str(pdf_path))
    doc.close()

    result = ingest_file(root, "golden", pdf_path, options=IngestOptions())
    assert len(result.page_statuses) == 12
    assert len(result.study_documents[0].pages) == 12
    assert all(status.status == "failed_with_reason" for status in result.page_statuses)
    assert len(result.unresolved_pages) == 12
