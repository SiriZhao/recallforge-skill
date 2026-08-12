from __future__ import annotations

from pathlib import Path

from exam_review_skill.models import (
    ExamPointModel,
    KnowledgeTopic,
    PastExamQuestion,
    PastExamSet,
    QuizQuestion,
    StudentModel,
    TopicField,
)
from exam_review_skill.tutor.quiz import QUIZ_MODES, generate_quiz
from exam_review_skill.tutor.tutor import build_tutor_response


def _topic(topic_id: str = "central_limit_theorem") -> KnowledgeTopic:
    return KnowledgeTopic(
        topic_id=topic_id,
        canonical_name="Central Limit Theorem",
        localized_names={"zh-CN": "中心极限定理", "en-US": "Central Limit Theorem"},
        definitions=[TopicField(text="中心极限定理是指大量独立随机变量之和近似服从正态分布。", evidence_refs=["e1"])],
        formulas=[TopicField(text="Xn ≈ N(μ, σ²/n)", evidence_refs=["e1"])],
        methods=[TopicField(text="方法：标准化后用正态分布查表。", evidence_refs=["e1"])],
        common_mistakes=[TopicField(text="易错：忘记条件 n 足够大。", evidence_refs=["e1"])],
        question_types=["calculation", "short answer"],
        evidence=["e1"],
        teacher_emphasis="observed",
        past_exam_links=[{"exam_set_id": "past_exam_2024.pdf", "question_number": "1", "year": "2024"}],
    )


def _topic_no_formula() -> KnowledgeTopic:
    return KnowledgeTopic(
        topic_id="botany_leaf",
        canonical_name="Leaf structure",
        localized_names={"zh-CN": "叶片结构", "en-US": "Leaf structure"},
        definitions=[TopicField(text="叶片结构是指叶片由表皮、叶肉和叶脉组成。", evidence_refs=["e2"])],
        question_types=["short answer"],
        evidence=["e2"],
    )


def _exam_points():
    return [
        ExamPointModel(
            exam_point_id="EP1", topic_id="central_limit_theorem", topic_name="Central Limit Theorem",
            importance=5, likelihood_estimate=0.9, priority="S", evidence=["e1"],
            question_types=["calculation"],
        ),
        ExamPointModel(
            exam_point_id="EP2", topic_id="botany_leaf", topic_name="Leaf structure",
            importance=2, likelihood_estimate=0.1, priority="C", evidence=["e2"],
        ),
    ]


def test_tutor_course_first_and_supplementary():
    topic = _topic()
    response = build_tutor_response(topic, StudentModel(course_id="p"), locale="zh-CN")
    titles = [s.title for s in response.sections]
    assert any("直觉" in title for title in titles)
    assert any("定义" in title for title in titles)
    assert any("公式" in title for title in titles)
    assert any("方法" in title for title in titles)
    assert any("常见错误" in title for title in titles)
    # course content is not marked supplementary
    assert not any(s.supplementary for s in response.sections if s.evidence_refs)
    assert response.check_question
    # definition is verbatim from the topic evidence
    assert response.sections[0].content == topic.definitions[0].text


def test_tutor_no_formula_subject_adaptive():
    """A subject with no formulas must NOT get a formula section."""
    topic = _topic_no_formula()
    response = build_tutor_response(topic, StudentModel(course_id="b"), locale="zh-CN")
    titles = [s.title for s in response.sections]
    assert not any("公式" in title for title in titles)


def test_quiz_all_modes_supported():
    topics = [_topic(), _topic_no_formula()]
    student = StudentModel(course_id="p")
    for mode in QUIZ_MODES:
        questions = generate_quiz(
            topics=topics,
            exam_points=_exam_points(),
            past_exam_sets=[],
            student=student,
            wrongbook_entries=[],
            mode=mode,
            count=4,
        )
        assert questions, mode


