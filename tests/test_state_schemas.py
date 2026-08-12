from __future__ import annotations

import json
from pathlib import Path

from jsonschema import ValidationError, validate

from exam_review_skill.models import DayOverride
from exam_review_skill.orchestrator.scheduler import generate_daily_plan
from exam_review_skill.state import course as course_mod
from exam_review_skill.state import workspace as workspace_mod

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schemas"


def _schema(name: str) -> dict:
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def _validate_file(path: Path, schema_name: str) -> None:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    validate(instance=data, schema=_schema(schema_name))


def _build_workspace(root: Path) -> Path:
    workspace_mod.create_workspace(root, user_locale="zh-CN", daily_total_hours=6.0)
    workspace_mod.add_course_to_workspace(
        root, course_id="probability", course_name="概率论",
        source_languages=["zh-CN"], exam_date="2026-06-23", target_score=85,
    )
    workspace_mod.add_course_to_workspace(
        root, course_id="organic-chemistry", course_name="有机化学",
        source_languages=["zh-CN"], exam_date="2026-06-20", target_score=80,
    )
    workspace_mod.add_course_to_workspace(
        root, course_id="botany", course_name="植物学", target_score=70,
    )
    return root


def test_workspace_and_course_files_validate_against_schemas(tmp_path: Path):
    root = _build_workspace(tmp_path / "ws")
    _validate_file(root / "workspace_state.json", "workspace.schema.json")
    _validate_file(root / "exam_calendar.json", "exam_calendar.schema.json")
    _validate_file(root / "overrides.json", "overrides.schema.json")
    for cid in workspace_mod.list_courses(root):
        cdir = course_mod.course_dir(root, cid)
        _validate_file(cdir / "course_manifest.json", "course_manifest.schema.json")
        _validate_file(cdir / "document_index.json", "document_index.schema.json")
        _validate_file(cdir / "knowledge_graph.json", "knowledge_graph.schema.json")
        _validate_file(cdir / "exam_model.json", "exam_model.schema.json")
        _validate_file(cdir / "student_state.json", "course_student_state.schema.json")
        _validate_file(cdir / "wrongbook.json", "course_wrongbook.schema.json")
        _validate_file(cdir / "evidence_store.json", "evidence_store.schema.json")
        _validate_file(cdir / "study_plan.json", "course_study_plan.schema.json")
        _validate_file(cdir / "terminology_map.json", "terminology_map.schema.json")


def test_global_plan_validates_against_schema(tmp_path: Path):
    root = _build_workspace(tmp_path / "ws")
    plan = generate_daily_plan(root, "2026-06-18")
    _validate_file(root / "global_study_plan.json", "global_study_plan.schema.json")
    assert plan.blocks


def test_override_validates_against_schema(tmp_path: Path):
    root = _build_workspace(tmp_path / "ws")
    workspace_mod.upsert_override(
        root,
        DayOverride(
            date="2026-06-18",
            skip_courses=["botany"],
            total_hours=3.0,
            target_scores={"calculus": 60},
            exam_date_changes={"organic-chemistry": "2026-06-19"},
            note="user note",
        ),
    )
    _validate_file(root / "overrides.json", "overrides.schema.json")


def test_schemas_use_stable_english_keys(tmp_path: Path):
    root = _build_workspace(tmp_path / "ws")
    state_data = json.loads((root / "workspace_state.json").read_text(encoding="utf-8"))
    assert "user_locale" in state_data
    assert "daily_total_hours" in state_data
    assert not any("日期" in k or "掌握度" in k for k in state_data)
    manifest = json.loads(
        (course_mod.course_dir(root, "probability") / "course_manifest.json").read_text(encoding="utf-8")
    )
    assert "exam_date" in manifest and "target_score" in manifest
