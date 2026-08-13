"""Small, reproducible Material Intelligence throughput benchmark.

This measures native parsing and routing only. It deliberately excludes host vision
and optional OCR because those depend on the selected host/provider and machine.
"""
from __future__ import annotations

import json
import platform
import time
from pathlib import Path

from recallforge.ingestion.catalog import catalog_to_dict, inspect_materials


def run(input_dir: str | Path) -> dict:
    root = Path(input_dir)
    files = sorted(path for path in root.rglob("*") if path.is_file())
    start = time.perf_counter()
    entries = inspect_materials(files)
    elapsed = time.perf_counter() - start
    units = sum(entry.units for entry in entries)
    return {
        "reference": {
            "os": platform.platform(),
            "python": platform.python_version(),
            "processor": platform.processor() or "not reported",
        },
        "dataset": str(root),
        "files": len(entries),
        "pages_or_slides": units,
        "elapsed_seconds": round(elapsed, 4),
        "pages_per_second": round(units / elapsed, 3) if elapsed else None,
        "native_units": sum(entry.native_units for entry in entries),
        "vision_units": sum(entry.vision_units for entry in entries),
        "unresolved_units": sum(entry.unresolved_units for entry in entries),
        "entries": catalog_to_dict(entries),
        "scope": "native structural scan only; excludes host vision and optional OCR",
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        raise SystemExit("usage: python benchmarks/material_ingestion.py <fixture-directory>")
    print(json.dumps(run(sys.argv[1]), ensure_ascii=False, indent=2))
