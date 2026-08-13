from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .types import RenderedPage


def cache_key(*, file_hash: str, page_or_slide: str, profile: str, dpi: int) -> str:
    payload = f"{file_hash}|{page_or_slide}|{profile}|{dpi}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_render(cache_dir: str | Path | None, *, key: str) -> RenderedPage | None:
    if not cache_dir:
        return None
    root = Path(cache_dir)
    meta = root / f"{key}.json"
    image = root / f"{key}.png"
    if not meta.is_file() or not image.is_file():
        return None
    try:
        data = json.loads(meta.read_text(encoding="utf-8"))
        return RenderedPage(image_png=image.read_bytes(), **data)
    except Exception:
        return None


def save_render(cache_dir: str | Path | None, *, key: str, page: RenderedPage) -> None:
    if not cache_dir:
        return
    root = Path(cache_dir)
    root.mkdir(parents=True, exist_ok=True)
    (root / f"{key}.png").write_bytes(page.image_png)
    (root / f"{key}.json").write_text(json.dumps({
        "page_or_slide": page.page_or_slide, "width": page.width,
        "height": page.height, "dpi": page.dpi, "source": page.source,
    }, sort_keys=True), encoding="utf-8")
