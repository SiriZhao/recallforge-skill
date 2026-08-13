from __future__ import annotations

from pathlib import Path

import pytest

from recallforge.ingestion.evidence import read_evidence, write_evidence
from recallforge.ingestion.pipeline import ingest_file
from recallforge.ingestion.types import Evidence, IngestOptions
from recallforge.state import course as course_mod
from recallforge.state import workspace as workspace_mod
from recallforge.state.isolation import StateContaminationError, find_mock_markers

from ingestion_fixtures import make_scanned_pdf


def _workspace_with_course(root: Path) -> Path:
    workspace_mod.create_workspace(root, user_locale="zh-CN")
    workspace_mod.add_course_to_workspace(root, course_id="chem101", course_name="Chemistry")
    return root


def test_synthetic_record_rejected_from_real_store(tmp_path: Path):
    root = _workspace_with_course(tmp_path / "ws")
    pdf = make_scanned_pdf(tmp_path / "scan.pdf")
    # synthetic provider + real store -> the write must be rejected
    with pytest.raises(StateContaminationError):
        ingest_file(
            root, "chem101", pdf, options=IngestOptions(provider_name="synthetic", store_mode="real")
        )
    assert read_evidence(root, "chem101") == []


def test_synthetic_allowed_only_in_demo_mode(tmp_path: Path):
    root = _workspace_with_course(tmp_path / "ws")
    pdf = make_scanned_pdf(tmp_path / "scan.pdf")
    result = ingest_file(
        root, "chem101", pdf, options=IngestOptions(provider_name="synthetic", store_mode="demo")
    )
    assert result.evidence_added
    records = read_evidence(root, "chem101")
    assert len(records) == 1
    assert records[0]["synthetic"] is True


def test_direct_write_evidence_rejects_synthetic(tmp_path: Path):
    root = _workspace_with_course(tmp_path / "ws")
    evidence = Evidence(
        course_id="chem101",
        source_file="fake.pdf",
        document_type="pdf",
        page_or_slide="1",
        extraction_method="multimodal",
        confidence=0.5,
        evidence_weight=1.0,
        content={"text": "x"},
        synthetic=True,
    )
    with pytest.raises(StateContaminationError):
        write_evidence(root, "chem101", [evidence], store_mode="real")


def test_marker_detection_finds_synthetic_flag():
    hits = find_mock_markers({"course_id": "x", "records": [{"synthetic": True}]})
    assert hits
    hits = find_mock_markers({"course_id": "x", "records": [{"synthetic": False}]})
    assert hits == []


def test_no_mock_content_in_real_state_after_clean_ingest(tmp_path: Path):
    root = _workspace_with_course(tmp_path / "ws")
    txt = tmp_path / "note.txt"
    txt.write_text("Clean real notes without any mock markers.", encoding="utf-8")
    result = ingest_file(root, "chem101", txt, options=IngestOptions())
    assert result.evidence_added
    records = read_evidence(root, "chem101")
    assert records[0]["synthetic"] is False
    assert find_mock_markers(records) == []
