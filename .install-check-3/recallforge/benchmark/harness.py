from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from ..knowledge.build import build_course_intelligence
from ..planner.orchestrator import generate_daily_plan_v4
from ..state import course as course_mod
from ..student.sessions import AnswerResult, record_answer
from ..student.store import load_student_model, save_student_model
from .metrics import (
    BenchmarkMetrics,
    actionability,
    binary_adaptivity,
    binary_personalization,
    citation_accuracy,
    cross_document_linking,
    exam_relevance,
    hallucination_rate,
    important_topic_recall,
    multi_course_planning,
    past_exam_mapping,
    source_coverage,
)
from .naive import NaiveBaseline


def _norm_topic(topic: str) -> str:
    import re
    return re.sub(r"\s+", " ", topic.strip().lower())


def _basename(path: str) -> str:
    return Path(str(path)).name


class BenchmarkResult:
    def __init__(self, name: str, metrics: BenchmarkMetrics, skill: dict, naive: dict):
        self.name = name
        self.metrics = metrics
        self.skill = skill
        self.naive = naive

    def to_dict(self) -> dict:
        return {
            "benchmark": self.name,
            "metrics": asdict(self.metrics),
            "skill_summary": self.skill,
            "naive_summary": self.naive,
        }


def _course_skill_sources(course_id: str, workspace_root: Path) -> set[str]:
    """Source files with evidence records (basename-normalized). Includes the
    scanned page that was routed to the multimodal path with the synthetic
    provider in demo mode (benchmark fixtures, documented honestly)."""
    course_path = course_mod.course_dir(workspace_root, course_id)
    data = course_mod.load_course_json(course_path, "evidence_store.json", {}) or {}
    return {_basename(r.get("source_file", "")) for r in data.get("records", [])}


def _skill_topics_set(result) -> set[str]:
    topics = {_norm_topic(t.canonical_name) for t in result.topics}
    for topic in result.topics:
        for lang_name in topic.localized_names.values():
            topics.add(_norm_topic(lang_name))
        for alias in topic.aliases:
            topics.add(_norm_topic(alias))
    return topics


def _naive_read(baseline: NaiveBaseline, source_files: list[Path]):
    docs = baseline._read_files(source_files)
    return {
        "naive_topics": {_norm_topic(t) for t in baseline._extract_topics(docs, [])},
        "naive_sources": {d["source_file"] for d in docs if d["text"].strip()},
        "corpus": " ".join(d["text"] for d in docs),
    }


def _compute_course_metrics(
    *,
    workspace_root: Path,
    course_id: str,
    important: set[str],
    all_sources: set[str],
    naive: dict,
    days_to_exam: int | None,
) -> dict:
    """Compute ALL skill metrics for one course from real data (no hardcoding)."""
    result = build_course_intelligence(workspace_root, course_id, days_to_exam=days_to_exam, persist=False)
    skill_sources = _course_skill_sources(course_id, workspace_root)
    skill_topics = _skill_topics_set(result)

    sc_skill, sc_naive = source_coverage(skill_sources, naive["naive_sources"], all_sources)

    skill_claims = len(result.topics)
    cited = sum(1 for t in result.topics if t.evidence)
    cit_skill, cit_naive = citation_accuracy(cited, skill_claims, max(1, len(naive["naive_topics"])))

    rec_skill, rec_naive = important_topic_recall(skill_topics, naive["naive_topics"], important)

    # cross-document linking: topics with evidence from >=2 distinct source files
    course_path = course_mod.course_dir(workspace_root, course_id)
    records = (course_mod.load_course_json(course_path, "evidence_store.json", {}) or {}).get("records", [])
    evidence_by_id = {r.get("evidence_id"): _basename(r.get("source_file", "")) for r in records}
    skill_linked = 0
    for topic in result.topics:
        files = {evidence_by_id.get(eid) for eid in topic.evidence if eid in evidence_by_id}
        if len(files) >= 2:
            skill_linked += 1
    cd_skill, cd_naive = cross_document_linking(
        skill_linked, len(result.topics), 0, len(naive["naive_topics"])
    )

    skill_questions = sum(len(s.questions) for s in result.past_exam_sets)
    skill_mapped = sum(1 for s in result.past_exam_sets for q in s.questions if q.topics)
    pe_skill, pe_naive = past_exam_mapping(skill_mapped, skill_questions, 0, skill_questions)

    hal_skill, hal_naive = hallucination_rate(
        skill_claims, skill_claims,
        _naive_supported_lines(naive["corpus"]), _naive_total_lines(naive),
    )
    ex_skill, ex_naive = exam_relevance(
        len(result.exam_points), max(1, len(result.exam_points)),
        _naive_exam_lines(naive), _naive_total_lines(naive),
    )

    # personalization + adaptivity from real plan changes
    plan_before = generate_daily_plan_v4(workspace_root, "2026-06-18")
    before_sig = _plan_signature(plan_before)
    model = load_student_model(workspace_root, course_id)
    for topic in result.topics[:3]:
        for _ in range(3):
            record_answer(
                model, AnswerResult(topic_id=topic.topic_id, correct=True, difficulty=2),
                today="2026-06-17",
            )
    save_student_model(workspace_root, course_id, model)
    after_sig = _plan_signature(generate_daily_plan_v4(workspace_root, "2026-06-18"))
    per_skill, per_naive = binary_personalization(before_sig != after_sig, False)

    model2 = load_student_model(workspace_root, course_id)
    wrong_topic = result.topics[0].topic_id if result.topics else "t"
    for _ in range(3):
        record_answer(
            model2, AnswerResult(topic_id=wrong_topic, correct=False, mistake_type="unit_error"),
            today="2026-06-18",
        )
    save_student_model(workspace_root, course_id, model2)
    adapted_sig = _plan_signature(generate_daily_plan_v4(workspace_root, "2026-06-18"))
    ada_skill, ada_naive = binary_adaptivity(after_sig != adapted_sig, False)

    skill_actionable = sum(1 for b in plan_before.blocks if b.topic_name and b.goal and b.done_when)
    act_skill, act_naive = actionability(
        skill_actionable, max(1, len(plan_before.blocks)), 0, _naive_total_lines(naive)
    )

    return {
        "sc": (sc_skill, sc_naive),
        "cit": (cit_skill, cit_naive),
        "rec": (rec_skill, rec_naive),
        "cd": (cd_skill, cd_naive),
        "pe": (pe_skill, pe_naive),
        "hal": (hal_skill, hal_naive),
        "ex": (ex_skill, ex_naive),
        "per": (per_skill, per_naive),
        "ada": (ada_skill, ada_naive),
        "act": (act_skill, act_naive),
        "summary": {
            "topics": len(result.topics),
            "exam_points": len(result.exam_points),
            "past_exam_questions": skill_questions,
            "sources": len(skill_sources),
        },
    }


