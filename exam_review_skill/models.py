from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Any


def _list(value: Any) -> list:
    return value if isinstance(value, list) else ([] if value is None else [value])


@dataclass
class SourceRef:
    source_file: str
    page_or_slide: str | None = None
    question_number: str | None = None
    heading: str | None = None
    confidence: float = 0.8


@dataclass
class DocumentBlock:
    source_file: str
    content: str
    page_or_slide: str | None = None
    question_number: str | None = None
    doc_type: str = "unknown"
    chapter: str | None = None
    heading: str | None = None
    confidence: float = 0.8
    source_refs: list[dict] = field(default_factory=list)
    low_confidence: bool = False


@dataclass
class Document:
    source_file: str
    doc_type: str = "unknown"
    blocks: list[DocumentBlock] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Chunk:
    chunk_id: str
    source_file: str
    content: str
    page_or_slide: str | None = None
    question_number: str | None = None
    doc_type: str = "unknown"
    chapter: str | None = None
    heading: str | None = None
    keywords: list[str] = field(default_factory=list)
    possible_exam_points: list[str] = field(default_factory=list)
    confidence: float = 0.8
    source_refs: list[dict] = field(default_factory=list)


@dataclass
class Topic:
    topic_id: str
    topic_name: str
    chapter: str | None = None
    source_chunks: list[str] = field(default_factory=list)
    definitions: list[str] = field(default_factory=list)
    formulas: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)
    related_topics: list[str] = field(default_factory=list)
    prerequisite_topics: list[str] = field(default_factory=list)
    difficulty: int = 2
    importance: int = 3
    source_confidence: float = 0.75
    inferred: bool = False
    source_refs: list[dict] = field(default_factory=list)


@dataclass
class ExamPoint:
    exam_point_id: str
    topic_id: str
    topic_name: str
    exam_forms: list[str] = field(default_factory=list)
    past_exam_refs: list[dict] = field(default_factory=list)
    frequency: int = 1
    difficulty: int = 2
    score_potential: int = 3
    common_traps: list[str] = field(default_factory=list)
    possible_variants: list[str] = field(default_factory=list)
    priority: str = "B"
    confidence: float = 0.75
    source_refs: list[dict] = field(default_factory=list)


@dataclass
class RiskItem:
    exam_point_id: str
    topic_name: str
    chapter: str | None = None
    exam_probability: float = 0.5
    score_potential: int = 3
    difficulty: int = 2
    current_mastery: str = "unknown"
    traps: list[str] = field(default_factory=list)
    priority: str = "B"
    review_action: str = "复习定义、模板题和来源题。"
    source_refs: list[dict] = field(default_factory=list)
    rationale: str = ""


@dataclass
class Question:
    question_id: str
    question_text: str
    question_type: str
    topic_id: str
    exam_point_id: str
    difficulty: int
    answer: str
    explanation: str
    common_trap: str
    source_refs: list[dict] = field(default_factory=list)
    confidence: float = 0.75


@dataclass
class WrongQuestion:
    question_id: str
    question_text: str
    user_answer: str
    correct_answer: str
    topic_id: str
    exam_point_id: str
    wrong_reason: str
    trap_type: str
    fix_strategy: str
    next_review_date: str
    variant_questions: list[str] = field(default_factory=list)


@dataclass
class ReviewPlan:
    course_name: str
    target_score: int
    exam_date: str | None
    daily_hours: float
    days: list[dict] = field(default_factory=list)
    strategy: str = "80分稳妥策略"


@dataclass
class StudentState:
    course_name: str
    target_score: int = 80
    exam_date: str | None = None
    daily_hours: float = 4
    topic_mastery: dict[str, Any] = field(default_factory=dict)
    weak_points: list[str] = field(default_factory=list)
    strong_points: list[str] = field(default_factory=list)
    wrong_questions: list[dict] = field(default_factory=list)
    review_history: list[dict] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
    last_updated: str = field(default_factory=lambda: date.today().isoformat())


@dataclass
class GenerationReport:
    files_seen: list[str] = field(default_factory=list)
    files_read: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    provider: str = "mock"
    outputs: list[str] = field(default_factory=list)
    quality_checks: list[dict] = field(default_factory=list)

    def warn(self, message: str) -> None:
        if message not in self.warnings:
            self.warnings.append(message)


def to_dict(obj: Any) -> Any:
    if hasattr(obj, "__dataclass_fields__"):
        return asdict(obj)
    if isinstance(obj, list):
        return [to_dict(x) for x in obj]
    if isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}
    return obj
