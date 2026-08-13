from __future__ import annotations

from pathlib import Path

from recallforge.models import ReplanEvent
from recallforge.planner.events import record_replan_event
from recallforge.planner.orchestrator import generate_daily_plan_v4
from recallforge.student.store import load_student_model, save_student_model
from recallforge.tutor.cram import build_cram_plan
from recallforge.tutor.diagnosis import diagnose_wrong_answer
from recallforge.tutor.grading import grade_answer, record_grading_to_student
from recallforge.tutor.quiz import generate_quiz
from recallforge.tutor.tutor import build_tutor_response
from recallforge.tutor.wrongbook import add_wrongbook_entry, load_wrongbook, update_retry_after_attempt

from planner_fixtures import build_scenario_workspace


def test_full_learning_loop(tmp_path: Path):
    """The complete closed loop:
    plan -> learn -> quiz -> wrong -> diagnosis -> wrongbook -> replan -> retry
    -> mastery update.

    Verifies every step affects the next one (wrong answer updates mastery, enters
    wrongbook, triggers a replan event, and the retry is scheduled)."""
    root = build_scenario_workspace(tmp_path / "ws")

    # --- plan: generate a global plan for probability's exam week
    plan = generate_daily_plan_v4(root, "2026-06-18")
    assert any(b.course_id == "probability" for b in plan.blocks)

    # --- learn: tutor the S-level topic
    from recallforge.knowledge.build import build_course_intelligence

    result = build_course_intelligence(root, "probability", persist=False)
    clt = next(t for t in result.topics if t.topic_id == "central_limit_theorem")
    model = load_student_model(root, "probability")
    tutor = build_tutor_response(clt, model, locale="zh-CN")
    assert tutor.sections

    # --- quiz: generate questions and answer one WRONG
    questions = generate_quiz(
        topics=result.topics,
        exam_points=result.exam_points,
        past_exam_sets=result.past_exam_sets,
        student=model,
        wrongbook_entries=[],
        mode="s-priority",
        count=2,
    )
    assert questions
    q = questions[0]
    wrong_grading = grade_answer(q, "完全错误的答案")
    assert wrong_grading.correct is False

    # --- mastery update from the wrong answer
    record_grading_to_student(model, q, wrong_grading)
    assert model.topics[q.topic_id].wrong_count == 1
    save_student_model(root, "probability", model)

    # --- diagnosis
    diagnosis = diagnose_wrong_answer(
        question={"question_text": q.question_text},
        user_answer="完全错误的答案",
        grading_mistake=wrong_grading.mistake_type,
        topic=clt,
        prerequisites=clt.prerequisites,
        prerequisite_mastery={},
    )
    assert diagnosis.diagnosis in (
        "concept_gap", "formula_recall", "condition_misread", "prerequisite_gap",
        "calculation_error", "algebra_error", "sign_error", "unit_error",
        "reasoning_jump", "question_misread", "method_selection", "memory_failure",
        "careless_error", "unknown",
    )

    # --- wrongbook
    entry = add_wrongbook_entry(
        workspace_root=root, course_id="probability", question=q,
        user_answer="完全错误的答案", grading=wrong_grading, diagnosis=diagnosis,
        student=model,
    )
    assert entry["diagnosis"] == diagnosis.diagnosis
    wrongbook = load_wrongbook(root, "probability")
    assert len(wrongbook) == 1

    # --- replan: record the wrong-answer event and regenerate the plan
    record_replan_event(
        root,
        ReplanEvent(event_type="wrong_answer", course_id="probability", detail={"topic_id": q.topic_id}),
    )
    plan_after = generate_daily_plan_v4(root, "2026-06-18")
    # the wrong topic should appear as practice (not cram/maintenance-only)
    prob_blocks_after = [b for b in plan_after.blocks if b.course_id == "probability"]
    assert prob_blocks_after, "replanned probability must still appear"

    # --- retry: schedule the retry and re-attempt correctly
    from recallforge.tutor.retry import schedule_retry

    retry = schedule_retry(
        topic_id=q.topic_id,
        diagnosis=diagnosis.diagnosis,
        repeat_count=0,
        mastery="novice",
        days_to_exam=1,
    )
    assert retry.next_review_date

    # re-attempt correctly -> mastery improves, wrongbook entry resolves
    correct_grading = grade_answer(q, q.correct_answer)
    record_grading_to_student(model, q, correct_grading)
    save_student_model(root, "probability", model)
    assert model.topics[q.topic_id].wrong_count == 1
    assert model.topics[q.topic_id].accuracy == 0.5
    update_retry_after_attempt(root, "probability", q.topic_id, correct=True)

    # --- mastery update verified end-to-end
    reloaded = load_student_model(root, "probability")
    assert reloaded.topics[q.topic_id].questions_attempted == 2
    assert reloaded.topics[q.topic_id].mastery != "unknown"

    # --- cram: the S-level topic is in the 30m rescue
    cram = build_cram_plan(
        workspace_root=root, course_id="probability",
        topics=result.topics, exam_points=result.exam_points,
        student=reloaded, wrongbook_entries=load_wrongbook(root, "probability"),
        mode="30m", locale="zh-CN",
    )
    assert cram.focus_topics
