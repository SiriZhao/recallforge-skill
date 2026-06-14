from __future__ import annotations

import re
from pathlib import Path


def classify_document(path: str | Path, text: str = "") -> str:
    name = Path(path).name.lower()
    sample = (name + "\n" + text[:2000].lower())
    if any(k in sample for k in ["答案", "answer key", "参考答案"]):
        if any(k in sample for k in ["试卷", "exam", "往年"]):
            return "past_exam"
        return "answer_key"
    if any(k in sample for k in ["往年", "试卷", "期末", "exam", "选择题", "简答题", "计算题"]) and re.search(r"\b20\d{2}\b|第?\s*\d+\s*[题、.]", sample):
        return "past_exam"
    if any(k in sample for k in ["老师强调", "老师说", "必考", "重点", "画重点"]):
        return "teacher_hint" if "hint" in name or "重点" in name else "class_notes"
    if any(k in name for k in ["lecture", "slide", "ppt", "课件"]):
        return "lecture_slide"
    if any(k in name for k in ["note", "笔记"]):
        return "class_notes"
    if any(k in name for k in ["exercise", "作业", "习题"]):
        return "exercise"
    if any(k in name for k in ["lab", "实验手册"]):
        return "lab_manual"
    if any(k in name for k in ["book", "textbook", "教材"]):
        return "textbook"
    return "unknown"
