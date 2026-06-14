import json
from pathlib import Path

from exam_review_skill.cli import main


def test_smoke_run(tmp_path: Path):
    output = tmp_path / "out"
    main([
        "run",
        "--input", "examples/input",
        "--output", str(output),
        "--course", "实验化学",
        "--exam-date", "2026-06-25",
        "--target-score", "80",
        "--daily-hours", "4",
    ])
    assert output.exists()
    assert (output / "course_index.json").exists()
    assert (output / "exam_graph.json").exists()
    assert (output / "risk_radar.json").exists()
    assert (output / "13_临考急救包.md").exists()
    assert (output / "generation_report.md").exists()
    graph = json.loads((output / "exam_graph.json").read_text(encoding="utf-8"))
    assert any(p.get("source_refs") for p in graph)
