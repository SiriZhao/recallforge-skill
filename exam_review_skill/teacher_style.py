from __future__ import annotations

from pathlib import Path

from .models import Chunk, ExamPoint


def generate_teacher_style(chunks: list[Chunk], points: list[ExamPoint], output_dir: Path) -> Path:
    path = output_dir / "14_老师命题风格报告.md"
    lecture = sum(1 for c in chunks if c.doc_type == "lecture_slide")
    past = sum(1 for c in chunks if c.doc_type == "past_exam")
    teacher = sum(1 for c in chunks if any(k in c.content for k in ["老师", "重点", "必考", "容易考"]))
    calc = sum(1 for p in points if "计算题" in p.exam_forms)
    lines = [
        "# 老师命题风格报告",
        "",
        f"- 命题风格判断：{'PPT/课堂重点导向' if teacher or lecture else '需人工确认'}",
        f"- PPT依赖程度：{'高' if lecture >= 3 else '中/需确认'}",
        "- 教材依赖程度：需结合教材来源确认",
        f"- 往年题重复倾向：{'可参考往年题高频点' if past else '资料中未发现往年题，需人工确认'}",
        f"- 计算题难度：{'中高' if calc else '未发现明显计算题'}",
        "- 简答题偏好：定义 + 实验步骤 + 误差分析",
        "- 实验题偏好：步骤、现象、误差来源、注意事项",
        "- 常见陷阱：单位、有效数字、条件漏看、只背结论不解释",
        f"- 可能重点章节：{', '.join(p.topic_name for p in points[:5]) or '需人工确认'}",
        "- 复习策略建议：先按风险雷达处理 S/A，再用真题变式检查迁移能力。",
        f"- 判断依据：课件块 {lecture} 个，往年题块 {past} 个，老师强调块 {teacher} 个。",
        f"- 置信度：{0.75 if teacher or past else 0.45}",
        "- 需人工确认项：未提供教师真实评分细则时，不推断具体原题。",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
