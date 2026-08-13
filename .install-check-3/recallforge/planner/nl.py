from __future__ import annotations

import re


class NLCommand:
    """Parsed natural-language user control, zh-CN and en-US equivalent."""

    def __init__(self, action: str, course_id: str | None = None, value: float | int | None = None, date: str | None = None):
        self.action = action  # skip | pin | reduce | change_target | change_hours | schedule | none
        self.course_id = course_id
        self.value = value
        self.date = date


_STOPWORDS = {
    "a", "an", "the", "i", "we", "you", "my", "our", "today", "tomorrow", "only",
    "have", "has", "want", "need", "to", "for", "of", "in", "on", "at", "with",
    "study", "learn", "do", "skip", "just", "pass", "hours", "hour", "and", "but",
}


_KNOWN_EN_COURSES = {
    "probability": "probability",
    "calculus": "calculus",
    "botany": "botany",
    "organic-chemistry": "organic-chemistry",
    "organic chemistry": "organic-chemistry",
    "inorganic-chemistry": "inorganic-chemistry",
    "linear-algebra": "linear-algebra",
    "linear algebra": "linear-algebra",
}


def _extract_course(text: str) -> str | None:
    """Map a course mention to a course_id: known English names first, then Chinese
    names, then a bare id-like token (excluding stopwords)."""
    lower = text.lower()
    for name, cid in _KNOWN_EN_COURSES.items():
        if name in lower:
            return cid
    for zh, en in _COURSE_NAMES:
        if zh in text:
            return en
    match = re.search(r"\b([a-z][a-z0-9-]*)\b", lower)
    if match:
        candidate = match.group(1)
        if candidate not in _STOPWORDS:
            return candidate
    return None


def parse_command(text: str) -> NLCommand:
    """Parse bilingual user intent into a structured command.

    Equivalent inputs (zh/en) map to the same action:
      "今天不想学植物学" / "I don't want to study botany today"  -> skip botany
      "微积分只求及格"   / "I only need to pass calculus"       -> change target
      "明天只有3小时"    / "I only have three hours tomorrow"   -> change hours
      "有机化学考试提前了" / "My organic chemistry exam moved up" -> schedule (exam reschedule)
      "今天学什么"       / "What should I study today?"         -> none (just plan)
    """
    text = text.strip()
    lower = text.lower()

    # skip (zh)
    if any(p in text for p in ["不想学", "不学", "跳过"]):
        course = _extract_course(text)
        return NLCommand("skip", course_id=course)
    # skip (en): "don't want to study X", "skip X"
    skip_en = re.search(
        r"(?:don'?t\s+want\s+to\s+(?:study|do|learn)\s+|skip\s+)"
        r"((?:organic|inorganic)\s?chemistry|[a-z][a-z0-9-]*)",
        lower,
    )
    if skip_en:
        cid = _extract_course(skip_en.group(1))
        return NLCommand("skip", course_id=cid)
    if re.search(r"\bskip\s+([a-z-]+)", lower):
        match = re.search(r"skip\s+([a-z-]+)", lower)
        return NLCommand("skip", course_id=match.group(1))

    # change hours
    if (
        "只有" in text
        or "小时" in text
        or re.search(r"\d+\s*(hour|h)s?\b", lower)
        or re.search(r"\b(one|two|three|four|five|six|seven|eight|nine|ten)\s+(?:hour|hours|h)\b", lower)
    ):
        hours = _extract_hours(text)
        if hours is not None:
            return NLCommand("change_hours", value=hours)

    # change target (pass only)
    if any(p in text for p in ["只求及格", "及格", "pass", "just pass"]):
        course = _extract_course(text)
        return NLCommand("change_target", course_id=course, value=60)

    # exam rescheduled
    if any(p in text for p in ["提前", "考试提前", "moved up", "rescheduled"]):
        course = _extract_course(text)
        return NLCommand("schedule", course_id=course)

    # pin
    if any(p in text for p in ["优先", "重点学", "pin", "priority"]):
        course = _extract_course(text)
        return NLCommand("pin", course_id=course)

    return NLCommand("none")


_COURSE_NAMES = [
    ("概率论", "probability"),
    ("植物学", "botany"),
    ("微积分", "calculus"),
    ("有机化学", "organic-chemistry"),
    ("无机化学", "inorganic-chemistry"),
    ("线性代数", "linear-algebra"),
]


def _extract_hours(text: str) -> float | None:
    zh = re.search(r"(\d+(?:\.\d+)?)\s*小时", text)
    if zh:
        return float(zh.group(1))
    en = re.search(r"(\d+(?:\.\d+)?)\s*(?:hour|hours|h)\b", text.lower())
    if en:
        return float(en.group(1))
    # English number words: "three hours", "four hours"
    words = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
        "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    }
    word_match = re.search(r"\b(one|two|three|four|five|six|seven|eight|nine|ten)\s+(?:hour|hours|h)\b", text.lower())
    if word_match:
        return float(words[word_match.group(1)])
    return None
