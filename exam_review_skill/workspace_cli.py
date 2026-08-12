from __future__ import annotations

import json
from pathlib import Path

from .i18n import TerminologyMap, t
from .models import DayOverride, to_dict
from .orchestrator.calendar import mark_completed, upsert_entry
from .orchestrator.scheduler import generate_daily_plan, render_plan
from .state import course as course_mod
from .state import workspace as workspace_mod


def _num(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def command_workspace(args) -> None:
    """v2 commands: workspace init / add-course / list / calendar / exam /
    override / term / plan."""
    root = Path(args.dir)
    action = args.action

    if action == "init":
        try:
            state = workspace_mod.create_workspace(
                root,
                user_locale=args.locale,
                content_language=args.content_language,
                output_language=args.output_language,
                daily_total_hours=args.daily_hours,
            )
        except FileExistsError:
            state = workspace_mod.load_workspace_state(root)
            print(t(state.user_locale, "workspace.init.exists", path=str(root)))
            return
        print(t(state.user_locale, "workspace.init.ok", path=str(root)))
        print(
            t(
                state.user_locale,
                "workspace.init.locale",
                ui_locale=state.user_locale,
                content_language=state.content_language,
                output_language=state.output_language,
            )
        )
        return

    if action == "add-course":
        state = workspace_mod.load_workspace_state(root)
        locale = state.user_locale
        localized: dict[str, str] = {}
        if getattr(args, "name_zh", None):
            localized["zh-CN"] = args.name_zh
        if getattr(args, "name_en", None):
            localized["en-US"] = args.name_en
        source_languages = getattr(args, "source_language", None) or []
        try:
            workspace_mod.add_course_to_workspace(
                root,
                course_id=args.course,
                course_name=args.name,
                course_name_localized=localized or None,
                source_languages=source_languages or None,
                exam_date=args.exam_date,
                exam_time=args.exam_time,
                target_score=args.target_score,
                current_estimated_score=args.estimated_score,
                daily_preference=args.daily_preference,
                importance_override=args.importance,
                status=args.status,
            )
        except (ValueError, FileExistsError) as exc:
            print(f"error: {exc}")
            return
        if args.exam_date:
            calendar = workspace_mod.load_exam_calendar(root)
            upsert_entry(
                calendar,
                course_id=args.course,
                exam_date=args.exam_date,
                exam_time=args.exam_time,
            )
            workspace_mod.save_exam_calendar(root, calendar)
        print(t(locale, "workspace.course.added", course_id=args.course, name=args.name))
        return

    if action == "list":
        state = workspace_mod.load_workspace_state(root)
        locale = state.user_locale
        print(
            t(
                locale,
                "workspace.list.title",
                workspace_id=state.workspace_id,
                ui_locale=locale,
                hours=_num(state.daily_total_hours),
            )
        )
        courses = workspace_mod.list_courses(root)
        if not courses:
            print(t(locale, "workspace.list.empty"))
            return
        for cid in courses:
            manifest = course_mod.load_manifest(course_mod.course_dir(root, cid))
            if manifest.exam_date:
                print(
                    t(
                        locale,
                        "workspace.list.course",
                        course_id=cid,
                        name=manifest.course_name,
                        exam_date=manifest.exam_date,
                        target=manifest.target_score,
                    )
                )
            else:
                print(
                    t(
                        locale,
                        "workspace.list.course.no_exam",
                        course_id=cid,
                        name=manifest.course_name,
                        target=manifest.target_score,
                    )
                )
        return

    if action == "calendar":
        state = workspace_mod.load_workspace_state(root)
        locale = state.user_locale
        calendar = workspace_mod.load_exam_calendar(root)
        print(t(locale, "workspace.calendar.title", workspace_id=state.workspace_id))
        if not calendar.entries:
            print(t(locale, "workspace.calendar.empty"))
            return
        for entry in calendar.entries:
            date_label = entry.exam_date or t(locale, "course.exam.unknown")
            if entry.exam_date:
                print(
                    t(
                        locale,
                        "workspace.calendar.entry",
                        course_id=entry.course_id,
                        date_label=date_label,
                        time_label=entry.exam_time or "",
                        status=t(locale, f"cal.status.{entry.status}"),
                        weight=_num(entry.weight),
                    )
                )
            else:
                print(
                    t(
                        locale,
                        "workspace.calendar.entry.no_date",
                        course_id=entry.course_id,
                        status=t(locale, f"cal.status.{entry.status}"),
                    )
                )
        return

    if action == "exam":
        state = workspace_mod.load_workspace_state(root)
        locale = state.user_locale
        calendar = workspace_mod.load_exam_calendar(root)
        if args.mark == "completed":
            mark_completed(calendar, args.course)
            date_label = t(locale, "course.exam.unknown")
        else:
            upsert_entry(
                calendar,
                course_id=args.course,
                exam_date=args.date,
                exam_time=args.time,
            )
            date_label = args.date or t(locale, "course.exam.unknown")
        workspace_mod.save_exam_calendar(root, calendar)
        print(
            t(
                locale,
                "workspace.exam.updated",
                course_id=args.course,
                date_label=date_label,
                time_label=args.time or "",
                status=t(locale, f"cal.status.{args.mark}"),
            )
        )
        return

    if action == "override":
        state = workspace_mod.load_workspace_state(root)
        locale = state.user_locale
        course_hours: dict[str, float] = {}
        for pair in getattr(args, "course_hours", None) or []:
            cid, hours = pair.split(":", 1)
            course_hours[cid] = float(hours)
        targets: dict[str, int] = {}
        for pair in getattr(args, "target", None) or []:
            cid, score = pair.split(":", 1)
            targets[cid] = int(score)
        date_changes: dict[str, str] = {}
        for pair in getattr(args, "exam_date", None) or []:
            cid, value = pair.split(":", 1)
            date_changes[cid] = value
        override = DayOverride(
            date=args.date,
            skip_courses=getattr(args, "skip", None) or [],
            total_hours=args.hours,
            course_hours=course_hours,
            target_scores=targets,
            exam_date_changes=date_changes,
            note=args.note,
        )
        workspace_mod.upsert_override(root, override)
        print(t(locale, "workspace.override.saved", date=args.date))
        print(
            t(
                locale,
                "workspace.override.detail",
                skip=", ".join(override.skip_courses) or t(locale, "common.none"),
                hours=_num(override.total_hours) if override.total_hours is not None else t(locale, "common.none"),
                course_hours=", ".join(f"{k}:{v}" for k, v in course_hours.items()) or t(locale, "common.none"),
                targets=", ".join(f"{k}:{v}" for k, v in targets.items()) or t(locale, "common.none"),
            )
        )
        return

    if action == "term":
        state = workspace_mod.load_workspace_state(root)
        locale = state.user_locale
        course_path = course_mod.course_dir(root, args.course)
        data = course_mod.load_course_json(course_path, "terminology_map.json", {}) or {}
        term_map = TerminologyMap.from_state(data)
        term_map.add(
            args.key,
            zh=args.zh,
            en=args.en,
            aliases=getattr(args, "alias", None),
        )
        course_mod._write_json(course_path / "terminology_map.json", term_map.to_state())
        print(
            t(
                locale,
                "workspace.term.added",
                course_id=args.course,
                term_key=args.key,
                zh=args.zh or "",
                en=args.en or "",
            )
        )
        return

    if action == "plan":
        state = workspace_mod.load_workspace_state(root)
        locale = state.user_locale
        plan = generate_daily_plan(
            root,
            args.date,
            total_hours_override=args.hours,
            skip_courses=getattr(args, "skip", None) or None,
        )
        print(render_plan(plan, locale))
        if args.json:
            print(json.dumps(to_dict(plan), ensure_ascii=False, indent=2))
        return

    raise SystemExit(f"unknown workspace action: {action}")


def add_workspace_parser(subparsers) -> None:
    """Register the v2 'workspace' command tree on the top-level subparsers."""
    ws = subparsers.add_parser("workspace", help="v2 multi-course workspace management")
    ws_sub = ws.add_subparsers(dest="action", required=True)

    init = ws_sub.add_parser("init", help="create a new exam-week workspace")
    init.add_argument("--dir", required=True)
    init.add_argument("--locale", default="zh-CN", choices=["zh-CN", "en-US"])
    init.add_argument("--content-language", default="auto")
    init.add_argument("--output-language", default=None)
    init.add_argument("--daily-hours", type=float, default=6.0)
    init.set_defaults(func=command_workspace)

    add = ws_sub.add_parser("add-course", help="add a course with its isolated state")
    add.add_argument("--dir", required=True)
    add.add_argument("--course", required=True, help="stable id, e.g. organic-chemistry")
    add.add_argument("--name", required=True)
    add.add_argument("--name-zh", default=None)
    add.add_argument("--name-en", default=None)
    add.add_argument("--source-language", action="append", default=None)
    add.add_argument("--exam-date", default=None)
    add.add_argument("--exam-time", default=None)
    add.add_argument("--target-score", type=int, default=80)
    add.add_argument("--estimated-score", type=int, default=None)
    add.add_argument("--daily-preference", type=float, default=1.0)
    add.add_argument("--importance", type=float, default=None)
    add.add_argument("--status", default="active")
    add.set_defaults(func=command_workspace)

    list_ = ws_sub.add_parser("list", help="list courses in the workspace")
    list_.add_argument("--dir", required=True)
    list_.set_defaults(func=command_workspace)

    cal = ws_sub.add_parser("calendar", help="show the global exam calendar")
    cal.add_argument("--dir", required=True)
    cal.set_defaults(func=command_workspace)

    exam = ws_sub.add_parser("exam", help="set or update a course exam")
    exam.add_argument("--dir", required=True)
    exam.add_argument("--course", required=True)
    exam.add_argument("--date", default=None)
    exam.add_argument("--time", default=None)
    exam.add_argument("--mark", choices=["scheduled", "completed", "canceled"], default="scheduled")
    exam.set_defaults(func=command_workspace)

    override = ws_sub.add_parser("override", help="store a per-date user override")
    override.add_argument("--dir", required=True)
    override.add_argument("--date", required=True)
    override.add_argument("--skip", action="append", default=None)
    override.add_argument("--hours", type=float, default=None)
    override.add_argument("--course-hours", action="append", default=None, help="course:hours")
    override.add_argument("--target", action="append", default=None, help="course:score")
    override.add_argument("--exam-date", action="append", default=None, help="course:new-date")
    override.add_argument("--note", default=None)
    override.set_defaults(func=command_workspace)

    term = ws_sub.add_parser("term", help="add a terminology entry to a course")
    term.add_argument("--dir", required=True)
    term.add_argument("--course", required=True)
    term.add_argument("--key", required=True)
    term.add_argument("--zh", default=None)
    term.add_argument("--en", default=None)
    term.add_argument("--alias", action="append", default=None)
    term.set_defaults(func=command_workspace)

    plan = ws_sub.add_parser("plan", help="generate the global daily study plan")
    plan.add_argument("--dir", required=True)
    plan.add_argument("--date", default=None)
    plan.add_argument("--hours", type=float, default=None)
    plan.add_argument("--skip", action="append", default=None)
    plan.add_argument("--json", action="store_true")
    plan.set_defaults(func=command_workspace)
