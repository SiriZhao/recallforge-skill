from __future__ import annotations

from dataclasses import asdict

from ..models import ExamPointModel, _now_iso


MASTERY_GAP = {
    "unknown": 0.8,
    "novice": 0.6,
    "developing": 0.4,
    "proficient": 0.1,
}


def build_risk_radar(
    exam_points: list[ExamPointModel],
    *,
    mastery: dict | None = None,
    days_to_exam: int | None = None,
) -> list[ExamPointModel]:
    """Explainable S/A/B/C risk radar.

    score = 0.30*exam_value + 0.25*evidence_support + 0.25*mastery_gap
            + 0.15*urgency + 0.05*(1 - learning_cost_norm)

    Every component is recorded in priority_rationale so the user can see exactly
    WHY an item is S (or A/B/C). S >= 0.78, A >= 0.62, B >= 0.46, else C.
    """
    mastery = mastery or {}
    urgency = 1.0 / (days_to_exam + 1) if days_to_exam is not None else 0.2
    for point in exam_points:
        exam_value = (point.importance / 5.0) * point.likelihood_estimate
        evidence_support = min(1.0, len(point.evidence) / 4.0)
        level = mastery.get(point.topic_id, {}).get("level", "unknown")
        gap = MASTERY_GAP.get(level, 0.8)
        learning_cost_norm = min(1.0, point.learning_cost / 5.0)

        score = (
            0.30 * exam_value
            + 0.25 * evidence_support
            + 0.25 * gap
            + 0.15 * urgency
            + 0.05 * (1 - learning_cost_norm)
        )
        priority = "S" if score >= 0.78 else "A" if score >= 0.62 else "B" if score >= 0.46 else "C"
        point.priority = priority
        point.priority_rationale = [
            f"score={score:.2f} = 0.30*exam_value({exam_value:.2f}) + "
            f"0.25*evidence({evidence_support:.2f}) + 0.25*mastery_gap({gap:.2f}) + "
            f"0.15*urgency({urgency:.2f}) + 0.05*(1-cost({learning_cost_norm:.2f}))",
            f"importance={point.importance}, likelihood={point.likelihood_estimate:.2f} "
            f"(heuristic, not a statistical probability), evidence={len(point.evidence)} refs",
            f"mastery level={level}, days_to_exam={days_to_exam}",
        ]
    return sorted(exam_points, key=lambda p: {"S": 0, "A": 1, "B": 2, "C": 3}[p.priority])


def risk_radar_state(exam_points: list[ExamPointModel]) -> dict:
    return {
        "items": [asdict(p) for p in exam_points],
        "updated_at": _now_iso(),
    }
