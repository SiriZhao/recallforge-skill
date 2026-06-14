from __future__ import annotations

import re
from dataclasses import asdict
from pathlib import Path

from .models import Chunk, Topic
from .state_manager import write_json


def build_course_index(chunks: list[Chunk], output_dir: Path | None = None) -> list[Topic]:
    topic_map: dict[str, Topic] = {}
    for ch in chunks:
        candidates = ch.possible_exam_points + ch.keywords[:3]
        for name in candidates:
            clean = re.sub(r"\s+", " ", name).strip(" ：:。")
            if not clean or len(clean) < 2:
                continue
            key = clean.lower()
            if key not in topic_map:
                topic_map[key] = Topic(
                    topic_id=f"T{len(topic_map)+1:03d}",
                    topic_name=clean[:40],
                    chapter=ch.chapter,
                    source_chunks=[ch.chunk_id],
                    definitions=[],
                    formulas=[],
                    examples=[],
                    difficulty=3 if any(k in ch.content for k in ["计算", "公式", "="]) else 2,
                    importance=5 if any(k in ch.content for k in ["重点", "必考", "往年", "老师"]) else 3,
                    source_confidence=ch.confidence,
                    inferred=False,
                    source_refs=ch.source_refs,
                )
            else:
                t = topic_map[key]
                if ch.chunk_id not in t.source_chunks:
                    t.source_chunks.append(ch.chunk_id)
                t.source_refs.extend([r for r in ch.source_refs if r not in t.source_refs])
                t.importance = min(5, t.importance + 1)
            t = topic_map[key]
            if any(k in ch.content for k in ["定义", "概念", "是指"]):
                t.definitions.append(ch.content[:220])
            if re.search(r"[A-Za-z]\s*=|Δ|\\frac|公式", ch.content):
                t.formulas.append(ch.content[:220])
            if any(k in ch.content for k in ["例如", "例题", "实验", "题"]):
                t.examples.append(ch.content[:220])
    topics = list(topic_map.values())
    for i, topic in enumerate(topics):
        topic.related_topics = [t.topic_id for t in topics[max(0, i - 1): i] + topics[i + 1: i + 2]]
        topic.prerequisite_topics = [topics[i - 1].topic_id] if i > 0 else []
    if not topics:
        topics = [Topic(topic_id="T001", topic_name="需人工确认课程范围", inferred=True, source_confidence=0.2)]
    if output_dir:
        write_json(output_dir / "course_index.json", [asdict(t) for t in topics])
        (output_dir / "01_课程知识索引.md").write_text(render_course_index(topics), encoding="utf-8")
    return topics


def render_course_index(topics: list[Topic]) -> str:
    lines = ["# 课程知识索引", "", "核心口号：输入课程资料，输出提分路径。", ""]
    for t in topics:
        src = "; ".join(r.get("source_file", "") for r in t.source_refs[:3]) or "需人工确认"
        lines += [
            f"## {t.topic_id} {t.topic_name}",
            f"- 章节：{t.chapter or '未标注'}",
            f"- 难度/重要度：{t.difficulty}/{t.importance}",
            f"- 来源：{src}",
            f"- 定义：{(t.definitions[0] if t.definitions else '需从原资料补充精读')}",
            f"- 公式：{(t.formulas[0] if t.formulas else '未发现明确公式')}",
            f"- 例题/场景：{(t.examples[0] if t.examples else '未发现明确例题')}",
            f"- 关系：前置 {', '.join(t.prerequisite_topics) or '无'}；相关 {', '.join(t.related_topics) or '无'}",
            "",
        ]
    return "\n".join(lines)
