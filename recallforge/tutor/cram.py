from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from ..i18n import t
from ..models import (
    CramItem,
    CramPlan,
    ExamPointModel,
    KnowledgeTopic,
    StudentModel,
)
from ..state import course as course_mod


CRAM_MODES = ("7d", "3d", "24h", "3h", "1h", "30m")

# Each mode is genuinely different: different scope, different item kinds.
MODE_SCOPE = {
    # Each mode is a strict subset of the previous one: genuinely different scope.
    "7d": {"hours": 14.0, "max_items": 30, "kinds": ["formula", "condition", "definition", "answer_template", "mistake", "trap", "s_risk"], "detail": "full"},
    "3d": {"hours": 6.0, "max_items": 20, "kinds": ["formula", "condition", "definition", "answer_template", "mistake", "trap"], "detail": "full"},
    "24h": {"hours": 2.0, "max_items": 12, "kinds": ["formula", "condition", "definition", "mistake", "trap"], "detail": "medium"},
    "3h": {"hours": 3.0, "max_items": 8, "kinds": ["formula", "condition", "definition", "trap"], "detail": "condensed"},
    "1h": {"hours": 1.0, "max_items": 5, "kinds": ["formula", "condition", "trap"], "detail": "condensed"},
    "30m": {"hours": 0.5, "max_items": 3, "kinds": ["formula", "condition", "trap"], "detail": "rescue", "s_only": True},
}


def build_cram_plan(
    *,
    workspace_root: Path,
    course_id: str,
    topics: list[KnowledgeTopic],
    exam_points: list[ExamPointModel],
    student: StudentModel,
    wrongbook_entries: list[dict],
    mode: str,
    locale: str = "zh-CN",
) -> CramPlan:
    """Build a genuinely distinct cram plan per mode. The 30-minute rescue keeps
    ONLY S-level risks, core formulas, conditions, definitions, answer templates,
    recent unresolved mistakes, and high-frequency traps - never the whole book."""
    if mode not in CRAM_MODES:
        raise ValueError(f"unknown cram mode {mode!r}; expected {CRAM_MODES}")
    scope = MODE_SCOPE[mode]
    zh = locale.startswith("zh")
    exam_by_topic = {p.topic_id: p for p in exam_points}

    # rank topics by exam priority then mastery gap
    def rank(topic: KnowledgeTopic):
        ep = exam_by_topic.get(topic.topic_id)
        priority = {"S": 5, "A": 4, "B": 2, "C": 1}.get(ep.priority if ep else "C", 1)
        tm = student.topics.get(topic.topic_id)
        mastery_gap = 0.8 if tm is None or tm.mastery == "unknown" else (
            0.6 if tm.mastery in ("novice", "developing") else 0.1
        )
        return priority + mastery_gap

    ordered = sorted(topics, key=lambda x: -rank(x))
    # 30m rescue: strictly S/A-first; if none exist, fall back to the highest-priority
    # topics so the rescue is never empty (but still capped and condensed).
    if scope.get("s_only"):
        sa_ordered = [t for t in ordered if _priority_of(t, exam_by_topic) in ("S", "A")]
        if sa_ordered:
            ordered = sa_ordered
    items: list[CramItem] = []
    focused: list[str] = []
    for topic in ordered[:scope["max_items"]]:
        ep = exam_by_topic.get(topic.topic_id)
        focused.append(topic.topic_id)
        if "definition" in scope["kinds"] and topic.definitions:
            items.append(
                CramItem(
                    course_id=course_id,
                    topic_id=topic.topic_id,
                    topic_name=topic.canonical_name,
                    kind="definition",
                    content=topic.definitions[0].text,
                    evidence_refs=list(topic.evidence),
                )
            )
        if "formula" in scope["kinds"] and topic.formulas:
            items.append(
                CramItem(
                    course_id=course_id,
                    topic_id=topic.topic_id,
                    topic_name=topic.canonical_name,
                    kind="formula",
                    content=topic.formulas[0].text,
                    evidence_refs=list(topic.evidence),
                )
            )
        if "condition" in scope["kinds"] and topic.common_mistakes:
            items.append(
                CramItem(
                    course_id=course_id,
                    topic_id=topic.topic_id,
                    topic_name=topic.canonical_name,
                    kind="condition",
                    content=topic.common_mistakes[0].text,
                    evidence_refs=list(topic.evidence),
                )
            )
        if "trap" in scope["kinds"] and topic.common_mistakes:
            items.append(
                CramItem(
                    course_id=course_id,
                    topic_id=topic.topic_id,
                    topic_name=topic.canonical_name,
                    kind="trap",
                    content=topic.common_mistakes[0].text,
                    evidence_refs=list(topic.evidence),
                )
            )
        if "answer_template" in scope["kinds"]:
            items.append(
                CramItem(
                    course_id=course_id,
                    topic_id=topic.topic_id,
                    topic_name=topic.canonical_name,
                    kind="answer_template",
                    content=(
                        "答案模板：定义一句话 + 条件/步骤 + 公式 + 结果与单位"
                        if zh
                        else "Answer template: definition + conditions/steps + formula + result/unit"
                    ),
                    evidence_refs=list(topic.evidence),
                )
            )
        if "mistake" in scope["kinds"]:
            for entry in wrongbook_entries:
                if entry.get("topic_id") == topic.topic_id and not entry.get("resolved"):
                    items.append(
                        CramItem(
                            course_id=course_id,
                            topic_id=topic.topic_id,
                            topic_name=topic.canonical_name,
                            kind="mistake",
                            content=entry.get("question_text", ""),
                            evidence_refs=entry.get("evidence_refs", []),
                        )
                    )
        if "s_risk" in scope["kinds"] and ep and ep.priority == "S":
            items.append(
                CramItem(
                    course_id=course_id,
                    topic_id=topic.topic_id,
                    topic_name=topic.canonical_name,
                    kind="s_risk",
                    content=(
                        f"S 级风险：{ep.priority_rationale[0] if ep.priority_rationale else ''}"
                        if zh
                        else f"S-level risk: {ep.priority_rationale[0] if ep.priority_rationale else ''}"
                    ),
                    evidence_refs=list(topic.evidence),
                )
            )

    return CramPlan(
        course_id=course_id,
        mode=mode,
        hours_left=scope["hours"],
        items=items,
        focus_topics=focused,
        priority="S" if mode in ("30m", "1h", "3h") else "A",
        rationale=[t(locale, "cram.scope", mode=mode, items=len(items), hours=scope["hours"])],
    )


def _priority_of(topic: KnowledgeTopic, exam_by_topic: dict) -> str:
    ep = exam_by_topic.get(topic.topic_id)
    return ep.priority if ep else "C"


def render_cram_plan(plan: CramPlan, locale: str) -> str:
    zh = locale.startswith("zh")
    lines = [
        f"{t(locale, 'cram.title', mode=plan.mode, hours=plan.hours_left)}",
        "",
    ]
    for item in plan.items:
        kind_label = {
            "formula": "公式" if zh else "Formula",
            "condition": "条件" if zh else "Condition",
            "definition": "定义" if zh else "Definition",
            "answer_template": "答案模板" if zh else "Answer template",
            "mistake": "未解决错题" if zh else "Unresolved mistake",
            "trap": "高频陷阱" if zh else "High-frequency trap",
            "s_risk": "S级风险" if zh else "S-level risk",
        }.get(item.kind, item.kind)
        lines.append(f"- [{kind_label}] {item.topic_name}: {item.content}")
    lines.append("")
    lines.extend(f"- {r}" for r in plan.rationale)
    return "\n".join(lines)
