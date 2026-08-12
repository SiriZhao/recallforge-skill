from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date, datetime
from pathlib import Path

from ..i18n import t
from ..models import (
    CourseManifest,
    CoursePlan,
    CourseSignal,
    DayOverride,
    GlobalStudyPlan,
    PlanBlock,
    StudentModel,
    StudyBlock,
)
from ..state.course import course_dir, load_course_json, load_manifest
from ..state.workspace import (
    load_exam_calendar,
    load_workspace_state,
    override_for,
    save_global_plan,
)
from ..student.store import load_student_model
from ..orchestrator.calendar import active_entries, days_between, days_to_exam
from .course_planner import build_course_plan

# Transparent heuristic constants (documented, not a precise science)
MIN_MAINTENANCE_HOURS = 0.5
MAX_SHARE = 0.6
CRAM_SHARE = 0.8
CRAM_DAYS = 2
MIN_BLOCK_MINUTES = 30
MAX_BLOCK_MINUTES = 90
BREAK_MINUTES = 15
DAY_START = "09:00"
NO_DATE_URGENCY = 0.15
UNKNOWN_GAP = 0.5


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _fmt(v: float, digits: int = 2) -> str:
    return f"{v:.{digits}f}"


def _hhmm(total_minutes: int) -> str:
    total_minutes = max(0, total_minutes)
    return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"


def _parse_time(value: str) -> int:
    hours, minutes = value.split(":")
    return int(hours) * 60 + int(minutes)


def _load_topics(course_path: Path) -> list[dict]:
    data = load_course_json(course_path, "knowledge_graph.json", {}) or {}
    return data.get("topics", []) or []


def _load_exam_points(course_path: Path) -> list[dict]:
    data = load_course_json(course_path, "exam_model.json", {}) or {}
    return data.get("exam_points", []) or []


def _load_wrongbook(course_path: Path) -> list[dict]:
    data = load_course_json(course_path, "wrongbook.json", {}) or {}
    return data.get("entries", []) or []


def build_course_signal_v4(
    *,
    manifest: CourseManifest,
    entry_days: int | None,
    student: StudentModel,
    topics: list[dict],
    exam_points: list[dict],
    wrongbook: list[dict],
    today: date,
) -> CourseSignal:
    """Cross-course priority signal (Round 4 formal version).

    Components (all recorded in expected_gain):
      urgency          = 1/(days+1)                     (exam proximity)
      score_gain       = target gap * risk signal       (score gain opportunity)
      risk             = share of S/A exam points       (unmastered high risk)
      target_gap       = (target - current)/100
      learning_cost    = normalized learning cost       (cheaper wins slightly)
      forgetting       = avg topic forgetting risk      (learned-but-decaying)
      unfinished       = planned - logged hours
    """
    if entry_days is None:
        urgency = NO_DATE_URGENCY
    else:
        urgency = _clamp(1.0 / (entry_days + 1.0))

    current = manifest.current_estimated_score
    target_gap = UNKNOWN_GAP if current is None else _clamp((manifest.target_score - current) / 100.0)

    risk_signal = 0.5
    if exam_points:
        sa = [p for p in exam_points if p.get("priority") in ("S", "A")]
        risk_signal = _clamp(len(sa) / len(exam_points))

    # mastery gap from the real student model
    mastery_gap = UNKNOWN_GAP
    if student.topics:
        gaps = []
        for tm in student.topics.values():
            if tm.mastery == "unknown":
                gaps.append(0.8)
            elif tm.mastery == "novice":
                gaps.append(0.6)
            elif tm.mastery == "developing":
                gaps.append(0.4)
            else:
                gaps.append(0.1)
        mastery_gap = _clamp(sum(gaps) / len(gaps)) if gaps else UNKNOWN_GAP

    # forgetting: average over topics with data
    forgetting_values = [tm.forgetting_risk for tm in student.topics.values() if tm.questions_attempted > 0]
    forgetting = _clamp(sum(forgetting_values) / len(forgetting_values)) if forgetting_values else 0.5

    # unfinished work (logged hours come from review_history)
    logged = len(student.review_history) * 0.5
    planned = 0.0
    unfinished = _clamp(max(0.0, planned - logged) / 2.0)

    # score gain opportunity: high target gap AND high risk AND time before exam
    score_gain = _clamp(target_gap * (0.5 + 0.5 * risk_signal) * (0.5 + 0.5 * urgency))

    # learning cost (normalized)
    total_cost = sum(float(p.get("learning_cost", 1.0) or 1.0) for p in exam_points)
    learning_cost_norm = _clamp(total_cost / max(1, len(exam_points) or 1) / 5.0) if exam_points else 0.3

    expected_gain = _clamp(
        0.30 * urgency
        + 0.25 * score_gain
        + 0.20 * risk_signal
        + 0.10 * mastery_gap
        + 0.05 * (1.0 - learning_cost_norm)
        + 0.10 * forgetting
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
        learning_cost_hours=learning_cost_norm * 5.0,
        forgetting_risk=forgetting,
        unfinished_work=unfinished,
        coverage=None,
        priority=priority,
    )


