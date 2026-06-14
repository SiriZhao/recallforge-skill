from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from .models import ExamPoint, RiskItem, StudentState
from .state_manager import write_json


def calculate_priority(score: float) -> str:
    if score >= 8:
        return "S"
    if score >= 6:
        return "A"
    if score >= 4:
        return "B"
    return "C"


def build_risk_radar(points: list[ExamPoint], state: StudentState | None = None, days_left: int | None = None, output_dir: Path | None = None) -> list[RiskItem]:
    items: list[RiskItem] = []
    mastery = (state.topic_mastery if state else {}) or {}
    time_pressure = 1.2 if days_left is not None and days_left <= 3 else 1.0
    for p in points:
        m = mastery.get(p.topic_id, "unknown")
        mastery_penalty = 1.5 if m in {"unknown", "estimated", None} else max(0, 1 - float(m)) if isinstance(m, (int, float)) else 1
        score = (p.frequency * 1.2 + p.score_potential * 0.9 + p.difficulty * 0.7 + mastery_penalty) * time_pressure
        pri = calculate_priority(score)
        items.append(RiskItem(
            exam_point_id=p.exam_point_id,
            topic_name=p.topic_name,
            exam_probability=min(0.95, 0.25 + p.frequency * 0.12),
            score_potential=p.score_potential,
            difficulty=p.difficulty,
            current_mastery=str(m),
            traps=p.common_traps,
            priority=pri,
            review_action=_action(pri, p),
            source_refs=p.source_refs,
            rationale=f"频率{p.frequency}、分值{p.score_potential}、难度{p.difficulty}、掌握度{m}、时间压力{time_pressure} 综合得分 {score:.1f}。",
        ))
    items.sort(key=lambda x: {"S": 0, "A": 1, "B": 2, "C": 3}[x.priority])
    if output_dir:
        write_json(output_dir / "risk_radar.json", [asdict(i) for i in items])
        (output_dir / "03_考试风险雷达.md").write_text(render_risk_radar(items), encoding="utf-8")
    return items


def _action(priority: str, p: ExamPoint) -> str:
    if priority == "S":
        return "先背定义/公式，再刷来源题和 2 道变式，最后复述陷阱。"
    if priority == "A":
        return "完成模板题和错因检查，确保可稳定拿基础分。"
    if priority == "B":
        return "按章节快速过一遍，保留自测。"
    return "时间不足时可暂缓，只看 30 分钟速背版。"


def render_risk_radar(items: list[RiskItem]) -> str:
    lines = ["# 考试风险雷达", "", "|优先级|考点|考试概率|分值潜力|难度|掌握度|推荐动作|来源|排序理由|", "|---|---|---:|---:|---:|---|---|---|---|"]
    for i in items:
        src = "; ".join(r.get("source_file", "") for r in i.source_refs[:2]) or "需人工确认"
        lines.append(f"|{i.priority}|{i.topic_name}|{i.exam_probability:.0%}|{i.score_potential}|{i.difficulty}|{i.current_mastery}|{i.review_action}|{src}|{i.rationale}|")
    return "\n".join(lines)
