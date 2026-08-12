"""Shared helpers for building runnable example scenarios (v2 workflow).

Each example builds a real workspace with courses, terminology, evidence, the
exam brain, and (for some) recorded answers - so the exact commands in each
example README can be run against the produced state.
"""

from __future__ import annotations

from pathlib import Path

from exam_review_skill.i18n import TerminologyMap
from exam_review_skill.knowledge.build import build_course_intelligence
from exam_review_skill.state import course as course_mod
from exam_review_skill.state import workspace as workspace_mod


def make_workspace(root: Path, *, locale: str = "zh-CN", daily_hours: float = 6.0) -> Path:
    workspace_mod.create_workspace(root, user_locale=locale, daily_total_hours=daily_hours)
    return root


def add_course_with_evidence(
    root: Path,
    *,
    course_id: str,
    name: str,
    exam_date: str | None,
    target_score: int,
    topics: list[tuple[str, str, str]],  # (topic_id, zh, en)
    extra_evidence: list[dict] | None = None,
    days_to_exam: int | None = 6,
) -> None:
    workspace_mod.add_course_to_workspace(
        root,
        course_id=course_id,
        course_name=name,
        exam_date=exam_date,
        target_score=target_score,
    )
    course_path = course_mod.course_dir(root, course_id)
    tm = TerminologyMap(course_id=course_id)
    for topic_id, zh, en in topics:
        tm.add(topic_id, zh=zh, en=en)
    course_mod._write_json(course_path / "terminology_map.json", tm.to_state())

    records = []
    for i, (topic_id, zh, en) in enumerate(topics):
        records.append(
            {
                "evidence_id": f"EV-{course_id}-{i}",
                "course_id": course_id,
                "source_file": f"lecture_{i}.pdf",
                "document_type": "pdf",
                "page_or_slide": "1",
                "heading": f"Chapter {i + 1}",
                "source_language": "zh-CN" if zh else "en-US",
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
        )
    records.extend(extra_evidence or [])
    course_mod._write_json(
        course_path / "evidence_store.json",
        {"course_id": course_id, "documents": {}, "records": records, "updated_at": ""},
    )
    build_course_intelligence(root, course_id, days_to_exam=days_to_exam)
