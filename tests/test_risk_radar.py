from exam_review_skill.models import ExamPoint, StudentState
from exam_review_skill.risk_radar import build_risk_radar


def test_risk_priority_reasonable():
    points = [
        ExamPoint(exam_point_id="EP1", topic_id="T1", topic_name="高频计算", frequency=5, score_potential=5, difficulty=4, source_refs=[{"source_file": "past.txt"}]),
        ExamPoint(exam_point_id="EP2", topic_id="T2", topic_name="低频概念", frequency=1, score_potential=1, difficulty=1, source_refs=[{"source_file": "lecture.txt"}]),
    ]
    risks = build_risk_radar(points, StudentState(course_name="x"), days_left=2)
    by_name = {r.topic_name: r.priority for r in risks}
    assert by_name["高频计算"] in {"S", "A"}
    assert by_name["低频概念"] in {"B", "C"}
    assert risks[0].priority in {"S", "A"}
