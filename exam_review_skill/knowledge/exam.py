from __future__ import annotations

import re
from dataclasses import asdict

from ..i18n import TerminologyMap
from ..models import (
    ExamPointModel,
    PastExamQuestion,
    PastExamSet,
    TeacherStyle,
    KnowledgeTopic,
    _now_iso,
)
from .teacher import build_teacher_style
from .topic import _extract_text, _mention_topics, _sentences


EXAM_FILE_MARKERS = ("exam", "test", "past", "试卷", "真题", "期末", "考题")
YEAR_RE = re.compile(r"(19|20)\d{2}")

# Per-course overrideable evidence weights (never hard-coded globally; default table
# applies unless the manifest/course config overrides it).
DEFAULT_EVIDENCE_WEIGHTS = {
    "past_exam": 2.0,
    "answer_key": 2.0,
    "teacher_hint": 1.6,
    "lecture_slide": 1.0,
    "class_notes": 1.1,
    "textbook": 1.0,
    "exercise": 1.2,
    "lab_manual": 0.8,
    "unknown": 0.9,
}


def _role_of_record(record: dict) -> str:
    source = (record.get("source_file") or "").lower()
    if "answer" in source:
        return "answer_key"
    if any(marker in source for marker in EXAM_FILE_MARKERS):
        return "past_exam"
    for name, markers in {
        "teacher_hint": ["teacher", "hint", "老师", "重点"],
        "lecture_slide": ["lecture", "slide", "ppt", "课件", "课堂"],
        "class_notes": ["note", "笔记", "讲义"],
        "textbook": ["book", "textbook", "教材", "课本"],
        "exercise": ["exercise", "练习", "习题", "作业"],
        "lab_manual": ["lab", "实验"],
    }.items():
        if any(m in source for m in markers):
            return name
    return "unknown"


def evidence_weight_for(record: dict, weights: dict | None = None) -> float:
    table = {**DEFAULT_EVIDENCE_WEIGHTS, **(weights or {})}
    role = _role_of_record(record)
    return table.get(role, 0.9)


def build_past_exam_sets(
    evidence_records: list[dict], term_map: TerminologyMap
) -> list[PastExamSet]:
    """Model each past-exam file separately. Extract questions with topics mapped
    through the terminology map. Bidirectional links are derived later from topic
    `past_exam_links` and each question's `topics`."""
    sets: dict[str, PastExamSet] = {}
    for record in evidence_records:
        if record.get("synthetic") is True:
            continue
        content = record.get("content", {}) or {}
        exam_structure = content.get("exam_structure") or []
        source = record.get("source_file", "")
        if not exam_structure and not any(m in source.lower() for m in EXAM_FILE_MARKERS):
            continue
        evidence_id = record.get("evidence_id")
        if source not in sets:
            year_match = YEAR_RE.search(source)
            sets[source] = PastExamSet(
                exam_set_id=source,
                source_file=source,
                year=year_match.group(0) if year_match else None,
                evidence_ref=evidence_id,
            )
        exam_set = sets[source]
        for q in exam_structure:
            body = q.get("body", "") or ""
            topics = _mention_topics(body, term_map)
            score = q.get("score")
            score_value = None
            if score:
                try:
                    score_value = int(re.sub(r"\D", "", score)[:2])
                except (ValueError, TypeError):
                    score_value = None
            exam_set.questions.append(
                PastExamQuestion(
                    exam_set_id=source,
                    question_number=q.get("question_number", ""),
                    question_type=q.get("question_type") or _infer_question_type(body),
                    score=str(score_value) if score_value else score,
                    topics=topics,
                    subtopics=_mention_subtopics(body, term_map),
                    difficulty=_infer_difficulty(body),
                    methods=[],
                    common_traps=_infer_traps(body),
                    solution=None,
                    evidence_ref=evidence_id,
                    year=exam_set.year,
                    confidence=0.6,
                )
            )
    return list(sets.values())


def _infer_question_type(body: str) -> str:
    for zh, en in (
        ("计算", "calculation"),
        ("选择", "multiple choice"),
        ("简答", "short answer"),
        ("判断", "true/false"),
        ("填空", "fill in the blank"),
        ("实验", "lab"),
    ):
        if zh in body or en in body:
            return en
    return "unknown"


def _infer_difficulty(body: str) -> int:
    if "综合" in body or "integrated" in body.lower():
        return 4
    if "计算" in body or "calculation" in body.lower():
        return 3
    if "选择" in body or "multiple choice" in body.lower():
        return 2
    return 2


