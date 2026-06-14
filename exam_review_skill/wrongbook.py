from __future__ import annotations

from dataclasses import asdict
from datetime import date, timedelta
from pathlib import Path

from .models import Question, WrongQuestion
from .state_manager import write_json

REASONS = ["概念不清", "公式记错", "条件漏看", "单位错误", "审题错误", "步骤缺失", "计算错误", "背诵不熟", "不会迁移"]


def build_wrongbook(existing: list[dict] | None, questions: list[Question], output_dir: Path) -> list[WrongQuestion]:
    wrongs = [WrongQuestion(**w) for w in (existing or []) if isinstance(w, dict)]
    if not wrongs and questions:
        q = questions[0]
        wrongs.append(WrongQuestion(
            question_id=q.question_id,
            question_text=q.question_text,
            user_answer="示例：未作答",
            correct_answer=q.answer,
            topic_id=q.topic_id,
            exam_point_id=q.exam_point_id,
            wrong_reason="需答题后确认",
            trap_type="不会迁移",
            fix_strategy="回到来源材料，重写定义、条件和标准步骤，再做 2 道变式。",
            next_review_date=(date.today() + timedelta(days=1)).isoformat(),
            variant_questions=[f"变式：换一个题干情境重新考 {q.topic_id}。"],
        ))
    write_json(output_dir / "wrongbook.json", [asdict(w) for w in wrongs])
    (output_dir / "12_错题本.md").write_text(render_wrongbook(wrongs), encoding="utf-8")
    return wrongs


def render_wrongbook(wrongs: list[WrongQuestion]) -> str:
    lines = ["# 错题本", "", f"错误原因分类：{', '.join(REASONS)}", ""]
    if not wrongs:
        lines.append("暂无错题。完成专项训练后，把错题追加到 wrongbook.json。")
    for w in wrongs:
        lines += [
            f"## {w.question_id}",
            f"- 题干：{w.question_text}",
            f"- 你的答案：{w.user_answer}",
            f"- 正确答案：{w.correct_answer}",
            f"- 错因：{w.wrong_reason}",
            f"- 陷阱类型：{w.trap_type}",
            f"- 修复策略：{w.fix_strategy}",
            f"- 下次复习：{w.next_review_date}",
            f"- 变式：{'; '.join(w.variant_questions)}",
            "",
        ]
    return "\n".join(lines)
