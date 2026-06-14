from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf", ".pptx", ".docx", ".png", ".jpg", ".jpeg"}

DOC_TYPES = {
    "lecture_slide",
    "textbook",
    "class_notes",
    "past_exam",
    "exercise",
    "lab_manual",
    "answer_key",
    "teacher_hint",
    "unknown",
}


@dataclass
class RunConfig:
    input_dir: Path
    output_dir: Path
    course_name: str
    exam_date: str | None = None
    target_score: int = 80
    daily_hours: float = 4
    provider: str = "mock"
