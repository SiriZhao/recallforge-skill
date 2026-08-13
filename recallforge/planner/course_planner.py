from __future__ import annotations

from datetime import date
from pathlib import Path

from ..i18n import t
from ..models import CourseManifest, CoursePlan, ExamPointModel, KnowledgeTopic, StudentModel, StudyBlock
from ..state.course import load_course_json


def _topic_name(topic: KnowledgeTopic, locale: str) -> str:
    lang = locale.split("-")[0].upper()
    return topic.localized_names.get(f"{lang}-{locale.split('-')[-1]}") or topic.localized_names.get(
        "en-US"
    ) or topic.localized_names.get("zh-CN") or topic.canonical_name


def build_course_plan(
    *,
    workspace_root: Path,
    course_id: str,
    manifest: CourseManifest,
    topics: list[KnowledgeTopic],
    exam_points: list[ExamPointModel],
    student: StudentModel,
    wrongbook_entries: list[dict],
    days_left: int | None = None,
    hours_available: float | None = None,
    locale: str = "zh-CN",
) -> CoursePlan:
    """Single-course adaptive plan: 'what to study next in THIS course'.

    Combines exam date, target score, available time, risk radar, mastery,
    forgetting, past-exam coverage, and the wrongbook. Blocks are concrete:
    course / topic / duration / reason / task / practice / completion_criterion.
    """
    plan = CoursePlan(course_id=course_id)
    if not topics:
        plan.rationale.append(t(locale, "plan.none", course=course_id))
        return plan

    if days_left is None:
        days_left = 7
    if hours_available is None:
        hours_available = 4.0

    # rank topics by risk priority, then mastery gap, then forgetting
    exam_by_topic = {p.topic_id: p for p in exam_points}
    ranked: list[tuple[float, KnowledgeTopic]] = []
    for topic in topics:
        ep = exam_by_topic.get(topic.topic_id)
        priority_weight = {"S": 1.0, "A": 0.7, "B": 0.4, "C": 0.2}.get(ep.priority if ep else "C", 0.2)
        tm = student.topics.get(topic.topic_id)
        mastery_weight = 0.8 if tm is None or tm.mastery == "unknown" else (
            0.6 if tm.mastery == "novice" else 0.4 if tm.mastery == "developing" else 0.1
        )
        forgetting = tm.forgetting_risk if tm else 0.8
        # wrongbook boost
        wrong_count = sum(1 for w in wrongbook_entries if w.get("topic_id") == topic.topic_id)
        wrong_weight = min(0.3, 0.1 * wrong_count)
        score = priority_weight + mastery_weight + forgetting * 0.3 + wrong_weight
        ranked.append((score, topic))
    ranked.sort(key=lambda pair: -pair[0])

    # choose how many topics fit in the available hours (avg ~0.5-1h per block)
    blocks = []
    budget = hours_available
    for _, topic in ranked:
        if budget <= 0.25:
            break
        duration = min(1.5, max(0.5, budget / max(1, len(ranked[:4]))))
        duration = min(duration, budget)
        ep = exam_by_topic.get(topic.topic_id)
        tm = student.topics.get(topic.topic_id)
        kind = _kind_for(topic, tm, ep, days_left)
        reason = _reason_for(topic, tm, ep, days_left, _wrong_count(topic.topic_id, wrongbook_entries), locale)
        task = _task_for(topic, kind, locale)
        practice = _practice_for(topic, kind, locale)
        criterion = _criterion_for(kind, locale)
        blocks.append(
            StudyBlock(
                block_id=f"SB-{len(blocks) + 1:03d}",
                course_id=course_id,
                topic_id=topic.topic_id,
                topic_name=_topic_name(topic, locale),
                duration_hours=round(duration, 2),
                reason=reason,
                task=task,
                practice=practice,
                completion_criterion=criterion,
                kind=kind,
                priority=ep.priority if ep else "C",
                evidence_refs=list(topic.evidence),
            )
        )
        budget -= duration
    plan.blocks = blocks
    plan.strategy = (
        "cram" if days_left <= 2 else "focused" if days_left <= 5 else "balanced"
    )
    plan.rationale.append(
        t(locale, "plan.strategy", strategy=plan.strategy, hours=hours_available)
    )
    return plan


def _wrong_count(topic_id: str, wrongbook_entries: list[dict]) -> int:
    return sum(1 for w in wrongbook_entries if w.get("topic_id") == topic_id)


def _kind_for(topic, tm, ep, days_left: int) -> str:
    if tm is None or tm.mastery == "unknown":
        return "study" if days_left > 2 else "cram"
    if tm.mastery == "proficient":
        return "review" if tm.forgetting_risk > 0.4 else "maintenance"
    if tm.mastery in ("novice", "developing"):
        return "practice"
    return "study"


def _reason_for(topic, tm, ep, days_left: int, wrong_count: int, locale: str) -> str:
    parts = []
    if ep and ep.priority in ("S", "A"):
        parts.append(t(locale, "plan.reason.risk", risk=ep.priority))
    if tm is None or tm.mastery == "unknown":
        parts.append(t(locale, "plan.reason.mastery", mastery="unknown", forgetting="n/a"))
    else:
        parts.append(
            t(locale, "plan.reason.mastery", mastery=tm.mastery, forgetting=f"{tm.forgetting_risk:.2f}")
        )
    if wrong_count:
        parts.append(t(locale, "plan.reason.wrongbook", count=wrong_count))
    return "；".join(parts) if locale.startswith("zh") else "; ".join(parts)


def _task_for(topic, kind: str, locale: str) -> str:
    if locale.startswith("zh"):
        tasks = {
            "study": f"学习 {topic.canonical_name} 的定义、公式与方法",
            "review": f"复习 {topic.canonical_name} 并重做错题",
            "practice": f"针对 {topic.canonical_name} 做专项练习",
            "cram": f"冲刺 {topic.canonical_name}：背诵核心+刷真题",
            "maintenance": f"维护 {topic.canonical_name}：快速回顾",
            "wrongbook": f"重练 {topic.canonical_name} 的错题",
        }
    else:
        tasks = {
            "study": f"Study {topic.canonical_name}: definitions, formulas, methods",
            "review": f"Review {topic.canonical_name} and redo wrong items",
            "practice": f"Practice {topic.canonical_name} with focused exercises",
            "cram": f"Cram {topic.canonical_name}: core memorization + past exam",
            "maintenance": f"Maintain {topic.canonical_name}: quick recap",
            "wrongbook": f"Redo wrong items for {topic.canonical_name}",
        }
    return tasks.get(kind, tasks["study"])


def _practice_for(topic, kind: str, locale: str) -> str:
    qt = topic.question_types[0] if topic.question_types else "short_answer"
    if locale.startswith("zh"):
        return f"做 {qt} 类型题 3–5 道；若有往年题则优先"
    return f"Answer 3-5 {qt} questions; prefer past-exam items when available"


def _criterion_for(kind: str, locale: str) -> str:
    if locale.startswith("zh"):
        return "自测正确率 ≥ 80% 且能独立写出关键步骤/公式"
    return "self-test accuracy >= 80% and can independently write key steps/formulas"
