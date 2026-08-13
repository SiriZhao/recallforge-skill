"""Self-authored OCR benchmark fixtures with human-confirmed ground truth.

All fixtures are generated at runtime from exact text strings. Nothing from
copyrighted textbooks or private study materials is used.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path

from PIL import Image


def _font_for(text: str) -> str:
    return "china-s" if any("\u4e00" <= ch <= "\u9fff" for ch in text) else "helv"


def _new_page(doc, width: int = 900, height: int = 1100):
    return doc.new_page(width=width, height=height)


def _insert(page, x: float, y: float, text: str, size: float = 28):
    page.insert_textbox(
        (x, y, 840, y + 500),
        text,
        fontsize=size,
        fontname=_font_for(text),
        lineheight=1.25,
    )


def _page_to_png(page, dpi: int = 200) -> Image.Image:
    pix = page.get_pixmap(dpi=dpi)
    return Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")


@dataclass
class OcrFixture:
    name: str
    ground_truth: str
    image: Image.Image
    language: str
    kind: str


def build_fixtures(tmp: Path) -> list[OcrFixture]:
    import pymupdf

    fixtures: list[OcrFixture] = []

    # OCR-01 English clean scan
    eng_truth = (
        "The standard solution is a solution of known concentration. "
        "Titration requires an indicator and a burette."
    )
    doc = pymupdf.open()
    page = _new_page(doc)
    _insert(page, 70, 90, "Standard Solution", 36)
    _insert(page, 70, 170, eng_truth, 26)
    fixtures.append(OcrFixture("OCR-01-english-clean", eng_truth, _page_to_png(page, 200), "eng", "text"))
    doc.close()

    # OCR-02 Chinese clean scan
    zh_truth = "标准溶液是已知浓度的溶液。滴定分析需要使用指示剂和滴定管。"
    doc = pymupdf.open()
    page = _new_page(doc)
    _insert(page, 70, 120, "标准溶液", 40)
    _insert(page, 70, 210, zh_truth, 28)
    fixtures.append(OcrFixture("OCR-02-chinese-clean", zh_truth, _page_to_png(page, 200), "chi_sim", "text"))
    doc.close()

    # OCR-03 Mixed Chinese-English
    mixed_truth = (
        "贝叶斯定理用于条件概率计算。P(A|B) = P(B|A) * P(A) / P(B)。"
        "其中 A 和 B 是事件。"
    )
    doc = pymupdf.open()
    page = _new_page(doc)
    _insert(page, 70, 120, "Bayes theorem", 36)
    _insert(page, 70, 200, mixed_truth, 26)
    fixtures.append(OcrFixture("OCR-03-mixed", mixed_truth, _page_to_png(page, 200), "chi_sim+eng", "mixed"))
    doc.close()

    # OCR-04 Low-resolution English
    low_truth = (
        "Photosynthesis converts light energy into chemical energy. "
        "Chlorophyll absorbs red and blue light."
    )
    doc = pymupdf.open()
    page = _new_page(doc)
    _insert(page, 70, 110, "Photosynthesis", 34)
    _insert(page, 70, 190, low_truth, 24)
    fixtures.append(OcrFixture("OCR-04-low-resolution", low_truth, _page_to_png(page, 72), "eng", "low_quality"))
    doc.close()

    # OCR-05 Rotated (3 degrees)
    rot_truth = (
        "Meiosis produces four haploid cells. "
        "Each cell contains one copy of every chromosome."
    )
    doc = pymupdf.open()
    page = _new_page(doc)
    _insert(page, 80, 140, rot_truth, 26)
    rotated = _page_to_png(page, 180).rotate(3, expand=True, fillcolor="white")
    fixtures.append(OcrFixture("OCR-05-rotated", rot_truth, rotated, "eng", "rotated"))
    doc.close()

    # OCR-06 Two-column
    left_truth = "The nucleus stores genetic material. Transcription happens in the nucleus."
    right_truth = "Translation happens at the ribosome. Proteins fold into their final shape."
    doc = pymupdf.open()
    page = _new_page(doc)
    page.insert_textbox(
        (60, 90, 430, 500), left_truth, fontsize=24,
        fontname=_font_for(left_truth), lineheight=1.25,
    )
    page.insert_textbox(
        (490, 90, 850, 500), right_truth, fontsize=24,
        fontname=_font_for(right_truth), lineheight=1.25,
    )
    two_col_truth = left_truth + " " + right_truth
    fixtures.append(OcrFixture("OCR-06-two-column", two_col_truth, _page_to_png(page, 200), "eng", "two_column"))
    doc.close()

    # OCR-07 Exam paper
    exam_truth = (
        "1. 标准溶液的定义是什么？\n"
        "A. 已知浓度的溶液\n"
        "B. 未知浓度的溶液\n"
        "C. 不需要标定\n"
        "D. 必须立即使用\n"
        "2. 系统误差和偶然误差有什么区别？"
    )
    doc = pymupdf.open()
    page = _new_page(doc)
    _insert(page, 60, 80, "期末试卷", 34)
    _insert(page, 60, 160, exam_truth, 24)
    fixtures.append(OcrFixture("OCR-07-exam-paper", exam_truth, _page_to_png(page, 200), "chi_sim", "exam"))
    doc.close()

    # OCR-08 Formula context (formula itself is not scored as visual perfection)
    formula_truth = (
        "条件概率公式：P(A|B) = P(A∩B) / P(B)。"
        "独立事件满足 P(A∩B) = P(A)P(B)。"
    )
    doc = pymupdf.open()
    page = _new_page(doc)
    _insert(page, 70, 110, "Conditional probability", 34)
    _insert(page, 70, 190, formula_truth, 26)
    fixtures.append(OcrFixture("OCR-08-formula-context", formula_truth, _page_to_png(page, 220), "chi_sim+eng", "formula_context"))
    doc.close()

    # OCR-09 Table (3x3 with header)
    table_truth = (
        "术语 定义\n"
        "标准溶液 已知浓度的溶液\n"
        "指示剂 判断滴定终点"
    )
    doc = pymupdf.open()
    page = _new_page(doc)
    # Header
    _insert(page, 80, 90, "术语", 28)
    _insert(page, 330, 90, "定义", 28)
    _insert(page, 80, 170, "标准溶液", 24)
    _insert(page, 330, 170, "已知浓度的溶液", 24)
    _insert(page, 80, 250, "指示剂", 24)
    _insert(page, 330, 250, "判断滴定终点", 24)
    for y in (60, 130, 210, 290):
        page.draw_line((60, y), (860, y), color=(0, 0, 0), width=2)
    for x in (60, 320, 860):
        page.draw_line((x, 60), (x, 290), color=(0, 0, 0), width=2)
    fixtures.append(OcrFixture("OCR-09-table", table_truth, _page_to_png(page, 200), "chi_sim", "table"))
    doc.close()

    # OCR-10 Annotation overlap (handwritten B? must not become printed answer)
    annot_truth = "标准溶液是已知浓度的溶液。指示剂用于判断滴定终点。"
    doc = pymupdf.open()
    page = _new_page(doc)
    _insert(page, 70, 120, annot_truth, 26)
    img = _page_to_png(page, 200)
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arialbd.ttf", 64)
    except Exception:
        font = None
    draw.text((300, 80), "B?", fill=(220, 38, 38), font=font)
    fixtures.append(OcrFixture("OCR-10-annotation-overlap", annot_truth, img, "chi_sim", "annotation"))
    doc.close()

    for fixture in fixtures:
        fixture.image.save(tmp / f"{fixture.name}.png")
        fixture.image.close()
    return fixtures
