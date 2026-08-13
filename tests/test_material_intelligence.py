from __future__ import annotations

from pathlib import Path

from recallforge.ingestion.catalog import inspect_materials
from recallforge.ingestion.cache import cache_key, load_render, save_render
from recallforge.ingestion.classifier import document_type
from recallforge.ingestion.native_parser import parse_native
from recallforge.ingestion.pipeline import ingest_file
from recallforge.ingestion.types import IngestOptions
from recallforge.ingestion.types import RenderedPage
from recallforge.state import workspace as workspace_mod

from ingestion_fixtures import make_docx, make_image, make_pptx, make_scanned_pdf, make_text_pdf


def _workspace(root: Path) -> Path:
    workspace_mod.create_workspace(root, user_locale="en-US")
    workspace_mod.add_course_to_workspace(root, course_id="course", course_name="Material Intelligence")
    return root


def test_webp_is_supported_and_routes_to_vision(tmp_path: Path):
    image = make_image(tmp_path / "diagram.png", kind="diagram")
    from PIL import Image
    webp = tmp_path / "diagram.webp"
    with Image.open(image) as source:
        source.save(webp, format="WEBP")
    assert document_type(webp) == "webp"
    pages = parse_native(webp, "webp")
    assert pages[0].has_images and not pages[0].has_text_layer


def test_pptx_ir_preserves_title_blocks_notes_and_source_anchor(tmp_path: Path):
    pptx = make_pptx(tmp_path / "lecture.pptx", slides=2)
    pages = parse_native(pptx, "pptx")
    assert pages[0].heading == "Lecture: Standard Solution"
    assert pages[0].blocks
    assert pages[0].source_anchor == "lecture.pptx, slide 1"
    assert pages[0].page_hash


def test_docx_table_is_not_flattened_in_native_ir(tmp_path: Path):
    docx = make_docx(tmp_path / "notes.docx", with_table=True)
    page = parse_native(docx, "docx")[0]
    table = next(block for block in page.blocks if block["type"] == "table")
    assert table["headers"] == ["Functional group", "Reaction"]
    assert table["rows"][1] == ["-OH", "esterification"]


def test_fast_catalog_reports_every_unit_and_route(tmp_path: Path):
    pdf = make_text_pdf(tmp_path / "digital.pdf")
    scan = make_scanned_pdf(tmp_path / "scan.pdf")
    entries = inspect_materials([pdf, scan])
    assert len(entries) == 2
    for entry in entries:
        assert entry.units == entry.native_units + entry.vision_units + entry.unresolved_units
        assert entry.file_hash
    assert next(e for e in entries if e.filename == "scan.pdf").vision_units == 1


def test_catalog_marks_exact_duplicate_files(tmp_path: Path):
    first = make_text_pdf(tmp_path / "a.pdf")
    second = tmp_path / "b.pdf"
    second.write_bytes(first.read_bytes())
    entries = inspect_materials([first, second])
    assert entries[0].duplicate_of is None
    assert entries[1].duplicate_of == "a.pdf"


def test_render_cache_key_includes_profile_and_round_trips(tmp_path: Path):
    key = cache_key(file_hash="abc", page_or_slide="1", profile="precision", dpi=220)
    assert key != cache_key(file_hash="abc", page_or_slide="1", profile="fast", dpi=150)
    page = RenderedPage("1", b"png", 10, 20, 220, "test")
    save_render(tmp_path, key=key, page=page)
    assert load_render(tmp_path, key=key) == page


def test_zero_silent_page_drop_and_study_document_ir(tmp_path: Path):
    root = _workspace(tmp_path / "ws")
    scan = make_scanned_pdf(tmp_path / "scan.pdf")
    result = ingest_file(root, "course", scan, options=IngestOptions())
    assert len(result.page_statuses) == 1
    assert result.page_statuses[0].status == "failed_with_reason"
    assert len(result.study_documents) == 1
    assert len(result.study_documents[0].pages) == 1
    assert result.study_documents[0].pages[0].source_anchor == "scan.pdf, p. 1"


def test_native_text_is_kept_when_visual_verification_is_unavailable(tmp_path: Path):
    root = _workspace(tmp_path / "ws")
    docx = make_docx(tmp_path / "table.docx", with_table=True)
    result = ingest_file(root, "course", docx, options=IngestOptions(provider_name="synthetic", store_mode="demo"))
    assert len(result.evidence_added) == 1
    evidence = result.evidence_added[0]
    assert evidence.content["unresolved_visual"] is True
    assert evidence.source_anchor == "table.docx, p. 1"
    assert result.page_statuses[0].status == "processed_with_warning"
