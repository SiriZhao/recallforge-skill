"""Round 2: Native Multimodal Document Intelligence.

Pipeline: File -> Classifier -> Native Parser -> Visual Renderer ->
          Multimodal Understanding -> Structured Evidence.

Native-first: reliable text layers (PDF text, PPTX text boxes, DOCX paragraphs)
are preferred. Vision is used only when cheap routing says a page actually needs it
(scanned/image-only pages, formulas, diagrams, tables, handwriting, exam papers).
Local OCR is disabled by default and never supports high-confidence conclusions.
"""

from . import classifier, evidence, native_parser, pipeline, provider, renderer, router, types

__all__ = [
    "classifier",
    "evidence",
    "native_parser",
    "pipeline",
    "provider",
    "renderer",
    "router",
    "types",
]
