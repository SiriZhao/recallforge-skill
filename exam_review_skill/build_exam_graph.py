from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from .models import Chunk, ExamPoint, Topic
from .state_manager import write_json


def build_exam_graph(topics: list[Topic], chunks: list[Chunk], output_dir: Path | None = None) -> list[ExamPoint]:
    points: list[ExamPoint] = []
    for topic in topics:
        related = [c for c in chunks if c.chunk_id in topic.source_chunks or topic.topic_name in c.content]
        past = [c for c in related if c.doc_type == "past_exam" or c.question_number]
        teacher = [c for c in related if any(k in c.content for k in ["重点", "必考", "老师", "容易考"])]
        forms = []
        if any("计算" in c.content or "=" in c.content for c in related):
            forms.append("计算题")
        if any("简答" in c.content or "定义" in c.content for c in related):
            forms.append("简答题")
        if any("选择" in c.content for c in related):
            forms.append("选择题")
        if not forms:
            forms = ["概念辨析题"]
        frequency = len(past) + len(teacher) + max(1, len(related) // 2)
        confidence = 0.85 if past or teacher else 0.55
        points.append(ExamPoint(
            exam_point_id=f"EP{len(points)+1:03d}",
            topic_id=topic.topic_id,
            topic_name=topic.topic_name,
            exam_forms=forms,
            past_exam_refs=[r for c in past for r in c.source_refs],
            frequency=frequency,
            difficulty=topic.difficulty,
            score_potential=5 if "计算题" in forms else 3,
            common_traps=["忽略适用条件", "步骤不完整", "单位或有效数字错误"] if "计算题" in forms else ["只背关键词，不会解释"],
            possible_variants=[f"把 {topic.topic_name} 放入新实验情境考察", f"比较 {topic.topic_name} 与相邻概念"],
            priority="A" if frequency >= 3 else "B",
            confidence=confidence,
            source_refs=topic.source_refs,
        ))
    if output_dir:
        write_json(output_dir / "exam_graph.json", [asdict(p) for p in points])
        (output_dir / "02_考试考点图谱.md").write_text(render_exam_graph(points), encoding="utf-8")
    return points


def render_exam_graph(points: list[ExamPoint]) -> str:
    lines = ["# 考试考点图谱", ""]
    for p in points:
        src = "; ".join(r.get("source_file", "") for r in p.source_refs[:3]) or "需人工确认"
        lines += [
            f"## {p.exam_point_id} {p.topic_name}",
            f"- 可能题型：{', '.join(p.exam_forms)}",
            f"- 出现频率：{p.frequency}",
            f"- 分值潜力：{p.score_potential}",
            f"- 这个点可能怎么考：{'; '.join(p.possible_variants)}",
            f"- 常见陷阱：{'; '.join(p.common_traps)}",
            f"- 置信度：{p.confidence:.2f}",
            f"- 来源：{src}",
            "",
        ]
    return "\n".join(lines)
