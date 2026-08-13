from __future__ import annotations

from pathlib import Path

from ..i18n import t
from ..models import KnowledgeTopic, StudentModel, TutorResponse, TutorSection, _now_iso


def _topic_name(topic: KnowledgeTopic, locale: str) -> str:
    lang = locale.split("-")[0].upper()
    return (
        topic.localized_names.get(f"{lang}-{locale.split('-')[-1]}")
        or topic.localized_names.get("en-US")
        or topic.localized_names.get("zh-CN")
        or topic.canonical_name
    )


def _first(topic: KnowledgeTopic, attr: str) -> str | None:
    values = getattr(topic, attr, [])
    if values:
        return values[0].text
    return None


def build_tutor_response(
    topic: KnowledgeTopic,
    student: StudentModel | None = None,
    *,
    locale: str = "zh-CN",
    course_name: str | None = None,
) -> TutorResponse:
    """Course-materials-first tutor explanation.

    Structure: Intuition -> Definition -> Core Formula/Principle -> Conditions ->
    Method -> Example -> Common Mistake -> Check Question. Subject-adaptive: only
    include a Formula section when the topic actually has formulas in its evidence.
    Any content not present in the materials is clearly marked Supplementary
    explanation, never silently presented as teacher material.
    """
    zh = locale.startswith("zh")
    sections: list[TutorSection] = []
    evidence_refs = list(topic.evidence)

    # 1. Intuition (from definitions if available, else clearly marked supplementary)
    definition = _first(topic, "definitions")
    if definition:
        sections.append(
            TutorSection(
                title=t(locale, "tutor.intuition"),
                content=definition,
                kind="text",
                evidence_refs=evidence_refs,
            )
        )
    else:
        sections.append(
            TutorSection(
                title=t(locale, "tutor.intuition"),
                content=(
                    "直觉：先理解这个概念在解决什么问题。"
                    if zh
                    else "Intuition: understand what problem this concept solves."
                ),
                kind="text",
                supplementary=True,
            )
        )

    # 2. Definition
    if definition:
        sections.append(
            TutorSection(
                title=t(locale, "tutor.definition"),
                content=definition,
                kind="text",
                evidence_refs=evidence_refs,
            )
        )
    else:
        sections.append(
            TutorSection(
                title=t(locale, "tutor.definition"),
                content=t(locale, "tutor.no_definition"),
                kind="text",
                evidence_refs=evidence_refs,
            )
        )

    # 3. Core Formula / Principle (subject-adaptive: only if the topic has formulas)
    formula = _first(topic, "formulas")
    if formula:
        sections.append(
            TutorSection(
                title=t(locale, "tutor.formula"),
                content=formula,
                kind="formula",
                evidence_refs=evidence_refs,
            )
        )

    # 4. Conditions (from common mistakes / method hints)
    conditions = _first(topic, "common_mistakes")
    if conditions:
        sections.append(
            TutorSection(
                title=t(locale, "tutor.conditions"),
                content=conditions,
                kind="text",
                evidence_refs=evidence_refs,
            )
        )

    # 5. Method
    method = _first(topic, "methods")
    if method:
        sections.append(
            TutorSection(
                title=t(locale, "tutor.method"),
                content=method,
                kind="list",
                evidence_refs=evidence_refs,
            )
        )

    # 6. Example (from evidence; if absent, mark as needing materials)
    example = _first(topic, "methods")
    if example and len(topic.methods) > 1:
        sections.append(
            TutorSection(
                title=t(locale, "tutor.example"),
                content=topic.methods[1].text,
                kind="text",
                evidence_refs=evidence_refs,
            )
        )
    else:
        sections.append(
            TutorSection(
                title=t(locale, "tutor.example"),
                content=t(locale, "tutor.no_example"),
                kind="text",
                evidence_refs=evidence_refs,
            )
        )

    # 7. Common Mistake
    mistake = _first(topic, "common_mistakes")
    if mistake:
        sections.append(
            TutorSection(
                title=t(locale, "tutor.mistake"),
                content=mistake,
                kind="text",
                evidence_refs=evidence_refs,
            )
        )

    # Check question: self-test to verify understanding
    check_question = (
        f"{t(locale, 'tutor.check_question')} {_topic_name(topic, locale)}"
        if zh
        else f"{t(locale, 'tutor.check_question')} {_topic_name(topic, locale)}"
    )
    return TutorResponse(
        topic_id=topic.topic_id,
        topic_name=_topic_name(topic, locale),
        sections=sections,
        check_question=check_question,
        check_question_topic_id=topic.topic_id,
        language=locale,
        evidence_refs=evidence_refs,
    )
