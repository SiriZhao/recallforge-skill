from __future__ import annotations

from pathlib import Path

from .models import RiskItem, StudentState
from .state_manager import save_student_state


def diagnose_mastery(state: StudentState, risks: list[RiskItem], output_dir: Path | None = None) -> StudentState:
    if not state.topic_mastery:
        for r in risks:
            state.topic_mastery[r.exam_point_id] = "unknown"
        state.weak_points = [r.topic_name for r in risks if r.priority in {"S", "A"}][:8]
        state.next_actions = ["先处理 S 级考点", "用专项训练题暴露薄弱点", "把错题加入 wrongbook 后生成变式"]
    if output_dir:
        (output_dir / "09_个人薄弱点诊断.md").write_text(render_diagnosis(state, risks), encoding="utf-8")
        save_student_state(output_dir / "student_state.json", state)
    return state


def render_diagnosis(state: StudentState, risks: list[RiskItem]) -> str:
    lines = ["# 个人薄弱点诊断", "", "没有真实答题数据时，本报告不会假装知道掌握度；默认标记为 unknown/estimated。", ""]
    lines.append("## 最危险薄弱点")
    for r in risks[:8]:
        lines.append(f"- {r.priority} {r.topic_name}：掌握度 {r.current_mastery}；补救动作：{r.review_action}")
    lines += ["", "## 下一步训练建议", "- 先做 S 级专项训练题。", "- 错题写明错因分类，再生成错题变式。", "- 临考前只看急救包和来源题。"]
    return "\n".join(lines)
