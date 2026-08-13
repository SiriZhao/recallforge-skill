from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable

from .classifier import document_type, is_supported
from .evidence import current_file_hash
from .native_parser import parse_native
from .router import route_page


@dataclass
class CatalogEntry:
    filename: str
    document_type: str
    units: int
    native_units: int = 0
    vision_units: int = 0
    unresolved_units: int = 0
    languages: list[str] = field(default_factory=list)
    file_hash: str = ""
    warnings: list[str] = field(default_factory=list)
    duplicate_of: str | None = None


def inspect_materials(paths: Iterable[str | Path]) -> list[CatalogEntry]:
    """Run the fast structural pass before expensive multimodal processing."""
    entries: list[CatalogEntry] = []
    seen_hashes: dict[str, str] = {}
    for raw in paths:
        path = Path(raw)
        if not path.is_file() or not is_supported(path):
            continue
        dtype = document_type(path)
        try:
            pages = parse_native(path, dtype)
        except Exception as exc:
            entries.append(CatalogEntry(path.name, dtype, 0, file_hash=current_file_hash(path), warnings=[f"parse failed: {exc}"]))
            continue
        file_hash = current_file_hash(path)
        entry = CatalogEntry(path.name, dtype, len(pages), file_hash=file_hash, duplicate_of=seen_hashes.get(file_hash))
        seen_hashes.setdefault(file_hash, path.name)
        for page in pages:
            route = route_page(page, document_type=dtype).method
            if route == "native_text": entry.native_units += 1
            elif route == "vision": entry.vision_units += 1
            else: entry.unresolved_units += 1
            if page.language_hint and page.language_hint not in entry.languages:
                entry.languages.append(page.language_hint)
        entries.append(entry)
    return entries


def catalog_to_dict(entries: list[CatalogEntry]) -> list[dict]:
    return [asdict(entry) for entry in entries]
