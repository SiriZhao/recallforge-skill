from __future__ import annotations

from datetime import date

import pytest

from exam_review_skill.models import StudentModel, TopicMastery
from exam_review_skill.state.isolation import StateContaminationError
from exam_review_skill.student.mastery import (
    compute_forgetting_risk,
    compute_mastery,
    sync_mastery_levels,
)
from exam_review_skill.student.sessions import AnswerResult, record_answer, record_wrongbook_entry
from exam_review_skill.student.store import load_student_model, save_student_model


def _model() -> StudentModel:
    return StudentModel(course_id="probability")


def test_no_data_means_mastery_unknown(tmp_path):
    """No answer data -> mastery must be 'unknown', never a pretend 0.5."""
    model = _model()
    model.topics["central_limit_theorem"] = TopicMastery(topic_id="central_limit_theorem")
    compute_mastery(model.topics["central_limit_theorem"])
    assert model.topics["central_limit_theorem"].mastery == "unknown"
    assert model.topics["central_limit_theorem"].mastery_score is None
    # unknown mastery is NOT added to weak/strong points (no fabricated labels)
    sync_mastery_levels(model)
    assert model.weak_points == []
    assert model.strong_points == []


def test_mastery_is_not_equal_to_accuracy(tmp_path):
    """Mastery combines accuracy + difficulty + independence + recency + transfer;
    it must differ from raw accuracy when other factors intervene."""
    model = _model()
    # all correct, difficulty 1 only, no hints, no transfer -> high accuracy
    for _ in range(5):
        record_answer(
            model,
            AnswerResult(topic_id="t1", correct=True, difficulty=1, question_type="multiple choice"),
            today="2026-06-18",
        )
    tm = model.topics["t1"]
    assert tm.accuracy == 1.0
    assert tm.mastery_score is not None and tm.mastery_score < 1.0  # not equal to accuracy
    assert tm.mastery == "developing"  # narrow difficulty coverage caps it


def test_difficulty_and_hints_and_transfer_improve_mastery(tmp_path):
    low = _model()
    for _ in range(4):
        record_answer(
            low,
            AnswerResult(topic_id="t1", correct=True, difficulty=1, question_type="multiple choice"),
            today="2026-06-18",
        )
    high = _model()
    for _ in range(4):
        record_answer(
            high,
            AnswerResult(topic_id="t1", correct=True, difficulty=3, question_type="calculation"),
            today="2026-06-18",
        )
    # transfer evidence
    record_answer(
        high,
        AnswerResult(topic_id="t1", correct=True, difficulty=3, question_type="calculation", is_new_form=True),
        today="2026-06-18",
    )
    assert high.topics["t1"].mastery_score > low.topics["t1"].mastery_score


def test_hint_dependency_lowers_mastery(tmp_path):
    independent = _model()
    hinted = _model()
    for _ in range(4):
        record_answer(
            independent,
            AnswerResult(topic_id="t1", correct=True, difficulty=2, question_type="short_answer"),
            today="2026-06-18",
        )
    for _ in range(4):
        record_answer(
            hinted,
            AnswerResult(topic_id="t1", correct=True, difficulty=2, question_type="short_answer", used_hint=True),
            today="2026-06-18",
        )
    assert hinted.topics["t1"].hint_dependency == 1.0
    assert independent.topics["t1"].hint_dependency == 0.0
    assert independent.topics["t1"].mastery_score > hinted.topics["t1"].mastery_score


def test_repeat_errors_penalize(tmp_path):
    clean = _model()
    sloppy = _model()
    for _ in range(4):
        record_answer(clean, AnswerResult(topic_id="t1", correct=True, difficulty=2), today="2026-06-18")
    for i in range(4):
        record_answer(
            sloppy,
            AnswerResult(
                topic_id="t1",
                correct=bool(i % 2),
                difficulty=2,
                mistake_type="calculation_error" if not i % 2 else None,
            ),
            today="2026-06-18",
        )
    assert sloppy.topics["t1"].wrong_count == 2
    assert clean.topics["t1"].mastery_score > sloppy.topics["t1"].mastery_score


def test_forgetting_risk_rises_with_time(tmp_path):
    tm = TopicMastery(topic_id="t1", mastery="proficient", last_reviewed="2026-06-01")
    fresh = compute_forgetting_risk(tm, today=date(2026, 6, 2))
    old = compute_forgetting_risk(tm, today=date(2026, 6, 15))
    assert old > fresh


def test_session_record_updates_mastery_and_history(tmp_path):
    model = _model()
    record_answer(
        model,
        AnswerResult(topic_id="t1", correct=True, difficulty=2, question_type="calculation"),
        today="2026-06-18",
    )
    record_answer(
        model,
        AnswerResult(topic_id="t1", correct=False, difficulty=3, mistake_type="unit_error", question_type="calculation"),
        today="2026-06-18",
    )
    tm = model.topics["t1"]
    assert tm.questions_attempted == 2
    assert tm.accuracy == 0.5
    assert tm.wrong_count == 1
    assert "unit_error" in tm.mistake_types
    assert len(model.review_history) == 2
    assert model.review_history[1]["correct"] is False


def test_wrongbook_rejects_fabricated_content(tmp_path):
    model = _model()
    answer = AnswerResult(topic_id="t1", correct=False, mistake_type="unit_error")
    with pytest.raises(StateContaminationError):
        record_wrongbook_entry(
            model,
            answer,
            question_text="Mock provider 生成的规则题",
            correct_answer="x",
            user_answer="示例：未作答",
        )
    entry = record_wrongbook_entry(
        model,
        answer,
        question_text="What is c(HCl)?",
        correct_answer="0.09920 mol/L",
        user_answer="0.1",
    )
    assert entry["topic_id"] == "t1"
    assert entry["wrong_reason"] == "单位错误"
    assert entry["date"] == date.today().isoformat()


def test_student_model_round_trip(tmp_path):
    root = tmp_path / "ws"
    from exam_review_skill.state import course as course_mod
    from exam_review_skill.state import workspace as workspace_mod

    workspace_mod.create_workspace(root)
    workspace_mod.add_course_to_workspace(root, course_id="probability", course_name="概率论")
    model = load_student_model(root, "probability")
    assert model.course_id == "probability"
    assert model.topics == {}  # no data -> no topics
    record_answer(
        model,
        AnswerResult(topic_id="central_limit_theorem", correct=True, difficulty=2),
        today="2026-06-18",
    )
    save_student_model(root, "probability", model)
    reloaded = load_student_model(root, "probability")
    assert "central_limit_theorem" in reloaded.topics
    assert reloaded.topics["central_limit_theorem"].questions_attempted == 1
    # compatibility view for Round 3 risk radar
    import json

    state = json.loads(
        (course_mod.course_dir(root, "probability") / "student_state.json").read_text(encoding="utf-8")
    )
    assert state["mastery"]["central_limit_theorem"]["level"] in ("novice", "developing", "proficient")
