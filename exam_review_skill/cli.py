from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path

from .adaptive_quiz import generate_quiz
from .build_exam_graph import build_exam_graph
from .chunk import chunk_documents
from .diagnose_mastery import diagnose_mastery
from .export_pack import export_anki_csv, export_docx
from .generate_cram_pack import generate_cram_pack
from .generate_review_pack import generate_review_pack
from .generate_variants import generate_variants
from .index_course import build_course_index
from .ingest import ingest_path
from .llm_provider import MockLLMProvider
from .models import ExamPoint, GenerationReport, RiskItem, StudentState, to_dict
from .plan_review import build_review_plan
from .quality_guard import check_generation, render_generation_report
from .risk_radar import build_risk_radar
from .state_manager import load_student_state, read_json, save_student_state, update_history, write_json
from .teacher_style import generate_teacher_style
from .wrongbook import build_wrongbook


def run_pipeline(args: argparse.Namespace) -> None:
    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    report = GenerationReport(provider="mock")
    provider = MockLLMProvider()
    report.warn("Using MockLLMProvider: no real API key required; outputs are rule-based and should be reviewed for high-stakes use.")

    docs = ingest_path(input_dir, report)
    _write_source_report(output_dir, docs, report)
    chunks = chunk_documents(docs)
    state = load_student_state(output_dir / "student_state.json", args.course, args.target_score, getattr(args, "exam_date", None), args.daily_hours)
    state.course_name = args.course
    state.target_score = args.target_score
    state.exam_date = getattr(args, "exam_date", None)
    state.daily_hours = args.daily_hours
    update_history(state, "run", {"input": str(input_dir), "chunks": len(chunks)})

    topics = build_course_index(chunks, output_dir)
    points = build_exam_graph(topics, chunks, output_dir)
    risks = build_risk_radar(points, state, output_dir=output_dir)
    generate_review_pack(topics, points, output_dir)
    generate_variants(chunks, points, output_dir, count=20)
    diagnose_mastery(state, risks, output_dir)
    plan = build_review_plan(state, risks, output_dir=output_dir)
    questions = generate_quiz(risks, [asdict(p) for p in points], output_dir, mode="s-priority", count=20, provider=provider)
    build_wrongbook(state.wrong_questions, questions, output_dir)
    generate_cram_pack(state, risks, output_dir)
    generate_teacher_style(chunks, points, output_dir)
    export_anki_csv([asdict(q) for q in questions], output_dir / "anki_cards.csv")
    export_docx([output_dir / "04_章节重点精讲.md", output_dir / "05_高频考点与命题预测.md"], output_dir / "review_pack.docx", report.warnings)
    save_student_state(output_dir / "student_state.json", state)
    report.outputs = [p.name for p in output_dir.iterdir() if p.is_file()]
    check_generation(output_dir, report, points, risks)
    (output_dir / "generation_report.md").write_text(render_generation_report(report), encoding="utf-8")


def _write_source_report(output_dir: Path, docs, report: GenerationReport) -> None:
    lines = ["# 资料来源与解析报告", "", "|文件|类型|块数|警告|", "|---|---|---:|---|"]
    for d in docs:
        lines.append(f"|{d.source_file}|{d.doc_type}|{len(d.blocks)}|{'; '.join(d.warnings) or '无'}|")
    if not docs:
        lines.append("|无|unknown|0|未读取到支持格式资料|")
    (output_dir / "00_资料来源与解析报告.md").write_text("\n".join(lines), encoding="utf-8")


def _load_points(output_dir: Path) -> list[ExamPoint]:
    return [ExamPoint(**x) for x in read_json(output_dir / "exam_graph.json", [])]


def _load_risks(output_dir: Path) -> list[RiskItem]:
    return [RiskItem(**x) for x in read_json(output_dir / "risk_radar.json", [])]


def command_cram(args: argparse.Namespace) -> None:
    state_path = Path(args.state)
    output_dir = state_path.parent
    state = load_student_state(state_path)
    risks = _load_risks(output_dir)
    if not risks:
        risks = [RiskItem(exam_point_id="EP000", topic_name="需人工确认高风险考点", priority="S")]
    generate_cram_pack(state, risks, output_dir, hours_left=args.hours_left)


def command_plan(args: argparse.Namespace) -> None:
    state_path = Path(args.state)
    output_dir = state_path.parent
    state = load_student_state(state_path)
    risks = _load_risks(output_dir) or [RiskItem(exam_point_id="EP000", topic_name="需人工确认考点", priority="S")]
    build_review_plan(state, risks, days_left=args.days_left, daily_hours=args.daily_hours, target_score=args.target_score, output_dir=output_dir)


def command_quiz(args: argparse.Namespace) -> None:
    state_path = Path(args.state)
    output_dir = state_path.parent
    points = [asdict(p) for p in _load_points(output_dir)]
    risks = _load_risks(output_dir) or [RiskItem(exam_point_id="EP000", topic_name="需人工确认考点", priority="S")]
    questions = generate_quiz(risks, points, output_dir, mode=args.mode, count=args.count, provider=MockLLMProvider())
    if args.mode == "wrongbook":
        build_wrongbook(read_json(output_dir / "wrongbook.json", []), questions, output_dir)


def command_variants(args: argparse.Namespace) -> None:
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    report = GenerationReport(provider="mock")
    docs = ingest_path(Path(args.input), report)
    chunks = chunk_documents(docs)
    topics = build_course_index(chunks)
    points = build_exam_graph(topics, chunks)
    generate_variants(chunks, points, output_dir, count=args.count)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="exam-review-skill", description="输入课程资料，输出提分路径。")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="完整运行")
    run.add_argument("--input", required=True)
    run.add_argument("--output", required=True)
    run.add_argument("--course", required=True)
    run.add_argument("--exam-date")
    run.add_argument("--target-score", type=int, default=80)
    run.add_argument("--daily-hours", type=float, default=4)
    run.set_defaults(func=run_pipeline)

    cram = sub.add_parser("cram", help="只生成临考急救包")
    cram.add_argument("--state", required=True)
    cram.add_argument("--hours-left", type=float, required=True)
    cram.set_defaults(func=command_cram)

    variants = sub.add_parser("variants", help="只生成真题变式")
    variants.add_argument("--input", required=True)
    variants.add_argument("--output", required=True)
    variants.add_argument("--count", type=int, default=20)
    variants.set_defaults(func=command_variants)

    plan = sub.add_parser("plan", help="只生成复习计划")
    plan.add_argument("--state", required=True)
    plan.add_argument("--days-left", type=int, required=True)
    plan.add_argument("--daily-hours", type=float, required=True)
    plan.add_argument("--target-score", type=int, required=True)
    plan.set_defaults(func=command_plan)

    quiz = sub.add_parser("quiz", help="生成训练题")
    quiz.add_argument("--state", required=True)
    quiz.add_argument("--mode", choices=["s-priority", "weak-points", "wrongbook", "mock-exam", "cram"], default="s-priority")
    quiz.add_argument("--count", type=int, default=20)
    quiz.set_defaults(func=command_quiz)
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
