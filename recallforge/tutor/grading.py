from __future__ import annotations

import re

from ..i18n import t
from ..models import GradingResult, QuizQuestion, StudentModel
from ..student.mastery import compute_mastery

# Bilingual keyword aliases so a Chinese answer to an English reference (or vice
# versa) is graded by meaning, not just token identity.
BILINGUAL_ALIASES = {
    "standardize": "标准化",
    "standard": "标准",
    "normal": "正态",
    "table": "表",
    "use": "用",
    "calculate": "计算",
    "formula": "公式",
    "condition": "条件",
    "unit": "单位",
    "significant": "有效数字",
    "substitute": "代入",
    "solve": "求解",
    "definition": "定义",
    "mean": "均值",
    "variance": "方差",
    "probability": "概率",
    "random": "随机",
    "derivative": "导数",
    "integral": "积分",
    "limit": "极限",
    "matrix": "矩阵",
    "eigenvalue": "特征值",
    "titration": "滴定",
    "photosynthesis": "光合作用",
}


def grade_answer(
    question: QuizQuestion,
    user_answer: str,
    *,
    student: StudentModel | None = None,
    locale: str = "zh-CN",
) -> GradingResult:
    """Grade one answer with process analysis, not just correct/wrong.

    Supports: multiple choice (exact option), fill-blank (normalized match),
    short answer / calculation / derivation / essay / diagram (keyword + length
    heuristics), bilingual (zh/en answers both accepted).
    """
    zh = locale.startswith("zh")
    correct, score, process = _grade(question, user_answer, zh)
    mistake_type = _classify_mistake(question, user_answer, correct)
    feedback = _feedback(question, correct, mistake_type, zh)
    return GradingResult(
        question_id=question.question_id,
        correct=correct,
        score=score,
        feedback=feedback,
        process_analysis=process,
        mistake_type=mistake_type,
        concept_gap_topic=question.topic_id,
        evidence_refs=list(question.evidence_refs),
    )


def _grade(question: QuizQuestion, user_answer: str, zh: bool) -> tuple[bool, float, str]:
    user = (user_answer or "").strip()
    correct = (question.correct_answer or "").strip()
    if not user:
        return False, 0.0, "未作答" if zh else "no answer"

    if question.question_type == "multiple_choice":
        ok = user.lower() == correct.lower()
        return ok, 1.0 if ok else 0.0, "选项匹配" if zh else "option match"

    if question.question_type == "fill_blank":
        ok = _normalize(user) in _normalize(correct) or _normalize(correct) in _normalize(user)
        return ok, 1.0 if ok else 0.0, "填空匹配" if zh else "fill-blank match"

    # free-text: keyword + coverage heuristic, with process analysis
    keywords = _extract_keywords(correct)
    hits = [k for k in keywords if _keyword_in_answer(k, _normalize(user))]
    coverage = len(hits) / max(1, len(keywords))
    length_ok = len(user) >= max(20, len(correct) * 0.4)
    process = _process_analysis(question, user, hits, zh)
    if coverage >= 0.7 and length_ok:
        return True, 0.9, process
    if coverage >= 0.5:
        return False, 0.6, process
    return False, 0.3, process


def _normalize(text: str) -> str:
    return re.sub(r"\s+", "", (text or "").lower())



def _keyword_in_answer(keyword: str, user_normalized: str) -> bool:
    """A reference keyword matches if the token OR its bilingual alias appears."""
    if keyword and _normalize(keyword) in user_normalized:
        return True
    alias = BILINGUAL_ALIASES.get(keyword.lower())
    return bool(alias and _normalize(alias) in user_normalized)

def _extract_keywords(text: str) -> list[str]:
    """Extract meaningful keywords from the reference answer (zh/en)."""
    tokens = re.findall(r"[\u4e00-\u9fff]{2,6}|[A-Za-z][A-Za-z0-9_]{2,}", text or "")
    stop = {"the", "and", "for", "with", "that", "this", "from", "write", "state", "使用", "写出", "注意"}
    return [token for token in tokens if token.lower() not in stop][:8]


def _process_analysis(question: QuizQuestion, user: str, hits: list[str], zh: bool) -> str:
    if zh:
        if hits:
            return f"命中了 {len(hits)} 个关键点：{'、'.join(hits[:4])}；步骤基本完整。"
        return "未命中参考答案的关键点；请检查公式/定义是否用对。"
    if hits:
        return f"Matched {len(hits)} key points: {', '.join(hits[:4])}; steps look complete."
    return "No key points from the reference matched; check formula/definition."


def _classify_mistake(question: QuizQuestion, user_answer: str, correct: bool) -> str:
    if correct:
        return "none"
    user = _normalize(user_answer)
    if question.question_type == "calculation":
        return "calculation_error"
    if question.question_type == "multiple_choice":
        return "concept_gap"
    if not user:
        return "question_misread"
    return "method_selection"


def _feedback(question: QuizQuestion, correct: bool, mistake_type: str, zh: bool) -> str:
    if correct:
        return "回答正确。请对照标准步骤检查是否遗漏条件。" if zh else "Correct. Re-check you did not omit conditions."
    hint = {
        "concept_gap": "概念有缺口，先复习定义。",
        "calculation_error": "计算错误，请重算并核对单位/有效数字。",
        "question_misread": "审题不清，先圈出关键词。",
        "method_selection": "方法选择有误，回顾该方法的使用条件。",
    }
    if zh:
        return "回答不正确。" + hint.get(mistake_type, "请对照讲解复习。")
    en_hint = {
        "concept_gap": "Concept gap; review the definition first.",
        "calculation_error": "Calculation error; redo and check units/sig figs.",
        "question_misread": "Question misread; circle the keywords first.",
        "method_selection": "Wrong method; review the conditions for this method.",
    }
    return "Incorrect. " + en_hint.get(mistake_type, "Review the explanation.")


def record_grading_to_student(
    student: StudentModel,
    question: QuizQuestion,
    result: GradingResult,
    *,
    today: str | None = None,
) -> StudentModel:
    """Feed a graded answer into the student model (mastery update)."""
    from ..student.sessions import AnswerResult, record_answer

    mistake = None if result.correct else result.mistake_type
    if mistake == "none":
        mistake = None
    answer = AnswerResult(
        topic_id=question.topic_id,
        correct=result.correct,
        difficulty=question.level,
        used_hint=False,
        mistake_type=mistake,
        question_type=question.question_type,
        is_new_form=question.level >= 3,
    )
    record_answer(student, answer, today=today)
    return student
