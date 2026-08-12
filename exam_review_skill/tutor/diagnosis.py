from __future__ import annotations

from ..models import DiagnosisResult, KnowledgeTopic, StudentModel


DIAGNOSIS_TAXONOMY = [
    "concept_gap",
    "formula_recall",
    "condition_misread",
    "prerequisite_gap",
    "calculation_error",
    "algebra_error",
    "sign_error",
    "unit_error",
    "reasoning_jump",
    "question_misread",
    "method_selection",
    "memory_failure",
    "careless_error",
    "unknown",
]


def diagnose_wrong_answer(
    *,
    question: dict,
    user_answer: str,
    grading_mistake: str,
    topic: KnowledgeTopic,
    prerequisites: list[str],
    prerequisite_mastery: dict[str, str],
    locale: str = "zh-CN",
) -> DiagnosisResult:
    """Classify a wrong answer into the taxonomy and pick a remediation path.

    Special case: if a prerequisite topic is 'unknown' or weak, the root cause is
    likely a prerequisite_gap, not the topic itself - return that so the planner
    fixes the prerequisite first.
    """
    severity = 2
    prerequisite_fix: list[str] = []
    diagnosis = grading_mistake if grading_mistake in DIAGNOSIS_TAXONOMY else "unknown"

    # prerequisite check: a weak/unknown prerequisite is the likely root cause
    for prereq_id in prerequisites:
        level = prerequisite_mastery.get(prereq_id, "unknown")
        if level in ("unknown", "novice"):
            diagnosis = "prerequisite_gap"
            severity = 3
            prerequisite_fix.append(prereq_id)
            break

    if diagnosis == "unknown":
        # fallback classification from answer shape
        if not user_answer.strip():
            diagnosis = "question_misread"
            severity = 1
        elif any(k in user_answer for k in ["=", "+", "-", "*", "/"]) and "计算" in question.get("question_text", ""):
            diagnosis = "calculation_error"
            severity = 2

    explanation = _explain(diagnosis, locale=locale)
    return DiagnosisResult(
        topic_id=topic.topic_id,
        diagnosis=diagnosis,
        severity=severity,
        evidence_refs=list(topic.evidence),
        prerequisite_fix=prerequisite_fix,
        explanation=explanation,
    )


def _explain(diagnosis: str, locale: str = "zh-CN") -> str:
    """Localized explanation for a diagnosis category."""
    from ..i18n import t
    return t(locale, f"diag.explain.{diagnosis}")
