from __future__ import annotations

from pathlib import Path

from .llm_provider import BaseLLMProvider, MockLLMProvider
from .models import Question, RiskItem
from .state_manager import write_json


def generate_quiz(risks: list[RiskItem], exam_points: list[dict], output_dir: Path, mode: str = "s-priority", count: int = 20, provider: BaseLLMProvider | None = None) -> list[Question]:
    provider = provider or MockLLMProvider()
    selected_ids = {r.exam_point_id for r in risks if mode != "s-priority" or r.priority == "S"}
    pool = [p for p in exam_points if not selected_ids or p.get("exam_point_id") in selected_ids] or exam_points
    qdicts = provider.generate_questions(pool, count=count, mode=mode)
    questions = [Question(**q) for q in qdicts]
    if mode == "mock-exam":
        (output_dir / "10_模拟卷.md").write_text(render_quiz(questions, "模拟卷"), encoding="utf-8")
        (output_dir / "11_模拟卷答案解析.md").write_text(render_answers(questions), encoding="utf-8")
    else:
        (output_dir / "11_专项训练题.md").write_text(render_quiz(questions, "专项训练题"), encoding="utf-8")
    return questions


def render_quiz(questions: list[Question], title: str) -> str:
    lines = [f"# {title}", ""]
    for q in questions:
        src = "; ".join(r.get("source_file", "") for r in q.source_refs[:2]) or "需人工确认"
        lines += [f"## {q.question_id}", q.question_text, f"- 类型：{q.question_type}", f"- 难度：{q.difficulty}", f"- 来源：{src}", ""]
    lines += ["# 答案与解析", ""]
    for q in questions:
        lines += [f"## {q.question_id}", f"- 答案：{q.answer}", f"- 解析：{q.explanation}", f"- 常见陷阱：{q.common_trap}", ""]
    return "\n".join(lines)


def render_answers(questions: list[Question]) -> str:
    return "\n".join(["# 模拟卷答案解析", ""] + [f"## {q.question_id}\n- 答案：{q.answer}\n- 解析：{q.explanation}\n" for q in questions])
