from __future__ import annotations

import re
from pathlib import Path

from ..i18n import t
from ..models import (
    ExamPointModel,
    KnowledgeTopic,
    PastExamSet,
    QuizQuestion,
    StudentModel,
)


QUIZ_MODES = ("diagnostic", "s-priority", "weak-topic", "past-exam-style", "mixed", "wrongbook", "speed-run", "cram")


def _localized_topic_name(topic: KnowledgeTopic, locale: str) -> str:
    lang = locale.split("-")[0].upper()
    return (
        topic.localized_names.get(f"{lang}-{locale.split('-')[-1]}")
        or topic.localized_names.get("en-US")
        or topic.localized_names.get("zh-CN")
        or topic.canonical_name
    )


def _build_question(
    *,
    topic: KnowledgeTopic,
    exam_point: ExamPointModel | None,
    level: int,
    question_type: str,
    question_language: str,
    explanation_language: str,
    derived_from: str | None = None,
    source_question: str | None = None,
    variation_type: str | None = None,
    index: int = 0,
    past_exam_question: dict | None = None,
) -> QuizQuestion:
    """Build a question grounded in the topic's evidence. question_language and
    explanation_language are independently controllable (e.g. English question,
    Chinese explanation)."""
    zh = question_language.startswith("zh")
    topic_name = _localized_topic_name(topic, question_language)

    # provenance: past-exam questions produce variants with derived_from
    if past_exam_question and past_exam_question.get("body"):
        original = past_exam_question["body"]
        variation = _make_variant(original, topic, level, zh, variation_type)
        question_text = variation["text"]
        correct_answer = variation["answer"]
        explanation = variation["explanation"]
        common_trap = variation["trap"]
    else:
        # generate from topic evidence
        definition = topic.definitions[0].text if topic.definitions else ""
        formula = topic.formulas[0].text if topic.formulas else ""
        method = topic.methods[0].text if topic.methods else ""
        mistake = topic.common_mistakes[0].text if topic.common_mistakes else ""

        if level == 1:
            question_text = (
                f"【回忆】请写出 {topic_name} 的定义。"
                if zh
                else f"[Recall] State the definition of {topic_name}."
            )
            correct_answer = definition or t(question_language, "quiz.no_definition")
            explanation = definition
            common_trap = mistake or None
        elif level == 2:
            question_text = (
                f"【标准】{topic_name} 的核心公式/原理与适用条件是什么？"
                if zh
                else f"[Standard] What is the core formula/principle of {topic_name} and its conditions?"
            )
            correct_answer = (formula + "\n" + (mistake if mistake else "")) if formula else (definition or "见讲解")
            explanation = formula or definition
            common_trap = mistake or None
        elif level == 3:
            question_text = (
                f"【变式】改变一个条件或数值，重新应用 {topic_name} 的方法，写出解题步骤。"
                if zh
                else f"[Variant] Change one condition/number, re-apply the {topic_name} method, write the steps."
            )
            correct_answer = method or definition or "应用对应公式并写明条件"
            explanation = method or formula or definition
            common_trap = mistake or None
        else:
            question_text = (
                f"【迁移】把 {topic_name} 放到一个新情境（如新实验/新题型），解释如何应用并指出易错点。"
                if zh
                else f"[Transfer] Put {topic_name} in a new context, explain how to apply it and the traps."
            )
            correct_answer = definition or f"结合 {topic_name} 的原理进行迁移"
            explanation = (method + "\n" + (mistake if mistake else "")) if method else (definition or "见讲解")
            common_trap = mistake or None

    return QuizQuestion(
        question_id=f"Q{index + 1:03d}",
        topic_id=topic.topic_id,
        topic_name=topic_name,
        question_type=question_type,
        level=level,
        question_text=question_text,
        correct_answer=correct_answer,
        explanation=explanation,
        common_trap=common_trap,
        derived_from=derived_from,
        source_question=source_question,
        variation_type=variation_type,
        evidence_refs=list(topic.evidence),
        question_language=question_language,
        explanation_language=explanation_language,
    )


def _make_variant(original: str, topic: KnowledgeTopic, level: int, zh: bool, variation_type: str | None) -> dict:
    """Create a past-exam-style variant that keeps provenance. Variations:
    parameter change (L3) and new-context transfer (L4) - always derived from the
    original question, never invented."""
    definition = topic.definitions[0].text if topic.definitions else ""
    formula = topic.formulas[0].text if topic.formulas else ""
    vt = variation_type or ("parameter" if level <= 3 else "new_context")
    if zh:
        if vt == "new_context":
            return {
                "text": f"【迁移变式·源自真题】{original} 现在把数字/情境换成新参数，重新求解。",
                "answer": f"步骤：写出公式 {formula}，代入新参数，注意单位与有效数字。",
                "explanation": f"原题为：{original}。变式只改参数，考察同一考点。",
                "trap": "注意条件与有效数字",
            }
        return {
            "text": f"【参数变式·源自真题】{original} 改为：把题目中的数值换一组，重新计算。",
            "answer": f"用公式 {formula} 代入新值，保留合理有效数字。",
            "explanation": f"原题为：{original}。核心公式不变，仅参数变化。",
            "trap": "单位或有效数字错误",
        }
    if vt == "new_context":
        return {
            "text": f"[Transfer variant, from past exam] {original} Now change the numbers/context and re-solve.",
            "answer": f"Write the formula {formula}, substitute new values, watch units.",
            "explanation": f"Original: {original}. Only parameters changed.",
            "trap": "condition/unit error",
        }
    return {
        "text": f"[Parameter variant, from past exam] {original} Change the values and re-calculate.",
        "answer": f"Substitute into {formula}, keep significant figures.",
        "explanation": f"Original: {original}. Same core formula.",
        "trap": "unit/significant figure error",
    }


