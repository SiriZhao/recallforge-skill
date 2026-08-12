from __future__ import annotations

from datetime import date
from pathlib import Path

from exam_review_skill.models import (
    ExamPointModel,
    KnowledgeTopic,
    QuizQuestion,
    StudentModel,
    TopicField,
)
from exam_review_skill.state import course as course_mod
from exam_review_skill.state import workspace as workspace_mod
from exam_review_skill.tutor.cram import CRAM_MODES, build_cram_plan, render_cram_plan
from exam_review_skill.tutor.diagnosis import diagnose_wrong_answer
from exam_review_skill.tutor.grading import grade_answer
from exam_review_skill.tutor.retry import schedule_retry
from exam_review_skill.tutor.wrongbook import add_wrongbook_entry, load_wrongbook


def _topic() -> KnowledgeTopic:
    return KnowledgeTopic(
        topic_id="t1", canonical_name="CLT",
        localized_names={"zh-CN": "中心极限定理", "en-US": "CLT"},
        definitions=[TopicField(text="定义", evidence_refs=["e1"])],
        formulas=[TopicField(text="Z=(x-μ)/(σ/√n)", evidence_refs=["e1"])],
        common_mistakes=[TopicField(text="易错：忘记条件", evidence_refs=["e1"])],
        question_types=["calculation"], evidence=["e1"],
        past_exam_links=[{"exam_set_id": "p.pdf", "question_number": "1"}],
    )


def _exam_points():
    return [
        ExamPointModel(
            exam_point_id="EP1", topic_id="t1", topic_name="CLT",
            importance=5, likelihood_estimate=0.9, priority="S", evidence=["e1"],
            priority_rationale=["score=0.90 ..."],
        ),
        ExamPointModel(
            exam_point_id="EP2", topic_id="t2", topic_name="条件概率",
            importance=2, likelihood_estimate=0.1, priority="C", evidence=["e2"],
        ),
    ]


def _wrongbook_entries() -> list[dict]:
    return [
        {
            "topic_id": "t1", "question_text": "计算概率", "diagnosis": "calculation_error",
            "severity": 2, "retry_count": 0, "resolved": False, "evidence_refs": ["e1"],
        }
    ]


def test_add_wrongbook_entry_persists(tmp_path: Path):
    root = tmp_path / "ws"
    workspace_mod.create_workspace(root)
    workspace_mod.add_course_to_workspace(root, course_id="p", course_name="概率论")
    question = QuizQuestion(
        question_id="Q1", topic_id="t1", topic_name="CLT", question_type="calculation",
        level=2, question_text="计算", correct_answer="答案", explanation="讲",
        evidence_refs=["e1"],
    )
    grading = grade_answer(question, "错的")
    topic = _topic()
    diagnosis = diagnose_wrong_answer(
        question={"question_text": "计算"}, user_answer="错的", grading_mistake="calculation_error",
        topic=topic, prerequisites=[], prerequisite_mastery={},
    )
    entry = add_wrongbook_entry(
        workspace_root=root, course_id="p", question=question, user_answer="错的",
        grading=grading, diagnosis=diagnosis, student=StudentModel(course_id="p"),
    )
    assert entry["topic_id"] == "t1"
    assert entry["diagnosis"] == "calculation_error"
    assert entry["next_review_date"]
    stored = load_wrongbook(root, "p")
    assert len(stored) == 1


def test_wrongbook_rejects_fabricated(tmp_path: Path):
    root = tmp_path / "ws"
    workspace_mod.create_workspace(root)
    workspace_mod.add_course_to_workspace(root, course_id="p", course_name="概率论")
    question = QuizQuestion(
        question_id="Q1", topic_id="t1", topic_name="CLT", question_type="short_answer",
        level=1, question_text="Mock provider 生成的规则题", correct_answer="x",
    )
    grading = grade_answer(question, "示例：未作答")
    topic = _topic()
    diagnosis = diagnose_wrong_answer(
        question={"question_text": "x"}, user_answer="示例：未作答", grading_mistake="unknown",
        topic=topic, prerequisites=[], prerequisite_mastery={},
    )
    from exam_review_skill.state.isolation import StateContaminationError

    try:
        add_wrongbook_entry(
            workspace_root=root, course_id="p", question=question, user_answer="示例：未作答",
            grading=grading, diagnosis=diagnosis, student=StudentModel(course_id="p"),
        )
        assert False, "should have raised"
    except StateContaminationError:
        pass
    assert load_wrongbook(root, "p") == []


