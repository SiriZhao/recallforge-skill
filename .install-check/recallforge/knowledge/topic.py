from __future__ import annotations

import re
from dataclasses import asdict
from pathlib import Path

from ..i18n import TerminologyMap
from ..models import KnowledgeTopic, TopicField, _now_iso


# Markers (deterministic; every extracted field is a verbatim evidence substring).
DEFINITION_ZH = re.compile(r"(是指|定义为|指的是|定义是|即[:：]?)")
DEFINITION_EN = re.compile(r"(is defined as|definition[:：]|refers to|means)")
METHOD_ZH = re.compile(r"(方法[:：]|步骤如下|解题思路|做法[:：])")
METHOD_EN = re.compile(r"(procedure[:：]|method[:：]|steps are|approach[:：])")
MISTAKE_ZH = re.compile(r"(易错|常见错误|常见陷阱|陷阱|注意不要|错误[:：]|容易错)")
MISTAKE_EN = re.compile(r"(common mistake|common trap|pitfall|be careful not to|wrong[:：])")
TEACHER_ZH = re.compile(r"(重点|必考|常考|容易考|老师强调|老师[说讲]|画重点)")
TEACHER_EN = re.compile(r"(key point|must know|frequently tested|teacher emphasized|exam focus)")

QUESTION_TYPES_ZH = ["选择题", "简答题", "计算题", "实验题", "判断题", "填空题", "名词解释", "综合题", "论述题"]
QUESTION_TYPES_EN = ["multiple choice", "short answer", "calculation", "true/false", "fill in the blank", "essay"]

CHAPTER_ZH = re.compile(r"(第\s*[一二三四五六七八九十百0-9]+\s*章)")
CHAPTER_EN = re.compile(r"(chapter\s+[0-9ivx]+)", re.I)

SENTENCE_SPLIT = re.compile(r"(?<=[。！？!?；;])\s*|\n+")

EXAM_FILE_MARKERS = ("exam", "test", "past", "试卷", "真题", "期末", "考题")
GENERIC_HEADING_MARKERS = (
    "chapter", "page", "slide", "file", "document", "试卷", "期末", "笔记",
    "notes", "目录", "contents", "introduction", "引言", "总结", "summary",
    "作业", "教材", "课件", "真题", "讲义", "习题", "考卷",
)


def _sentences(text: str) -> list[str]:
    out = []
    for part in SENTENCE_SPLIT.split(text or ""):
        part = part.strip()
        if part:
            out.append(part)
    return out


def _extract_text(record: dict) -> str:
    """Get the readable text surface of an evidence record across shapes."""
    content = record.get("content", {}) or {}
    if isinstance(content, dict):
        if content.get("text"):
            return str(content["text"])
        blocks = content.get("text_blocks") or []
        return "\n".join(b.get("text", "") for b in blocks if isinstance(b, dict))
    if isinstance(content, str):
        return content
    return ""


def _chapter_from(heading: str | None, text: str) -> str | None:
    sample = (heading or "") + "\n" + text[:300]
    m = CHAPTER_ZH.search(sample) or CHAPTER_EN.search(sample)
    return m.group(0).strip() if m else None


def _mention_topics(text: str, term_map: TerminologyMap) -> list[str]:
    """Recognize known topic names (any language/alias) appearing in text via the
    terminology map. Only explicit map entries fuse across languages - no guessing."""
    found: list[str] = []
    for alias in term_map.terms:
        entry = term_map.terms[alias]
        names = list(entry.get("names", {}).values()) + list(entry.get("aliases", []))
        for name in names:
            if name and name in text:
                key = term_map.canonical_key(name) or alias
                if key not in found:
                    found.append(key)
    return found