def allocate_hours_v4(
    signals: list[CourseSignal],
    total_hours: float,
    skip_courses: list[str],
    course_hours_override: dict[str, float] | None,
    locale: str,
) -> tuple[dict[str, float], list[str]]:
    """Anti-starvation allocation: minimum maintenance for every active course,
    cram boost for exam-close courses, user course-hour override wins."""
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

    urgent = {s.course_id for s in active if s.days_to_exam is not None and s.days_to_exam <= CRAM_DAYS}
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


def _topic_blocks_from_course_plan(course_plan: CoursePlan) -> list[StudyBlock]:
    return list(course_plan.blocks)


def generate_daily_plan_v4(
    workspace_root: Path,
    plan_date: str | None = None,
    *,
    total_hours_override: float | None = None,
    skip_courses: list[str] | None = None,
    target_score_changes: dict[str, int] | None = None,
    exam_date_changes: dict[str, str] | None = None,
    course_hours: dict[str, float] | None = None,
    persist: bool = True,
    locale: str | None = None,
) -> GlobalStudyPlan:
    """Formal Exam Week Orchestrator: topic-level global daily schedule across all
    courses, built from each course's adaptive plan. Never a mechanical average."""
    today = date.today()
    plan_date = plan_date or today.isoformat()
    try:
        target_date = datetime.fromisoformat(plan_date).date()
    except (TypeError, ValueError):
        target_date = today

    workspace = load_workspace_state(workspace_root)
    locale = locale or workspace.user_locale
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
    course_plans: dict[str, CoursePlan] = {}
    for cid in workspace.courses:
        course_path = course_dir(workspace_root, cid)
        if not (course_path / "course_manifest.json").exists():
            continue
        manifest = load_manifest(course_path)
        if manifest.status == "completed":
            continue  # exam over: release this course's time to others
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

        student = load_student_model(workspace_root, cid)
        topics = _load_topics(course_path)
        exam_points = _load_exam_points(course_path)
        wrongbook = _load_wrongbook(course_path)

        signals.append(
            build_course_signal_v4(
                manifest=manifest,
                entry_days=entry_days,
                student=student,
                topics=topics,
                exam_points=exam_points,
                wrongbook=wrongbook,
                today=target_date,
            )
        )

        # build the topic-level course plan
        course_plans[cid] = build_course_plan(
            workspace_root=workspace_root,
            course_id=cid,
            manifest=manifest,
            topics=_topics_objects(topics),
            exam_points=_exam_point_objects(exam_points),
            student=student,
            wrongbook_entries=wrongbook,
            days_left=entry_days,
            hours_available=total_hours,
            locale=locale,
        )

    allocation, notes = allocate_hours_v4(
        signals, total_hours, merged_skip, merged_course_hours or None, locale
    )
    blocks = _blocks_from_course_plans(
        signals,
        allocation,
        course_plans,
        manifests,
        locale,
    )
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


def _topics_objects(topics: list[dict]):
    from ..models import KnowledgeTopic, TopicField

    objects = []
    for raw in topics:
        defs = [TopicField(**{**d, "text": d.get("text", "")}) for d in raw.get("definitions", [])]
        formulas = [TopicField(**{**d, "text": d.get("text", "")}) for d in raw.get("formulas", [])]
        methods = [TopicField(**{**d, "text": d.get("text", "")}) for d in raw.get("methods", [])]
        mistakes = [TopicField(**{**d, "text": d.get("text", "")}) for d in raw.get("common_mistakes", [])]
        objects.append(
            KnowledgeTopic(
                topic_id=raw.get("topic_id", ""),
                canonical_name=raw.get("canonical_name", ""),
                localized_names=raw.get("localized_names", {}),
                aliases=raw.get("aliases", []),
                chapter=raw.get("chapter"),
                prerequisites=raw.get("prerequisites", []),
                definitions=defs,
                formulas=formulas,
                concepts=raw.get("concepts", []),
                methods=methods,
                common_mistakes=mistakes,
                question_types=raw.get("question_types", []),
                evidence=raw.get("evidence", []),
                teacher_emphasis=raw.get("teacher_emphasis", "unknown"),
                past_exam_links=raw.get("past_exam_links", []),
                fusion_confidence=raw.get("fusion_confidence", 0.3),
                source_confidence=raw.get("source_confidence", 0.3),
                inferred=raw.get("inferred", True),
            )
        )
    return objects