def test_retry_scheduling_priority():
    s = schedule_retry(topic_id="t1", diagnosis="prerequisite_gap", repeat_count=0, mastery="unknown", days_to_exam=1)
    assert s.priority == "S"
    assert s.next_review_days == 1
    s2 = schedule_retry(topic_id="t1", diagnosis="careless_error", repeat_count=0, mastery="proficient", days_to_exam=10)
    assert s2.priority == "B"
    assert s2.next_review_days >= 3
    # repeated errors -> retry sooner
    s3 = schedule_retry(topic_id="t1", diagnosis="calculation_error", repeat_count=3, mastery="developing", days_to_exam=5)
    assert s3.next_review_days == 1


def test_cram_modes_are_distinct(tmp_path: Path):
    root = tmp_path / "ws"
    workspace_mod.create_workspace(root)
    workspace_mod.add_course_to_workspace(root, course_id="p", course_name="概率论")
    student = StudentModel(course_id="p")
    plans = {}
    for mode in CRAM_MODES:
        plan = build_cram_plan(
            workspace_root=root, course_id="p",
            topics=[_topic()],
            exam_points=_exam_points(),
            student=student,
            wrongbook_entries=_wrongbook_entries(),
            mode=mode,
            locale="zh-CN",
        )
        plans[mode] = plan
    # item counts must genuinely differ across modes (not the same plan relabeled)
    counts = {mode: len(plan.items) for mode, plan in plans.items()}
    assert counts["7d"] > counts["24h"] > counts["3h"] > counts["30m"]
    assert counts["7d"] > counts["3d"]


def test_cram_30m_rescue_is_strict(tmp_path: Path):
    """30-min rescue only keeps S-level (or A), core formulas, conditions, traps."""
    root = tmp_path / "ws"
    workspace_mod.create_workspace(root)
    workspace_mod.add_course_to_workspace(root, course_id="p", course_name="概率论")
    plan = build_cram_plan(
        workspace_root=root, course_id="p",
        topics=[_topic()],
        exam_points=_exam_points(),
        student=StudentModel(course_id="p"),
        wrongbook_entries=_wrongbook_entries(),
        mode="30m",
        locale="zh-CN",
    )
    assert plan.items, "30m rescue must still have content for S-level topics"
    # only S/A focus topics
    assert all(t in ("t1",) for t in plan.focus_topics)
    # no low-priority topics in focus
    assert "t2" not in plan.focus_topics
    # kinds restricted to formula/condition/trap for 30m
    assert all(item.kind in ("formula", "condition", "trap") for item in plan.items)
    # NOT the whole book: item count small
    assert len(plan.items) <= 3


def test_cram_renders_bilingual(tmp_path: Path):
    root = tmp_path / "ws"
    workspace_mod.create_workspace(root, user_locale="zh-CN")
    workspace_mod.add_course_to_workspace(root, course_id="p", course_name="概率论")
    plan = build_cram_plan(
        workspace_root=root, course_id="p",
        topics=[_topic()], exam_points=_exam_points(),
        student=StudentModel(course_id="p"), wrongbook_entries=_wrongbook_entries(),
        mode="1h", locale="zh-CN",
    )
    text = render_cram_plan(plan, "zh-CN")
    assert "冲刺计划" in text


def test_cram_multicourse_coordination(tmp_path: Path):
    """Multi-course cram: exam-close courses get emergency cram, far courses get
    maintenance - both present, not just the last-mentioned course."""
    from planner_fixtures import build_scenario_workspace
    from exam_review_skill.planner.orchestrator import generate_daily_plan_v4

    root = build_scenario_workspace(tmp_path / "ws")
    # probability exam tomorrow, organic day after -> both near
    plan = generate_daily_plan_v4(root, "2026-06-18")
    prob_blocks = [b for b in plan.blocks if b.course_id == "probability"]
    org_blocks = [b for b in plan.blocks if b.course_id == "organic-chemistry"]
    botany_blocks = [b for b in plan.blocks if b.course_id == "botany"]
    # near-exam courses get cram blocks, far course gets maintenance/study
    assert any(b.kind == "cram" for b in prob_blocks)
    assert any(b.kind == "cram" for b in org_blocks)
    assert any(b.kind in ("maintenance", "study") for b in botany_blocks)
    assert all(course_id in {b.course_id for b in plan.blocks} for course_id in ("probability", "organic-chemistry", "botany"))
