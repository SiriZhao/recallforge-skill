from __future__ import annotations

import json
from pathlib import Path

import pytest

from exam_review_skill.benchmark.harness import run_multi_course_benchmark, run_single_course_benchmark

from benchmark_fixtures import (
    build_chinese_fixture,
    build_english_fixture,
    build_mixed_multi_fixture,
)


def _collect_all(root: Path) -> list:
    """Run all three benchmarks and return the result list."""
    results = []
    for fixture, multi in (
        (build_chinese_fixture(root / "a"), False),
        (build_english_fixture(root / "b"), False),
        (build_mixed_multi_fixture(root / "c"), True),
    ):
        if not multi:
            r = run_single_course_benchmark(
                name=fixture.name,
                workspace_root=fixture.workspace_root,
                course_id=fixture.courses[0]["course_id"],
                important_terms=fixture.important_terms,
                source_files=fixture.source_files,
                days_to_exam=3,
            )
        else:
            r = run_multi_course_benchmark(
                name=fixture.name,
                workspace_root=fixture.workspace_root,
                courses=fixture.courses,
                source_files=fixture.source_files,
                days_to_exam=3,
            )
        results.append(r)
    return results


def test_benchmark_all_three_sets_run(tmp_path: Path):
    results = _collect_all(tmp_path)
    assert len(results) == 3
    names = {r.name for r in results}
    assert names == {"chinese", "english", "mixed-multi"}
    for r in results:
        assert r.skill["topics"] >= 2, r.name
        assert r.naive is not None


def test_benchmark_acceptance_gate(tmp_path: Path):
    """The Skill must be meaningfully better than the naive baseline on the
    required metrics across every benchmark set."""
    results = _collect_all(tmp_path)
    # Both pipelines must read ALL the materials (naive is not sabotaged), so
    # source coverage may legitimately tie. The differentiating metrics are where
    # the Skill must be meaningfully better.
    required_tie_or_better = {"source_coverage"}
    required_clearly_better = {
        "citation_accuracy",
        "past_exam_mapping",
        "personalization",
        "adaptivity",
        "actionability",
    }
    for r in results:
        naive = r.metrics.details["naive"]
        for metric in required_tie_or_better | required_clearly_better:
            skill_v = getattr(r.metrics, metric)
            naive_v = naive.get(metric, 0.0)
            assert skill_v >= 0.9, f"{r.name}:{metric} skill={skill_v} too low"
            if metric in required_tie_or_better:
                assert skill_v >= naive_v - 1e-9, (
                    f"{r.name}:{metric} skill={skill_v} below naive={naive_v}"
                )
                continue
            assert skill_v > naive_v + 0.3, (
                f"{r.name}:{metric} skill={skill_v} not meaningfully better than "
                f"naive={naive_v}"
            )


def test_benchmark_hallucination_and_fusion(tmp_path: Path):
    """Hallucination must be ~0 and cross-document linking + multi-course planning
    must beat the baseline across all sets."""
    results = _collect_all(tmp_path)
    for r in results:
        naive = r.metrics.details["naive"]
        assert r.metrics.hallucination_rate <= 0.1, r.name
        assert naive.get("hallucination_rate", 1.0) >= 0.5, r.name
        assert r.metrics.cross_document_linking > naive.get("cross_document_linking", 0.0), r.name
        assert r.metrics.exam_relevance > naive.get("exam_relevance", 0.0), r.name


def test_multi_course_planning_beats_baseline(tmp_path: Path):
    fx = build_mixed_multi_fixture(tmp_path / "c")
    r = run_multi_course_benchmark(
        name="mixed-multi",
        workspace_root=fx.workspace_root,
        courses=fx.courses,
        source_files=fx.source_files,
        days_to_exam=3,
    )
    assert r.metrics.multi_course_planning == 1.0
    assert r.metrics.details["naive"]["multi_course_planning"] == 0.0
    assert r.skill["allocated_courses"] == 2  # both courses in one plan
    assert r.skill["blocks"] > 0


def test_benchmark_results_persist(tmp_path: Path):
    """Benchmark results are persisted for the final acceptance report."""
    results = _collect_all(tmp_path)
    out = tmp_path / "benchmark_results.json"
    out.write_text(
        json.dumps([r.to_dict() for r in results], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    data = json.loads(out.read_text(encoding="utf-8"))
    assert len(data) == 3
    for entry in data:
        assert "metrics" in entry
        assert "skill_summary" in entry
        assert "naive_summary" in entry
