from __future__ import annotations

"""Locale catalog registry.

Extensible by design: any locale can be registered at runtime via `register_locale`.
Lookups fail closed - an unknown key returns the key itself rather than crashing,
so a missing translation never breaks the planner.
"""


ZH_CN_CATALOG: dict[str, str] = {
    # workspace
    "workspace.init.ok": "工作区已创建：{path}",
    "workspace.init.exists": "工作区已存在：{path}",
    "workspace.init.locale": "UI 语言：{ui_locale}；源语言：{content_language}；输出语言：{output_language}",
    "workspace.course.added": "已添加课程 {course_id}（{name}）",
    "workspace.course.exists": "课程已存在：{course_id}",
    "workspace.list.title": "考试周工作区 {workspace_id}｜UI {ui_locale}｜每日 {hours} 小时",
    "workspace.list.course": "- {course_id}：{name}｜考试 {exam_date}｜目标 {target} 分",
    "workspace.list.course.no_exam": "- {course_id}：{name}｜考试未定｜目标 {target} 分",
    "workspace.list.empty": "尚无课程。使用 workspace add-course 添加。",
    "workspace.calendar.title": "考试日历（{workspace_id}）",
    "workspace.calendar.entry": "- {course_id}｜{date_label} {time_label}｜[{status}]｜权重 {weight}",
    "workspace.calendar.entry.no_date": "- {course_id}｜无考试日期｜[{status}]",
    "workspace.calendar.empty": "日历为空。",
    "workspace.exam.updated": "已更新 {course_id} 考试：{date_label} {time_label} [{status}]",
    "workspace.override.saved": "已保存 {date} 的覆盖规则。",
    "workspace.override.detail": "  跳过：{skip}；总时长：{hours}；课程时长：{course_hours}；目标分：{targets}",
    "workspace.term.added": "已向 {course_id} 术语表添加 {term_key}：zh={zh} en={en}",
    "course.exam.unknown": "未定",
    "common.none": "无",
    "common.empty": "（空）",
    # calendar status
    "cal.status.scheduled": "待考",
    "cal.status.completed": "已完成",
    "cal.status.canceled": "已取消",
    # plan
    "plan.title": "全局每日计划 {date}（共 {hours} 小时）",
    "plan.block.line": "{start}–{end} {course_id} [{kind_label}]",
    "plan.block.why": "为什么：{why}",
    "plan.block.risk": "风险：{risk}",
    "plan.block.goal": "目标：{goal}",
    "plan.block.done": "结束标准：{done_when}",
    "plan.why.urgency": "距离考试 {days} 天，紧迫度 {urgency}（启发式 1/(天+1)）",
    "plan.why.no_date": "暂无考试日期，紧迫度 {urgency}（最低维护档）",
    "plan.why.gap": "目标 {target} 分，当前 {current} 分，目标差 {gap}",
    "plan.why.gap_unknown": "尚无真实估分，目标差按 {gap}（未知）处理",
    "plan.why.gain": "综合增益 {gain}",
    "plan.risk.sa": "风险信号 {risk}（S/A 占比）",
    "plan.risk.default": "风险信号 {risk}（暂无考试模型，取默认 0.5）",
    "plan.goal": "覆盖 {topics} 个考点核心内容",
    "plan.done": "完成自测，正确率 ≥ {rate}%",
    "plan.note.maintenance": "防止课程挨饿：{course} 保留最低 {min_hours} 小时 spaced review（当日分配 {hours} 小时）",
    "plan.note.skip": "用户跳过：{course}",
    "plan.note.none": "没有可排课的课程。",
    "plan.kind.study": "学习",
    "plan.kind.review": "复习",
    "plan.kind.practice": "练习",
    "plan.kind.cram": "冲刺",
    "plan.kind.maintenance": "维护",
    "plan.kind.wrongbook": "错题",
    "plan.kind.diagnostic": "诊断",
    # terminology / mixed-language
    "term.normalized": "已归一化 {original} → {canonical}",
    # diagnostic
    "diag.none": "暂无主题，无法生成诊断测试。",
    "diag.coverage": "已按知识图谱覆盖度选择 {selected}/{topics} 个主题。",
    "diag.rule": "每题约 {minutes} 分钟，共 10–20 分钟。",
    "diag.reason.unknown": "尚无答题数据，需要基线估计",
    "diag.reason.weak": "掌握度偏低/发展中，需复核",
    "diag.reason.verify": "验证迁移与遗忘风险",
    # planner
    "plan.block.topic": "{course_id} · {topic_name} [{kind_label}]",
    "plan.block.task": "任务：{task}",
    "plan.block.practice": "练习：{practice}",
    "plan.block.criterion": "完成标准：{criterion}",
    "plan.block.reason": "原因：{reason}",
    "plan.reason.urgency": "距离考试 {days} 天，紧迫度 {urgency}",
    "plan.reason.gap": "目标 {target} 分 / 当前 {current} 分，差距 {gap}",
    "plan.reason.gap_unknown": "暂无真实估分，差距按未知处理",
    "plan.reason.risk": "风险 {risk}",
    "plan.reason.mastery": "掌握度 {mastery}，遗忘风险 {forgetting}",
    "plan.reason.wrongbook": "错题本 {count} 题需重练",
    "plan.reason.coverage": "真题覆盖 {coverage}",
    "plan.reason.maintenance": "最低维护：{hours} 小时 spaced review",
    "plan.none": "课程 {course} 暂无主题，无法规划。",
    "plan.strategy": "策略：{strategy}，可用 {hours} 小时。",
}


