from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


@dataclass
class Region:
    """A spatial region on a page/slide, used for formula/table/figure targeting."""

    page_or_slide: str
    bbox: list[float] | None = None  # [x0, y0, x1, y1] in PDF points
    region_type: str = "text"  # text | formula | table | figure | diagram | handwriting | answer_area
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class NativePage:
    """Output of the native parser for one page/slide."""

    page_or_slide: str
    raw_text: str = ""
    has_text_layer: bool = False
    has_images: bool = False
    heading: str | None = None
    question_numbers: list[str] = field(default_factory=list)
    formula_signals: list[str] = field(default_factory=list)  # e.g. "subscript", "fraction"
    table_signals: bool = False
    language_hint: str | None = None
    warning: str | None = None
    blocks: list[dict[str, Any]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    native_confidence: float = 0.0
    image_coverage: float = 0.0
    suspicious_char_ratio: float = 0.0
    rotation: int = 0
    visual_emphasis: list[dict[str, Any]] = field(default_factory=list)
    source_anchor: str = ""
    page_hash: str = ""


@dataclass
class RenderedPage:
    """A page rendered to an image, ready for multimodal understanding."""

    page_or_slide: str
    image_png: bytes
    width: int
    height: int
    dpi: int
    source: str  # "pymupdf" | "soffice" | "input_image"


@dataclass
class FormulaRegion:
    """Detected formula with its raw text and ambiguity signals."""

    region: Region
    text: str
    signals: list[str] = field(default_factory=list)
    confidence: float = 0.5


@dataclass
class ExamQuestion:
    question_number: str
    body: str = ""
    options: list[str] = field(default_factory=list)
    figure_refs: list[str] = field(default_factory=list)
    subquestions: list[dict] = field(default_factory=list)
    score: str | None = None
    answer_area: str | None = None
    handwritten_annotation: str | None = None
    printed_answer: str | None = None
    user_annotation: str | None = None
    annotation_type: str = "unknown"
    confidence: float = 0.5


@dataclass
class ExamPageStructure:
    page_or_slide: str
    questions: list[ExamQuestion] = field(default_factory=list)
    confidence: float = 0.5


@dataclass
class ProviderUnderstanding:
    """Structured understanding of one rendered page from a multimodal provider."""

    page_or_slide: str
    text_blocks: list[dict] = field(default_factory=list)
    formulas: list[FormulaRegion] = field(default_factory=list)
    tables: list[dict] = field(default_factory=list)
    figures: list[dict] = field(default_factory=list)
    handwriting: list[dict] = field(default_factory=list)
    exam: ExamPageStructure | None = None
    source_language: str | None = None
    confidence: float = 0.5
    synthetic: bool = False
    method: str = "multimodal"
    warning: str | None = None


@dataclass
class Evidence:
    """Unified evidence object written to the per-course evidence store."""

    course_id: str
    source_file: str
    document_type: str
    page_or_slide: str
    extraction_method: str  # native_text | multimodal | ocr_fallback
    confidence: float
    evidence_weight: float
    content: dict[str, Any]
    region: dict[str, Any] = field(default_factory=dict)
    heading: str | None = None
    question_number: str | None = None
    source_language: str | None = None
    synthetic: bool = False
    content_hash: str = ""
    evidence_id: str = ""
    created_at: str = field(default_factory=_now_iso)

    @property
    def source_anchor(self) -> str:
        label = "slide" if self.document_type == "pptx" else "p."
        return f"{self.source_file}, {label} {self.page_or_slide}"


@dataclass
class MaterialPage:
    """One page/slide in RecallForge's normalized StudyDocument IR."""

    index: str
    source_anchor: str
    title: str | None = None
    blocks: list[dict[str, Any]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    confidence: float = 0.0
    route: str = "unresolved"
    processing_level: str = "fast"
    status: str = "pending"
    warnings: list[str] = field(default_factory=list)
    page_hash: str = ""


@dataclass
class StudyDocument:
    """Host-neutral normalized representation consumed by later review stages."""

    document_id: str
    filename: str
    document_type: str
    file_hash: str
    language: str | None = None
    pages: list[MaterialPage] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class PageProcessingStatus:
    source_anchor: str
    status: str
    route: str
    processing_level: str
    reason: str = ""


@dataclass
class IngestOptions:
    """Pipeline options. Fail-closed by default: no vision provider, no OCR."""

    provider_name: str = ""  # empty -> no multimodal provider
    allow_ocr_fallback: bool = False
    offline_mode: bool = False
    store_mode: str = "real"  # "real" rejects synthetic records; "demo"/"test" allows
    cache_dir: str | None = None
    min_visual_confidence: float = 0.6
    ocr_engine: str = "tesseract"
    ocr_language: str | None = None


@dataclass
class IngestResult:
    documents_seen: list[str] = field(default_factory=list)
    documents_parsed: list[str] = field(default_factory=list)
    evidence_added: list[Evidence] = field(default_factory=list)
    evidence_duplicates: int = 0
    unresolved_pages: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    page_statuses: list[PageProcessingStatus] = field(default_factory=list)
    study_documents: list[StudyDocument] = field(default_factory=list)

    def warn(self, message: str) -> None:
        if message not in self.warnings:
            self.warnings.append(message)


def evidence_to_dict(evidence: Evidence) -> dict:
    return {
        "evidence_id": evidence.evidence_id,
        "course_id": evidence.course_id,
        "source_file": evidence.source_file,
        "document_type": evidence.document_type,
        "page_or_slide": evidence.page_or_slide,
        "heading": evidence.heading,
        "question_number": evidence.question_number,
        "region": evidence.region,
        "source_language": evidence.source_language,
        "extraction_method": evidence.extraction_method,
        "confidence": evidence.confidence,
        "evidence_weight": evidence.evidence_weight,
        "content": evidence.content,
        "synthetic": evidence.synthetic,
        "content_hash": evidence.content_hash,
        "created_at": evidence.created_at,
        "source_anchor": evidence.source_anchor,
    }
