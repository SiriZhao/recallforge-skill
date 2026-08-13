from __future__ import annotations

import re

from ..i18n import TerminologyMap
from ..models import TeacherStyle, KnowledgeTopic, _now_iso
from .topic import _extract_text


def build_teacher_style(
    course_id: str,
    topics: list[KnowledgeTopic],
    evidence_records: list[dict],
    term_map: TerminologyMap,
) -> TeacherStyle:
    """Teacher style analysis with explicit evidence tiers.

    Tier rules:
      observed          - claims backed by counted evidence (question types,
                          chapter frequency, homework reuse).
      strongly_inferred - multiple consistent signals (e.g. >=3 calculation
                          questions AND a formula-heavy topic).
      inferred          - a single indirect signal.
      unknown           - no evidence; never asserted.
    """
    style = TeacherStyle(course_id=course_id)
    refs: list[str] = []

    # chapter frequency: count evidence per chapter via topics
    for topic in topics:
        if topic.chapter:
            style.chapter_frequency[topic.chapter] = style.chapter_frequency.get(topic.chapter, 0) + len(topic.evidence)
            for ref in topic.evidence:
                if ref not in refs:
                    refs.append(ref)

    # question-type frequency + calc-vs-proof + trap style from exam structure
    calc = 0
    proof = 0
    conceptual = 0
    procedural = 0
    homework_reuse_hits = 0
    parameter_variation_hits = 0
    integrated = 0
    trap_hits: dict[str, int] = {}

    for record in evidence_records:
        if record.get("synthetic") is True:
            continue
        content = record.get("content", {}) or {}
        exam_structure = content.get("exam_structure") or []
        source = record.get("source_file", "")
        for q in exam_structure:
            qtype = (q.get("question_type") or "").lower()
            body = q.get("body", "") or ""
            style.question_type_frequency[qtype or "unknown"] = style.question_type_frequency.get(qtype or "unknown", 0) + 1
            if "计算" in body or "calculation" in body.lower() or qtype in ("calculation",):
                calc += 1
            if "证明" in body or "proof" in body.lower():
                proof += 1
            if "综合" in body or "integrated" in body.lower():
                integrated += 1
            if "概念" in body or "concept" in body.lower() or "定义" in body:
                conceptual += 1
            if "步骤" in body or "procedure" in body.lower() or "方法" in body:
                procedural += 1
            if "变形" in body or "变式" in body or "variation" in body.lower() or "参数" in body:
                parameter_variation_hits += 1
            for trap_key in ("有效数字", "单位", "条件", "陷阱", "signific", "unit", "condition", "trap"):
                if trap_key in body.lower():
                    trap_hits[trap_key] = trap_hits.get(trap_key, 0) + 1
        if "homework" in source.lower() or "作业" in source:
            homework_reuse_hits += 1

    if calc or proof:
        style.calc_vs_proof = {"calc": calc, "proof": proof}
    if conceptual or procedural:
        style.conceptual_vs_procedural = {"conceptual": conceptual, "procedural": procedural}
    style.integrated_questions = integrated
    if trap_hits:
        style.trap_style = sorted(trap_hits, key=trap_hits.get, reverse=True)

    # homework reuse: only asserted when a homework file actually appears
    if homework_reuse_hits > 0:
        style.homework_reuse = True
    if parameter_variation_hits >= 2:
        style.parameter_variation = True

    # tier + claims
    style.evidence_refs = refs
    _record_claim(style, "question type distribution", "observed" if style.question_type_frequency else "unknown", refs)
    _record_claim(style, "chapter distribution", "observed" if style.chapter_frequency else "unknown", refs)
    if calc >= 3:
        _record_claim(style, "calculation-heavy exam style", "strongly_inferred", refs)
    elif calc >= 1:
        _record_claim(style, "calculation appears in exam", "inferred", refs)
    if proof >= 1:
        _record_claim(style, "proof questions appear", "observed", refs)
    if style.homework_reuse:
        _record_claim(style, "homework material reused", "observed", refs)
    if style.parameter_variation:
        _record_claim(style, "parameter variation used", "inferred", refs)
    if integrated >= 2:
        _record_claim(style, "integrated questions used", "strongly_inferred", refs)

    style.tier = _overall_tier(style)
    style.updated_at = _now_iso()
    return style


def _record_claim(style: TeacherStyle, claim: str, tier: str, refs: list[str]) -> None:
    if tier == "unknown":
        return
    style.claims.append({"claim": claim, "tier": tier, "evidence_refs": refs})


def _overall_tier(style: TeacherStyle) -> str:
    tiers = [c["tier"] for c in style.claims]
    if "observed" in tiers:
        return "observed"
    if "strongly_inferred" in tiers:
        return "strongly_inferred"
    if "inferred" in tiers:
        return "inferred"
    return "unknown"
