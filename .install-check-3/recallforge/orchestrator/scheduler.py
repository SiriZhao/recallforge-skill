from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime
from pathlib import Path

from ..i18n import t
from ..models import (
    CourseManifest,
    CourseSignal,
    DayOverride,
    ExamCalendar,
    GlobalStudyPlan,
    PlanBlock,
    WorkspaceState,
)
from ..state.course import course_dir, load_course_json, load_manifest
from ..state.workspace import (
    load_exam_calendar,
    load_workspace_state,
    override_for,
    save_global_plan,
)
from .calendar import active_entries, days_between, days_to_exam

# Transparent heuristic constants (documented, not a precise science)
MIN_MAINTENANCE_HOURS = 0.5  # anti-starvation: every active course keeps >= this
MAX_SHARE = 0.6              # a normal course may not take more than 60% of the day
CRAM_SHARE = 0.8             # an exam within CRAM_DAYS may take up to 80%
CRAM_DAYS = 2
MIN_BLOCK_MINUTES = 30
MAX_BLOCK_MINUTES = 90
BREAK_MINUTES = 15
DAY_START = "09:00"
NO_DATE_URGENCY = 0.15       # courses without an exam date still get maintenance
UNKNOWN_GAP = 0.5            # no real data -> transparent neutral value, never fabricated


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _fmt(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}"


def _hhmm(total_minutes: int) -> str:
    total_minutes = max(0, total_minutes)
    return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"


def _parse_time(value: str) -> int:
    hours, minutes = value.split(":")
    return int(hours) * 60 + int(minutes)


def build_course_signal(
    manifest: CourseManifest,
    entry_days: int | None,
    exam_model: dict,
    student: dict,
    study_plan: dict,
    today: date,
) -> CourseSignal:
    """Compute one course's transparent scheduling signal.

    expected_gain = 0.35*urgency + 0.30*target_gap + 0.20*risk_signal
                    + 0.10*forgetting_risk + 0.05*unfinished_work
    """
    if entry_days is None:
        urgency = NO_DATE_URGENCY
    else:
        urgency = _clamp(1.0 / (entry_days + 1.0))

    current = manifest.current_estimated_score
    if current is None:
        target_gap = UNKNOWN_GAP
    else:
        target_gap = _clamp((manifest.target_score - current) / 100.0)

    mastery = student.get("mastery", {}) or {}
    if mastery:
        levels = {"unknown": 0.7, "novice": 0.6, "developing": 0.4, "proficient": 0.1}
        gaps = [levels.get(m.get("level", "unknown"), 0.5) for m in mastery.values()]
        mastery_gap = _clamp(sum(gaps) / len(gaps))
    else:
        mastery_gap = UNKNOWN_GAP

    points = exam_model.get("exam_points", []) or []
    if points:
        sa = [p for p in points if p.get("priority") in ("S", "A")]
        risk_signal = _clamp(len(sa) / len(points))
    else:
        risk_signal = 0.5

    sessions = student.get("review_history", []) or []
    last_seen = None
    for session in reversed(sessions):
        try:
            last_seen = datetime.fromisoformat(str(session.get("date", ""))).date()
            break
        except (TypeError, ValueError):
            continue
    if last_seen is None:
        forgetting = 0.8  # never reviewed -> high forgetting risk
    else:
        forgetting = _clamp(max(0, (today - last_seen).days) / 7.0)

    planned = float(study_plan.get("planned_hours", 0.0) or 0.0)
    logged = float(study_plan.get("logged_hours", 0.0) or 0.0)
    unfinished = _clamp(max(0.0, planned - logged) / 2.0)

    difficulty = float(exam_model.get("avg_difficulty", 2.0) or 2.0)
    topics = max(1, int(manifest.topic_count or 1))
    learning_cost_hours = _clamp(0.5 + difficulty * 0.25 + topics * 0.05, 0.5, 6.0)

    coverage = exam_model.get("coverage", {}) or {}
    cov = coverage.get("overall")
    if cov is None and points:
        covered = [p for p in points if p.get("past_exam_refs")]
        cov = len(covered) / len(points) if points else None
    coverage_value = _clamp(float(cov)) if cov is not None else None

    expected_gain = _clamp(
        0.35 * urgency
        + 0.30 * target_gap
        + 0.20 * risk_signal
        + 0.10 * forgetting
        + 0.05 * unfinished
    )
    importance = manifest.importance_override
    priority = expected_gain * (importance if importance is not None else 1.0)

    return CourseSignal(
        course_id=manifest.course_id,
        days_to_exam=entry_days,
        urgency=urgency,
        target_gap=target_gap,
        mastery_gap=mastery_gap,
        risk_signal=risk_signal,
        expected_gain=expected_gain,
        learning_cost_hours=learning_cost_hours,
        forgetting_risk=forgetting,
        unfinished_work=unfinished,
        coverage=coverage_value,
        priority=priority,
    )


