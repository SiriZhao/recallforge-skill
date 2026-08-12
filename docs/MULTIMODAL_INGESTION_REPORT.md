# Multimodal Ingestion Report — Round 2

> Rebuilds ingestion around **Native Multimodal First**, eliminating the old
> local-OCR-first design (`ocr.py` / `pytesseract` with fixed confidence). Real
> results recorded below; no mocked pipeline, no fake PASS.

## 1. Architecture delivered

```
File
  -> Classifier        (extension -> document_type: pdf/pptx/docx/txt/md/png/jpg)
  -> Native Parser     (PDF text layer / PPTX text boxes / DOCX paragraphs,
                        preserves file, page, slide, heading, question_number)
  -> Visual Renderer   (PDF pages via PyMuPDF; input images via Pillow;
                        PPTX/DOCX via LibreOffice when present)
  -> Multimodal Understanding  (provider abstraction, capability-described)
  -> Structured Evidence (evidence_store.json per course)
```

All code lives in `exam_review_skill/ingestion/`:
`classifier.py`, `native_parser.py`, `renderer.py`, `router.py`, `provider.py`,
`formula_verify.py`, `exam_parser.py`, `ocr_fallback.py`, `evidence.py`,
`pipeline.py`, `types.py`.

## 2. Native first (verified)

| Document type | Native path used | Test |
|---|---|---|
| text PDF | text layer, page/heading/question_number preserved | `test_text_pdf_uses_native_text` |
| PPTX | text boxes per slide, title heading | `test_pptx_uses_native_text_boxes` |
| DOCX | paragraphs + tables | `test_docx_with_table_routes_to_vision_and_degrades_honestly` |
| TXT / MD | UTF-8 text | `test_incremental_ingestion_skips_unchanged_file` |
| image | no native text -> routed to vision | `test_handwriting_image_routes_to_vision` |

Native pages emit `extraction_method=native_text` at confidence 0.85 with the source
metadata intact (`page_or_slide`, `heading`, `question_number`).

## 3. Cheap routing (verified)

`router.py` only spends vision where it is needed:

| Page signal | Route | Test |
|---|---|---|
| reliable text, no signals | native_text | `test_router_decisions` |
| image-only page (no text layer) | vision | same |
| formula tokens / sub/superscript / fraction / chemical eq | vision | same |
| table present | vision | same |
| question numbers present (exam paper) | vision | same |
| no text, no images | unresolved (never fabricated) | same |

## 4. Visual understanding (verified)

Scanned / image-only PDF, formula-heavy pages, diagrams, tables, handwriting, and
exam papers all route to vision. The provider receives the **rendered page image +
native text** (fusion). Verified:

* `test_scanned_pdf_with_synthetic_provider_demo` — scanned PDF -> multimodal
  evidence (demo mode, synthetic flag set).
* `test_handwriting_image_routes_to_vision` / `test_diagram_image` — image input.
* `test_mixed_language_page_keeps_language_hint` — mixed zh/en page keeps its
  language hint.

## 5. Provider abstraction (verified)

`provider.py`:

* `MultimodalProvider` with capability flags (`supports_images`, `supports_pdf`,
  `supports_structured_output`, `supports_long_context`).
* Runtime registry (`register_provider`) — no single-vendor hard-coding.
* Real providers: `openai` (Responses API) and `deepseek` (chat completions),
  configured via env vars, **fail closed** when unset.
* `SyntheticProvider` for tests/fixtures/demo/CI only, output flagged `synthetic`.
* `test_provider_registry_is_extensible`, `test_provider_unavailable_for_unset_env`,
  `test_multimodal_provider_failure_is_unresolved_not_faked`.

## 6. Local OCR is disabled by default (verified)

* `test_ocr_disabled_by_default` — `run_ocr` raises `OCRDisabled` unless explicitly
  enabled (env `EXAM_REVIEW_OCR_FALLBACK=1`) or offline mode.
* `test_ocr_enabled_but_engine_unavailable_never_fabricates` — with no tesseract
  binary, the page is recorded **unresolved** with a warning; **no fake content**.
* OCR output contract: `extraction_method=ocr_fallback`, confidence capped at 0.3,
  never supports high-confidence exam conclusions.

## 7. Formula verification (verified)

* `formula_verify.py` flags subscript/superscript, minus, Greek, matrix, fraction,
  and chemical-equation ambiguity from native text.
* Ambiguous formulas are re-viewed visually (higher-DPI re-render + focused
  provider call). Unconfirmed ambiguity is **never guessed**: confidence stays
  below 0.5.
