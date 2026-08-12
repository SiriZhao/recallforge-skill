from __future__ import annotations

import re

from .types import FormulaRegion, Region


AMBIGUITY_SIGNALS = {
    "subscript": "formula.ambiguity.subscript",
    "superscript": "formula.ambiguity.superscript",
    "minus": "formula.ambiguity.minus",
    "greek": "formula.ambiguity.greek",
    "matrix": "formula.ambiguity.matrix",
    "fraction": "formula.ambiguity.fraction",
    "chemical-equation": "formula.ambiguity.chemical-equation",
}


def localize_ambiguity_signals(signals: list[str], locale: str = "zh-CN") -> list[str]:
    """Translate raw ambiguity signal keys into user-facing localized text."""
    from ..i18n import t
    return [t(locale, AMBIGUITY_SIGNALS.get(sig, sig)) for sig in signals]


def extract_formula_regions(text: str, page_or_slide: str, signals: list[str]) -> list[FormulaRegion]:
    """Pull candidate formula lines from native text and tag ambiguity signals.

    Ambiguity means the text alone is NOT trustworthy: the region must be re-viewed
    visually before it may support any conclusion.
    """
    regions: list[FormulaRegion] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if not re.search(r"[=≠≈≤≥]|∑|∫|√|Δ|\\frac|_[a-zA-Z0-9]|\^|\d+\s*/\s*\d+", stripped):
            continue
        line_signals: list[str] = []
        if re.search(r"(?<![\w])([A-Za-z]{1,3})[_ ]([0-9]+)", stripped):
            line_signals.append("subscript")
        if re.search(r"(?<![\w])([A-Za-z]{1,3})[\^] ?([0-9]+)", stripped):
            line_signals.append("superscript")
        if re.search(r"(?<=\w)\s-\s(?=\d)", stripped):
            line_signals.append("minus")
        if re.search(r"[αβγδθλμπσφψωΔ∑∫√]", stripped):
            line_signals.append("greek")
        if re.search(r"\d+\s*/\s*\d+|\\frac", stripped):
            line_signals.append("fraction")
        if re.search(r"\b(?:NaOH|HCl|H2O|CO2|KMnO4|CaCO3)\b", stripped, re.I):
            line_signals.append("chemical-equation")
        # unknown confidence whenever any ambiguity exists; never guess higher
        confidence = 0.35 if line_signals else 0.7
        regions.append(
            FormulaRegion(
                region=Region(page_or_slide=page_or_slide, region_type="formula"),
                text=stripped,
                signals=line_signals,
                confidence=confidence,
            )
        )
    return regions


def verify_formula_visually(
    formula: FormulaRegion,
    *,
    review_result: dict | None,
    re_rendered: bool,
) -> FormulaRegion:
    """After visual re-view, update confidence only from real visual evidence.

    - If the page was re-rendered and the provider returned a confirmed formula,
      confidence may rise to a usable level.
    - If re-view is impossible or still ambiguous, confidence stays low
      (cannot support high-confidence exam conclusions). Never guess.
    """
    if not formula.signals:
        return formula
    if re_rendered and review_result and review_result.get("confirmed"):
        formula.confidence = min(0.85, float(review_result.get("confidence", 0.8)))
    else:
        formula.confidence = min(formula.confidence, 0.3)
    return formula
