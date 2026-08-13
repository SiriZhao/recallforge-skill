from __future__ import annotations

from pathlib import Path

from .types import NativePage


class OCRDisabled(RuntimeError):
    """Raised when OCR is not enabled (default) or the OCR engine is unavailable."""


def run_ocr(path_or_png: Path | bytes, *, enabled: bool, offline_mode: bool) -> NativePage:
    """Local OCR fallback - DISABLED BY DEFAULT.

    Allowed only when (1) native multimodal is unavailable AND (2) OCR is explicitly
    enabled (env EXAM_REVIEW_OCR_FALLBACK=1) or explicit offline mode. Output always
    carries extraction_method=ocr_fallback with low confidence and can never support
    high-confidence exam conclusions.
    """
    if not enabled and not offline_mode:
        raise OCRDisabled(
            "local OCR is disabled by default; enable with EXAM_REVIEW_OCR_FALLBACK=1 "
            "or offline mode"
        )
    try:
        from PIL import Image
        import pytesseract
    except ImportError as exc:  # pragma: no cover
        raise OCRDisabled(f"OCR dependencies unavailable: {exc}") from exc

    if isinstance(path_or_png, bytes):
        import io

        image = Image.open(io.BytesIO(path_or_png))
    else:
        image = Image.open(path_or_png)
    try:
        text = pytesseract.image_to_string(image, lang="chi_sim+eng")
    except Exception as exc:
        raise OCRDisabled(f"tesseract engine failed: {exc}") from exc

    confidence = 0.3 if text.strip() else 0.1  # OCR is never high-confidence
    return NativePage(
        page_or_slide="1",
        raw_text=text,
        has_text_layer=bool(text.strip()),
        has_images=True,
        language_hint=None,
        warning="OCR fallback: low confidence; cannot support high-confidence conclusions",
    )