EN_US_CATALOG: dict[str, str] = {
    "workspace.init.ok": "Workspace created: {path}",
    "workspace.init.exists": "Workspace already exists: {path}",
    "workspace.init.locale": "UI locale: {ui_locale}; source language: {content_language}; output language: {output_language}",
    "workspace.course.added": "Course added: {course_id} ({name})",
    "workspace.course.exists": "Course already exists: {course_id}",
    "workspace.list.title": "Exam-week workspace {workspace_id} | UI {ui_locale} | {hours} hours/day",
    "workspace.list.course": "- {course_id}: {name} | exam {exam_date} | target {target}",
    "workspace.list.course.no_exam": "- {course_id}: {name} | exam TBD | target {target}",
    "workspace.list.empty": "No courses yet. Use workspace add-course.",
    "workspace.calendar.title": "Exam calendar ({workspace_id})",
    "workspace.calendar.entry": "- {course_id} | {date_label} {time_label} | [{status}] | weight {weight}",
    "workspace.calendar.entry.no_date": "- {course_id} | no exam date | [{status}]",
    "workspace.calendar.empty": "Calendar is empty.",
    "workspace.exam.updated": "Updated {course_id} exam: {date_label} {time_label} [{status}]",
    "workspace.override.saved": "Saved overrides for {date}.",
    "workspace.override.detail": "  skip: {skip}; total hours: {hours}; course hours: {course_hours}; targets: {targets}",
    "workspace.term.added": "Added {term_key} to {course_id} terminology: zh={zh} en={en}",
    "course.exam.unknown": "TBD",
    "common.none": "none",
    "common.empty": "(empty)",
    "cal.status.scheduled": "scheduled",
    "cal.status.completed": "completed",
    "cal.status.canceled": "canceled",
    "plan.title": "Global daily plan {date} ({hours} hours total)",
    "plan.block.line": "{start}–{end} {course_id} [{kind_label}]",
    "plan.block.why": "Why: {why}",
    "plan.block.risk": "Risk: {risk}",
    "plan.block.goal": "Goal: {goal}",
    "plan.block.done": "Done when: {done_when}",
    "plan.why.urgency": "{days} days to exam, urgency {urgency} (heuristic 1/(days+1))",
    "plan.why.no_date": "No exam date yet, urgency {urgency} (minimum-maintenance tier)",
    "plan.why.gap": "target {target}, current {current}, gap {gap}",
    "plan.why.gap_unknown": "no real score estimate yet, gap treated as {gap} (unknown)",
    "plan.why.gain": "expected gain {gain}",
    "plan.risk.sa": "risk signal {risk} (S/A share)",
    "plan.risk.default": "risk signal {risk} (no exam model yet, default 0.5)",
    "plan.goal": "cover core content of {topics} exam points",
    "plan.done": "pass self-test with accuracy >= {rate}%",
    "plan.note.maintenance": "anti-starvation: {course} keeps a minimum of {min_hours} hours spaced review (allocated {hours} hours today)",
    "plan.note.skip": "user skipped: {course}",
    "plan.note.none": "No courses available to schedule.",
    "plan.kind.study": "Study",
    "plan.kind.review": "Review",
    "plan.kind.practice": "Practice",
    "plan.kind.cram": "Cram",
    "plan.kind.maintenance": "Maintenance",
    "plan.kind.wrongbook": "Wrongbook",
    "plan.kind.diagnostic": "Diagnostic",
    "term.normalized": "normalized {original} -> {canonical}",
    # diagnostic
    "diag.none": "No topics; cannot build a diagnostic test.",
    "diag.coverage": "Selected {selected}/{topics} topics by graph coverage.",
    "diag.rule": "About {minutes} minutes per item, 10-20 min total.",
    "diag.reason.unknown": "no answer data, baseline estimate needed",
    "diag.reason.weak": "low/developing mastery, needs re-check",
    "diag.reason.verify": "verify transfer and forgetting risk",
    # planner
    "plan.block.topic": "{course_id} · {topic_name} [{kind_label}]",
    "plan.block.task": "Task: {task}",
    "plan.block.practice": "Practice: {practice}",
    "plan.block.criterion": "Done when: {criterion}",
    "plan.block.reason": "Why: {reason}",
    "plan.reason.urgency": "{days} days to exam, urgency {urgency}",
    "plan.reason.gap": "target {target} / current {current}, gap {gap}",
    "plan.reason.gap_unknown": "no real score estimate, gap treated as unknown",
    "plan.reason.risk": "risk {risk}",
    "plan.reason.mastery": "mastery {mastery}, forgetting {forgetting}",
    "plan.reason.wrongbook": "{count} wrongbook items to redo",
    "plan.reason.coverage": "past-exam coverage {coverage}",
    "plan.reason.maintenance": "minimum maintenance: {hours} hours spaced review",
    "plan.none": "Course {course} has no topics; cannot plan.",
    "plan.strategy": "Strategy: {strategy}, {hours} hours available.",
}


