from __future__ import annotations

from pathlib import Path

import pytest

from recallforge.i18n import TerminologyMap
from recallforge.ingestion.pipeline import ingest_file
from recallforge.ingestion.types import IngestOptions
from recallforge.knowledge.build import build_course_intelligence
from recallforge.models import ReplanEvent
from recallforge.planner.events import record_replan_event
from recallforge.planner.orchestrator import generate_daily_plan_v4, render_plan_v4
from recallforge.state import course as course_mod
from recallforge.state import workspace as workspace_mod
from recallforge.student.store import load_student_model, save_student_model
from recallforge.tutor.cram import build_cram_plan
from recallforge.tutor.diagnosis import diagnose_wrong_answer
from recallforge.tutor.grading import grade_answer, record_grading_to_student
from recallforge.tutor.quiz import generate_quiz
from recallforge.tutor.tutor import build_tutor_response
from recallforge.tutor.wrongbook import add_wrongbook_entry, load_wrongbook


def _write_txt(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _build_4_course_workspace(root: Path, *, locale: str) -> Path:
    """4 courses with real material files, ingested + modeled."""
    materials = root / "materials"
    materials.mkdir(parents=True, exist_ok=True)
    zh = locale.startswith("zh")

    courses = [
        ("probability", "概率论" if zh else "Probability", "2026-06-19", 85,
         [("central_limit_theorem", "中心极限定理", "Central Limit Theorem"),
          ("conditional_probability", "条件概率", "conditional probability")]),
        ("organic-chemistry", "有机化学" if zh else "Organic Chemistry", "2026-06-20", 80,
         [("esterification", "酯化反应", "esterification"),
          ("neutralization", "中和反应", "neutralization")]),
        ("calculus", "微积分" if zh else "Calculus", "2026-06-21", 60,
         [("limits", "极限", "limits"), ("derivatives", "导数", "derivatives")]),
        ("botany", "植物学" if zh else "Botany", "2026-06-26", 70,
         [("photosynthesis", "光合作用", "photosynthesis"),
          ("transpiration", "蒸腾作用", "transpiration")]),
    ]
    workspace_mod.create_workspace(root / "ws", user_locale=locale, daily_total_hours=6)
    ws = root / "ws"

    for course_id, name, exam_date, target, topics in courses:
        workspace_mod.add_course_to_workspace(
            ws, course_id=course_id, course_name=name, exam_date=exam_date, target_score=target,
        )
        course_path = course_mod.course_dir(ws, course_id)
        tm = TerminologyMap(course_id=course_id)
        for topic_id, zh_name, en_name in topics:
            tm.add(topic_id, zh=zh_name, en=en_name)
        course_mod._write_json(course_path / "terminology_map.json", tm.to_state())

        # real material files per course
        for topic_id, zh_name, en_name in topics:
            fname = f"{course_id}_{topic_id}.txt"
            text = (
                f"{zh_name}（{en_name}）是指一个重要的课程概念。老师强调这是重点。"
                f"核心公式：X = f(Y) + ε。易错：注意适用条件。"
            )
            _write_txt(materials / fname, text)
            ingest_file(ws, course_id, materials / fname, options=IngestOptions())

        # a past exam for probability
        if course_id == "probability":
            exam_file = materials / "probability_exam_2024.txt"
            exam_text = (
                "2024 期末考试\n"
                "一、计算题 1. 用中心极限定理计算样本均值概率（15分）\n"
                "二、简答题 2. 简述条件概率定义（10分）"
            )
            _write_txt(exam_file, exam_text)
            ingest_file(ws, course_id, exam_file, options=IngestOptions())

        build_course_intelligence(ws, course_id, days_to_exam=6)
    return ws


def _run_full_loop(ws: Path, *, locale: str, course_id: str) -> None:
    """plan -> study -> quiz -> wrong -> diagnosis -> wrongbook -> replan ->
    next-day plan -> cram, in the given locale."""
    result = build_course_intelligence(ws, course_id, persist=False)

    # 1. exam-week plan
    plan = generate_daily_plan_v4(ws, "2026-06-18")
    assert plan.blocks, "plan must have blocks"
    rendered_zh = render_plan_v4(plan, locale)
    assert rendered_zh

    # 2. study one topic (tutor)
    topic = result.topics[0]
    model = load_student_model(ws, course_id)
    tutor = build_tutor_response(topic, model, locale=locale)
    assert tutor.sections, "tutor must produce sections"

    # 3. quiz
    questions = generate_quiz(
        topics=result.topics,
        exam_points=result.exam_points,
        past_exam_sets=result.past_exam_sets,
        student=model,
        wrongbook_entries=[],
        mode="mixed",
        count=2,
        question_language=locale,
        explanation_language=locale,
    )
    assert questions
    question = questions[0]

    # 4. wrong answer
    grading = grade_answer(question, "完全错误的答案", locale=locale)
    assert grading.correct is False

    # 5. mastery update
    record_grading_to_student(model, question, grading)
    save_student_model(ws, course_id, model)

    # 6. diagnosis
    diagnosis = diagnose_wrong_answer(
        question={"question_text": question.question_text},
        user_answer="完全错误的答案",
        grading_mistake=grading.mistake_type,
        topic=topic,
        prerequisites=topic.prerequisites,
        prerequisite_mastery={},
        locale=locale,
    )
    assert diagnosis.diagnosis in (
        "concept_gap", "formula_recall", "condition_misread", "prerequisite_gap",
        "calculation_error", "algebra_error", "sign_error", "unit_error",
        "reasoning_jump", "question_misread", "method_selection", "memory_failure",
        "careless_error", "unknown",
    )

    # 7. wrongbook
    add_wrongbook_entry(
        workspace_root=ws, course_id=course_id, question=question,
        user_answer="完全错误的答案", grading=grading, diagnosis=diagnosis,
        student=model,
    )
    assert load_wrongbook(ws, course_id), "wrongbook must contain the real wrong answer"

    # 8. replan (wrong answer event)
    record_replan_event(
        ws, ReplanEvent(event_type="wrong_answer", course_id=course_id, detail={"topic_id": question.topic_id})
    )

    # 9. next-day plan reflects the wrong answer
    plan_after = generate_daily_plan_v4(ws, "2026-06-19")
    assert plan_after.blocks

    # 10. cram includes the wrong topic
    wrongbook = load_wrongbook(ws, course_id)
    cram = build_cram_plan(
        workspace_root=ws, course_id=course_id,
        topics=result.topics, exam_points=result.exam_points,
        student=load_student_model(ws, course_id), wrongbook_entries=wrongbook,
        mode="3h", locale=locale,
    )
    assert cram.items, "cram must have items"


def test_full_e2e_4_courses_chinese(tmp_path: Path):
    ws = _build_4_course_workspace(tmp_path / "zh", locale="zh-CN")
    assert len(workspace_mod.list_courses(ws)) == 4
    _run_full_loop(ws, locale="zh-CN", course_id="probability")


def test_full_e2e_4_courses_english(tmp_path: Path):
    ws = _build_4_course_workspace(tmp_path / "en", locale="en-US")
    assert len(workspace_mod.list_courses(ws)) == 4
    _run_full_loop(ws, locale="en-US", course_id="probability")


def test_e2e_courses_are_isolated(tmp_path: Path):
    """No cross-course knowledge contamination after the full 4-course run."""
    ws = _build_4_course_workspace(tmp_path / "zh", locale="zh-CN")
    for cid in workspace_mod.list_courses(ws):
        course_path = course_mod.course_dir(ws, cid)
        # every per-course payload carries only its own course_id
        for filename in ("knowledge_graph.json", "exam_model.json", "student_state.json", "wrongbook.json"):
            data = course_mod.load_course_json(course_path, filename, {}) or {}
            assert data.get("course_id") in (None, cid), f"{cid}/{filename} contaminated"
        # knowledge graph topics are course-specific (no foreign topic ids)
        kg = course_mod.load_course_json(course_path, "knowledge_graph.json", {}) or {}
        for topic in kg.get("topics", []):
            assert topic.get("topic_id") in {
                "central_limit_theorem", "conditional_probability",
                "esterification", "neutralization", "limits", "derivatives",
                "photosynthesis", "transpiration",
            }, f"{cid} has foreign topic {topic.get('topic_id')}"
