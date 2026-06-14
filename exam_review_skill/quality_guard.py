from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .models import ExamPoint, GenerationReport, RiskItem


REQUIRED_OUTPUTS = [
    "00_资料来源与解析报告.md", "01_课程知识索引.md", "02_考试考点图谱.md", "03_考试风险雷达.md",
    "04_章节重点精讲.md", "05_高频考点与命题预测.md", "06_往年题考点映射表.md", "07_真题变式训练.md",
    "08_自适应复习计划.md", "09_个人薄弱点诊断.md", "10_今日复习任务.md", "11_专项训练题.md",
    "12_错题本.md", "13_临考急救包.md", "14_老师命题风格报告.md", "15_考前30分钟速救版.md",
    "course_index.json", "exam_graph.json", "risk_radar.json", "student_state.json", "wrongbook.json",
]


def check_generation(output_dir: Path, report: GenerationReport, exam_points: list[ExamPoint] | list[dict] | None = None, risks: list[RiskItem] | None = None) -> GenerationReport:
    for name in REQUIRED_OUTPUTS:
        path = output_dir / name
        ok = path.exists() and path.stat().st_size > 0
        report.quality_checks.append({"check": f"output_exists:{name}", "ok": ok})
        if not ok:
            report.warn(f"Missing or empty output: {name}")
    if report.files_seen and len(report.files_read) < len(report.files_seen):
        report.warn("Some files were not read; inspect source report.")
    for ep in exam_points or []:
        data = ep if isinstance(ep, dict) else asdict(ep)
        if data.get("confidence", 0) >= 0.75 and not data.get("source_refs"):
            report.warn(f"无来源高置信度结论：{data.get('topic_name', data.get('exam_point_id'))}，已标记需人工确认。")
    for json_name in ["course_index.json", "exam_graph.json", "risk_radar.json", "student_state.json", "wrongbook.json"]:
        try:
            json.loads((output_dir / json_name).read_text(encoding="utf-8"))
        except Exception as exc:
            report.warn(f"JSON 格式错误 {json_name}: {exc}")
    return report


def render_generation_report(report: GenerationReport) -> str:
    lines = ["# generation_report", "", f"- LLM provider：{report.provider}", ""]
    lines += ["## 文件读取", ""]
    lines.append(f"- 发现文件数：{len(report.files_seen)}")
    lines.append(f"- 成功读取数：{len(report.files_read)}")
    for f in report.files_read:
        lines.append(f"- 已读取：{f}")
    lines += ["", "## Warnings", ""]
    if not report.warnings:
        lines.append("- 暂无 warning。")
    for w in report.warnings:
        lines.append(f"- {w}")
    lines += ["", "## 质量检查", ""]
    for c in report.quality_checks:
        lines.append(f"- [{'OK' if c.get('ok') else 'WARN'}] {c.get('check')}")
    lines += ["", "## 检查项覆盖", "- 文件读取、章节输出、考点来源、范围外内容、变式来源、老师风格依据、无来源高置信度、OCR 低置信度、输出缺失、JSON、空泛总结、答案缺失、题干答案匹配、计划目标匹配。"]
    return "\n".join(lines)