def _infer_traps(body: str) -> list[str]:
    traps = []
    if "有效数字" in body or "significant" in body.lower():
        traps.append("有效数字/单位")
    if "条件" in body or "condition" in body.lower():
        traps.append("适用条件遗漏")
    return traps


def _mention_subtopics(body: str, term_map: TerminologyMap) -> list[str]:
    return _mention_topics(body, term_map)


def _topic_name(topic: KnowledgeTopic) -> str:
    return topic.localized_names.get("en-US") or topic.localized_names.get("zh-CN") or topic.canonical_name


def build_exam_points(
    topics: list[KnowledgeTopic],
    past_exam_sets: list[PastExamSet],
    teacher_style: TeacherStyle,
    evidence_records: list[dict],
    term_map: TerminologyMap,
    *,
    evidence_weights: dict | None = None,
) -> list[ExamPointModel]:
    """Build one ExamPointModel per topic with a transparent likelihood heuristic.

    likelihood_estimate is a deterministic score in [0,1] - an ordinal heuristic, NOT
    a statistical probability. It combines past-exam frequency, teacher emphasis,
    and evidence weight; the components are all recorded in `priority_rationale`.
    """
    question_by_topic: dict[str, list[PastExamQuestion]] = {}
    for exam_set in past_exam_sets:
        for question in exam_set.questions:
            for topic_id in question.topics:
                question_by_topic.setdefault(topic_id, []).append(question)

    points: list[ExamPointModel] = []
    for topic in topics:
        questions = question_by_topic.get(topic.topic_id, [])
        frequency = len(questions)
        teacher_tier = topic.teacher_emphasis
        evidence = list(topic.evidence)
        weight_sum = sum(evidence_weight_for(r, evidence_weights) for r in evidence_records if r.get("evidence_id") in evidence)

        # likelihood heuristic: transparent, ordinal, not a real probability
        freq_component = min(1.0, frequency / 5.0) * 0.5
        teacher_component = {
            "observed": 0.35,
            "strongly_inferred": 0.25,
            "inferred": 0.15,
            "unknown": 0.0,
        }.get(teacher_tier, 0.0)
        weight_component = min(1.0, weight_sum / 5.0) * 0.15
        likelihood = min(1.0, freq_component + teacher_component + weight_component)

        importance = 3
        if frequency >= 3:
            importance = 5
        elif frequency >= 1:
            importance = 4
        elif teacher_tier in ("observed", "strongly_inferred"):
            importance = 4

        expected_score = _expected_score_range(questions)
        q_types = list(topic.question_types)
        for q in questions:
            if q.question_type and q.question_type not in q_types:
                q_types.append(q.question_type)

        past_links = [asdict(q) for q in questions]
        points.append(
            ExamPointModel(
                exam_point_id=f"EP{len(points) + 1:03d}",
                topic_id=topic.topic_id,
                topic_name=_topic_name(topic),
                importance=importance,
                likelihood_estimate=round(likelihood, 3),
                confidence=round(topic.source_confidence, 2),
                expected_score_range=expected_score,
                question_types=q_types,
                teacher_emphasis=teacher_tier,
                past_exam_frequency=frequency,
                learning_cost=round(_learning_cost(topic), 2),
                evidence=evidence,
                past_exam_questions=past_links,
                priority="C",
                inferred=not bool(frequency or teacher_tier != "unknown"),
            )
        )
    return points


def _expected_score_range(questions: list[PastExamQuestion]) -> list[int]:
    scores = []
    for q in questions:
        if q.score:
            try:
                scores.append(int(re.sub(r"\D", "", q.score)[:3]))
            except (ValueError, TypeError):
                continue
    if not scores:
        return [0, 0]
    return [min(scores), max(scores)]


def _learning_cost(topic: KnowledgeTopic) -> float:
    base = 1.0
    if topic.formulas:
        base += 0.5
    if len(topic.methods) > 1:
        base += 0.3
    if len(topic.definitions) > 1:
        base += 0.2
    if topic.question_types:
        base += 0.2
    return min(base, 5.0)


def exam_model_state(
    course_id: str,
    exam_points: list[ExamPointModel],
    past_exam_sets: list[PastExamSet],
    teacher_style: TeacherStyle,
    evidence_weights: dict | None = None,
) -> dict:
    return {
        "course_id": course_id,
        "exam_points": [asdict(p) for p in exam_points],
        "past_exam_sets": [asdict(s) for s in past_exam_sets],
        "teacher_style": asdict(teacher_style),
        "evidence_weights": {**DEFAULT_EVIDENCE_WEIGHTS, **(evidence_weights or {})},
        "updated_at": _now_iso(),
    }
