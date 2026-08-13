from __future__ import annotations

from collections import Counter

from ..models import CoverageReport, ExamPointModel, PastExamSet, TeacherStyle, KnowledgeTopic, _now_iso


def build_coverage_report(
    course_id: str,
    topics: list[KnowledgeTopic],
    exam_points: list[ExamPointModel],
    past_exam_sets: list[PastExamSet],
    teacher_style: TeacherStyle,
    evidence_records: list[dict],
    unresolved_pages: list[str],
) -> CoverageReport:
    """Answer 'do I have enough materials?' with concrete, explainable numbers."""
    report = CoverageReport(course_id=course_id)

    total_evidence = len([r for r in evidence_records if not r.get("synthetic")])
    report.material_coverage = {
        "evidence_records": total_evidence,
        "topics": len(topics),
        "sources": len({r.get("source_file") for r in evidence_records}),
    }

    chapters = Counter(t.chapter for t in topics if t.chapter)
    report.chapter_coverage = {
        "chapters_with_evidence": len(chapters),
        "chapters": dict(chapters),
    }

    report.past_exam_coverage = {
        "exam_sets": len(past_exam_sets),
        "questions": sum(len(s.questions) for s in past_exam_sets),
        "topics_covered_by_exams": len({t.topic_id for t in topics if t.past_exam_links}),
        "total_topics": len(topics),
    }

    answer_count = 0
    for record in evidence_records:
        source = (record.get("source_file") or "").lower()
        if "answer" in source:
            answer_count += 1
    report.answer_coverage = {"answer_sources": answer_count}

    report.unresolved_documents = unresolved_pages
    report.low_confidence_topics = [
        t.topic_id for t in topics if t.source_confidence < 0.5
    ]

    # verdict: honest, fail-closed
    verdict_parts = []
    if total_evidence == 0:
        verdict_parts.append("no evidence ingested")
    if not topics:
        verdict_parts.append("no topics extracted")
    if not past_exam_sets:
        verdict_parts.append("no past-exam materials")
    if report.answer_coverage["answer_sources"] == 0:
        verdict_parts.append("no answer keys")
    if unresolved_pages:
        verdict_parts.append(f"{len(unresolved_pages)} unresolved pages")
    if verdict_parts:
        report.verdict = "insufficient: " + "; ".join(verdict_parts)
    else:
        report.verdict = "adequate"

    report.generated_at = _now_iso()
    return report
