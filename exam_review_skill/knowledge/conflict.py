from __future__ import annotations

import re
from dataclasses import asdict

from ..i18n import TerminologyMap
from ..models import ExamConflict, KnowledgeTopic, _now_iso
from .topic import _extract_text, _sentences


SOURCE_AUTHORITY = {
    "teacher_hint": 5,
    "answer_key": 5,
    "past_exam": 4,
    "lecture_slide": 3,
    "class_notes": 3,
    "textbook": 2,
    "exercise": 2,
    "lab_manual": 1,
    "unknown": 0,
}


def _source_type(source_file: str) -> str:
    name = source_file.lower()
    if "answer" in name:
        return "answer_key"
    if any(m in name for m in ("exam", "past", "试卷", "真题", "期末", "考题")):
        return "past_exam"
    if "teacher" in name or "老师" in name or "hint" in name:
        return "teacher_hint"
    if "lecture" in name or "slide" in name or "ppt" in name or "课件" in name:
        return "lecture_slide"
    if "note" in name or "笔记" in name or "讲义" in name:
        return "class_notes"
    if "book" in name or "textbook" in name or "教材" in name:
        return "textbook"
    if "exercise" in name or "练习" in name or "作业" in name:
        return "exercise"
    return "unknown"


def _definition_key(sentence: str) -> str:
    return re.sub(r"\s+", " ", sentence)[:120].strip()


def detect_conflicts(
    topics: list[KnowledgeTopic],
    evidence_records: list[dict],
    term_map: TerminologyMap,
) -> list[ExamConflict]:
    """Detect differing definitions for the same topic from different sources.
    Never silently overwrites: records the conflict, ranks alternatives by
    (authority, exam relevance, recency, teacher material) and marks resolution
    for the user to confirm. Different-language pairs (likely translations) are
    reported with a distinct rationale, not silently merged."""
    conflicts: list[ExamConflict] = []
    for topic in topics:
        alternatives: list[dict] = []
        for record in evidence_records:
            if record.get("synthetic") is True:
                continue
            evidence_id = record.get("evidence_id")
            if evidence_id not in topic.evidence:
                continue
            text = _extract_text(record)
            source_file = record.get("source_file", "")
            for sentence in _sentences(text):
                if "是指" in sentence or "定义为" in sentence or "is defined as" in sentence.lower():
                    alternatives.append(
                        {
                            "text": sentence,
                            "source_file": source_file,
                            "source_type": _source_type(source_file),
                            "authority": SOURCE_AUTHORITY.get(_source_type(source_file), 0),
                            "created_at": record.get("created_at", ""),
                            "source_language": record.get("source_language"),
                            "evidence_ref": evidence_id,
                        }
                    )
        alternatives = _dedupe_alternatives(alternatives)
        if len(alternatives) < 2:
            continue
        distinct = {_definition_key(a["text"]) for a in alternatives}
        if len(distinct) < 2:
            continue
        chosen, reason = _rank_alternatives(alternatives)
        conflicts.append(
            ExamConflict(
                conflict_id=f"CF-{topic.topic_id}-{len(conflicts) + 1}",
                topic_id=topic.topic_id,
                field="definition",
                alternatives=alternatives,
                resolved=False,
                chosen=chosen,
                resolution_reason=reason,
            )
        )
    return conflicts


def _dedupe_alternatives(alternatives: list[dict]) -> list[dict]:
    seen: dict[str, dict] = {}
    for alt in alternatives:
        key = _definition_key(alt["text"])
        if key not in seen:
            seen[key] = alt
    return list(seen.values())


def _rank_alternatives(alternatives: list[dict]) -> tuple[dict, str]:
    """Transparent priority: exam relevance & source authority > recency > teacher
    material. Different-language pairs are flagged as likely translations needing
    user confirmation rather than silently picked. Returns (chosen, reason)."""
    languages = {a.get("source_language") for a in alternatives if a.get("source_language")}
    spans_multiple_languages = len(languages) > 1
    best = max(alternatives, key=lambda a: (a["authority"], a["created_at"] or ""))
    if spans_multiple_languages:
        reason = (
            f"definitions differ across languages (likely translation pair, not a real "
            f"contradiction); proposed '{best['source_file']}' (authority={best['authority']}); "
            f"user confirmation required before merging"
        )
    else:
        reason = (
            f"chosen '{best['source_file']}' (source_type={best['source_type']}, "
            f"authority={best['authority']}) by exam-relevance/authority; user confirmation required"
        )
    return best, reason
