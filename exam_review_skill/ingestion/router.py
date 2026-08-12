from __future__ import annotations

from .types import NativePage


class RoutingDecision:
    def __init__(self, method: str, reasons: list[str]):
        self.method = method  # native_text | vision | unresolved
        self.reasons = reasons


def route_page(page: NativePage, *, exam_role: str | None = None) -> RoutingDecision:
    """Cheap, deterministic routing: only pay for vision when it is actually needed.

    Native text wins when the text layer is reliable and the page is not
    formula-heavy, table-heavy, image-bearing, handwritten, or an exam paper.
    """
    reasons: list[str] = []

    if not page.has_text_layer:
        if page.has_images:
            return RoutingDecision("vision", ["image-only page (no text layer)"])
        return RoutingDecision("unresolved", ["no text layer and no images"])

    if page.has_images:
        reasons.append("embedded images/diagrams need visual understanding")

    if page.formula_signals:
        reasons.append("formula signals: " + ", ".join(page.formula_signals))

    if page.table_signals:
        reasons.append("table content needs structured verification")

    if exam_role in {"past_exam", "answer_key"} or page.question_numbers:
        reasons.append("exam paper structure needs visual confirmation")

    if reasons:
        return RoutingDecision("vision", reasons)
    return RoutingDecision("native_text", ["reliable native text layer"])