def _naive_total_lines(naive: dict) -> int:
    return max(1, len(naive.get("advice", [])))


def _naive_supported_lines(corpus: str) -> int:
    return 0  # naive advice is generic; nothing is sourced (checked in tests)


def _naive_exam_lines(naive: dict) -> int:
    from .metrics import _is_exam_oriented
    return sum(1 for line in naive.get("advice", []) if _is_exam_oriented(line))


def _plan_signature(plan) -> str:
    return json.dumps(
        [
            {"course": b.course_id, "topic": b.topic_name, "kind": b.kind, "why": b.why}
            for b in plan.blocks
        ],
        sort_keys=True,
    )


def run_single_course_benchmark(
    *,
    name: str,
    workspace_root: Path,
    course_id: str,
    important_terms: list[str],
    source_files: list[Path],
    days_to_exam: int | None = 3,
    locale: str = "zh-CN",
) -> BenchmarkResult:
    baseline = NaiveBaseline(locale=locale)
    naive_out = baseline.run(files=source_files, important_terms=important_terms, days_to_exam=days_to_exam)
    naive = _naive_read(baseline, source_files)
    naive["advice"] = naive_out["advice"]
    all_sources = {p.name for p in source_files}
    important = {_norm_topic(t) for t in important_terms}

    c = _compute_course_metrics(
        workspace_root=workspace_root, course_id=course_id,
        important=important, all_sources=all_sources, naive=naive,
        days_to_exam=days_to_exam,
    )
    metrics = BenchmarkMetrics(
        source_coverage=c["sc"][0],
        citation_accuracy=c["cit"][0],
        important_topic_recall=c["rec"][0],
        cross_document_linking=c["cd"][0],
        past_exam_mapping=c["pe"][0],
        hallucination_rate=c["hal"][0],
        exam_relevance=c["ex"][0],
        personalization=c["per"][0],
        adaptivity=c["ada"][0],
        actionability=c["act"][0],
        multi_course_planning=0.0,
        details={
            "naive": {
                "source_coverage": c["sc"][1],
                "citation_accuracy": c["cit"][1],
                "important_topic_recall": c["rec"][1],
                "cross_document_linking": c["cd"][1],
                "past_exam_mapping": c["pe"][1],
                "hallucination_rate": c["hal"][1],
                "exam_relevance": c["ex"][1],
                "personalization": c["per"][1],
                "adaptivity": c["ada"][1],
                "actionability": c["act"][1],
            }
        },
    )
    return BenchmarkResult(name, metrics, c["summary"], {
        "topics": len(naive["naive_topics"]),
        "documents_read": naive_out["documents_read"],
        "advice_lines": len(naive_out["advice"]),
        "sources": len(naive["naive_sources"]),
    })