def allocate_hours(
    signals: list[CourseSignal],
    total_hours: float,
    skip_courses: list[str],
    course_hours_override: dict[str, float] | None,
    locale: str,
) -> tuple[dict[str, float], list[str]]:
    """Allocate daily hours per course.

    Anti-starvation:
      1. every active (non-skipped) course keeps a minimum maintenance allocation;
      2. a course without an exam date still gets maintenance (no starvation);
      3. no course exceeds the daily cap unless it is exam-close (cram);
      4. explicit user course-hour overrides win.
    """
    active = [s for s in signals if s.course_id not in skip_courses]
    notes: list[str] = []
    result: dict[str, float] = {}
    if not active:
        return result, notes

    count = len(active)
    min_alloc = min(MIN_MAINTENANCE_HOURS, (total_hours / count) * 0.5)
    reserved = min(total_hours, min_alloc * count)
    for signal in active:
        result[signal.course_id] = min_alloc

    urgent = {
        s.course_id
        for s in active
        if s.days_to_exam is not None and s.days_to_exam <= CRAM_DAYS
    }
    share = CRAM_SHARE if urgent else MAX_SHARE
    cap = total_hours * share

    remaining = total_hours - reserved
    weights = {s.course_id: max(0.0, s.priority) for s in active}
    total_weight = sum(weights.values())
    if total_weight > 0 and remaining > 0:
        for signal in active:
            extra = remaining * (weights[signal.course_id] / total_weight)
            result[signal.course_id] += min(extra, max(0.0, cap - result[signal.course_id]))

    if course_hours_override:
        for cid, hours in course_hours_override.items():
            result[cid] = max(0.0, hours)
            notes.append(f"user course-hours override: {cid} = {_fmt(hours)}h")

    total_allocated = sum(result.values())
    if total_allocated > total_hours and total_allocated > 0:
        scale = total_hours / total_allocated
        result = {cid: hours * scale for cid, hours in result.items()}

    for signal in active:
        notes.append(
            t(
                locale,
                "plan.note.maintenance",
                course=signal.course_id,
                min_hours=_fmt(min_alloc),
                hours=_fmt(result[signal.course_id]),
            )
        )
    for cid in skip_courses:
        notes.append(t(locale, "plan.note.skip", course=cid))
    return result, notes


def _block_why(signal: CourseSignal, manifest: CourseManifest, locale: str) -> str:
    sep = "；" if locale.startswith("zh") else "; "
    if signal.days_to_exam is None:
        why = t(locale, "plan.why.no_date", urgency=_fmt(signal.urgency))
    else:
        why = t(locale, "plan.why.urgency", days=signal.days_to_exam, urgency=_fmt(signal.urgency))
    if manifest.current_estimated_score is None:
        why += sep + t(locale, "plan.why.gap_unknown", gap=_fmt(signal.target_gap))
    else:
        why += sep + t(
            locale,
            "plan.why.gap",
            target=manifest.target_score,
            current=manifest.current_estimated_score,
            gap=_fmt(signal.target_gap),
        )
    why += sep + t(locale, "plan.why.gain", gain=_fmt(signal.expected_gain))
    return why


def _block_risk(signal: CourseSignal, locale: str) -> str:
    if signal.days_to_exam is None or signal.risk_signal == 0.5:
        return t(locale, "plan.risk.default", risk=_fmt(signal.risk_signal))
    return t(locale, "plan.risk.sa", risk=_fmt(signal.risk_signal))


def _block_goal(signal: CourseSignal, manifest: CourseManifest, locale: str) -> str:
    return t(locale, "plan.goal", topics=max(1, manifest.topic_count or 1))


def _block_done(signal: CourseSignal, locale: str) -> str:
    rate = 60 if signal.days_to_exam is None else 80
    return t(locale, "plan.done", rate=rate)


def _blocks_for_day(
    signals: list[CourseSignal],
    allocation: dict[str, float],
    manifests: dict[str, CourseManifest],
    locale: str,
) -> list[PlanBlock]:
    ordered = sorted(signals, key=lambda s: (-s.priority, s.course_id))
    blocks: list[PlanBlock] = []
    cursor = _parse_time(DAY_START)
    for signal in ordered:
        minutes_total = int(round(allocation.get(signal.course_id, 0.0) * 60))
        if minutes_total < 1:
            continue
        manifest = manifests[signal.course_id]
        remaining = minutes_total
        while remaining > 0:
            chunk = min(remaining, MAX_BLOCK_MINUTES)
            if chunk < MIN_BLOCK_MINUTES:
                # merge a small sliver into the previous block of the same course
                if blocks and blocks[-1].course_id == signal.course_id:
                    previous = blocks[-1]
                    previous.end = _hhmm(_parse_time(previous.end) + chunk)
                    cursor += chunk  # keep the break aligned after the merged block
                remaining = 0
                break
            if signal.days_to_exam is None:
                kind = "maintenance"
            elif signal.days_to_exam <= CRAM_DAYS:
                kind = "cram"
            elif signal.forgetting_risk >= 0.5:
                kind = "review"
            else:
                kind = "study"
            blocks.append(
                PlanBlock(
                    block_id=f"B{len(blocks) + 1:03d}",
                    course_id=signal.course_id,
                    start=_hhmm(cursor),
                    end=_hhmm(cursor + chunk),
                    kind=kind,
                    why=_block_why(signal, manifest, locale),
                    risk=_block_risk(signal, locale),
                    goal=_block_goal(signal, manifest, locale),
                    done_when=_block_done(signal, locale),
                )
            )
            cursor += chunk + BREAK_MINUTES
            remaining -= chunk
    return blocks


