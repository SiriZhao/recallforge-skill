from pathlib import Path

from exam_review_skill.models import ExamPoint, GenerationReport
from exam_review_skill.quality_guard import check_generation


def test_quality_warns_on_high_confidence_without_source(tmp_path: Path):
    report = GenerationReport()
    ep = ExamPoint(exam_point_id="EP1", topic_id="T1", topic_name="无来源考点", confidence=0.9, source_refs=[])
    check_generation(tmp_path, report, [ep], [])
    assert any("无来源高置信度结论" in w for w in report.warnings)
