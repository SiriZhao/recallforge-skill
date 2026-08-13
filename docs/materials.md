# Materials guide

## PPTX

RecallForge’s native path reads slide order, titles, text boxes, native tables, speaker notes, images/charts as typed blocks, and spatial bounding boxes. A slide containing diagrams, arrows, visual comparisons, formulas, or images should also be rendered and inspected by host vision when available. Native text and visual interpretation are fused; neither replaces the other. Legacy binary `.ppt` is not implemented.

## Digital PDF

Each page is checked independently. Reliable native text and layout blocks use the fast path. Image-bearing, formula-heavy, rotated, suspicious, or exam-structured pages route to visual verification. This avoids OCRing an entire mixed document.

## Scanned PDF and images

Image-only pages route to host vision. Optional local Tesseract OCR exists only as a low-confidence fallback in the Python toolkit and is disabled by default. OCR text never replaces diagram structure, chemical structures, handwriting roles, or table layout.

## Past papers

When evidence is extractable, the normalized structure separates question number, prompt, options, subquestions, figure references, score, printed answer, and user/unknown annotation. A handwritten `B` is not a verified answer key.

## Formulas and tables

Formulas retain raw/interpreted representations, context, confidence, and source. Conflicting recognition is marked uncertain. Tables retain headers and row/cell structure; a failed layout is reported rather than silently flattened.

## Diagram-heavy subjects

Organic structures, reaction arrows, cell diagrams, floral diagrams, anatomy, morphology, graphs, and flow charts remain visual concepts. Provide a high-resolution crop when labels or relations are unclear.

## Large collections

Start with a catalog and structural scan, then build the course map and deepen only priority chunks. In a single conversation, new material can be merged incrementally. Cross-session persistence depends on the host; the installed Skill does not promise it.

## Cache and duplicates

The instruction-only Skill does not create its own cache. The optional Python toolkit records file SHA-256 values and evidence content hashes in the selected workspace’s course evidence store to skip unchanged files and duplicate evidence. When a `cache_dir` is explicitly configured, it also caches rendered pages by file hash, page/slide, processing profile, and DPI. Delete that selected cache directory or workspace evidence store only if you intentionally want a fresh local ingestion; do not delete the global Skills directory.