def generate_daily_plan(
    workspace_root: Path,
    plan_date: str | None = None,
    *,
    total_hours_override: float | None = None,
    skip_courses: list[str] | None = None,
    target_score_changes: dict[str, int] | None = None,
    exam_date_changes: dict[str, str] | None = None,
    course_hours: dict[str, float] | None = None,
    persist: bool = True,
) -> GlobalStudyPlan:
    """Generate the global daily plan for one date across all courses.

    User overrides (stored per date or passed inline) force re-planning:
      - skip a course today ("今天不想学植物学")
      - change total hours ("明天只有3小时")
      - change an exam date ("有机化学考试提前了")
      - change a target score ("微积分目标只要及格")
    """
    today = date.today()
    plan_date = plan_date or today.isoformat()
    try:
        target_date = datetime.fromisoformat(plan_date).date()
    except (TypeError, ValueError):
        target_date = today

    workspace = load_workspace_state(workspace_root)
    locale = workspace.user_locale
    calendar = load_exam_calendar(workspace_root)

    override = override_for(workspace_root, plan_date)
    merged_skip = list(skip_courses or [])
    merged_hours = total_hours_override
    merged_targets = dict(target_score_changes or {})
    merged_dates = dict(exam_date_changes or {})
    merged_course_hours = dict(course_hours or {})
    applied: list[str] = []
    if override:
        for cid in override.skip_courses:
            if cid not in merged_skip:
                merged_skip.append(cid)
        if override.total_hours is not None:
            merged_hours = override.total_hours
        merged_targets.update(override.target_scores)
        merged_dates.update(override.exam_date_changes)
        merged_course_hours.update(override.course_hours)
        if override.note:
            applied.append(override.note)

    total_hours = merged_hours if merged_hours is not None else workspace.daily_total_hours

    signals: list[CourseSignal] = []
    manifests: dict[str, CourseManifest] = {}
    for cid in workspace.courses:
        course_path = course_dir(workspace_root, cid)
        if not (course_path / "course_manifest.json").exists():
            continue
        manifest = load_manifest(course_path)
        if cid in merged_dates:
            manifest.exam_date = merged_dates[cid]
            applied.append(f"{cid} exam date -> {merged_dates[cid]}")
        if cid in merged_targets:
            manifest.target_score = merged_targets[cid]
            applied.append(f"{cid} target -> {merged_targets[cid]}")
        manifests[cid] = manifest

        entry_days = None
        for entry in active_entries(calendar):
            if entry.course_id == cid:
                entry_days = days_to_exam(entry, target_date)
                break
        if entry_days is None and manifest.exam_date:
            entry_days = days_between(manifest.exam_date, target_date)

        exam_model = load_course_json(course_path, "exam_model.json", {}) or {}
        student = load_course_json(course_path, "student_state.json", {}) or {}
        study_plan = load_course_json(course_path, "study_plan.json", {}) or {}
        signals.append(
            build_course_signal(manifest, entry_days, exam_model, student, study_plan, target_date)
        )

    allocation, notes = allocate_hours(
        signals, total_hours, merged_skip, merged_course_hours or None, locale
    )
    blocks = _blocks_for_day(signals, allocation, manifests, locale)

    plan = GlobalStudyPlan(
        workspace_id=workspace.workspace_id,
        date=plan_date,
        total_hours=total_hours,
        blocks=blocks,
        allocation=allocation,
        notes=notes,
        overrides_applied=applied,
    )
    if persist:
        save_global_plan(workspace_root, plan)
    return plan


def render_plan(plan: GlobalStudyPlan, locale: str) -> str:
    lines = [
        t(locale, "plan.title", date=plan.date, hours=_fmt(plan.total_hours)),
        "",
    ]
    for block in plan.blocks:
        kind_label = t(locale, f"plan.kind.{block.kind}", **{}) if block.kind in {
            "study", "review", "cram", "maintenance", "wrongbook",
        } else block.kind
        lines.append(
            t(
                locale,
                "plan.block.line",
                start=block.start,
                end=block.end,
                course_id=block.course_id,
                kind_label=kind_label,
            )
        )
        lines.append("  " + t(locale, "plan.block.why", why=block.why))
        lines.append("  " + t(locale, "plan.block.risk", risk=block.risk))
        lines.append("  " + t(locale, "plan.block.goal", goal=block.goal))
        lines.append("  " + t(locale, "plan.block.done", done_when=block.done_when))
        lines.append("")
    if plan.notes:
        lines.append("---")
        lines.extend(f"- {note}" for note in plan.notes)
    if plan.overrides_applied:
        lines.append("---")
        lines.append("Overrides applied:")
        lines.extend(f"- {applied}" for applied in plan.overrides_applied)
    return "\n".join(lines)
