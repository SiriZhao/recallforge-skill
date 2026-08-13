from __future__ import annotations

from pathlib import Path

import pytest

from recallforge.ingestion.evidence import read_evidence
from recallforge.ingestion.ocr_fallback import OCRDisabled, run_ocr
from recallforge.ingestion.pipeline import ingest_file
from recallforge.ingestion.provider import (
    ProviderUnavailable,
    available_providers,
    get_provider,
    register_provider,
)
from recallforge.ingestion.types import IngestOptions
from recallforge.state import workspace as workspace_mod

from ingestion_fixtures import make_image, make_scanned_pdf


def _workspace_with_course(root: Path) -> Path:
    workspace_mod.create_workspace(root, user_locale="zh-CN")
    workspace_mod.add_course_to_workspace(root, course_id="chem101", course_name="Chemistry")
    return root


def test_handwriting_image_routes_to_vision(tmp_path: Path):
    root = _workspace_with_course(tmp_path / "ws")
    img = make_image(tmp_path / "note.png", kind="handwriting")
    result = ingest_file(
        root, "chem101", img, options=IngestOptions(provider_name="synthetic", store_mode="demo")
    )
    assert result.evidence_added
    evidence = result.evidence_added[0]
    assert evidence.document_type == "png"
    assert evidence.extraction_method == "multimodal"
    assert evidence.synthetic is True


def test_diagram_image(tmp_path: Path):
    root = _workspace_with_course(tmp_path / "ws")
    img = make_image(tmp_path / "diagram.jpg", kind="diagram")
    result = ingest_file(
        root, "chem101", img, options=IngestOptions(provider_name="synthetic", store_mode="demo")
    )
    assert result.evidence_added
    assert result.evidence_added[0].document_type == "jpg"


def test_multimodal_provider_failure_is_unresolved_not_faked(tmp_path: Path):
    root = _workspace_with_course(tmp_path / "ws")
    pdf = make_scanned_pdf(tmp_path / "scan.pdf")
    # "openai" is registered but not configured -> understand_page fails closed
    result = ingest_file(root, "chem101", pdf, options=IngestOptions(provider_name="openai"))
    assert result.evidence_added == []
    assert result.unresolved_pages
    assert any("provider" in w.lower() for w in result.warnings)
    assert read_evidence(root, "chem101") == []


def test_provider_unavailable_for_unset_env():
    provider = get_provider("openai")
    assert provider.is_available() is False
    from recallforge.ingestion.types import RenderedPage

    with pytest.raises(ProviderUnavailable):
        provider.understand_page(
            RenderedPage(page_or_slide="1", image_png=b"x", width=1, height=1, dpi=72, source="test")
        )


def test_provider_registry_is_extensible():
    class MyProvider:
        name = "my-vendor"

    register_provider("my-vendor", lambda: MyProvider())
    assert "my-vendor" in available_providers()
    assert "synthetic" in available_providers()
    assert get_provider("my-vendor").name == "my-vendor"
    with pytest.raises(ProviderUnavailable):
        get_provider("")


def test_ocr_disabled_by_default():
    with pytest.raises(OCRDisabled) as exc:
        run_ocr(b"not-an-image", enabled=False, offline_mode=False)
    assert "disabled" in str(exc.value)


def test_ocr_enabled_but_engine_unavailable_never_fabricates(tmp_path: Path):
    root = _workspace_with_course(tmp_path / "ws")
    pdf = make_scanned_pdf(tmp_path / "scan.pdf")
    result = ingest_file(
        root,
        "chem101",
        pdf,
        options=IngestOptions(
            allow_ocr_fallback=True,
            store_mode="demo",
            ocr_engine="engine-that-does-not-exist",
        ),
    )
    assert result.evidence_added == []
    assert result.unresolved_pages
    assert any("ocr" in w.lower() or "OCR" in w for w in result.warnings)


def test_real_ocr_fallback_when_engine_available(tmp_path: Path):
    """Run the actual local OCR path when a usable engine is installed."""
    from PIL import Image, ImageDraw, ImageFont
    from recallforge.ingestion.ocr_fallback import OCRDisabled, run_ocr

    img = Image.new("RGB", (600, 200), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except Exception:
        font = None
    draw.text((30, 60), "Concentration C = n / V", fill="black", font=font)
    buf_path = tmp_path / "ocr-sample.png"
    img.save(buf_path)
    try:
        page = run_ocr(
            buf_path,
            enabled=True,
            offline_mode=False,
            engine="tesseract",
            language="eng",
        )
    except OCRDisabled as exc:
        pytest.skip(f"tesseract not usable here: {exc}")
    assert page.raw_text.strip()
    assert page.warning and "low confidence" in page.warning
    assert "Concentration" in page.raw_text or "concentration" in page.raw_text
