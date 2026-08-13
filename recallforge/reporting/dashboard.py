from __future__ import annotations

from datetime import date
from pathlib import Path

from ..i18n import t
from ..models import GlobalStudyPlan
from ..state import course as course_mod
from ..state import workspace as workspace_mod
from ..orchestrator.calendar import active_entries, days_to_exam
from ..student.store import load_student_model


def _risk_label(priority_signal: float) -> str:
    if priority_signal >= 0.6:
        return "HIGH"
    if priority_signal >= 0.35:
        return "MEDIUM"
    return "LOW"


def _readiness(topic_count: int, student) -> tuple[str | None, str]:
    """Honest readiness: only show a number when there is enough data. Otherwise
    'Unknown' / 'Insufficient evidence'. Never fabricate a readiness percentage."""
    if not student.topics:
        return None, "insufficient"
    scored = [tm for tm in student.topics.values() if tm.mastery_score is not None]
    if not scored:
        return None, "insufficient"
    if len(scored) < max(2, topic_count // 2):
        return None, "insufficient"
    avg = sum(tm.mastery_score for tm in scored) / len(scored)
    return round(avg * 100), "ok"


def build_dashboard(
    workspace_root: Path,
    *,
    plan: GlobalStudyPlan | None = None,
    plan_date: str | None = None,
    locale: str = "zh-CN",
    output_mode: str = "bilingual",
) -> str:
    """Text-based Exam Week dashboard: per-course exam proximity, risk, honest
    readiness, and today's time allocation. User-facing, not JSON."""
    zh = locale.startswith("zh")
    today = date.today()
    if plan_date:
        try:
            from datetime import datetime
            today = datetime.fromisoformat(plan_date).date()
        except (TypeError, ValueError):
            pass
    workspace = workspace_mod.load_workspace_state(workspace_root)
    calendar = workspace_mod.load_exam_calendar(workspace_root)
    entries = {e.course_id: e for e in active_entries(calendar)}

    lines: list[str] = []
    lines.append(t(locale, "dash.title", workspace_id=workspace.workspace_id))
    lines.append("")

    # per-course overview (sorted by exam proximity)
    course_rows: list[tuple[int | None, str]] = []
    for cid in workspace.courses:
        course_path = course_mod.course_dir(workspace_root, cid)
        if not (course_path / "course_manifest.json").exists():
            continue
        manifest = course_mod.load_manifest(course_path)
        if manifest.status == "completed":
            continue
        entry = entries.get(cid)
        if entry:
            days = days_to_exam(entry, today)
        elif manifest.exam_date:
            # fall back to the manifest exam date when the calendar has no entry
            try:
                from datetime import datetime
                exam_date = datetime.fromisoformat(manifest.exam_date).date()
                days = max(0, (exam_date - today).days)
            except (TypeError, ValueError):
                days = None
        else:
            days = None
        course_rows.append((days, cid))
    course_rows.sort(key=lambda x: (x[0] if x[0] is not None else 999, x[1]))

    if not course_rows:
        lines.append(t(locale, "dash.empty"))
        return "\n".join(lines)

    for days, cid in course_rows:
        course_path = course_mod.course_dir(workspace_root, cid)
        manifest = course_mod.load_manifest(course_path)
        student = load_student_model(workspace_root, cid)
        exam_model = course_mod.load_course_json(course_path, "exam_model.json", {}) or {}
        points = exam_model.get("exam_points", []) or []
        if points:
            sa = sum(1 for p in points if p.get("priority") in ("S", "A"))
            risk_signal = sa / len(points)
        else:
            risk_signal = 0.5
        risk = _risk_label(risk_signal)
        readiness_pct, readiness_state = _readiness(len(points), student)

        lines.append(f"## {manifest.course_name}")
        if days is None:
            lines.append(t(locale, "dash.exam", status=t(locale, "dash.exam.tbd")))
        elif days == 0:
            lines.append(t(locale, "dash.exam", status=t(locale, "dash.exam.today")))
        elif days == 1:
            lines.append(t(locale, "dash.exam", status=t(locale, "dash.exam.tomorrow")))
        else:
            lines.append(t(locale, "dash.exam", status=t(locale, "dash.exam.days", days=days)))
        lines.append(t(locale, "dash.risk", risk=risk))
        if readiness_state == "ok" and readiness_pct is not None:
            lines.append(t(locale, "dash.readiness", pct=readiness_pct))
        else:
            lines.append(t(locale, "dash.readiness.unknown"))
        # today's allocation
        if plan:
            hours = plan.allocation.get(cid, 0.0)
            if hours > 0:
                lines.append(t(locale, "dash.today", hours=f"{hours:.1f}"))
            else:
                lines.append(t(locale, "dash.today.none"))
        lines.append("")

    if plan and plan.blocks:
        lines.append("---")
        lines.append(t(locale, "dash.next"))
        for block in plan.blocks[:3]:
            topic = block.topic_name or block.course_id
            lines.append(
                t(
                    locale,
                    "dash.next.item",
                    topic=topic,
                    why=block.why,
                    duration=f"{_duration(block)}",
                    done=block.done_when,
                )
            )
    return "\n".join(lines)


def _duration(block) -> str:
    try:
        start_h, start_m = block.start.split(":")
        end_h, end_m = block.end.split(":")
        minutes = (int(end_h) * 60 + int(end_m)) - (int(start_h) * 60 + int(start_m))
        return f"{minutes} min"
    except Exception:
        return "?"