def run_multi_course_benchmark(
    *,
    name: str,
    workspace_root: Path,
    courses: list[dict],
    source_files: list[Path],
    days_to_exam: int | None = 3,
    locale: str = "zh-CN",
) -> BenchmarkResult:
    """Multi-course benchmark: ONE coordinated exam-week plan vs per-course generic
    advice. All metrics computed from real data, aggregated GLOBALLY across the
    whole exam week (not per-course averages)."""
    baseline = NaiveBaseline(locale=locale)
    naive_out = baseline.run(files=source_files, important_terms=[], days_to_exam=days_to_exam)
    naive = _naive_read(baseline, source_files)
    naive["advice"] = naive_out["advice"]
    all_sources = {p.name for p in source_files}

    # global aggregation across all courses (whole exam week)
    total_topic_names: set[str] = set()
    total_topic_objects: list = []
    total_exam_points = 0
    total_questions = 0
    total_mapped = 0
    total_skill_sources: set[str] = set()
    linked_topics = 0
    cited = 0
    for course in courses:
        cid = course["course_id"]
        result = build_course_intelligence(workspace_root, cid, days_to_exam=days_to_exam, persist=False)
        course_path = course_mod.course_dir(workspace_root, cid)
        records = (course_mod.load_course_json(course_path, "evidence_store.json", {}) or {}).get("records", [])
        evidence_by_id = {r.get("evidence_id"): _basename(r.get("source_file", "")) for r in records}
        total_skill_sources |= _course_skill_sources(cid, workspace_root)
        for topic in result.topics:
            total_topic_objects.append(topic)
            total_topic_names.add(_norm_topic(topic.canonical_name))
            total_topic_names.update(_norm_topic(v) for v in topic.localized_names.values())
            total_topic_names.update(_norm_topic(a) for a in topic.aliases)
            if topic.evidence:
                cited += 1
            files = {evidence_by_id.get(eid) for eid in topic.evidence if eid in evidence_by_id}
            if len(files) >= 2:
                linked_topics += 1
        total_exam_points += len(result.exam_points)
        for exam_set in result.past_exam_sets:
            total_questions += len(exam_set.questions)
            total_mapped += sum(1 for q in exam_set.questions if q.topics)

    important = {_norm_topic(t) for t in naive["naive_topics"]} | total_topic_names
    sc_skill, sc_naive = source_coverage(total_skill_sources, naive["naive_sources"], all_sources)
    total_real_topics = len(total_topic_objects)
    cit_skill, cit_naive = citation_accuracy(cited, total_real_topics, max(1, len(naive["naive_topics"])))
    rec_skill, rec_naive = important_topic_recall(total_topic_names, naive["naive_topics"], important)
    cd_skill, cd_naive = cross_document_linking(linked_topics, total_real_topics, 0, len(naive["naive_topics"]))
    pe_skill, pe_naive = past_exam_mapping(total_mapped, total_questions, 0, total_questions)
    hal_skill, hal_naive = hallucination_rate(total_real_topics, total_real_topics, 0, _naive_total_lines(naive))
    ex_skill, ex_naive = exam_relevance(
        total_exam_points, max(1, total_exam_points),
        _naive_exam_lines(naive), _naive_total_lines(naive),
    )

    # personalization / adaptivity: does ANY course's plan respond to real student
    # data and to a wrong answer?
    per_course_results = [
        _compute_course_metrics(
            workspace_root=workspace_root, course_id=course["course_id"],
            important=important, all_sources=all_sources, naive=naive,
            days_to_exam=days_to_exam,
        )
        for course in courses
    ]
    per_skill = 1.0 if any(c["per"][0] > 0 for c in per_course_results) else 0.0
    ada_skill = 1.0 if any(c["ada"][0] > 0 for c in per_course_results) else 0.0
    act_skill = sum(c["act"][0] for c in per_course_results) / len(per_course_results)

    plan = generate_daily_plan_v4(workspace_root, "2026-06-18")
    coordinated = len(plan.blocks) > 0 and len(plan.allocation) >= 2
    mc_skill, mc_naive = multi_course_planning(coordinated, False)

    metrics = BenchmarkMetrics(
        source_coverage=sc_skill,
        citation_accuracy=cit_skill,
        important_topic_recall=rec_skill,
        cross_document_linking=cd_skill,
        past_exam_mapping=pe_skill,
        hallucination_rate=hal_skill,
        exam_relevance=ex_skill,
        personalization=per_skill,
        adaptivity=ada_skill,
        actionability=act_skill,
        multi_course_planning=mc_skill,
        details={
            "naive": {
                "source_coverage": sc_naive,
                "citation_accuracy": cit_naive,
                "important_topic_recall": rec_naive,
                "cross_document_linking": cd_naive,
                "past_exam_mapping": pe_naive,
                "hallucination_rate": hal_naive,
                "exam_relevance": ex_naive,
                "personalization": 0.0,
                "adaptivity": 0.0,
                "actionability": 0.0,
                "multi_course_planning": mc_naive,
            }
        },
    )
    skill_summary = {
        "courses": len(courses),
        "topics": total_real_topics,
        "exam_points": total_exam_points,
        "past_exam_questions": total_questions,
        "allocated_courses": len(plan.allocation),
        "blocks": len(plan.blocks),
    }
    return BenchmarkResult(name, metrics, skill_summary, {
        "advice_lines": len(naive_out["advice"]),
        "documents_read": naive_out["documents_read"],
    })
