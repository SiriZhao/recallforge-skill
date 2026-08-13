from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BenchmarkMetrics:
    """Objective metrics comparing the Skill pipeline to the naive baseline."""

    source_coverage: float = 0.0
    citation_accuracy: float = 0.0
    important_topic_recall: float = 0.0
    cross_document_linking: float = 0.0
    past_exam_mapping: float = 0.0
    hallucination_rate: float = 0.0
    exam_relevance: float = 0.0
    personalization: float = 0.0
    adaptivity: float = 0.0
    actionability: float = 0.0
    multi_course_planning: float = 0.0
    details: dict = field(default_factory=dict)


def _norm(value: float) -> float:
    return max(0.0, min(1.0, value))


def source_coverage(skill_sources: set[str], naive_sources: set[str], all_sources: set[str]) -> tuple[float, float]:
    """Fraction of source files whose content is represented in the output."""
    if not all_sources:
        return 1.0, 1.0
    return _norm(len(skill_sources & all_sources) / len(all_sources)), _norm(len(naive_sources & all_sources) / len(all_sources))


def citation_accuracy(skill_claims_with_citations: int, skill_claims_total: int, naive_claims_total: int) -> tuple[float, float]:
    """Fraction of output claims that carry a correct source reference."""
    skill = _norm(skill_claims_with_citations / skill_claims_total) if skill_claims_total else 1.0
    naive = 0.0 if naive_claims_total else 1.0  # naive has no citations by construction
    return skill, naive


def important_topic_recall(skill_topics: set[str], naive_topics: set[str], important: set[str]) -> tuple[float, float]:
    if not important:
        return 1.0, 1.0
    return _norm(len(skill_topics & important) / len(important)), _norm(len(naive_topics & important) / len(important))


def cross_document_linking(
    skill_linked: int, skill_total_topics: int, naive_linked: int, naive_total_topics: int
) -> tuple[float, float]:
    """Fraction of topics that appear in 2+ source files AND are recognized as one
    topic (cross-document fusion)."""
    skill = _norm(skill_linked / skill_total_topics) if skill_total_topics else 1.0
    naive = _norm(naive_linked / naive_total_topics) if naive_total_topics else 0.0
    return skill, naive


def past_exam_mapping(skill_mapped: int, skill_questions: int, naive_mapped: int, naive_questions: int) -> tuple[float, float]:
    """Fraction of past-exam questions mapped to a topic."""
    skill = _norm(skill_mapped / skill_questions) if skill_questions else 1.0
    naive = _norm(naive_mapped / naive_questions) if naive_questions else 0.0
    return skill, naive


def hallucination_rate(
    skill_supported: int, skill_total: int, naive_supported: int, naive_total: int
) -> tuple[float, float]:
    """Fraction of output claims NOT supported by any source (lower is better).
    Returns (skill_rate, naive_rate)."""
    skill = _norm(1 - skill_supported / skill_total) if skill_total else 0.0
    naive = _norm(1 - naive_supported / naive_total) if naive_total else 1.0
    return skill, naive


def exam_relevance(skill_exam_claims: int, skill_total: int, naive_exam_claims: int, naive_total: int) -> tuple[float, float]:
    """Fraction of output that is exam-oriented (specific exam points / question
    types / frequency) vs generic summary."""
    skill = _norm(skill_exam_claims / skill_total) if skill_total else 0.0
    naive = _norm(naive_exam_claims / naive_total) if naive_total else 0.0
    return skill, naive


def binary_personalization(skill_changes: bool, naive_changes: bool) -> tuple[float, float]:
    """Whether the output changes when student performance data is provided."""
    return 1.0 if skill_changes else 0.0, 1.0 if naive_changes else 0.0


def binary_adaptivity(skill_changes: bool, naive_changes: bool) -> tuple[float, float]:
    """Whether a wrong answer changes the subsequent plan/output."""
    return 1.0 if skill_changes else 0.0, 1.0 if naive_changes else 0.0


def actionability(skill_actionable: int, skill_total: int, naive_actionable: int, naive_total: int) -> tuple[float, float]:
    """Fraction of advice that names a specific topic + task + completion criterion."""
    skill = _norm(skill_actionable / skill_total) if skill_total else 0.0
    naive = _norm(naive_actionable / naive_total) if naive_total else 0.0
    return skill, naive


def multi_course_planning(skill_coordinated: bool, naive_coordinated: bool) -> tuple[float, float]:
    """Whether a multi-course run produces ONE coordinated exam-week plan."""
    return 1.0 if skill_coordinated else 0.0, 1.0 if naive_coordinated else 0.0


def skill_advantage(skill_metrics: BenchmarkMetrics) -> dict[str, float]:
    """Per-metric advantage of the Skill over the naive baseline (skill - naive)."""
    return {
        "source_coverage": skill_metrics.source_coverage,
        "citation_accuracy": skill_metrics.citation_accuracy,
        "important_topic_recall": skill_metrics.important_topic_recall,
        "cross_document_linking": skill_metrics.cross_document_linking,
        "past_exam_mapping": skill_metrics.past_exam_mapping,
        "exam_relevance": skill_metrics.exam_relevance,
        "personalization": skill_metrics.personalization,
        "adaptivity": skill_metrics.adaptivity,
        "actionability": skill_metrics.actionability,
        "multi_course_planning": skill_metrics.multi_course_planning,
    }


def _is_exam_oriented(line: str) -> bool:
    markers = ("真题", "题型", "往年", "考点", "频次", "past exam", "exam format", "question type", "frequency")
    return any(m in line for m in markers)
