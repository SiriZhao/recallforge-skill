# Multimodal material

RecallForge combines evidence paths instead of treating OCR as multimodal understanding.

- **Text:** prefer reliable native extraction.
- **Scans:** render the page and use host vision; OCR is an optional fallback.
- **Tables:** preserve headers, rows, columns, and cells.
- **Formulas:** retain raw and interpreted forms, surrounding context, confidence, and source.
- **Diagrams:** preserve labels, grouping, arrows, legend, spatial relationships, and visual comparisons.
- **Handwriting:** identify it as a user or unknown annotation, not a verified answer.

The pipeline runs fast, standard, and precision passes. Precision is reserved for low-confidence scans, multi-column exams, complex formulas, chemistry structures, handwriting, and conflicting extraction.

If host vision is unavailable, reliable native content remains usable and visual blocks are reported unresolved. The optional Python OCR fallback is disabled by default; it may recover text but does not turn an image into a fully understood diagram.

For the actual host boundary, run the [manual verification](manual-verification.md).
