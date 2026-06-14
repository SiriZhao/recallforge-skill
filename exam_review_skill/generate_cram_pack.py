from __future__ import annotations

from pathlib import Path

from .models import RiskItem, StudentState


def generate_cram_pack(state: StudentState, risks: list[RiskItem], output_dir: Path, hours_left: float | None = None) -> list[Path]:
    main = output_dir / "13_临考急救包.md"
    short = output_dir / "15_考前30分钟速救版.md"
    main.write_text(render_cram(state, risks, hours_left), encoding="utf-8")
    short.write_text(render_30min(risks), encoding="utf-8")
    return [main, short]


def _section(name: str, risks: list[RiskItem], limit: int) -> list[str]:
    top = risks[:limit]
    return [
        f"## {name}",
        f"- 必看内容：{', '.join(r.topic_name for r in top) or 'S/A 考点'}",
        f"- 可放弃内容：{', '.join(r.topic_name for r in risks if r.priority == 'C') or '无明确 C 级'}",
        "- 必背定义：每个必看考点写一句定义 + 条件。",
        "- 必会公式：只背来源中出现且和计算题相关的公式。",
        "- 必刷题型：来源题、S级变式、错题变式。",
        "- 最容易捡分点：定义题、步骤题、单位/有效数字检查。",
        "- 最容易丢分点：条件漏看、实验误差漏写、计算步骤跳步。",
        "- 考场答题策略：先拿会做的基础分，再处理综合题；不会时写定义和步骤争取过程分。",
        "- 最后复习顺序：S -> A -> 错题 -> 30分钟速背。",
        "",
    ]


def render_cram(state: StudentState, risks: list[RiskItem], hours_left: float | None) -> str:
    lines = ["# 临考急救包", "", f"课程：{state.course_name}", f"剩余时间：{hours_left if hours_left is not None else '自动按多版本'} 小时", ""]
    for name, limit in [("3天冲刺版", 8), ("1天急救版", 6), ("3小时版", 4), ("1小时版", 3), ("30分钟版", 2), ("10分钟版", 1)]:
        lines.extend(_section(name, risks, limit))
    return "\n".join(lines)


def render_30min(risks: list[RiskItem]) -> str:
    lines = ["# 考前30分钟速救版", ""]
    for i, r in enumerate(risks[:5], 1):
        lines.append(f"{i}. {r.topic_name}：背定义/公式条件；陷阱：{'; '.join(r.traps[:2])}; 来源：{'; '.join(s.get('source_file','') for s in r.source_refs[:2]) or '需人工确认'}")
    lines += ["", "最后 5 分钟：只看错题本标题、单位、有效数字、实验误差关键词。"]
    return "\n".join(lines)
