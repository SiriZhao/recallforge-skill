from __future__ import annotations

import re
from dataclasses import asdict

from ..i18n import TerminologyMap
from ..models import KnowledgeEdge, KnowledgeTopic, _now_iso
from .topic import _extract_text, _mention_topics


PREREQ_ZH = re.compile(r"(前置知识[:：]?|先掌握|需要先|先学|前提是|基于|以\s*[^，。]{1,12}\s*为基础)")
PREREQ_EN = re.compile(r"(prerequisite[:：]?|requires |before studying|you need|based on)", re.I)
CONFUSED_ZH = re.compile(r"(易与|容易与|常与|与[^，。]{1,12}混淆)")
CONFUSED_EN = re.compile(r"(confused with|often confused|easily confused)", re.I)


def _prereq_targets(sentence: str, term_map: TerminologyMap) -> list[str]:
    """Find known topic names in a prerequisite sentence via the terminology map."""
    return _mention_topics(sentence, term_map)


def build_knowledge_edges(
    topics: list[KnowledgeTopic],
    evidence_records: list[dict],
    term_map: TerminologyMap,
) -> list[KnowledgeEdge]:
    """Build real, evidence-backed graph edges.

    prerequisite: only from explicit textual evidence ("先掌握X", "前置知识：X",
    "prerequisite: X"). Never derived from list adjacency (the v0 fake-graph bug).
    related_to: two recognized topics mentioned in the same evidence record.
    part_of: topic -> chapter topic when the chapter label itself is a recognized topic.
    often_confused_with: explicit confusion markers.
    used_in: two topics mapped to the same past-exam question.
    """
    edges: list[KnowledgeEdge] = []
    topic_ids = {t.topic_id for t in topics}
    chapter_ids: dict[str, str] = {}
    for topic in topics:
        if topic.chapter:
            key, matched = term_map.resolve_topic(topic.chapter)
            if matched:
                chapter_ids[topic.topic_id] = key

    evidence_by_id = {r.get("evidence_id"): r for r in evidence_records if not r.get("synthetic")}

    for record in evidence_records:
        if record.get("synthetic") is True:
            continue
        evidence_id = record.get("evidence_id")
        text = _extract_text(record)
        mentioned = _mention_topics(text, term_map)
        mentioned = [t for t in mentioned if t in topic_ids]
        source = record.get("source_file", "")

        # prerequisite edges from explicit sentences
        for sentence in re.split(r"[。！？!?；;]\s*|\n+", text):
            if PREREQ_ZH.search(sentence) or PREREQ_EN.search(sentence):
                targets = _prereq_targets(sentence, term_map)
                for target in targets:
                    if target in topic_ids and target != (mentioned[0] if mentioned else None):
                        # the topic the sentence belongs to is ambiguous; link each
                        # mentioned topic as target of the prerequisite when the
                        # sentence names both a known topic and the prerequisite.
                        for owner in mentioned:
                            if owner != target:
                                edges.append(
                                    KnowledgeEdge(
                                        source=target,
                                        target=owner,
                                        relation="prerequisite",
                                        evidence_refs=[evidence_id] if evidence_id else [],
                                        confidence=0.7,
                                    )
                                )

        # related_to: co-mentioned topics in one evidence record
        for i in range(len(mentioned)):
            for j in range(i + 1, len(mentioned)):
                edges.append(
                    KnowledgeEdge(
                        source=mentioned[i],
                        target=mentioned[j],
                        relation="related_to",
                        evidence_refs=[evidence_id] if evidence_id else [],
                        confidence=0.55,
                    )
                )

        # often_confused_with from explicit markers
        for sentence in re.split(r"[。！？!?；;]\s*|\n+", text):
            if CONFUSED_ZH.search(sentence) or CONFUSED_EN.search(sentence):
                names = _mention_topics(sentence, term_map)
                for name in names:
                    if name in topic_ids and name != (mentioned[0] if mentioned else None):
                        edges.append(
                            KnowledgeEdge(
                                source=mentioned[0] if mentioned else name,
                                target=name,
                                relation="often_confused_with",
                                evidence_refs=[evidence_id] if evidence_id else [],
                                confidence=0.6,
                            )
                        )

        # used_in: topics in the same past-exam question
        exam_structure = (record.get("content") or {}).get("exam_structure") or []
        for q in exam_structure:
            q_topics = _mention_topics(q.get("body", "") or "", term_map)
            q_topics = [t for t in q_topics if t in topic_ids]
            for i in range(len(q_topics)):
                for j in range(i + 1, len(q_topics)):
                    edges.append(
                        KnowledgeEdge(
                            source=q_topics[i],
                            target=q_topics[j],
                            relation="used_in",
                            evidence_refs=[evidence_id] if evidence_id else [],
                            confidence=0.65,
                        )
                    )

    # part_of edges: topic -> chapter topic
    for topic_id, chapter_id in chapter_ids.items():
        if chapter_id in topic_ids and chapter_id != topic_id:
            edges.append(
                KnowledgeEdge(
                    source=topic_id,
                    target=chapter_id,
                    relation="part_of",
                    evidence_refs=[],
                    confidence=0.6,
                )
            )

    return _dedupe_edges(edges)


def _dedupe_edges(edges: list[KnowledgeEdge]) -> list[KnowledgeEdge]:
    seen: dict[tuple[str, str, str], KnowledgeEdge] = {}
    for edge in edges:
        key = (edge.source, edge.target, edge.relation)
        if key not in seen:
            seen[key] = edge
        else:
            existing = seen[key]
            for ref in edge.evidence_refs:
                if ref and ref not in existing.evidence_refs:
                    existing.evidence_refs.append(ref)
            existing.confidence = max(existing.confidence, edge.confidence)
    return list(seen.values())


def edges_to_state(course_id: str, edges: list[KnowledgeEdge]) -> dict:
    return {
        "course_id": course_id,
        "edges": [asdict(e) for e in edges],
        "updated_at": _now_iso(),
    }
