from __future__ import annotations

import re
from pathlib import Path

from .classifier import document_type, is_image
from .evidence import (
    current_file_hash,
    load_processed_files,
    mark_file_processed,
    write_evidence,
)
from .exam_parser import merge_provider_exam_structure, parse_exam_page
from .formula_verify import extract_formula_regions, verify_formula_visually
from .native_parser import parse_native
from .ocr_fallback import OCRDisabled, run_ocr
from .provider import ProviderUnavailable, get_provider
from .renderer import render_input_image, render_pdf_pages
from .router import route_page
from .types import (
    Evidence,
    IngestOptions,
    IngestResult,
    NativePage,
    ProviderUnderstanding,
    RenderedPage,
)

DOCUMENT_WEIGHT = {
    "pdf": 1.0,
    "pptx": 1.0,
    "docx": 1.0,
    "txt": 0.9,
    "md": 0.9,
    "png": 1.1,
    "jpg": 1.1,
}

EXAM_FILENAME_MARKERS = ("exam", "test", "试卷", "真题", "期末", "考题", "past", "pastpaper")


def _role_hint(filename: str, text: str) -> str | None:
    """Role hint from the filename (reliable) - prose that merely mentions 'exam
    points' must never force vision routing. Structural routing for real exam
    papers happens through page.question_numbers in the router."""
    name = filename.lower()
    if any(marker in name for marker in EXAM_FILENAME_MARKERS):
        return "answer_key" if "answer" in name else "past_exam"
    return None


def _heading_from_page(page: NativePage) -> str | None:
    if page.heading:
        return page.heading
    for line in page.raw_text.splitlines():
        line = line.strip()
        if line and len(line) <= 60 and not re.match(r"^[\d\s.、．]+$", line):
            return line
    return None


def _make_evidence(
    *,
    course_id: str,
    source_file: str,
    document_type_name: str,
    page: NativePage,
    extraction_method: str,
    confidence: float,
    content: dict,
    synthetic: bool,
    question_number: str | None = None,
    heading: str | None = None,
    region: dict | None = None,
    source_language: str | None = None,
) -> Evidence:
    content_hash = ""
    evidence = Evidence(
        course_id=course_id,
        source_file=source_file,
        document_type=document_type_name,
        page_or_slide=page.page_or_slide,
        extraction_method=extraction_method,
        confidence=confidence,
        evidence_weight=DOCUMENT_WEIGHT.get(document_type_name, 1.0),
        content=content,
        region=region or {},
        heading=heading or _heading_from_page(page),
        question_number=question_number,
        source_language=source_language or page.language_hint,
        synthetic=synthetic,
    )
    from .evidence import _content_hash

    evidence.content_hash = _content_hash(evidence)
    evidence.evidence_id = f"EV-{evidence.content_hash[:8].upper()}"
    return evidence


def _evidence_from_provider(
    *,
    course_id: str,
    source_file: str,
    document_type_name: str,
    page: NativePage,
    understanding: ProviderUnderstanding,
    rendered: RenderedPage | None,
    min_visual_confidence: float,
) -> list[Evidence]:
    """Build evidence from provider structured output. Formulas that remain
    ambiguous after visual review stay low-confidence and can never support
    high-confidence exam conclusions."""
    records: list[Evidence] = []
    confidence = max(understanding.confidence, min_visual_confidence * 0.9)
    content: dict = {
        "text_blocks": understanding.text_blocks,
        "tables": understanding.tables,
        "figures": understanding.figures,
        "handwriting": understanding.handwriting,
        "formulas": [
            {"text": f.text, "signals": f.signals, "confidence": round(f.confidence, 2)}
            for f in understanding.formulas
        ],
    }
    # exam structure is preserved field-by-field, never flattened into a text blob
    if understanding.exam and understanding.exam.questions:
        content["exam_structure"] = [
            {
                "question_number": q.question_number,
                "body": q.body,
                "options": q.options,
                "figure_refs": q.figure_refs,
                "subquestions": q.subquestions,
                "score": q.score,
                "answer_area": q.answer_area,
                "handwritten_annotation": q.handwritten_annotation,
                "confidence": round(q.confidence, 2),
            }
            for q in understanding.exam.questions
        ]
    records.append(
        _make_evidence(
            course_id=course_id,
            source_file=source_file,
            document_type_name=document_type_name,
            page=page,
            extraction_method=understanding.method,
            confidence=confidence,
            content=content,
            synthetic=understanding.synthetic,
            source_language=understanding.source_language or page.language_hint,
        )
    )
    return records


