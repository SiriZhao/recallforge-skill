from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from .models import ReviewPlan, RiskItem, StudentState


def days_until(exam_date: str | None) -> int:
    if not exam_date:
        return 3
    try:
        return max(0, (datetime.fromisoformat(exam_date).date() - date.today()).days)
    except Exception:
        return 3


def choose_strategy(target_score: int, days_left: int) -> str:
    if days_left <= 0:
        return "考前一小时速救策略"
    if days_left <= 1:
        return "考前一天急救策略"
    if target_score < 80:
        return "及格保底策略"
    if target_score < 90:
        return "80分稳妥策略"
    return "90分冲刺策略"


def build_review_plan(state: StudentState, risks: list[RiskItem], days_left: int | None = None, daily_hours: float | None = None, target_score: int | None = None, output_dir: Path | None = None) -> ReviewPlan:
    dl = days_left if days_left is not None else days_until(state.exam_date)
    hours = daily_hours if daily_hours is not None else state.daily_hours
    score = target_score if target_score is not None else state.target_score
    strategy = choose_strategy(score, dl)
    total_days = max(1, dl)
    plan = ReviewPlan(state.course_name, score, state.exam_date, hours, strategy=strategy)
    top = risks[: max(3, min(len(risks), total_days * 3))]
    for d in range(1, total_days + 1):
        batch = top[(d - 1) * 3: d * 3] or top[:3]
        plan.days.append({
            "day": d,
            "hours": hours,
            "must_score": [r.topic_name for r in batch if r.priority in {"S", "A"}],
            "can_skip": [r.topic_name for r in risks if r.priority == "C"][:3],
            "tasks": [f"{r.topic_name}: {r.review_action}" for r in batch],
            "self_test": "闭卷写定义/公式/步骤，做 3 道专项题，错题立刻归因。",
        })
    if output_dir:
        (output_dir / "08_自适应复习计划.md").write_text(render_plan(plan), encoding="utf-8")
        (output_dir / "10_今日复习任务.md").write_text(render_daily_tasks(plan), encoding="utf-8")
    return plan


def render_plan(plan: ReviewPlan) -> str:
    lines = ["# 自适应复习计划", "", f"- 目标：{plan.target_score} 分", f"- 策略：{plan.strategy}", f"- 每日可用：{plan.daily_hours} 小时", ""]
    lines += ["## 策略说明", "- 及格：保定义、基础题、来源题。", "- 80分：S/A 考点全覆盖，B 级抽查。", "- 90分：增加变式、综合题、陷阱题。", "- 时间不足：压缩为抢分策略，放弃 C 级。", ""]
    for day in plan.days:
        lines.append(f"## Day {day['day']}")
        lines.append(f"- 时间：{day['hours']} 小时")
        lines.append(f"- 必须拿分：{', '.join(day['must_score']) or '基础概念'}")
        lines.append(f"- 可放弃：{', '.join(day['can_skip']) or '暂无'}")
        for task in day["tasks"]:
            lines.append(f"- {task}")
        lines.append(f"- 自测：{day['self_test']}")
        lines.append("")
    return "\n".join(lines)


def render_daily_tasks(plan: ReviewPlan) -> str:
    first = plan.days[0] if plan.days else {"tasks": [], "self_test": "完成自测"}
    lines = ["# 今日复习任务", "", f"策略：{plan.strategy}", ""]
    for task in first["tasks"]:
        lines.append(f"- {task}")
    lines.append(f"- 自测：{first['self_test']}")
    return "\n".join(lines)