def _adaptive_level(topic: KnowledgeTopic, student: StudentModel) -> int:
    """Adaptive difficulty: L1 Recall -> L4 Transfer.
    Sustained correct answers raise the level; repeated errors lower it and should
    trigger prerequisite review."""
    tm = student.topics.get(topic.topic_id)
    if tm is None or tm.questions_attempted == 0:
        return 1  # no data: start at recall
    if tm.accuracy is None:
        return 1
    if tm.accuracy >= 0.8 and tm.questions_attempted >= 4:
        # sustained correct -> move up
        return 4 if tm.questions_attempted >= 8 else 3
    if tm.accuracy >= 0.6:
        return 2
    return 1  # repeated errors -> back to recall


def generate_quiz(
    *,
    topics: list[KnowledgeTopic],
    exam_points: list[ExamPointModel],
    past_exam_sets: list[PastExamSet],
    student: StudentModel,
    wrongbook_entries: list[dict],
    mode: str = "mixed",
    count: int = 10,
    question_language: str = "zh-CN",
    explanation_language: str | None = None,
    speed: int = 1,
) -> list[QuizQuestion]:
    """Generate a quiz in any mode. Every question is evidence-grounded; past-exam
    variants keep derived_from / source_question / variation_type provenance."""
    if mode not in QUIZ_MODES:
        raise ValueError(f"unknown quiz mode {mode!r}; expected {QUIZ_MODES}")
    explanation_language = explanation_language or question_language

    # select topics per mode
    selected: list[tuple[KnowledgeTopic, int]] = []
    exam_by_topic = {p.topic_id: p for p in exam_points}

    if mode == "diagnostic":
        # unknown topics first
        ordered = sorted(
            topics,
            key=lambda x: (student.topics.get(x.topic_id) is not None, _topic_priority(x, exam_points)),
        )
        for topic in ordered[:count]:
            selected.append((topic, 1))
    elif mode == "s-priority":
        for topic in topics:
            ep = exam_by_topic.get(topic.topic_id)
            if ep and ep.priority in ("S", "A"):
                selected.append((topic, _adaptive_level(topic, student)))
    elif mode == "weak-topic":
        for topic in topics:
            tm = student.topics.get(topic.topic_id)
            if tm and tm.mastery in ("novice", "developing"):
                selected.append((topic, _adaptive_level(topic, student)))
        if not selected:
            selected = [(topic, 1) for topic in topics[:count]]
    elif mode == "past-exam-style":
        # use actual past-exam questions with variants
        for topic in topics:
            if topic.past_exam_links:
                selected.append((topic, 3))
    elif mode == "mixed":
        # balance: S/A priority, weak topics, unknown
        seen: set[str] = set()
        for topic in sorted(topics, key=lambda x: (-_topic_priority(x, exam_points), x.topic_id)):
            if len(selected) >= count:
                break
            if topic.topic_id in seen:
                continue
            seen.add(topic.topic_id)
            selected.append((topic, _adaptive_level(topic, student)))
    elif mode == "wrongbook":
        for entry in wrongbook_entries:
            tid = entry.get("topic_id")
            for topic in topics:
                if topic.topic_id == tid:
                    selected.append((topic, 1))
    elif mode == "speed-run":
        # fast recall questions, one per topic
        for topic in topics[:count]:
            selected.append((topic, 1))
    elif mode == "cram":
        for topic in topics:
            ep = exam_by_topic.get(topic.topic_id)
            if ep and ep.priority in ("S", "A"):
                selected.append((topic, 2))

    # cap to count
    selected = selected[:count]

    # fail-soft: if a mode selects nothing (e.g. no S/A topics, empty wrongbook),
    # fall back to a mixed breadth-first selection so the quiz is never empty
    if not selected and topics:
        for topic in sorted(topics, key=lambda x: (-_topic_priority(x, exam_points), x.topic_id)):
            if len(selected) >= count:
                break
            selected.append((topic, _adaptive_level(topic, student)))

    # find past-exam questions for provenance
    past_questions: dict[str, dict] = {}
    for exam_set in past_exam_sets:
        for q in exam_set.questions:
            for tid in q.topics:
                if tid not in past_questions:
                    past_questions[tid] = {
                        "body": q.body,
                        "question_number": q.question_number,
                        "exam_set_id": q.exam_set_id,
                    }

    questions: list[QuizQuestion] = []
    for i, (topic, level) in enumerate(selected):
        ep = exam_by_topic.get(topic.topic_id)
        pq = past_questions.get(topic.topic_id)
        qtype = _question_type_for(topic, ep, level, mode)
        questions.append(
            _build_question(
                topic=topic,
                exam_point=ep,
                level=level,
                question_type=qtype,
                question_language=question_language,
                explanation_language=explanation_language,
                derived_from=(pq["exam_set_id"] + ":" + pq["question_number"]) if pq else None,
                source_question=pq["body"] if pq else None,
                variation_type="past-exam-variant" if pq else None,
                index=i,
                past_exam_question=pq,
            )
        )
    return questions


def _topic_priority(topic: KnowledgeTopic, exam_points: list[ExamPointModel]) -> int:
    for p in exam_points:
        if p.topic_id == topic.topic_id:
            return {"S": 5, "A": 4, "B": 2, "C": 1}.get(p.priority, 1)
    return 0


def _question_type_for(topic: KnowledgeTopic, ep: ExamPointModel | None, level: int, mode: str) -> str:
    if level >= 3:
        return "calculation" if topic.formulas else "short_answer"
    if topic.question_types:
        return topic.question_types[0]
    if ep and ep.question_types:
        return ep.question_types[0]
    return "short_answer"