def _exam_point_objects(points: list[dict]):
    from ..models import ExamPointModel

    return [ExamPointModel(**p) for p in points]


def _blocks_from_course_plans(
    signals: list[CourseSignal],
    allocation: dict[str, float],
    course_plans: dict[str, CoursePlan],
    manifests: dict[str, CourseManifest],
    locale: str,
) -> list[PlanBlock]:
    """Slice each course's topic-level blocks into timed global blocks, ordered by
    course priority (urgent first), with a break between blocks. Not an average:
    allocation already reflects priority; this only lays out the timeline."""
    ordered = sorted(signals, key=lambda s: (-s.priority, s.course_id))
    blocks: list[PlanBlock] = []
    cursor = _parse_time(DAY_START)
    for signal in ordered:
        plan = course_plans.get(signal.course_id)
        if not plan or not plan.blocks:
            continue
        course_minutes = int(round(allocation.get(signal.course_id, 0.0) * 60))
        if course_minutes < 1:
            continue
        # distribute the course's allocated time across its topic blocks proportionally
        total_topic_hours = sum(b.duration_hours for b in plan.blocks)
        if total_topic_hours <= 0:
            continue
        for topic_block in plan.blocks:
            topic_minutes = int(round(course_minutes * (topic_block.duration_hours / total_topic_hours)))
            if topic_minutes < MIN_BLOCK_MINUTES:
                topic_minutes = MIN_BLOCK_MINUTES
            topic_minutes = min(topic_minutes, MAX_BLOCK_MINUTES)
            kind_label = t(locale, f"plan.kind.{topic_block.kind}") if topic_block.kind in {
                "study", "review", "practice", "cram", "maintenance", "diagnostic", "wrongbook",
            } else topic_block.kind
            blocks.append(
                PlanBlock(
                    block_id=f"B{len(blocks) + 1:03d}",
                    course_id=signal.course_id,
                    start=_hhmm(cursor),
                    end=_hhmm(cursor + topic_minutes),
                    kind=topic_block.kind,
                    why=topic_block.reason,
                    risk=f"{signal.risk_signal:.2f}",
                    goal=topic_block.task,
                    done_when=topic_block.completion_criterion,
                    source="planner",
                )
            )
            blocks[-1].topic_name = topic_block.topic_name
            blocks[-1].topic_id = topic_block.topic_id
            blocks[-1].practice = topic_block.practice
            cursor += topic_minutes + BREAK_MINUTES
    return blocks


def render_plan_v4(plan: GlobalStudyPlan, locale: str) -> str:
    """Render the formal topic-level global plan (zh/en)."""
    lines = [
        t(locale, "plan.title", date=plan.date, hours=_fmt(plan.total_hours)),
        "",
    ]
    for block in plan.blocks:
        kind_label = t(locale, f"plan.kind.{block.kind}") if block.kind in {
            "study", "review", "practice", "cram", "maintenance", "diagnostic", "wrongbook",
        } else block.kind
        topic_label = block.topic_name or block.course_id
        lines.append(
            t(
                locale,
                "plan.block.topic",
                course_id=block.course_id,
                topic_name=topic_label,
                kind_label=kind_label,
            )
        )
        lines.append("  " + t(locale, "plan.block.reason", reason=block.why))
        lines.append("  " + t(locale, "plan.block.task", task=block.goal))
        if block.practice:
            lines.append("  " + t(locale, "plan.block.practice", practice=block.practice))
        lines.append("  " + t(locale, "plan.block.criterion", criterion=block.done_when))
        lines.append("")
    if plan.notes:
        lines.append("---")
        lines.extend(f"- {note}" for note in plan.notes)
    if plan.overrides_applied:
        lines.append("---")
        lines.append("Overrides applied:")
        lines.extend(f"- {applied}" for applied in plan.overrides_applied)
    return "\n".join(lines)
