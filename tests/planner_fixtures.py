"""Realistic multi-course fixtures for Round 4 planner tests."""

from __future__ import annotations

import json
from pathlib import Path

from exam_review_skill.i18n import TerminologyMap
from exam_review_skill.knowledge.build import build_course_intelligence
from exam_review_skill.state import course as course_mod
from exam_review_skill.state import workspace as workspace_mod


COURSE_DEFS = {
    "probability": {
        "name": "概率论",
        "exam_date": "2026-06-19",
        "target_score": 85,
        "topics": [
            ("central_limit_theorem", "中心极限定理", "Central Limit Theorem"),
            ("conditional_probability", "条件概率", "conditional probability"),
            ("normal_distribution", "正态分布", "normal distribution"),
        ],
    },
    "organic-chemistry": {
        "name": "有机化学",
        "exam_date": "2026-06-20",
        "target_score": 80,
        "topics": [
            ("esterification", "酯化反应", "esterification"),
            ("neutralization", "中和反应", "neutralization"),
            ("functional_groups", "官能团", "functional groups"),
        ],
    },
    "botany": {
        "name": "植物学",
        "exam_date": "2026-06-26",
        "target_score": 70,
        "topics": [
            ("photosynthesis", "光合作用", "photosynthesis"),
            ("transpiration", "蒸腾作用", "transpiration"),
            ("cell_wall", "细胞壁", "cell wall"),
        ],
    },
    "calculus": {
        "name": "微积分",
        "exam_date": "2026-06-21",
        "target_score": 60,
        "topics": [
            ("limits", "极限", "limits"),
            ("derivatives", "导数", "derivatives"),
            ("integrals", "积分", "integrals"),
        ],
    },
}


def _evidence_record(course_id: str, i: int, zh: str, en: str) -> dict:
    return {
        "evidence_id": f"EV-{course_id}-{i}",
        "course_id": course_id,
        "source_file": f"lecture_{i}.pdf",
        "document_type": "pdf",
        "page_or_slide": "1",
        "heading": f"Chapter {i + 1}",
        "source_language": "zh-CN",
        "extraction_method": "native_text",
        "confidence": 0.85,
        "evidence_weight": 1.0,
        "synthetic": False,
        "created_at": "2026-06-01T00:00:00+08:00",
        "content": {
            "text": (
                f"{zh}（{en}）是指一个重要的课程概念。老师强调这是重点。易错：注意适用条件。"
                f"核心公式：X = f(Y) + ε。适用条件：Y 已知且 ε 独立。"
            ),
            "formula_signals": ["math-tokens"],
        },
    }


def build_scenario_workspace(
    root: Path,
    *,
    course_ids: list[str] | None = None,
    exam_dates: dict[str, str] | None = None,
    target_scores: dict[str, int] | None = None,
    daily_hours: float = 6.0,
) -> Path:
    """Build a realistic multi-course workspace (Scenario A default: 4 courses,
    exams within 7 days). Returns the workspace root."""
    workspace_mod.create_workspace(root, user_locale="zh-CN", daily_total_hours=daily_hours)
    course_ids = course_ids or list(COURSE_DEFS)
    for cid in course_ids:
        definition = COURSE_DEFS[cid]
        workspace_mod.add_course_to_workspace(
            root,
            course_id=cid,
            course_name=definition["name"],
            exam_date=exam_dates.get(cid, definition["exam_date"]) if exam_dates else definition["exam_date"],
            target_score=target_scores.get(cid, definition["target_score"]) if target_scores else definition["target_score"],
        )
        course_path = course_mod.course_dir(root, cid)
        tm = TerminologyMap(course_id=cid)
        for topic_id, zh, en in definition["topics"]:
            tm.add(topic_id, zh=zh, en=en)
        course_mod._write_json(course_path / "terminology_map.json", tm.to_state())
        records = [_evidence_record(cid, i, zh, en) for i, (_, zh, en) in enumerate(definition["topics"])]
        if cid == "probability":
            records.append(
                {
                    "evidence_id": "EV-prob-exam",
                    "course_id": cid,
                    "source_file": "past_exam_2024.pdf",
                    "document_type": "pdf",
                    "page_or_slide": "1",
                    "heading": "期末试卷",
                    "source_language": "zh-CN",
                    "extraction_method": "multimodal",
                    "confidence": 0.8,
                    "evidence_weight": 2.0,
                    "synthetic": False,
                    "created_at": "2026-06-03T00:00:00+08:00",
                    "content": {
                        "text": "",
                        "formula_signals": [],
                        "exam_structure": [
                            {"question_number": "1", "body": "中心极限定理计算", "question_type": "calculation", "score": "15"},
                            {"question_number": "2", "body": "条件概率简答", "question_type": "short answer", "score": "10"},
                        ],
                    },
                }
            )
        course_mod._write_json(
            course_path / "evidence_store.json",
            {"course_id": cid, "documents": {}, "records": records, "updated_at": ""},
        )
        build_course_intelligence(root, cid, days_to_exam=6)
    return root
