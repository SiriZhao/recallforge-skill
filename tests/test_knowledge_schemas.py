from __future__ import annotations

import json
from pathlib import Path

from jsonschema import validate

from recallforge.i18n import TerminologyMap
from recallforge.knowledge.build import build_course_intelligence
from recallforge.state import course as course_mod
from recallforge.state import workspace as workspace_mod


SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schemas"


def _schema(name: str) -> dict:
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def _term_map() -> TerminologyMap:
    tm = TerminologyMap(course_id="probability")
    tm.add("central_limit_theorem", zh="中心极限定理", en="Central Limit Theorem")
    tm.add("conditional_probability", zh="条件概率", en="conditional probability")
    return tm


def _records() -> list[dict]:
    return [
        {
            "evidence_id": "EV-AAA1", "course_id": "probability", "source_file": "lecture_03.pdf",
            "document_type": "pdf", "page_or_slide": "5", "heading": "第五章 中心极限定理",
            "source_language": "zh-CN", "extraction_method": "native_text", "confidence": 0.85,
            "evidence_weight": 1.0, "synthetic": False, "created_at": "2026-06-01T00:00:00+08:00",
            "content": {"text": "中心极限定理是指大量独立随机变量之和近似服从正态分布。老师强调这是必考重点。", "formula_signals": []},
        },
        {
            "evidence_id": "EV-CCC3", "course_id": "probability", "source_file": "past_exam_2024.pdf",
            "document_type": "pdf", "page_or_slide": "1", "heading": "期末试卷",
            "source_language": "zh-CN", "extraction_method": "multimodal", "confidence": 0.8,
            "evidence_weight": 2.0, "synthetic": False, "created_at": "2026-06-03T00:00:00+08:00",
            "content": {"text": "", "formula_signals": [], "exam_structure": [
                {"question_number": "1", "body": "中心极限定理计算", "question_type": "calculation", "score": "15"},
            ]},
        },
    ]


def _build(root: Path) -> Path:
    workspace_mod.create_workspace(root)
    workspace_mod.add_course_to_workspace(root, course_id="probability", course_name="概率论")
    course_path = course_mod.course_dir(root, "probability")
    tm = _term_map()
    course_mod._write_json(course_path / "terminology_map.json", tm.to_state())
    course_mod._write_json(
        course_path / "evidence_store.json",
        {"course_id": "probability", "documents": {}, "records": _records(), "updated_at": ""},
    )
    build_course_intelligence(root, "probability", days_to_exam=3)
    return course_path


def test_knowledge_graph_schema(tmp_path: Path):
    course_path = _build(tmp_path / "ws")
    data = json.loads((course_path / "knowledge_graph.json").read_text(encoding="utf-8"))
    validate(instance=data, schema=_schema("knowledge_graph.schema.json"))
    assert data["topics"], "topic-centric graph must contain topics"
    assert data["topics"][0]["topic_id"]
    assert data["topics"][0]["evidence"]


def test_exam_model_schema(tmp_path: Path):
    course_path = _build(tmp_path / "ws")
    data = json.loads((course_path / "exam_model.json").read_text(encoding="utf-8"))
    validate(instance=data, schema=_schema("exam_model.schema.json"))
    assert data["past_exam_sets"]
    assert "evidence_weights" in data


def test_risk_radar_schema(tmp_path: Path):
    course_path = _build(tmp_path / "ws")
    data = json.loads((course_path / "risk_radar.json").read_text(encoding="utf-8"))
    validate(instance=data, schema=_schema("risk_radar.schema.json"))
    assert data["items"]
    assert data["items"][0]["priority"] in ("S", "A", "B", "C")
    assert data["items"][0]["priority_rationale"]


def test_conflicts_schema(tmp_path: Path):
    course_path = _build(tmp_path / "ws")
    data = json.loads((course_path / "conflicts.json").read_text(encoding="utf-8"))
    validate(instance=data, schema=_schema("conflicts.schema.json"))


def test_coverage_schema(tmp_path: Path):
    course_path = _build(tmp_path / "ws")
    data = json.loads((course_path / "coverage_report.json").read_text(encoding="utf-8"))
    validate(instance=data, schema=_schema("coverage_report.schema.json"))
    assert data["verdict"]