def _process_vision_page(
    *,
    course_id: str,
    source_file: str,
    document_type_name: str,
    page: NativePage,
    rendered: RenderedPage,
    provider,
    options: IngestOptions,
    result: IngestResult,
) -> list[Evidence]:
    understanding = provider.understand_page(
        rendered, native_text=page.raw_text, context={"language_hint": page.language_hint}
    )
    # formula verification: ambiguous formulas must be re-viewed visually, never guessed
    if page.formula_signals:
        candidates = extract_formula_regions(page.raw_text, page.page_or_slide, page.formula_signals)
        ambiguous = [f for f in candidates if f.signals]
        review = None
        if ambiguous and source_file.lower().endswith(".pdf"):
            try:
                re_rendered = render_pdf_pages(Path(source_file), dpi=220)
                matched = next((r for r in re_rendered if r.page_or_slide == page.page_or_slide), None)
                if matched:
                    review_understanding = provider.understand_page(
                        matched, native_text=page.raw_text, context={"focus": "formulas"}
                    )
                    review = {
                        "confirmed": bool(review_understanding.formulas),
                        "confidence": review_understanding.confidence,
                    }
            except Exception:
                review = None
        for formula in ambiguous:
            verify_formula_visually(formula, review_result=review, re_rendered=review is not None)
        understanding.formulas = ambiguous or candidates

    # exam papers keep their structure (not a text blob)
    if page.question_numbers or understanding.exam is None:
        role = _role_hint(source_file, page.raw_text)
        if role and page.raw_text:
            understanding.exam = merge_provider_exam_structure(
                understanding.exam, page.raw_text, page.page_or_slide
            )
    return _evidence_from_provider(
        course_id=course_id,
        source_file=source_file,
        document_type_name=document_type_name,
        page=page,
        understanding=understanding,
        rendered=rendered,
        min_visual_confidence=options.min_visual_confidence,
    )


