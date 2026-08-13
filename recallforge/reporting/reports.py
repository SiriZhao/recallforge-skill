from __future__ import annotations

from pathlib import Path

from ..i18n import t
from ..models import CramPlan, StudentModel
from ..state import course as course_mod
from ..state import workspace as workspace_mod
from ..student.store import load_student_model
from ..knowledge.build import build_course_intelligence
from .welcome import build_first_use_report
from .dashboard import build_dashboard


REPORT_TYPES = (
    "course-overview",
    "exam-risk-radar",
    "past-exam-analysis",
    "teacher-style",
    "formula-sheet",
    "wrongbook",
    "7-day-plan",
    "mock-exam",
    "1-hour-cram",
    "30-min-rescue",
    "dashboard",
    "welcome",
)


def render_report(
    workspace_root: Path,
    report_type: str,
    *,
    course_id: str | None = None,
    locale: str = "zh-CN",
    output_mode: str = "bilingual",
    plan=None,
) -> str:
    """Render an on-demand report as Markdown. Export happens separately and its
    failure never affects the main learning flow."""
    if report_type not in REPORT_TYPES:
        raise ValueError(f"unknown report {report_type!r}; expected {REPORT_TYPES}")
    zh = locale.startswith("zh")

    # dashboard & welcome are workspace/course-level reports
    if report_type == "dashboard":
        return build_dashboard(workspace_root, plan=plan, locale=locale, output_mode=output_mode)

    if not course_id:
        raise ValueError(f"report {report_type!r} requires --course")
    course_path = course_mod.course_dir(workspace_root, course_id)
    if not (course_path / "course_manifest.json").exists():
        raise FileNotFoundError(f"no course {course_id!r}")
    manifest = course_mod.load_manifest(course_path)

    result = build_course_intelligence(workspace_root, course_id, persist=False)
    student = load_student_model(workspace_root, course_id)

    if report_type == "welcome":
        records = course_mod.load_course_json(course_path, "evidence_store.json", {}) or {}
        return build_first_use_report(
            workspace_root,
            course_id,
            topics=result.topics,
            student=student,
            coverage=result.coverage,
            evidence_records=records.get("records", []),
            unresolved_pages=result.coverage.unresolved_documents,
            locale=locale,
            output_mode=output_mode,
        )

    if report_type == "course-overview":
        return _course_overview(course_id, manifest, result, student, locale)
    if report_type == "exam-risk-radar":
        return _risk_radar(result.exam_points, locale)
    if report_type == "past-exam-analysis":
        return _past_exam(result.past_exam_sets, locale)
    if report_type == "teacher-style":
        return _teacher_style(result.teacher_style, locale)
    if report_type == "formula-sheet":
        return _formula_sheet(result.topics, locale)
    if report_type == "wrongbook":
        return _wrongbook(workspace_root, course_id, student, locale)
    if report_type == "7-day-plan":
        return _seven_day_plan(result.topics, result.exam_points, student, course_id, locale)
    if report_type == "mock-exam":
        return _mock_exam(result, student, course_id, locale)
    if report_type in ("1-hour-cram", "30-min-rescue"):
        return _cram(workspace_root, course_id, result, student, report_type, locale)
    raise ValueError(report_type)


def _course_overview(course_id, manifest, result, student: StudentModel, locale) -> str:
    zh = locale.startswith("zh")
    lines = [f"# {t(locale, 'report.course_overview.title', course=manifest.course_name)}", ""]
    lines.append(t(locale, "report.course.manifest",
                   target=manifest.target_score,
                   current=manifest.current_estimated_score if manifest.current_estimated_score is not None else t(locale, "common.none"),
                   exam=manifest.exam_date or t(locale, "course.exam.unknown"),
                   topics=len(result.topics)))
    lines.append("")
    lines.append(f"## {t(locale, 'report.topics')}")
    for topic in result.topics[:20]:
        ep = next((p for p in result.exam_points if p.topic_id == topic.topic_id), None)
        tm = student.topics.get(topic.topic_id)
        mastery = tm.mastery if tm else "unknown"
        priority = ep.priority if ep else "C"
        lines.append(f"- [{priority}] {topic.canonical_name} (mastery={mastery})")
    return "\n".join(lines)


def _risk_radar(exam_points, locale) -> str:
    zh = locale.startswith("zh")
    lines = [f"# {t(locale, 'report.risk_radar.title')}", ""]
    for p in sorted(exam_points, key=lambda x: {"S": 0, "A": 1, "B": 2, "C": 3}[x.priority]):
        lines.append(f"## [{p.priority}] {p.topic_name}")
        lines.append(t(locale, "report.risk.item",
                       importance=p.importance,
                       likelihood=p.likelihood_estimate,
                       freq=p.past_exam_frequency,
                       teacher=p.teacher_emphasis))
        for reason in p.priority_rationale[:2]:
            lines.append(f"  - {reason}")
    return "\n".join(lines)


