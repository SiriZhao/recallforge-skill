from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from ..i18n import TerminologyMap
from ..models import ExamPointModel, PastExamSet, TeacherStyle, KnowledgeTopic
from ..state.course import course_dir, load_course_json
from ..state.isolation import reject_mock_content
from .conflict import detect_conflicts
from .coverage import build_coverage_report
from .exam import build_exam_points, build_past_exam_sets, exam_model_state
from .graph import build_knowledge_edges, edges_to_state
from .risk import build_risk_radar, risk_radar_state
from .teacher import build_teacher_style
from .topic import build_topics, topics_to_state


def _load_evidence_records(course_path: Path) -> list[dict]:
    path = course_path / "evidence_store.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8")).get("records", [])
        except Exception:
            return []
    return []


def _load_terminology(course_path: Path) -> TerminologyMap:
    data = load_course_json(course_path, "terminology_map.json", {}) or {}
    return TerminologyMap.from_state(data)


def _write_state(course_path: Path, filename: str, payload: dict) -> None:
    reject_mock_content(payload, where=str(course_path / filename))
    (course_path / filename).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


class KnowledgeBuildResult:
    def __init__(
        self,
        topics: list[KnowledgeTopic],
        exam_points: list[ExamPointModel],
        past_exam_sets: list[PastExamSet],
        teacher_style: TeacherStyle,
        conflicts: list,
        coverage: object,
    ):
        self.topics = topics
        self.exam_points = exam_points
        self.past_exam_sets = past_exam_sets
        self.teacher_style = teacher_style
        self.conflicts = conflicts
        self.coverage = coverage


def build_course_intelligence(
    workspace_root: Path,
    course_id: str,
    *,
    evidence_weights: dict | None = None,
    days_to_exam: int | None = None,
    unresolved_pages: list[str] | None = None,
    persist: bool = True,
) -> KnowledgeBuildResult:
    """Run the full exam-brain build for one course:
    evidence -> topics -> graph -> exam model -> risk radar -> conflicts -> coverage.
    Returns an in-memory result and (optionally) persists state files."""
    course_path = course_dir(workspace_root, course_id)
    if not (course_path / "course_manifest.json").exists():
        raise FileNotFoundError(f"no course {course_id!r} in workspace {workspace_root}")

    records = _load_evidence_records(course_path)
    term_map = _load_terminology(course_path)

    topics = build_topics(records, term_map, course_id)
    edges = build_knowledge_edges(topics, records, term_map)
    teacher_style = build_teacher_style(course_id, topics, records, term_map)
    past_exam_sets = build_past_exam_sets(records, term_map)
    exam_points = build_exam_points(
        topics, past_exam_sets, teacher_style, records, term_map,
        evidence_weights=evidence_weights,
    )
    ranked = build_risk_radar(
        exam_points,
        mastery=load_course_json(course_path, "student_state.json", {}).get("mastery") or {},
        days_to_exam=days_to_exam,
    )
    conflicts = detect_conflicts(topics, records, term_map)
    coverage = build_coverage_report(
        course_id,
        topics,
        ranked,
        past_exam_sets,
        teacher_style,
        records,
        unresolved_pages or [],
    )

    if persist:
        graph_state = edges_to_state(course_id, edges)
        graph_state["topics"] = topics_to_state(topics)["topics"]
        _write_state(course_path, "knowledge_graph.json", graph_state)
        _write_state(
            course_path,
            "exam_model.json",
            exam_model_state(
                course_id, ranked, past_exam_sets, teacher_style, evidence_weights
            ),
        )
        _write_state(course_path, "risk_radar.json", risk_radar_state(ranked))
        _write_state(
            course_path,
            "conflicts.json",
            {"course_id": course_id, "conflicts": [asdict(c) for c in conflicts], "updated_at": ""},
        )
        _write_state(course_path, "coverage_report.json", asdict(coverage))

    return KnowledgeBuildResult(
        topics=topics,
        exam_points=ranked,
        past_exam_sets=past_exam_sets,
        teacher_style=teacher_style,
        conflicts=conflicts,
        coverage=coverage,
    )