def ingest_file(
    workspace_root: Path,
    course_id: str,
    file_path: str | Path,
    *,
    options: IngestOptions | None = None,
) -> IngestResult:
    """Run one file through the full pipeline and write evidence to the course store.

    File -> Classifier -> Native Parser -> (Visual Renderer -> Multimodal Understanding)
    -> Structured Evidence. Single-file failure never stops other files.
    """
    options = options or IngestOptions()
    result = IngestResult()
    path = Path(file_path)
    result.documents_seen.append(path.name)
    if not path.is_file():
        result.warn(f"{path.name}: not a file, skipped")
        return result

    try:
        doc_type = document_type(path)
    except ValueError as exc:
        result.warn(f"{path.name}: {exc}")
        return result

    # incremental ingestion: unchanged files are not re-parsed
    processed = load_processed_files(workspace_root, course_id)
    file_hash = current_file_hash(path)
    if processed.get(path.name) == file_hash and processed:
        result.warn(f"{path.name}: unchanged, incremental ingestion skipped")
        return result

    try:
        native_pages = parse_native(path, doc_type)
    except Exception as exc:
        result.warn(f"{path.name}: native parse failed ({exc}); page marked unresolved")
        return result
    result.documents_parsed.append(path.name)

    provider = None
    if options.provider_name:
        try:
            provider = get_provider(options.provider_name)
        except ProviderUnavailable as exc:
            result.warn(f"{path.name}: provider unavailable ({exc})")

    rendered_pages: list[RenderedPage] | None = None
    all_evidence: list[Evidence] = []

    for page in native_pages:
        decision = route_page(page, exam_role=_role_hint(path.name, page.raw_text))
        if decision.method == "native_text":
            all_evidence.append(
                _make_evidence(
                    course_id=course_id,
                    source_file=path.name,
                    document_type_name=doc_type,
                    page=page,
                    extraction_method="native_text",
                    confidence=0.85,
                    content={
                        "text": page.raw_text,
                        "formula_signals": page.formula_signals,
                        "table_signals": page.table_signals,
                    },
                    synthetic=False,
                    question_number=page.question_numbers[0] if page.question_numbers else None,
                )
            )
            continue

        if decision.method == "unresolved":
            result.unresolved_pages.append(f"{path.name}:{page.page_or_slide}")
            result.warn(f"{path.name} page {page.page_or_slide}: unresolved (no text, no images)")
            continue

        # vision path
        if provider is None:
            # explicit OCR fallback only when native multimodal is unavailable AND enabled
            if options.allow_ocr_fallback or options.offline_mode:
                ocr_text = ""
                ocr_warning = ""
                try:
                    if is_image(path):
                        ocr_page = run_ocr(
                            path, enabled=options.allow_ocr_fallback, offline_mode=options.offline_mode
                        )
                        ocr_text = ocr_page.raw_text
                        ocr_warning = ocr_page.warning or ""
                    elif doc_type == "pdf":
                        try:
                            rendered_pages = render_pdf_pages(path)
                        except Exception as exc:
                            rendered_pages = None
                            result.warn(f"{path.name}: render failed before OCR ({exc})")
                        if rendered_pages:
                            matched = next(
                                (r for r in rendered_pages if r.page_or_slide == page.page_or_slide), None
                            )
                            if matched:
                                ocr_page = run_ocr(
                                    matched.image_png,
                                    enabled=options.allow_ocr_fallback,
                                    offline_mode=options.offline_mode,
                                )
                                ocr_text = ocr_page.raw_text
                                ocr_warning = ocr_page.warning or ""
                except OCRDisabled as exc:
                    result.unresolved_pages.append(f"{path.name}:{page.page_or_slide}")
                    result.warn(f"{path.name} page {page.page_or_slide}: OCR fallback failed ({exc})")
                    continue
                ocr_evidence = _make_evidence(
                    course_id=course_id,
                    source_file=path.name,
                    document_type_name=doc_type,
                    page=page,
                    extraction_method="ocr_fallback",
                    confidence=0.3,
                    content={"text": ocr_text, "ocr_warning": ocr_warning},
                    synthetic=False,
                )
                all_evidence.append(ocr_evidence)
                continue
            result.unresolved_pages.append(f"{path.name}:{page.page_or_slide}")
            result.warn(
                f"{path.name} page {page.page_or_slide}: vision required but no provider "
                f"configured and OCR disabled; page marked unresolved (no fake content)"
            )
            continue

        # render the page
        if rendered_pages is None:
            if doc_type == "pdf":
                try:
                    rendered_pages = render_pdf_pages(path)
                except Exception as exc:
                    result.warn(f"{path.name}: PDF rendering failed ({exc})")
            elif is_image(path):
                try:
                    rendered_pages = [render_input_image(path)]
                except Exception as exc:
                    result.warn(f"{path.name}: image load failed ({exc})")
            else:
                # PPTX/DOCX visual rendering needs LibreOffice; degrade to native text
                rendered_pages = []
                result.warn(
                    f"{path.name}: visual rendering for {doc_type} requires LibreOffice "
                    f"(not available); native text only"
                )
        rendered = next(
            (r for r in (rendered_pages or []) if r.page_or_slide == page.page_or_slide), None
        )
        if rendered is None:
            result.unresolved_pages.append(f"{path.name}:{page.page_or_slide}")
            result.warn(
                f"{path.name} page {page.page_or_slide}: cannot render page for vision; unresolved"
            )
            continue
        try:
            page_evidence = _process_vision_page(
                course_id=course_id,
                source_file=str(path),
                document_type_name=doc_type,
                page=page,
                rendered=rendered,
                provider=provider,
                options=options,
                result=result,
            )
            all_evidence.extend(page_evidence)
        except ProviderUnavailable as exc:
            result.unresolved_pages.append(f"{path.name}:{page.page_or_slide}")
            result.warn(f"{path.name} page {page.page_or_slide}: provider failure ({exc}); unresolved")
        except Exception as exc:
            result.unresolved_pages.append(f"{path.name}:{page.page_or_slide}")
            result.warn(f"{path.name} page {page.page_or_slide}: understanding failed ({exc}); unresolved")

    if all_evidence:
        added, duplicates = write_evidence(
            workspace_root, course_id, all_evidence, store_mode=options.store_mode
        )
        result.evidence_added.extend(all_evidence)
        result.evidence_duplicates = duplicates
        if added == 0 and duplicates > 0:
            result.warn(f"{path.name}: all evidence duplicated (content-hash dedup)")
    if file_hash:
        mark_file_processed(workspace_root, course_id, path.name, file_hash)
    return result


def ingest_directory(
    workspace_root: Path,
    course_id: str,
    input_dir: str | Path,
    *,
    options: IngestOptions | None = None,
) -> IngestResult:
    """Ingest every supported file in a directory (recursively). A failing file
    never stops the rest."""
    from .classifier import is_supported

    options = options or IngestOptions()
    result = IngestResult()
    files = sorted(
        p for p in Path(input_dir).rglob("*") if p.is_file() and is_supported(p)
    )
    for path in files:
        file_result = ingest_file(workspace_root, course_id, path, options=options)
        result.documents_seen.extend(file_result.documents_seen)
        result.documents_parsed.extend(file_result.documents_parsed)
        result.evidence_added.extend(file_result.evidence_added)
        result.evidence_duplicates += file_result.evidence_duplicates
        result.unresolved_pages.extend(file_result.unresolved_pages)
        for warning in file_result.warnings:
            result.warn(warning)
    return result