def test_quiz_s_priority_selects_s_topics():
    topics = [_topic(), _topic_no_formula()]
    questions = generate_quiz(
        topics=topics,
        exam_points=_exam_points(),
        past_exam_sets=[],
        student=StudentModel(course_id="p"),
        wrongbook_entries=[],
        mode="s-priority",
        count=5,
    )
    # only S/A priority topics selected -> central_limit_theorem, not botany_leaf
    assert questions
    assert all(q.topic_id == "central_limit_theorem" for q in questions)


def test_quiz_weak_topic_selects_weak():
    student = StudentModel(course_id="p")
    # make botany weak via answers
    from exam_review_skill.student.sessions import AnswerResult, record_answer

    record_answer(
        student,
        AnswerResult(topic_id="botany_leaf", correct=False, mistake_type="concept_gap", difficulty=2),
        today="2026-06-18",
    )
    questions = generate_quiz(
        topics=[_topic(), _topic_no_formula()],
        exam_points=_exam_points(),
        past_exam_sets=[],
        student=student,
        wrongbook_entries=[],
        mode="weak-topic",
        count=5,
    )
    assert all(q.topic_id == "botany_leaf" for q in questions)


def test_past_exam_variant_keeps_provenance():
    topics = [_topic()]
    past = PastExamSet(
        exam_set_id="past_exam_2024.pdf",
        source_file="past_exam_2024.pdf",
        year="2024",
        questions=[
            PastExamQuestion(
                exam_set_id="past_exam_2024.pdf",
                question_number="1",
                question_type="calculation",
                topics=["central_limit_theorem"],
                body="用中心极限定理计算样本均值概率。",
                score="15",
            )
        ],
    )
    questions = generate_quiz(
        topics=topics,
        exam_points=_exam_points(),
        past_exam_sets=[past],
        student=StudentModel(course_id="p"),
        wrongbook_entries=[],
        mode="past-exam-style",
        count=3,
    )
    assert questions
    for q in questions:
        assert q.derived_from == "past_exam_2024.pdf:1"
        assert q.source_question
        assert q.variation_type == "past-exam-variant"
        assert q.topic_id == "central_limit_theorem"


def test_quiz_language_independent():
    """English question + Chinese explanation must be independently controllable."""
    questions = generate_quiz(
        topics=[_topic()],
        exam_points=_exam_points(),
        past_exam_sets=[],
        student=StudentModel(course_id="p"),
        wrongbook_entries=[],
        mode="diagnostic",
        count=2,
        question_language="en-US",
        explanation_language="zh-CN",
    )
    for q in questions:
        assert q.question_language == "en-US"
        assert q.explanation_language == "zh-CN"
        assert "[Recall]" in q.question_text or "[Standard]" in q.question_text


def test_adaptive_difficulty_rises_with_sustained_correct():
    """Sustained correct answers raise the difficulty level; repeated errors keep it low."""
    from exam_review_skill.student.sessions import AnswerResult, record_answer

    strong = StudentModel(course_id="p")
    for _ in range(8):
        record_answer(
            strong,
            AnswerResult(topic_id="central_limit_theorem", correct=True, difficulty=3, question_type="calculation"),
            today="2026-06-18",
        )
    weak = StudentModel(course_id="p")
    for _ in range(8):
        record_answer(
            weak,
            AnswerResult(topic_id="central_limit_theorem", correct=False, mistake_type="concept_gap", difficulty=2),
            today="2026-06-18",
        )

    strong_q = generate_quiz(
        topics=[_topic()], exam_points=_exam_points(), past_exam_sets=[],
        student=strong, wrongbook_entries=[], mode="mixed", count=1,
    )[0]
    weak_q = generate_quiz(
        topics=[_topic()], exam_points=_exam_points(), past_exam_sets=[],
        student=weak, wrongbook_entries=[], mode="mixed", count=1,
    )[0]
    assert strong_q.level > weak_q.level
