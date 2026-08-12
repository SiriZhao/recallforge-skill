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

    explanation = _explain(diagnosis)
    return DiagnosisResult(
        topic_id=topic.topic_id,
        diagnosis=diagnosis,
        severity=severity,
        evidence_refs=list(topic.evidence),
        prerequisite_fix=prerequisite_fix,
        explanation=explanation,
    )


def _explain(diagnosis: str) -> str:
    return {
        "concept_gap": "概念缺口：先回到定义与直觉。",
        "formula_recall": "公式回忆失败：重背公式并核对适用条件。",
        "condition_misread": "条件误读：圈出题目约束条件。",
        "prerequisite_gap": "前置知识缺口：先补前置主题。",
        "calculation_error": "计算错误：逐步验算并核对单位。",
        "algebra_error": "代数错误：检查移项与合并。",
        "sign_error": "符号错误：检查正负号。",
        "unit_error": "单位错误：统一单位后再计算。",
        "reasoning_jump": "推理跳跃：写出每步理由。",
        "question_misread": "审题错误：复述题目要求。",
        "method_selection": "方法选择错误：回顾各方法适用条件。",
        "memory_failure": "记忆失效：间隔重复强化。",
        "careless_error": "粗心错误：检查一遍书写。",
        "unknown": "无法归类，请查看讲解。",
    }.get(diagnosis, "见讲解")
