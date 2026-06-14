from __future__ import annotations

from pathlib import Path

from .models import ExamPoint, Topic


def generate_review_pack(topics: list[Topic], points: list[ExamPoint], output_dir: Path) -> list[Path]:
    paths = [output_dir / "04_章节重点精讲.md", output_dir / "05_高频考点与命题预测.md"]
    paths[0].write_text(render_chapter_review(topics, points), encoding="utf-8")
    paths[1].write_text(render_predictions(points), encoding="utf-8")
    return paths


def render_chapter_review(topics: list[Topic], points: list[ExamPoint]) -> str:
    lines = ["# 章节重点精讲", ""]
    by_topic = {p.topic_id: p for p in points}
    for t in topics:
        p = by_topic.get(t.topic_id)
        lines += [
            f"## {t.chapter or '未标注章节'}：{t.topic_name}",
            f"1. 本章考试地位：重要度 {t.importance}/5，{('高频考点' if p and p.frequency >= 3 else '基础考点')}",
            f"2. 核心概念：{t.definitions[0] if t.definitions else '需回看来源材料，当前只提取到标题级信息。'}",
            f"3. 必背定义：用自己的话写出 {t.topic_name} 的定义、条件和反例。",
            f"4. 关键公式：{t.formulas[0] if t.formulas else '未发现明确公式，若课堂有板书需人工补充。'}",
            f"5. 典型题型：{', '.join(p.exam_forms) if p else '概念辨析题'}",
            f"6. 往年题对应：{len(p.past_exam_refs) if p else 0} 条来源引用",
            f"7. 易错点：{'; '.join(p.common_traps) if p else '概念边界不清'}",
            "8. 简答题标准答法：定义一句话 + 条件/步骤 + 例子/误差 + 结论。",
            "9. 计算题解题模板：列公式 -> 代单位 -> 写有效数字 -> 检查量纲。",
            f"10. 30分钟速背版：背 {t.topic_name} 的定义、公式条件、一个来源题。",
            "",
        ]
    return "\n".join(lines)


def render_predictions(points: list[ExamPoint]) -> str:
    lines = ["# 高频考点与命题预测", "", "以下预测均基于资料出现频率、往年题、老师强调和题型信号；低来源内容标为需人工确认。", ""]
    for p in sorted(points, key=lambda x: (-x.frequency, x.topic_name)):
        src = "; ".join(r.get("source_file", "") for r in p.source_refs[:3]) or "需人工确认"
        lines += [
            f"## {p.topic_name}",
            f"- 预测题型：{', '.join(p.exam_forms)}",
            f"- 命题可能性：{'高' if p.frequency >= 3 else '中/需确认'}",
            f"- 分值潜力：{p.score_potential}",
            f"- 常见陷阱：{'; '.join(p.common_traps)}",
            f"- 来源：{src}",
            "",
        ]
    return "\n".join(lines)
