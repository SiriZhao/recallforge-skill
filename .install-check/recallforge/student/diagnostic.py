from __future__ import annotations

from datetime import date

from ..i18n import t
from ..models import DiagnosticItem, DiagnosticPlan, StudentModel, _now_iso
from ..models import KnowledgeTopic
from .mastery import compute_forgetting_risk


def build_diagnostic_plan(
    course_id: str,
    topics: list[KnowledgeTopic],
    model: StudentModel,
    *,
    minutes: int = 15,
    locale: str = "zh-CN",
) -> DiagnosticPlan:
    """Suggest a 10-20 minute diagnostic test that estimates the student's level.

    Topic selection covers the knowledge graph breadth first (topic coverage), then
    adds high-risk / high-likelihood topics. Never invents mastery - the diagnostic
    itself is what produces real mastery data afterwards.
    """
    if not topics:
        return DiagnosticPlan(course_id=course_id, items=[], rationale=[t(locale, "diag.none")])

    # unknown topics first (no data), then high-risk, then breadth
    def sort_key(topic: KnowledgeTopic):
        tm = model.topics.get(topic.topic_id)
        if tm is None or tm.questions_attempted == 0:
            return (0, 0.0)  # unknown topics first
        risk = compute_forgetting_risk(tm)
        return (1, -risk)

    selected: list[DiagnosticItem] = []
    seen: set[str] = set()
    for topic in sorted(topics, key=sort_key):
        if len(selected) >= 8:
            break
        if topic.topic_id in seen:
            continue
        seen.add(topic.topic_id)
        tm = model.topics.get(topic.topic_id)
        if tm is None or tm.questions_attempted == 0:
            reason = t(locale, "diag.reason.unknown")
        elif tm.mastery in ("novice", "developing"):
            reason = t(locale, "diag.reason.weak")
        else:
            reason = t(locale, "diag.reason.verify")
        selected.append(
            DiagnosticItem(
                topic_id=topic.topic_id,
                topic_name=topic.localized_names.get(locale.split("-")[0].upper().replace("EN", "en-US")) or topic.canonical_name,
                reason=reason,
                question_type=topic.question_types[0] if topic.question_types else "short_answer",
                difficulty=2,
            )
        )

    per_item = max(1, round(minutes / max(1, len(selected))))
    plan = DiagnosticPlan(
        course_id=course_id,
        items=selected,
        estimated_minutes=per_item * len(selected),
        rationale=[
            t(locale, "diag.coverage", topics=len(topics), selected=len(selected)),
            t(locale, "diag.rule", minutes=per_item),
        ],
    )
    return plan
