from __future__ import annotations

from exam_review_skill.models import KnowledgeTopic, QuizQuestion, StudentModel, TopicField
from exam_review_skill.tutor.diagnosis import DIAGNOSIS_TAXONOMY, diagnose_wrong_answer
from exam_review_skill.tutor.grading import grade_answer, record_grading_to_student


def _question(topic_id: str = "t1") -> QuizQuestion:
    return QuizQuestion(
        question_id="Q1",
        topic_id=topic_id,
        topic_name="CLT",
        question_type="calculation",
        level=2,
        question_text="计算样本均值概率。",
        correct_answer="先标准化：Z = (x - μ) / (σ/√n)，再查正态分布表。",
        explanation="标准化后用正态分布表。",
        common_trap="忘记 n 足够大条件",
        evidence_refs=["e1"],
    )


def test_grade_correct_answer():
    result = grade_answer(_question(), "先标准化：Z = (x - μ) / (σ/√n)，再查正态分布表。")
    assert result.correct is True
    assert result.score >= 0.8
    assert "命中" in result.process_analysis


def test_grade_wrong_answer():
    result = grade_answer(_question(), "直接查表")
    assert result.correct is False
    assert result.mistake_type == "calculation_error"
    assert result.feedback


def test_grade_no_answer():
    result = grade_answer(_question(), "")
    assert result.correct is False
    assert result.score == 0.0


def test_grade_multiple_choice():
    question = QuizQuestion(
        question_id="Q2", topic_id="t1", topic_name="CLT", question_type="multiple_choice",
        level=1, question_text="Which is correct?", correct_answer="B", explanation="x",
    )
    assert grade_answer(question, "B").correct is True
    assert grade_answer(question, "b").correct is True
    assert grade_answer(question, "A").correct is False


def test_grade_bilingual_answer():
    """Chinese answer to an English question is graded by keywords."""
    question = QuizQuestion(
        question_id="Q3", topic_id="t1", topic_name="CLT", question_type="short_answer",
        level=1, question_text="Explain the CLT.", correct_answer="Standardize with Z=(x-mu)/(sigma/sqrt n) and use the normal table.",
    )
    result = grade_answer(question, "用 Z=(x-mu)/(sigma/sqrt n) 标准化，再查正态分布表。")
    assert result.correct is True


def test_record_grading_updates_student_mastery():
    student = StudentModel(course_id="p")
    question = _question()
    wrong = grade_answer(question, "直接查表")
    record_grading_to_student(student, question, wrong)
    assert student.topics["t1"].questions_attempted == 1
    assert student.topics["t1"].wrong_count == 1
    right = grade_answer(question, "先标准化：Z = (x - μ) / (σ/√n)，再查正态分布表。")
    record_grading_to_student(student, question, right)
    assert student.topics["t1"].questions_attempted == 2
    assert student.topics["t1"].accuracy == 0.5


def test_diagnosis_taxonomy_complete():
    assert len(DIAGNOSIS_TAXONOMY) >= 13
    for required in (
        "concept_gap", "formula_recall", "condition_misread", "prerequisite_gap",
        "calculation_error", "algebra_error", "sign_error", "unit_error",
        "reasoning_jump", "question_misread", "method_selection", "memory_failure",
        "careless_error", "unknown",
    ):
        assert required in DIAGNOSIS_TAXONOMY


def test_diagnosis_prerequisite_gap_detected():
    """A weak prerequisite is the root cause -> prerequisite_gap diagnosis."""
    topic = KnowledgeTopic(
        topic_id="t2", canonical_name="积分", prerequisites=["t1"], evidence=["e1"],
        definitions=[TopicField(text="积分定义", evidence_refs=["e1"])],
    )
    result = diagnose_wrong_answer(
        question={"question_text": "计算积分"},
        user_answer="不会",
        grading_mistake="calculation_error",
        topic=topic,
        prerequisites=["t1"],
        prerequisite_mastery={"t1": "novice"},  # prerequisite weak
    )
    assert result.diagnosis == "prerequisite_gap"
    assert result.severity == 3
    assert result.prerequisite_fix == ["t1"]


def test_diagnosis_unknown_fallback():
    topic = KnowledgeTopic(topic_id="t1", canonical_name="CLT", evidence=["e1"])
    result = diagnose_wrong_answer(
        question={"question_text": "概念题"},
        user_answer="",
        grading_mistake="unknown",
        topic=topic,
        prerequisites=[],
        prerequisite_mastery={},
    )
    assert result.diagnosis == "question_misread"
