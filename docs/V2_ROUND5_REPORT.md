# Round 5 Report — Tutor + Quiz + Diagnosis + Wrongbook + Cram

> Scope per the master instruction: complete the learning loop - Tutor (course
> first, structured, supplementary-marked), Quiz Engine (all modes), adaptive
> difficulty L1-L4, question provenance, grading with process analysis, 13-category
> diagnosis, wrongbook that drives mastery/risk/planner/quiz/cram, retry scheduling,
> genuinely distinct cram tiers, 30-minute rescue, multi-course cram coordination,
> bilingual question/explanation language, and a full closed-loop test.

## What was built (all real, tested code)

New package `exam_review_skill/tutor/`: `tutor.py`, `quiz.py`, `grading.py`,
`diagnosis.py`, `wrongbook.py`, `retry.py`, `cram.py`.

### 1. Tutor — course-first, structured (verified)

`build_tutor_response` returns sections: **Intuition → Definition → Core
Formula/Principle → Conditions → Method → Example → Common Mistake → Check
Question**. Course content is used verbatim from the topic evidence. **Subject
adaptive**: a subject with no formulas gets NO formula section
(`test_tutor_no_formula_subject_adaptive`). When the course materials lack content,
the tutor says so ("课程资料中暂无示例，请补充资料") and marks model additions as
**Supplementary explanation** — never silently presented as teacher material.

### 2. Quiz Engine — all 8 modes (verified)

`diagnostic`, `s-priority`, `weak-topic`, `past-exam-style`, `mixed`, `wrongbook`,
`speed-run`, `cram` - all supported and tested (`test_quiz_all_modes_supported`).
Each mode selects topics by its own logic:
* `s-priority` → S/A exam points only (`test_quiz_s_priority_selects_s_topics`)
* `weak-topic` → novice/developing mastery topics (`test_quiz_weak_topic_selects_weak`)
* `past-exam-style` → topics with past-exam links, generating variants
* `wrongbook` → topics with unresolved wrongbook entries
* fallback: a mode that selects nothing degrades to a breadth-first mixed selection
  (never an empty quiz)

### 3. Adaptive difficulty L1-L4 (verified)

`_adaptive_level`: no data → L1 Recall; sustained correct (≥4 attempts ≥80%) → L3
Variant / L4 Transfer; repeated errors → L1 Recall. Verified:
`test_adaptive_difficulty_rises_with_sustained_correct` (8/8 correct → higher level
than 8/8 wrong). The student model already routes `is_new_form` (L3+) into transfer
performance, feeding back into mastery.

### 4. Question provenance (verified)

Every past-exam variant keeps `derived_from` (`past_exam_2024.pdf:1`),
`source_question` (the original body), `variation_type`, and `topic`
(`test_past_exam_variant_keeps_provenance`).

### 5. Grading with process analysis (verified)

`grade_answer` returns `correct`, `score`, `feedback`, `process_analysis`,
`mistake_type`. Supports multiple choice (option match), fill-blank (normalized
match), short answer/calculation/derivation/essay/diagram (keyword + coverage +
length heuristics), and **bilingual answers** (a Chinese answer to an English
reference is graded by meaning via a bilingual alias map -
`test_grade_bilingual_answer`).

### 6. Diagnosis taxonomy — 13 categories (verified)

`concept_gap`, `formula_recall`, `condition_misread`, `prerequisite_gap`,
`calculation_error`, `algebra_error`, `sign_error`, `unit_error`,
`reasoning_jump`, `question_misread`, `method_selection`, `memory_failure`,
`careless_error`, `unknown`. `diagnose_wrong_answer` also detects a **prerequisite
gap** when a prerequisite topic is unknown/weak (the real root cause) and returns
`prerequisite_fix` topic ids (`test_diagnosis_prerequisite_gap_detected`).

### 7. Wrongbook drives everything (verified)

`add_wrongbook_entry` persists real wrong answers with diagnosis, severity,
prerequisite fix, and next-review date. Fabricated content is rejected
(`test_wrongbook_rejects_fabricated`). Wrongbook entries affect:
* **mastery** - via `record_grading_to_student` feeding the student model
* **planner** - the course planner's wrong_count boost (Round 4)
* **future quiz** - the `wrongbook` quiz mode selects those topics
* **cram** - unresolved mistakes appear in cram plans

### 8. Retry scheduling (verified)

`schedule_retry` factors mistake type (severity), repeat count, mastery, and exam
proximity: severe (prerequisite_gap) → retry in 1 day priority S; careless + near
proficient → spaced 3+ days priority B; repeated errors → tomorrow
(`test_retry_scheduling_priority`).

### 9. Cram modes genuinely distinct (verified)

`7d` (7 item kinds) > `3d` (6) > `24h` (5) > `3h` (4) > `1h` (3) > `30m` (2 kinds +
S-only). Each is a strict subset of the previous - item counts must differ
(`test_cram_modes_are_distinct` asserts 7d > 24h > 3h > 30m and 7d > 3d).

### 10. 30-minute rescue is strict (verified)

Keeps ONLY S/A-level topics (falling back to highest-priority if no S/A exists),
with only core formula/condition/trap items - never the whole book
(`test_cram_30m_rescue_is_strict` asserts kinds restricted and ≤3 items).

### 11. Multi-course cram coordination (verified)

When probability (exam tomorrow) and organic (exam in 2 days) are both near, the
Exam Week Orchestrator schedules emergency cram for BOTH plus maintenance for the
far botany course - not just the last-mentioned one
(`test_cram_multicourse_coordination`).

### 12. Language: question_language / explanation_language (verified)

Independently controlled (`test_quiz_language_independent`): English question
("State the definition of ...") + Chinese explanation works for English textbooks /
international courses.

## CLI

New commands: `workspace tutor`, `workspace quiz`, `workspace cram`. All smoke-tested
live (tutor structured output, past-exam-style quiz with provenance + bilingual
language, 30m cram plan).

## Full closed-loop test (verified)

`test_full_learning_loop` runs the complete loop end-to-end:

```
plan -> learn (tutor) -> quiz -> wrong answer -> grading + diagnosis
-> wrongbook entry -> replan event -> replanned plan -> retry scheduling
-> correct re-attempt -> mastery update -> cram includes the topic
```

It asserts every step mutates the next: the wrong answer updates mastery
(wrong_count=1), enters the wrongbook with the diagnosis, records a replan event,
the re-attempt improves accuracy to 0.5, and the mastery is non-unknown on reload.

## Test results

* Full suite: **146 passed, 1 skipped** (Round 4 baseline 121 + 25 new Round 5
  tests). The 1 skipped test is the unchanged Round 2 OCR-engine-present branch.

## Schemas

New: `quiz_question.schema.json`, `cram_plan.schema.json`, `wrongbook_v2.schema.json`.

Commit: `feat: complete adaptive tutoring and practice loop`