def _past_exam(past_exam_sets, locale) -> str:
    zh = locale.startswith("zh")
    lines = [f"# {t(locale, 'report.past_exam.title')}", ""]
    if not past_exam_sets:
        lines.append(t(locale, "report.past_exam.none"))
        return "\n".join(lines)
    for exam_set in past_exam_sets:
        lines.append(f"## {exam_set.source_file}" + (f" ({exam_set.year})" if exam_set.year else ""))
        for q in exam_set.questions:
            lines.append(f"- Q{q.question_number} [{q.question_type}] topics={','.join(q.topics) or 'unknown'}")
    return "\n".join(lines)


def _teacher_style(teacher, locale) -> str:
    zh = locale.startswith("zh")
    lines = [f"# {t(locale, 'report.teacher_style.title')}", ""]
    lines.append(t(locale, "report.teacher_style.tier", tier=teacher.tier))
    for claim in teacher.claims:
        lines.append(f"- {claim['claim']} [{claim['tier']}]")
    if not teacher.claims:
        lines.append(t(locale, "report.teacher_style.no_claims"))
    return "\n".join(lines)


def _formula_sheet(topics, locale) -> str:
    zh = locale.startswith("zh")
    lines = [f"# {t(locale, 'report.formula_sheet.title')}", ""]
    found = False
    for topic in topics:
        if topic.formulas:
            found = True
            lines.append(f"## {topic.canonical_name}")
            for formula in topic.formulas:
                lines.append(f"- {formula.text}")
    if not found:
        lines.append(t(locale, "report.formula_sheet.none"))
    return "\n".join(lines)


def _wrongbook(workspace_root, course_id, student, locale) -> str:
    zh = locale.startswith("zh")
    course_path = course_mod.course_dir(workspace_root, course_id)
    data = course_mod.load_course_json(course_path, "wrongbook.json", {}) or {}
    entries = data.get("entries", []) or []
    lines = [f"# {t(locale, 'report.wrongbook.title')}", ""]
    if not entries:
        lines.append(t(locale, "report.wrongbook.none"))
        return "\n".join(lines)
    for entry in entries:
        resolved = "OK" if entry.get("resolved") else "OPEN"
        diagnosis = entry.get("diagnosis", "unknown")
        label = t(locale, f"mistake.{diagnosis}") if diagnosis in _mistake_keys() else diagnosis
        lines.append(
            f"- [{resolved}] {entry.get('question_text', '')} ({label}) "
            f"retry={entry.get('retry_count', 0)}"
        )
    return "\n".join(lines)


def _mistake_keys() -> list[str]:
    return [
        "concept_gap", "formula_recall", "condition_misread", "prerequisite_gap",
        "calculation_error", "algebra_error", "sign_error", "unit_error",
        "reasoning_jump", "question_misread", "method_selection", "memory_failure",
        "careless_error", "unknown",
    ]


def _seven_day_plan(topics, exam_points, student, course_id, locale) -> str:
    zh = locale.startswith("zh")
    lines = [f"# {t(locale, 'report.7day.title')}", ""]
    from ..planner.course_planner import build_course_plan
    from ..models import CourseManifest

    manifest = CourseManifest(course_id=course_id, course_name=course_id)
    plan = build_course_plan(
        workspace_root=Path("."),
        course_id=course_id,
        manifest=manifest,
        topics=topics,
        exam_points=exam_points,
        student=student,
        wrongbook_entries=[],
        days_left=7,
        hours_available=4.0,
        locale=locale,
    )
    for block in plan.blocks:
        lines.append(f"- {block.topic_name} ({block.duration_hours}h) [{block.kind}]")
        lines.append(f"    {block.task}")
        lines.append(f"    完成：{block.completion_criterion}")
    return "\n".join(lines)


def _mock_exam(result, student, course_id, locale) -> str:
    zh = locale.startswith("zh")
    from ..tutor.quiz import generate_quiz

    questions = generate_quiz(
        topics=result.topics,
        exam_points=result.exam_points,
        past_exam_sets=result.past_exam_sets,
        student=student,
        wrongbook_entries=[],
        mode="mixed",
        count=8,
    )
    lines = [f"# {t(locale, 'report.mock_exam.title')}", ""]
    for q in questions:
        lines.append(f"## {q.question_id} L{q.level} [{q.question_type}] {q.topic_name}")
        lines.append(q.question_text)
        if q.options:
            for opt in q.options:
                lines.append(f"  {opt}")
    lines.append("")
    lines.append(f"## {t(locale, 'report.mock_exam.answers')}")
    for q in questions:
        lines.append(f"- {q.question_id}: {q.correct_answer}")
    return "\n".join(lines)


def _cram(workspace_root, course_id, result, student, report_type, locale) -> str:
    zh = locale.startswith("zh")
    from ..tutor.cram import build_cram_plan, render_cram_plan
    from ..state import course as course_mod

    wrongbook = course_mod.load_course_json(
        course_mod.course_dir(workspace_root, course_id), "wrongbook.json", {}
    ) or {}
    mode = "1h" if report_type == "1-hour-cram" else "30m"
    plan = build_cram_plan(
        workspace_root=workspace_root,
        course_id=course_id,
        topics=result.topics,
        exam_points=result.exam_points,
        student=student,
        wrongbook_entries=wrongbook.get("entries", []),
        mode=mode,
        locale=locale,
    )
    return render_cram_plan(plan, locale)
