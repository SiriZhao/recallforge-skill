from __future__ import annotations

import hashlib
from pathlib import Path


def ocr_image(path: Path, cache_dir: Path, warnings: list[str]) -> tuple[str, float]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(str(path.resolve()).encode("utf-8")).hexdigest()
    cache_file = cache_dir / f"{key}.txt"
    if cache_file.exists():
        return cache_file.read_text(encoding="utf-8", errors="ignore"), 0.7
    try:
        from PIL import Image
        import pytesseract

        text = pytesseract.image_to_string(Image.open(path), lang="chi_sim+eng")
        confidence = 0.65 if text.strip() else 0.2
        cache_file.write_text(text, encoding="utf-8")
        return text, confidence
    except Exception as exc:
        warnings.append(f"OCR unavailable or failed for {path.name}: {exc}. 已继续流程。")
        return "", 0.0