_CATALOGS: dict[str, dict[str, str]] = {
    "zh-CN": ZH_CN_CATALOG,
    "en-US": EN_US_CATALOG,
}

SUPPORTED_LOCALES = tuple(sorted(_CATALOGS))


def register_locale(locale: str, catalog: dict[str, str]) -> None:
    """Register (or replace) a locale catalog at runtime. Keeps the system extensible."""
    if not locale or not isinstance(catalog, dict):
        raise ValueError("locale and catalog are required")
    _CATALOGS[locale] = dict(catalog)


def get_catalog(locale: str) -> dict[str, str]:
    """Return the catalog for a locale; falls back to en-US for unknown locales."""
    if locale in _CATALOGS:
        return _CATALOGS[locale]
    if locale.split("-")[0] in {c.split("-")[0] for c in _CATALOGS}:
        # language-level fallback (e.g. zh-TW -> zh-CN) keeps basic lookups working
        lang = locale.split("-")[0]
        for cand in _CATALOGS:
            if cand.startswith(lang + "-"):
                return _CATALOGS[cand]
    return _CATALOGS["en-US"]


def t(locale: str, key: str, **fmt) -> str:
    """Translate a catalog key with {name} formatting; fail closed to the key itself."""
    template = get_catalog(locale).get(key, key)
    if not fmt:
        return template
    try:
        return template.format(**fmt)
    except (KeyError, IndexError, ValueError):
        return template
