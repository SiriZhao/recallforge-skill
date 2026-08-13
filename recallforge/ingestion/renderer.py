from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from .types import RenderedPage


def render_pdf_pages(path: Path, dpi: int = 150) -> list[RenderedPage]:
    """Render every PDF page to a PNG via PyMuPDF. Native, no external binary."""
    import pymupdf

    doc = pymupdf.open(str(path))
    pages: list[RenderedPage] = []
    try:
        for i, page in enumerate(doc, 1):
            pix = page.get_pixmap(dpi=dpi)
            pages.append(
                RenderedPage(
                    page_or_slide=str(i),
                    image_png=pix.tobytes("png"),
                    width=pix.width,
                    height=pix.height,
                    dpi=dpi,
                    source="pymupdf",
                )
            )
    finally:
        doc.close()
    return pages


def find_soffice() -> str | None:
    """Locate LibreOffice for PPTX/DOCX visual rendering (optional)."""
    exe = shutil.which("soffice")
    if exe:
        return exe
    candidates = [
        Path(r"C:\Program Files\LibreOffice\program\soffice.exe"),
        Path(r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None


def render_office_pages(
    path: Path,
    *,
    soffice: str | None = None,
    dpi: int = 150,
) -> list[RenderedPage] | None:
    """Render PPTX/DOCX pages via LibreOffice. Returns None when unavailable
    (graceful degradation - the caller keeps native text only)."""
    soffice = soffice or find_soffice()
    if soffice is None:
        return None
    if path.suffix.lower() not in (".pptx", ".docx"):
        return None
    from .native_parser import _parse_pptx, _parse_docx
    from .types import NativePage

    with tempfile.TemporaryDirectory() as tmp:
        out_dir = Path(tmp) / "pdf"
        out_dir.mkdir()
        proc = subprocess.run(
            [soffice, "--headless", "--convert-to", "pdf", "--outdir", str(out_dir), str(path)],
            capture_output=True,
            timeout=120,
        )
        if proc.returncode != 0:
            return None
        pdfs = list(out_dir.glob("*.pdf"))
        if not pdfs:
            return None
        return render_pdf_pages(pdfs[0], dpi=dpi)


def render_input_image(path: Path) -> RenderedPage:
    from PIL import Image

    with Image.open(path) as img:
        rgb = img.convert("RGB")
        import io

        buf = io.BytesIO()
        rgb.save(buf, format="PNG")
        width, height = rgb.size
    return RenderedPage(
        page_or_slide="1",
        image_png=buf.getvalue(),
        width=width,
        height=height,
        dpi=72,
        source="input_image",
    )
