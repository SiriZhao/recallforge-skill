from __future__ import annotations

import math
from datetime import date, datetime

from ..models import StudentModel, TopicMastery


LEVELS = ["unknown", "novice", "developing", "proficient"]


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def compute_mastery(topic: TopicMastery, *, today: date | None = None) -> TopicMastery:
    """Compute the composite mastery for one topic.

    Mastery is deliberately NOT equal to accuracy. It combines:
      accuracy                 (how many correct)
      question difficulty      (correct at higher difficulty weighs more)
      independent completion   (correct without hints > correct with hints)
      hints                    (hint_dependency lowers the score)
      recency                  (recent practice > old practice)
      repeat errors            (repeated mistakes on the same topic penalize)
      transfer performance     (correct on new-form questions proves understanding)
      question-type coverage   (breadth of question types practiced)

    No real data -> mastery stays 'unknown' (never pretended to be 0.5).
    """
    today = today or date.today()
    attempts = topic.questions_attempted
    if attempts == 0:
        topic.mastery = "unknown"
        topic.mastery_score = None
        topic.confidence = 0.0
        return topic

    accuracy = topic.accuracy if topic.accuracy is not None else 0.0

    # 1) accuracy component (base)
    acc_comp = accuracy

    # 2) difficulty component: how many distinct difficulty levels attempted + correct
    numeric_levels = {k: v for k, v in topic.difficulty_coverage.items() if str(k).isdigit()}
    levels_attempted = len(numeric_levels)
    difficulty_comp = min(1.0, levels_attempted / 4.0)
    hard_correct = sum(
        n for d, n in numeric_levels.items() if int(d) >= 3
    )
    total = max(1, attempts)
    difficulty_quality = min(1.0, hard_correct / total)

    # 3) independence: hints lower the score
    hint = topic.hint_dependency if topic.hint_dependency is not None else 0.0
    independence_comp = 1.0 - hint

    # 4) recency: last review within 3 days preserves mastery, older decays
    if topic.last_reviewed:
        try:
            last = datetime.fromisoformat(topic.last_reviewed).date()
            days = max(0, (today - last).days)
        except (TypeError, ValueError):
            days = 14
    else:
        days = 14
    recency_comp = math.exp(-days / 10.0)

    # 5) repeat errors penalty
    repeat_penalty = 0.0
    if topic.wrong_count > 0 and attempts > 0:
        wrong_ratio = topic.wrong_count / attempts
        repeat_penalty = min(0.3, wrong_ratio * 0.3)

    # 6) transfer performance: correct on NEW question forms proves understanding
    new_correct = topic.transfer_performance.get("new_form_correct", 0)
    new_total = topic.transfer_performance.get("new_form", 0)
    transfer_comp = (new_correct / new_total) if new_total else 0.0
    if new_total == 0:
        transfer_comp = 0.5 * (1.0 - 0.3)  # no transfer data: mild neutral, not zero

    # 7) question-type coverage
    qtypes = len(topic.question_type_coverage)
    type_comp = min(1.0, qtypes / 3.0)

    score = (
        0.35 * acc_comp
        + 0.15 * (0.5 * difficulty_comp + 0.5 * difficulty_quality)
        + 0.15 * independence_comp
        + 0.10 * recency_comp
        + 0.10 * transfer_comp
        + 0.05 * type_comp
    ) * (1.0 - repeat_penalty)

    score = _clamp(score)
    topic.mastery_score = round(score, 3)

    if score < 0.35:
        topic.mastery = "novice"
    elif score < 0.65:
        topic.mastery = "developing"
    else:
        topic.mastery = "proficient"

    # confidence grows with attempts
    topic.confidence = _clamp(0.3 + attempts * 0.12)
    topic.forgetting_risk = _clamp((1.0 - score) * 0.5 + math.exp(-days / 7.0) * 0.5)
    return topic


def compute_forgetting_risk(topic: TopicMastery, *, today: date | None = None) -> float:
    """Forgetting risk: time since last review + current mastery. Higher mastery and
    recent review => lower risk."""
    today = today or date.today()
    if not topic.last_reviewed:
        return 0.8
    try:
        last = datetime.fromisoformat(topic.last_reviewed).date()
        days = max(0, (today - last).days)
    except (TypeError, ValueError):
        days = 7
    time_factor = math.exp(-days / 7.0)
    mastery_factor = 0.2 if topic.mastery == "proficient" else 0.4 if topic.mastery == "developing" else 0.7
    return _clamp(1.0 - (time_factor * (1.0 - mastery_factor * 0.5)))


def update_weak_strong_points(model: StudentModel) -> None:
    """Derive weak/strong points from real mastery data only. Never keyword-seeded."""
    weak: list[str] = []
    strong: list[str] = []
    for tid, tm in model.topics.items():
        if tm.questions_attempted == 0 or tm.mastery == "unknown":
            continue
        if tm.mastery in ("novice", "developing"):
            weak.append(tid)
        elif tm.mastery == "proficient" and tm.confidence >= 0.5:
            strong.append(tid)
    model.weak_points = weak
    model.strong_points = strong


def wrong_patterns_from_topics(model: StudentModel) -> None:
    """Aggregate mistake types across topics into course-level wrong patterns."""
    from collections import Counter

    counter: Counter = Counter()
    for tm in model.topics.values():
        for mistake in tm.mistake_types:
            counter[mistake] += 1
    model.wrong_patterns = [m for m, _ in counter.most_common(6)]


def sync_mastery_levels(model: StudentModel, *, today: date | None = None) -> StudentModel:
    """Recompute all topic masteries and derived fields. Returns the model."""
    for tm in model.topics.values():
        compute_mastery(tm, today=today)
        tm.forgetting_risk = compute_forgetting_risk(tm, today=today)
    update_weak_strong_points(model)
    wrong_patterns_from_topics(model)
    return model
