"""Build self-authored fixtures and benchmark the native Material Intelligence pass."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from benchmarks.material_ingestion import run


def main() -> None:
    from tests.ingestion_fixtures import (
        make_docx, make_exam_pdf, make_formula_pdf, make_image,
        make_mixed_language_pdf, make_pptx, make_scanned_pdf, make_text_pdf,
    )
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_text_pdf(root / "digital.pdf")
        make_scanned_pdf(root / "scan-en.pdf")
        make_scanned_pdf(root / "scan-zh.pdf", text="Chinese scan fixture")
        make_mixed_language_pdf(root / "mixed.pdf")
        make_formula_pdf(root / "formula.pdf")
        make_exam_pdf(root / "two-column-exam.pdf")
        make_pptx(root / "lecture.pptx")
        make_docx(root / "table.docx")
        make_image(root / "low-quality.jpg", kind="handwriting")
        make_image(root / "organic-structure.png", kind="diagram")
        make_image(root / "botany-diagram.webp", kind="diagram")
        print(json.dumps(run(root), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
