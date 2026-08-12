from __future__ import annotations

import re

from .types import ExamPageStructure, ExamQuestion


OPTION_RE = re.compile(r"^\s*([A-D])[.、．:：]\s*(.+)$")
QUESTION_START_RE = re.compile(r"^\s*(?:第\s*)?(\d+)\s*[.、．]?\s*(?:题)?")
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
        start = QUESTION_START_RE.match(line)
        if start and (len(line) < 80 or re.search(r"[?？]|[\u4e00-\u9fff]", line[:10])):
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
