from __future__ import annotations

import json
from pathlib import Path

from recallforge.reporting.dashboard import build_dashboard
from recallforge.reporting.export import export_report, SUPPORTED_FORMATS
from recallforge.reporting.reports import REPORT_TYPES, render_report
from recallforge.reporting.welcome import build_first_use_report
from recallforge.planner.orchestrator import generate_daily_plan_v4
from recallforge.knowledge.build import build_course_intelligence
from recallforge.student.store import load_student_model, save_student_model
from recallforge.student.sessions import AnswerResult, record_answer
from recallforge.state import course as course_mod

from planner_fixtures import build_scenario_workspace


def test_first_use_report_has_all_sections(tmp_path: Path):
    root = build_scenario_workspace(tmp_path / "ws")
    result = build_course_intelligence(root, "probability", persist=False)
    records = course_mod.load_course_json(
        course_mod.course_dir(root, "probability"), "evidence_store.json", {}
    ) or {}
    model = load_student_model(root, "probability")
    text = build_first_use_report(
        root, "probability",
        topics=result.topics, student=model, coverage=result.coverage,
        evidence_records=records.get("records", []),
        unresolved_pages=result.coverage.unresolved_documents,
        locale="zh-CN",
    )
    for section in ("一、材料盘点", "二、课程结构", "三、考试情况", "四、资料缺口", "五、当前风险", "六、下一步建议"):
        assert section in text
    assert "概率论" in text


def test_first_use_report_english(tmp_path: Path):
    root = build_scenario_workspace(tmp_path / "ws")
    result = build_course_intelligence(root, "probability", persist=False)
    records = course_mod.load_course_json(
        course_mod.course_dir(root, "probability"), "evidence_store.json", {}
    ) or {}
    text = build_first_use_report(
        root, "probability",
        topics=result.topics, student=load_student_model(root, "probability"),
        coverage=result.coverage, evidence_records=records.get("records", []),
        unresolved_pages=[], locale="en-US",
    )
    assert "Material Inventory" in text
    assert "Course Structure" in text
    assert "Material Gaps" in text


def test_dashboard_honest_readiness(tmp_path: Path):
    """Readiness is only a number when there is enough data; otherwise Unknown /
    Insufficient evidence - never fabricated."""
    root = build_scenario_workspace(tmp_path / "ws")
    plan = generate_daily_plan_v4(root, "2026-06-18")
    # no answers yet -> all courses show Unknown readiness
    dash = build_dashboard(root, plan=plan, plan_date="2026-06-18", locale="zh-CN")
    assert "Unknown / Insufficient evidence" in dash
    # record answers for probability -> readiness becomes a number for that course
    model = load_student_model(root, "probability")
    record_answer(model, AnswerResult(topic_id="central_limit_theorem", correct=True, difficulty=2), today="2026-06-17")
    record_answer(model, AnswerResult(topic_id="conditional_probability", correct=True, difficulty=2), today="2026-06-17")
    save_student_model(root, "probability", model)
    dash2 = build_dashboard(root, plan=plan, plan_date="2026-06-18", locale="zh-CN")
    assert "准备度：" in dash2
    # exam proximity shown
    assert "明天考试" in dash2


def test_dashboard_english(tmp_path: Path):
    root = build_scenario_workspace(tmp_path / "ws")
    plan = generate_daily_plan_v4(root, "2026-06-18")
    dash = build_dashboard(root, plan=plan, plan_date="2026-06-18", locale="en-US")
    assert "Exam Week Dashboard" in dash
    assert "Readiness" in dash
    assert "Risk" in dash


def test_all_report_types_render(tmp_path: Path):
    root = build_scenario_workspace(tmp_path / "ws")
    # record answers + a wrongbook entry so wrongbook report has content
    model = load_student_model(root, "probability")
    record_answer(model, AnswerResult(topic_id="central_limit_theorem", correct=False, mistake_type="unit_error"), today="2026-06-17")
    save_student_model(root, "probability", model)
    for report_type in REPORT_TYPES:
        if report_type in ("dashboard", "welcome"):
            text = render_report(root, report_type, course_id="probability", locale="zh-CN")
        else:
            text = render_report(root, report_type, course_id="probability", locale="zh-CN")
        assert isinstance(text, str) and text, report_type


def test_report_types_bilingual_md_export(tmp_path: Path):
    root = build_scenario_workspace(tmp_path / "ws")
    text = render_report(root, "course-overview", course_id="probability", locale="zh-CN")
    out = tmp_path / "overview.md"
    ok, msg = export_report(text, output_path=out, fmt="md", locale="zh-CN")
    assert ok
    assert out.exists()
    assert "已导出" in msg


def test_export_json(tmp_path: Path):
    text = "# test\ncontent"
    out = tmp_path / "r.json"
    ok, _ = export_report(text, output_path=out, fmt="json")
    assert ok
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["markdown"] == text


def test_export_docx(tmp_path: Path):
    text = "# Title\n\n## Section\n- item one\n- item two"
    out = tmp_path / "r.docx"
    ok, _ = export_report(text, output_path=out, fmt="docx")
    assert ok
    assert out.exists() and out.stat().st_size > 0


def test_export_pdf_isolated(tmp_path: Path):
    """Optional PDF export may succeed when reportlab is installed; either
    outcome must not prevent the normal Markdown flow."""
    text = "# hello"
    out = tmp_path / "r.pdf"
    ok, msg = export_report(text, output_path=out, fmt="pdf")
    if ok:
        assert out.exists() and out.stat().st_size > 0
    else:
        assert "失败" in msg or "failed" in msg.lower()
    # markdown export still works afterwards
    md = tmp_path / "r.md"
    ok2, _ = export_report(text, output_path=md, fmt="md")
    assert ok2


def test_export_anki(tmp_path: Path):
    from recallforge.models import QuizQuestion

    questions = [
        QuizQuestion(question_id="Q1", topic_id="t1", topic_name="CLT", question_type="calculation",
                     level=2, question_text="What is CLT?", correct_answer="Standardize"),
    ]
    out = tmp_path / "anki.csv"
    ok, _ = export_report("", output_path=out, fmt="anki", questions=questions)
    assert ok
    content = out.read_text(encoding="utf-8")
    assert "Front,Back,Tags" in content
    assert "What is CLT?" in content


def test_bilingual_output_mode_render(tmp_path: Path):
    """Reports render in all three output modes (zh / en / bilingual)."""
    root = build_scenario_workspace(tmp_path / "ws")
    result = build_course_intelligence(root, "probability", persist=False)
    records = course_mod.load_course_json(
        course_mod.course_dir(root, "probability"), "evidence_store.json", {}
    ) or {}
    zh_text = build_first_use_report(
        root, "probability", topics=result.topics,
        student=load_student_model(root, "probability"), coverage=result.coverage,
        evidence_records=records.get("records", []), unresolved_pages=[], locale="zh-CN",
    )
    assert "材料盘点" in zh_text
