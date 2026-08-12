# Round 4 Report — Student Model + 多课程 Adaptive Planner

> Scope per the master instruction: persistent per-course Student Model with
> composite mastery, diagnostic test, single-course adaptive planner, formal Exam
> Week Orchestrator, cross-course priority (not simple average), anti-starvation,
> topic-level study blocks, dynamic replan events, exam-day release, bilingual user
> control, and five realistic scenario fixtures.

## What was built (all real, tested code)

New packages:
* `exam_review_skill/student/` — `mastery.py`, `sessions.py`, `diagnostic.py`,
  `store.py`.
* `exam_review_skill/planner/` — `course_planner.py`, `orchestrator.py`,
  `events.py`, `nl.py`.

### 1. Student Model (per-course, persistent)

Each topic carries: `mastery`, `mastery_score`, `confidence`, `questions_attempted`,
`accuracy`, `difficulty_coverage`, `hint_dependency`, `last_reviewed`, `wrong_count`,
`mistake_types`, `forgetting_risk`, `transfer_performance`, `question_type_coverage`.
Only real answer sessions mutate it (`record_answer` is the sole write path).

### 2. Mastery ≠ Accuracy (verified)

Composite formula:

```
score = 0.35*accuracy + 0.15*(0.5*difficulty_coverage + 0.5*difficulty_quality)
      + 0.15*independence(1-hint_dependency) + 0.10*recency
      + 0.10*transfer + 0.05*type_coverage
      scaled by (1 - repeat_error_penalty)
```

Tests prove it differs from raw accuracy (5/5 correct at difficulty-1 only →
accuracy 1.0 but mastery `developing`), that difficulty/transfer raise it, hints
lower it, and repeat errors penalize it.

### 3. No data → unknown (verified)

`compute_mastery` returns `mastery="unknown"`, `mastery_score=None` when
`questions_attempted == 0`. Unknown topics are never added to weak/strong points
(no fabricated labels).

### 4. Diagnostic Test (verified)

10-20 minute diagnostic covering the knowledge graph: unknown topics first, then
weak/high-forgetting, then breadth. `test_diagnostic_prioritizes_unknown_and_weak`.

### 5. Single-course Adaptive Planner (verified)

`build_course_plan` combines exam date, target score, available time, risk radar,
mastery, forgetting, past-exam coverage, and wrongbook. Blocks are concrete
(course / topic / duration / reason / task / practice / completion_criterion).
Mastery data drives block kind (weak → practice, unknown near exam → cram,
proficient → maintenance).

### 6. Formal Exam Week Orchestrator (verified)

Upgraded from the Round 1 skeleton to a real scheduler producing topic-level global
daily plans. Cross-course priority considers:

* **Urgency** — exam proximity
* **Score Gain Opportunity** — target gap × risk × urgency
* **Risk** — share of S/A exam points
* **Target Gap** — (target − current)/100
* **Learning Cost** — normalized (cheaper wins slightly)
* **Forgetting** — average topic forgetting risk
* **Course Maintenance** — anti-starvation minimum for every active course

### 7. Not simple average (verified)

Scenario A: probability (exam in 1d) and organic (2d) get more time than botany
(8d) — never a 3h/3h split. `test_scenario_a_four_courses_not_simple_average`.

### 8. Anti-starvation (verified)

Every active course keeps a minimum maintenance allocation + spaced review; the far
botany course still appears in the plan. `test_scenario_a_anti_starvation_maintenance`.

### 9. Study Blocks (verified)

Every block carries course / topic / duration / reason / task / practice /
completion_criterion (schema: `global_study_plan.schema.json` now includes
`topic_id` / `topic_name` / `practice`).

### 10. Dynamic replan events (verified)

`replan_events.jsonl` + state effects:
* `quiz_completed`, `wrong_answer`, `topic_mastered`, `new_material`,
  `new_past_exam` — recorded for replanning.
* `exam_rescheduled` — updates the exam calendar + manifest.
* `hours_changed` — updates workspace daily hours.
* `target_changed` — updates the course manifest.
* `course_completed` — marks the course completed AND releases its future time to
  other courses (verified: calculus removed, botany allocation grows).

### 11. Bilingual natural-language control (verified)

Equivalent zh/en inputs map to the same action:

| zh | en | action |
|---|---|---|
| 今天不想学植物学 | "I don't want to study botany today" | skip botany |
| 微积分只求及格 | "I only need to pass calculus" | change_target 60 |
| 明天只有3小时 | "I only have three hours tomorrow" | change_hours 3.0 |
| 有机化学考试提前了 | "My probability exam moved up" | schedule |
| 今天学什么 | "What should I study today?" | none (just plan) |

### 12. User control > planner

`skip_courses` / `total_hours_override` / `course_hours` / `target_score_changes` /
`exam_date_changes` all win over the planner (verified in
`test_hours_override_and_skip`).

## CLI

New commands: `workspace diagnostic`, `workspace answer`, `workspace plan-v4`,
`workspace replan`, `workspace nl`. All smoke-tested live.

## QA coverage vs. required list

| Scenario | Test |
|---|---|
| A: 4 courses, 7 days | `test_scenario_a_four_courses_not_simple_average`, `test_scenario_a_anti_starvation_maintenance` |
| B: two exams same day | `test_scenario_b_two_exams_same_day` |
| C: exam moved earlier | `test_scenario_c_exam_moved_up_replans` |
| D: one course badly behind | `test_scenario_d_lagging_course_gets_boosted` |
| E: mixed zh/en courses | `test_scenario_e_mixed_chinese_english` |

Plus: composite-mastery tests (5), diagnostic tests (3), session/wrongbook tests (5),
event tests (4), NL tests (2), orchestrator behavior tests (3).

## Test results

* Full suite: **121 passed, 1 skipped** (Round 3 baseline 95 + 26 new Round 4 tests).
* The 1 skipped test is the Round 2 OCR-engine-present branch (tesseract binary not
  installed) — unchanged.

## Schemas

* `course_student_state.schema.json` — v4 per-topic mastery fields.
* `global_study_plan.schema.json` — topic_id/topic_name/practice on blocks,
  expanded kind enum.

Commit: `feat: add persistent student model and exam-week planner`
