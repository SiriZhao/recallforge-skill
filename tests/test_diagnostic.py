from __future__ import annotations

from pathlib import Path

from recallforge.models import StudentModel
from recallforge.student.diagnostic import build_diagnostic_plan
from recallforge.student.sessions import AnswerResult, record_answer


def _topics():
    from recallforge.models import KnowledgeTopic, TopicField

    return [
        KnowledgeTopic(topic_id="t1", canonical_name="CLT", question_types=["calculation"], evidence=["e1"]),
        KnowledgeTopic(topic_id="t2", canonical_name="条件概率", question_types=["short_answer"], evidence=["e2"]),
        KnowledgeTopic(topic_id="t3", canonical_name="正态分布", question_types=["multiple choice"], evidence=["e3"]),
    ]


def test_diagnostic_plan_covers_topics(tmp_path):
    model = StudentModel(course_id="p")
    plan = build_diagnostic_plan("p", _topics(), model, minutes=15, locale="zh-CN")
    assert plan.items, "diagnostic must select topics"
    assert plan.estimated_minutes <= 20
    # no data -> all topics are 'unknown' reasons
    assert all(item.reason for item in plan.items)
    assert plan.rationale


def test_diagnostic_prioritizes_unknown_and_weak(tmp_path):
    model = StudentModel(course_id="p")
    # t1 already mastered
    record_answer(model, AnswerResult(topic_id="t1", correct=True, difficulty=2), today="2026-06-18")
    record_answer(model, AnswerResult(topic_id="t1", correct=True, difficulty=3), today="2026-06-18")
    record_answer(model, AnswerResult(topic_id="t1", correct=True, difficulty=3, is_new_form=True), today="2026-06-18")
    plan = build_diagnostic_plan("p", _topics(), model, minutes=15, locale="zh-CN")
    # unknown topics (t2, t3) come before the mastered t1
    ids = [item.topic_id for item in plan.items]
    assert ids.index("t2") < ids.index("t1")
    assert ids.index("t3") < ids.index("t1")


def test_diagnostic_empty_no_topics(tmp_path):
    plan = build_diagnostic_plan("p", [], StudentModel(course_id="p"), locale="zh-CN")
    assert plan.items == []
    assert plan.rationale
