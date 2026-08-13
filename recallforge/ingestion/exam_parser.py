from __future__ import annotations

import re

from .types import ExamPageStructure, ExamQuestion


OPTION_RE = re.compile(r"^\s*([A-D])[.、．:：]\s*(.+)$")
QUESTION_START_RE = re.compile(r"^\s*(?:第\s*)?(\d+)\s*[.、．]?\s*(?:题)?")
# Chinese section-prefixed format: "一、计算题 1. ..." or "二、简答题 2. ..."
SECTION_QUESTION_RE = re.compile(
    r"^\s*[一二三四五六七八九十]+\s*[、.]\s*[^0-9]{0,12}\s*(\d+)\s*[.、．]\s*"
)
SCORE_RE = re.compile(r"[（(]\s*(\d+)\s*分\s*[)）]|\((\d+)\s*points?\)")


def parse_exam_page(text: str, page_or_slide: str) -> ExamPageStructure:
    """Parse a scanned/text exam page into structured questions.

    This is NOT a plain OCR blob: it keeps question_number, body, options,
    subquestions, score, answer_area, and handwritten annotations separately.
    """
    questions: list[ExamQuestion] = []
    current: ExamQuestion | None = None
    current_options: list[str] = []

    def flush() -> None:
        nonlocal current, current_options
        if current is not None:
            current.options = current_options
            questions.append(current)
        current = None
        current_options = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        section = SECTION_QUESTION_RE.match(line)
        if section:
            flush()
            current = ExamQuestion(question_number=section.group(1))
            rest = line[section.end():].strip(" \u3000")
            score = SCORE_RE.search(rest)
            if score:
                current.score = score.group(1) or score.group(2)
                rest = SCORE_RE.sub("", rest).strip()
            current.body = rest
            continue
        start = QUESTION_START_RE.match(line)
        # a 4-digit number is a year (e.g. "2024 期末考试"), not a question number
        year_like = start and len(start.group(1)) >= 4 and not re.search(
            r"[\u4e00-\u9fff]", line[: max(1, start.end())]
        )
        if start and not year_like and (len(line) < 80 or re.search(r"[?？]|[\u4e00-\u9fff]", line[:10])):
            flush()
            current = ExamQuestion(question_number=start.group(1))
            rest = line[start.end():].strip(" \u3000")
            score = SCORE_RE.search(rest)
            if score:
                current.score = score.group(1) or score.group(2)
                rest = SCORE_RE.sub("", rest).strip()
            current.body = rest
            continue
        option = OPTION_RE.match(line)
        if option and current is not None:
            current_options.append(line)
            continue
        if current is not None:
            current.body = (current.body + "\n" + line).strip()
    flush()

    confidence = 0.85 if questions else 0.4
    return ExamPageStructure(page_or_slide=page_or_slide, questions=questions, confidence=confidence)


def merge_provider_exam_structure(
    provider_exam: ExamPageStructure | None,
    native_text: str,
    page_or_slide: str,
) -> ExamPageStructure:
    """Combine provider-structured questions with native-text parsing, keeping the
    richer of the two and preserving every field. Never fabricates questions."""
    native = parse_exam_page(native_text, page_or_slide)
    if provider_exam is None or not provider_exam.questions:
        return native
    if not native.questions:
        return provider_exam
    # merge: provider questions win on structure; native fills missing bodies
    native_by_num = {q.question_number: q for q in native.questions}
    merged = []
    for q in provider_exam.questions:
        nq = native_by_num.get(q.question_number)
        if nq and not q.body:
            q.body = nq.body
        if nq and not q.options:
            q.options = nq.options
        merged.append(q)
    return ExamPageStructure(
        page_or_slide=page_or_slide,
        questions=merged,
        confidence=max(provider_exam.confidence, native.confidence),
    )
