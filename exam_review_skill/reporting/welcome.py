from __future__ import annotations

from pathlib import Path

from ..i18n import t
from ..models import KnowledgeTopic, StudentModel
from ..state import course as course_mod
from ..state import workspace as workspace_mod


def build_first_use_report(
    workspace_root: Path,
    course_id: str,
    *,
    topics: list[KnowledgeTopic],
    student: StudentModel,
    coverage: object,
    evidence_records: list[dict],
    unresolved_pages: list[str],
    locale: str = "zh-CN",
    output_mode: str = "bilingual",
) -> str:
    """First-use material report: what the system understood about the uploaded
    materials, the course structure, the exam situation, material gaps, current
    risk, and what to do next. This is what the user sees after upload - not a
    dump of files."""
    zh = locale.startswith("zh")
    lines: list[str] = []

    def h(level: int, key: str, **fmt) -> None:
        lines.append("#" * level + " " + t(locale, key, **fmt))

    def bullet(key: str, **fmt) -> None:
        lines.append("- " + t(locale, key, **fmt))

    course_path = course_mod.course_dir(workspace_root, course_id)
    manifest = course_mod.load_manifest(course_path)

    h(1, "welcome.title", course=manifest.course_name)
    lines.append("")

    # 1. Material inventory
    h(2, "welcome.inventory")
    sources = sorted({r.get("source_file", "") for r in evidence_records})
    bullet("welcome.inventory.files", count=len(sources))
    bullet("welcome.inventory.evidence", count=len(evidence_records))
    bullet("welcome.inventory.topics", count=len(topics))
    if unresolved_pages:
        bullet("welcome.inventory.unresolved", count=len(unresolved_pages))
    lines.append("")

    # 2. Course structure
    h(2, "welcome.structure")
    if topics:
        chapters: dict[str, int] = {}
        for topic in topics:
            ch = topic.chapter or t(locale, "welcome.no_chapter")
            chapters[ch] = chapters.get(ch, 0) + 1
        bullet("welcome.structure.chapters", count=len(chapters))
        for ch, count in sorted(chapters.items(), key=lambda x: -x[1])[:8]:
            bullet("welcome.structure.chapter", chapter=ch, count=count)
    else:
        bullet("welcome.structure.empty")
    lines.append("")

    # 3. Exam situation
    h(2, "welcome.exam")
    if manifest.exam_date:
        bullet("welcome.exam.date", date=manifest.exam_date, target=manifest.target_score)
    else:
        bullet("welcome.exam.no_date")
    if manifest.current_estimated_score is None:
        bullet("welcome.exam.no_estimate")
    else:
        bullet("welcome.exam.estimate", score=manifest.current_estimated_score, target=manifest.target_score)
    lines.append("")

    # 4. Material gaps
    h(2, "welcome.gaps")
    if coverage:
        if coverage.verdict.startswith("insufficient"):
            bullet("welcome.gaps.verdict", verdict=coverage.verdict)
        if coverage.answer_coverage.get("answer_sources", 0) == 0:
            bullet("welcome.gaps.answers")
        if coverage.past_exam_coverage.get("exam_sets", 0) == 0:
            bullet("welcome.gaps.past_exam")
        if coverage.past_exam_coverage.get("topics_covered_by_exams", 0) == 0 and coverage.past_exam_coverage.get("total_topics", 0):
            bullet("welcome.gaps.exam_coverage")
        for low in coverage.low_confidence_topics[:5]:
            bullet("welcome.gaps.low_confidence", topic=low)
    if not coverage or (coverage and coverage.verdict == "adequate"):
        bullet("welcome.gaps.none")
    lines.append("")

    # 5. Current risk
    h(2, "welcome.risk")
    if student.topics:
        mastered = sum(1 for tm in student.topics.values() if tm.mastery == "proficient")
        weak = sum(1 for tm in student.topics.values() if tm.mastery in ("novice", "developing"))
        unknown = sum(1 for tm in student.topics.values() if tm.mastery == "unknown")
        bullet("welcome.risk.mastery", mastered=mastered, weak=weak, unknown=unknown)
    else:
        bullet("welcome.risk.no_data")
    lines.append("")

    # 6. Next steps
    h(2, "welcome.next")
    if not student.diagnostic_completed and topics:
        bullet("welcome.next.diagnostic")
    if coverage and coverage.verdict.startswith("insufficient"):
        bullet("welcome.next.fill_gaps")
    if not topics:
        bullet("welcome.next.add_materials")
    else:
        bullet("welcome.next.plan")
        bullet("welcome.next.tutor")
    lines.append("")
    return "\n".join(lines)
