from __future__ import annotations

from pathlib import Path

SUPPORTED_EXTENSIONS = {".pdf", ".pptx", ".docx", ".txt", ".md", ".png", ".jpg", ".jpeg"}

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}


def document_type(path: str | Path) -> str:
    """Classify the physical file format (not the pedagogical role).

    This is the first stage of the unified pipeline: File -> Classifier.
    """
    ext = Path(path).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"unsupported document extension: {ext!r}")
    if ext == ".jpeg":
        return "jpg"
    return ext.lstrip(".")


def is_image(path: str | Path) -> bool:
    return Path(path).suffix.lower() in IMAGE_EXTENSIONS


def is_supported(path: str | Path) -> bool:
    return Path(path).suffix.lower() in SUPPORTED_EXTENSIONS
