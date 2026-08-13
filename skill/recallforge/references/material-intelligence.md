# Material Intelligence Layer

Read this reference whenever the user supplies files, scans, slides, images, tables, formulas, diagrams, or past papers.

## Intake and catalog

1. Catalog only the files actually available. Record filename, type, page/slide count when the host exposes it, and a source anchor for each processed unit.
2. Never invent file counts, page counts, OCR coverage, or processing status. If the host does not expose these details, say what was received without numeric claims.
3. Run a fast structural pass before deep extraction. For very large collections, build a course outline and prioritize relevant chunks instead of placing everything in context at once.
4. In the current conversation, merge newly added material into the existing catalog. Do not claim cross-session persistence unless the host provides it.

## Page- and slide-level routing

For each page or slide, choose the least expensive reliable path:

- Use native text for reliable digital text, headings, slide titles, notes, and native tables.
- Use host vision for image-only pages, scans, visual comparisons, arrows, grouping, diagrams, charts, chemical structures, biological figures, handwriting, and layout-dependent meaning.
- Fuse native text and vision for PPTX slides and pages containing formulas, tables, figures, or conflicting extraction.
- Use optional local OCR only when host vision is unavailable or the user explicitly enables local batch processing. OCR is text evidence, not a substitute for visual structure.

Use progressive depth:

- **Fast:** metadata, native text, low-resolution overview, headings, slide titles.
- **Standard:** ordinary figures, tables, formulas, diagrams, and page layout.
- **Precision:** low-confidence scans, multi-column exams, complex formulas, chemical structures, handwriting, crops, and conflicting extraction.

Do not run precision processing on every page by default.

## Normalized StudyDocument

Keep a simple internal representation:

```text
StudyDocument
  document_id, filename, type, hash, language, warnings
  pages/slides[]
    index, title, source_anchor, route, status, confidence
    blocks[]: text | formula | table | diagram | image | annotation | question
    notes, visual_emphasis, warnings
```

Every unit must end as `processed`, `processed_with_warning`, `skipped_with_reason`, or `failed_with_reason`. Never silently drop a page or slide.

## Evidence rules

- Preserve source anchors such as `Probability_Week4.pdf, p. 12` or `Lecture_06.pptx, slide 23` internally. Show them for important claims, ambiguity, conflicts, past-paper evidence, or when requested.
- Preserve tables as headers, rows, columns, and cells. If structure cannot be recovered, mark the table unresolved rather than flattening it silently.
- Preserve formulas as raw representation, interpreted representation, context, source, and confidence. If native/OCR/vision paths disagree, show the alternatives and ask for source verification. Never silently rewrite a formula.
- Treat chemical structures and biological/botanical diagrams as visual concepts. Do not force them into OCR-only text.
- Treat handwriting as `user_annotation` or `unknown_annotation`, never as a verified answer unless an answer key explicitly confirms it.
- Treat bold, highlight, boxes, and color as visual emphasis only. Treat explicit words such as `IMPORTANT`, `EXAM`, `must know`, `重点`, and `考试要求` as stronger but still source-bounded evidence.
- When course sources conflict, present each claim with its source. Do not invent a third synthesis.

## Material inspection mode

When asked for `inspect-materials` or to inspect without reviewing, return only:

1. Files detected
2. Material types and page/slide counts that are actually available
3. Native-readable, scan-heavy, and visual-heavy units
4. Recognition warnings and uncertain formulas/tables/diagrams
5. Recommended next processing step

Do not begin a long review.

## Multimodal self-test

When asked for `multimodal-test`, use `assets/self-test/multimodal/probability-slide.svg` or its attached/rendered version. Identify the visible title, conditional-probability formula, the event comparison table, and the arrow relationship. Produce one source-grounded recall question and finish with `Status: MULTIMODAL_READY`.

If the host cannot inspect the image/SVG, return exactly `MULTIMODAL_HOST_CAPABILITY_UNAVAILABLE`, explain that the text self-test can still run, and do not mark RecallForge itself as failed.
