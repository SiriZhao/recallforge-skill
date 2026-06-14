from __future__ import annotations

from pathlib import Path

from .models import Chunk, ExamPoint


def generate_variants(chunks: list[Chunk], points: list[ExamPoint], output_dir: Path, count: int = 20) -> list[Path]:
    mapping = output_dir / "06_往年题考点映射表.md"
    variants = output_dir / "07_真题变式训练.md"
    mapping.write_text(render_mapping(chunks, points), encoding="utf-8")
    variants.write_text(render_variants(points, count), encoding="utf-8")
    return [mapping, variants]


def render_mapping(chunks: list[Chunk], points: list[ExamPoint]) -> str:
    past = [c for c in chunks if c.doc_type == "past_exam" or c.question_number]
    lines = ["# 往年题考点映射表", "", "|原题编号|原题考点|对应章节|标准解法|命题意图|来源|", "|---|---|---|---|---|---|"]
    if not past:
        lines.append("|需人工确认|未发现往年题|未标注|补充往年题后生成|当前无法确认|无|")
    for c in past:
        point = next((p for p in points if p.topic_name in c.content), points[0] if points else None)
        lines.append(f"|{c.question_number or c.chunk_id}|{point.topic_name if point else '需人工确认'}|{c.chapter or '未标注'}|先定位概念/公式，再按题型模板作答|考查来源材料中的核心概念和迁移|{c.source_file}|")
    return "\n".join(lines)


def render_variants(points: list[ExamPoint], count: int) -> str:
    lines = ["# 真题变式训练", "", "变式均基于已提取考点；来源不足处标记为需人工确认。", ""]
    pool = points or []
    for i in range(count):
        p = pool[i % len(pool)] if pool else None
        name = p.topic_name if p else "需人工确认考点"
        src = "; ".join(r.get("source_file", "") for r in (p.source_refs if p else [])[:2]) or "需人工确认"
        lines += [
            f"## 变式 {i+1}: {name}",
            f"- 原题编号：{(p.past_exam_refs[0].get('question_number') if p and p.past_exam_refs else '需人工确认')}",
            f"- 原题考点：{name}",
            f"- 对应章节：需结合来源确认",
            "- 标准解法：定义/公式/步骤/单位/结论五段式。",
            f"- 命题意图：检查是否真正理解 {name}，而不是只背关键词。",
            f"- 可能变式 1：改变实验条件后判断 {name} 是否仍适用。",
            f"- 可能变式 2：给出错误步骤，要求指出陷阱。",
            f"- 可能变式 3：把概念放入新题干做简答或选择。",
            "- 难度升级版：加入干扰条件或多步骤计算。",
            "- 易错陷阱版：隐藏单位、有效数字或前提条件。",
            "- 临考提醒：先写来源材料中的关键词，再补解释。",
            f"- 来源引用：{src}",
            "",
        ]
    return "\n".join(lines)