def _heading_is_topic_candidate(heading: str) -> bool:
    """A heading only names a topic when it is short and not a generic document
    label. Prevents 'chapter 12' / '期末试卷' from becoming fake topics."""
    text = heading.strip()
    if not text or len(text) > 60:
        return False
    lower = text.lower()
    if any(marker in lower for marker in GENERIC_HEADING_MARKERS):
        return False
    # file-name-like headings (e.g. "课件_第五章", "past_exam_2024") are never topics
    if "_" in text or "." in text or "(" in text or "（" in text:
        return False
    if re.match(r"^(第\s*[一二三四五六七八九十百0-9]+\s*[章节讲]|chapter\s+[0-9ivx]+|page\s+\d+)", lower):
        return False
    return True


class TopicBuilder:
    """Builds evidence-grounded Topics from evidence records + a terminology map.

    Chunks/pages are only proof: every KnowledgeTopic field is a verbatim evidence substring
    carrying evidence_refs. A topic without any evidence is never created.
    """

    def __init__(self, course_id: str, term_map: TerminologyMap):
        self.course_id = course_id
        self.term_map = term_map
        self.topics: dict[str, KnowledgeTopic] = {}

    def _get_or_create(self, topic_id: str, canonical_name: str, evidence_id: str) -> KnowledgeTopic:
        topic = self.topics.get(topic_id)
        if topic is None:
            topic = KnowledgeTopic(
                topic_id=topic_id,
                canonical_name=canonical_name,
                localized_names=dict(self.term_map.terms.get(topic_id, {}).get("names", {})),
                aliases=list(self.term_map.terms.get(topic_id, {}).get("aliases", [])),
                inferred=False,
                fusion_confidence=0.5,
                source_confidence=0.4,
            )
            self.topics[topic_id] = topic
        if evidence_id not in topic.evidence:
            topic.evidence.append(evidence_id)
        return topic

    def _add_field(self, topic: KnowledgeTopic, attr: str, text: str, evidence_id: str, *, signals=None, source_language=None) -> None:
        values = getattr(topic, attr)
        existing = {f.text for f in values}
        if text in existing:
            return
        values.append(
            TopicField(
                text=text,
                evidence_refs=[evidence_id],
                confidence=0.6,
                signals=signals or [],
                source_language=source_language,
            )
        )

    def add_evidence(self, record: dict) -> None:
        evidence_id = record.get("evidence_id") or record.get("content_hash", "")[:8]
        text = _extract_text(record)
        heading = record.get("heading")
        source_language = record.get("source_language")
        source_file = record.get("source_file", "")
        chapter = _chapter_from(heading, text)

        # 1) topics from the terminology map mentioned in this evidence
        mentioned = _mention_topics(text, self.term_map)
        # 2) heading as a candidate topic name (only when not a bare file/page label)
        if heading and not re.match(r"^(page|slide|第\d+页|第\d+张|file)\b", heading, re.I):
            if _heading_is_topic_candidate(heading):
                key, matched = self.term_map.resolve_topic(heading)
                if key and key not in mentioned:
                    mentioned.append(key)

        # exam-structure content can also name topics
        exam_structure = (record.get("content") or {}).get("exam_structure") or []
        for q in exam_structure:
            body = q.get("body", "") or ""
            for topic_id in _mention_topics(body, self.term_map):
                if topic_id not in mentioned:
                    mentioned.append(topic_id)

        for topic_id in mentioned:
            entry = self.term_map.terms.get(topic_id, {})
            canonical = entry.get("names", {}).get("en-US") or entry.get("names", {}).get("zh-CN") or topic_id
            topic = self._get_or_create(topic_id, canonical, evidence_id)
            if chapter and not topic.chapter:
                topic.chapter = chapter
            if not topic.inferred:
                topic.inferred = False

            # definitions / methods / mistakes from sentence markers
            for sentence in _sentences(text):
                if DEFINITION_ZH.search(sentence) or DEFINITION_EN.search(sentence):
                    self._add_field(topic, "definitions", sentence, evidence_id, source_language=source_language)
                if METHOD_ZH.search(sentence) or METHOD_EN.search(sentence):
                    self._add_field(topic, "methods", sentence, evidence_id, source_language=source_language)
                if MISTAKE_ZH.search(sentence) or MISTAKE_EN.search(sentence):
                    self._add_field(topic, "common_mistakes", sentence, evidence_id, source_language=source_language)
                if TEACHER_ZH.search(sentence) or TEACHER_EN.search(sentence):
                    topic.teacher_emphasis = "observed"
                    if evidence_id not in topic.teacher_emphasis_refs:
                        topic.teacher_emphasis_refs.append(evidence_id)

            # formulas (from native text lines or multimodal formulas field)
            formula_lines = self._formula_lines(record)
            for line in formula_lines:
                self._add_field(topic, "formulas", line, evidence_id, source_language=source_language)

            # question types
            combined = text + " " + " ".join(q.get("question_type", "") for q in exam_structure)
            for qt in QUESTION_TYPES_ZH + QUESTION_TYPES_EN:
                if qt in combined and qt not in topic.question_types:
                    topic.question_types.append(qt)

            # past-exam links: only questions that actually mention THIS topic
            if self._is_exam_source(source_file) or exam_structure:
                year_match = re.search(r"(19|20)\d{2}", source_file)
                year = year_match.group(0) if year_match else None
                for q in exam_structure:
                    q_body = q.get("body", "") or ""
                    if topic_id not in _mention_topics(q_body, self.term_map):
                        continue
                    link = {
                        "exam_set_id": source_file,
                        "question_number": q.get("question_number", ""),
                        "year": year,
                    }
                    if link not in topic.past_exam_links:
                        topic.past_exam_links.append(link)

    @staticmethod
    def _formula_lines(record: dict) -> list[str]:
        content = record.get("content", {}) or {}
        lines: list[str] = []
        if isinstance(content, dict):
            for formula in content.get("formulas", []) or []:
                if isinstance(formula, dict) and formula.get("text"):
                    lines.append(str(formula["text"]))
            if content.get("formula_signals") and content.get("text"):
                for line in str(content["text"]).splitlines():
                    if re.search(r"[=≠≤≥]|[∑∫√Δπ]|\\frac|_[a-zA-Z0-9]|\^", line):
                        lines.append(line.strip())
        return list(dict.fromkeys(lines))

    @staticmethod
    def _is_exam_source(source_file: str) -> bool:
        name = source_file.lower()
        return any(marker in name for marker in EXAM_FILE_MARKERS)

    def finalize(self) -> list[KnowledgeTopic]:
        """Compute fusion confidence from cross-file/cross-language evidence and
        set the hallucination guard: any topic with zero evidence is dropped."""
        result = []
        for topic in self.topics.values():
            if not topic.evidence:
                continue  # hallucination guard: no evidence, no topic
            sources = {e.split(":", 1)[0] for e in topic.evidence}
            languages = {
                f.source_language
                for f in (topic.definitions + topic.formulas + topic.methods + topic.common_mistakes)
                if f.source_language
            }
            n_sources = len(sources)
            n_langs = len(languages)
            topic.fusion_confidence = min(0.95, 0.5 + 0.15 * (n_sources - 1) + 0.1 * (n_langs > 1))
            topic.source_confidence = min(0.95, max(topic.source_confidence, 0.4 + 0.1 * n_sources))
            topic.inferred = False
            result.append(topic)
        return result


def build_topics(evidence_records: list[dict], term_map: TerminologyMap, course_id: str) -> list[KnowledgeTopic]:
    builder = TopicBuilder(course_id=course_id, term_map=term_map)
    for record in evidence_records:
        if record.get("synthetic") is True:
            continue  # synthetic evidence never builds real topics
        builder.add_evidence(record)
    return builder.finalize()


def topics_to_state(topics: list[KnowledgeTopic]) -> dict:
    return {
        "topics": [asdict(t) for t in topics],
        "updated_at": _now_iso(),
    }