* `test_formula_ambiguity_stays_low_confidence` asserts the low-confidence contract.

## 8. Exam paper structure (verified)

* `exam_parser.py` keeps `question_number`, `question_body`, `options`, `figure_refs`,
  `subquestions`, `score`, `answer_area`, and `handwritten_annotation` — never a
  flattened OCR blob.
* `test_exam_paper_structure_is_preserved` — a 3-question exam page is parsed into
  3 structured questions; Q1 keeps 4 options, Q2 keeps its Chinese body.

## 9. Evidence object (verified)

Each record carries `source_file`, `document_type`, `page_or_slide`, `heading`,
`question_number`, `region`, `source_language`, `extraction_method`, `confidence`,
`evidence_weight`, plus `content`, `content_hash`, `synthetic`, `created_at`.
Validated by `schemas/evidence_store.schema.json` in `test_state_schemas.py`.

## 10. Error degradation (verified)

* Single-file failure: recorded as a warning, other files continue
  (`ingest_directory`).
* Single-page failure: added to `unresolved_pages` with a reason — never fabricated.
* Provider failure: retry structure in place; unconfigured provider fails closed to
  unresolved.
* Renderer missing (LibreOffice absent for PPTX/DOCX visual): page unresolved +
  warning; native text remains available.
* `test_scanned_pdf_without_provider_is_unresolved_not_faked`,
  `test_multimodal_provider_failure_is_unresolved_not_faked`,
  `test_docx_with_table_routes_to_vision_and_degrades_honestly`.

## 11. No mock contamination (verified)

* `SyntheticProvider` output carries `synthetic=true`.
* `reject_synthetic` + extended `find_mock_markers` reject `synthetic: true` and mock
  markers before any real-state write.
* `test_synthetic_record_rejected_from_real_store`,
  `test_direct_write_evidence_rejects_synthetic`, `test_marker_detection_finds_synthetic_flag`,
  `test_no_mock_content_in_real_state_after_clean_ingest`.
* CLI: `workspace ingest` without `--demo` refuses synthetic content with a clean
  error (verified live: `error: real state rejected synthetic/mock content: ...`).

## 12. Performance (verified)

* Content-hash cache per course (`evidence_store.json["documents"]`).
* Incremental ingestion: unchanged files are skipped
  (`test_incremental_ingestion_skips_unchanged_file`).
* Content-hash dedup on evidence records (duplicate counting).
* Cheap routing avoids running vision on every page.

## 13. Real test results (this environment)

* Full suite: **70 passed, 1 skipped** (pytest 9.1.1, Python 3.14.3, Windows).
* New ingestion tests: **22 passed, 1 skipped** across
  `test_ingestion_pipeline.py`, `test_ingestion_vision.py`,
  `test_ingestion_contamination.py`.
* The 1 skipped test is the "OCR engine present" branch: the tesseract binary is not
  installed in this environment, so the honest OCR-fallback degradation path is what
  runs (unresolved, no fake content).
* LibreOffice is not installed: PPTX/DOCX visual rendering degrades to native text +
  explicit unresolved warning (recorded, not hidden).
* CLI live smoke: 3 documents (text PDF, exam PDF, scanned PDF) -> 3 evidence
  records, 0 unresolved (demo mode); real mode rejected the synthetic record.

## 14. Coverage vs. required test list

| Required | Covered by |
|---|---|
| text PDF | `test_text_pdf_uses_native_text` |
| scanned PDF | `test_scanned_pdf_*` (2 tests) |
| PPT slide | `test_pptx_uses_native_text_boxes` |
| formula | `test_formula_ambiguity_stays_low_confidence` |
| table | `test_docx_with_table_routes_to_vision_and_degrades_honestly` |
| exam question | `test_exam_paper_structure_is_preserved` |
| handwritten annotation | `test_handwriting_image_routes_to_vision` |
| mixed Chinese-English page | `test_mixed_language_page_keeps_language_hint` |
| multimodal provider failure | `test_multimodal_provider_failure_*`, `test_provider_unavailable_for_unset_env` |
| OCR fallback | `test_ocr_disabled_by_default`, `test_ocr_enabled_but_engine_unavailable_never_fabricates`, `test_ocr_fallback_flag_on_output` |
| no mock contamination | `tests/test_ingestion_contamination.py` (5 tests) |

Commit: `feat: rebuild ingestion around native multimodal understanding`
