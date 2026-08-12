# Round 3 Report — Course Knowledge Model + Exam Intelligence (the exam brain)

> Scope per the master instruction: Topic-centric architecture (Topic replaces
> chunk as the core object), full Topic schema, cross-language Topic fusion,
> knowledge graph with real prerequisite edges, separate exam model, explainable
> risk radar, past-exam intelligence, teacher style with evidence tiers, conflict
> handling, and exam coverage report. Then QA, docs, commit.

## What was built (all real, tested code)

New package `exam_review_skill/knowledge/`:
`topic.py`, `fusion` (inside topic), `graph.py`, `exam.py`, `teacher.py`,
`conflict.py`, `coverage.py`, `risk.py`, `build.py`.

### 1. Topic-centric architecture

`Topic` (v3 `KnowledgeTopic`) is the core object; evidence (chunks/pages) is only
the proof. Every Topic field (`definitions`, `formulas`, `methods`,
`common_mistakes`) stores a **verbatim evidence substring** plus `evidence_refs`.
The hallucination guard drops any topic with zero evidence refs.

### 2. Topic schema (all required fields)

`topic_id`, `canonical_name`, `localized_names` (zh-CN/en-US), `aliases`,
`chapter`, `prerequisites`, `definitions`, `formulas`, `concepts`, `methods`,
`common_mistakes`, `question_types`, `evidence` (citation ids),
`teacher_emphasis` (observed/strongly_inferred/inferred/unknown),
`teacher_emphasis_refs`, `past_exam_links`, `fusion_confidence`,
`source_confidence`, `inferred`.

### 3. Cross-language Topic fusion (verified)

`Central Limit Theorem` / `中心极限定理` / `CLT` fuse into ONE topic via the
terminology map (Round 1). Aliases are preserved; `fusion_confidence` rises with
cross-file + cross-language evidence. **No false merging**: different concepts
(CLT vs conditional probability) stay separate topics, and generic headings
(`chapter 12`, `期末试卷`, `第五章 ...`) never become topics.

### 4. Knowledge Graph (verified)

Edges: `prerequisite`, `related_to`, `part_of`, `often_confused_with`, `used_in`.
**`prerequisite` is real**: created only from explicit text evidence
(`Prerequisite: normal distribution`), carrying `evidence_refs` — never from list
adjacency (the v0 fake-graph fix). `related_to` from co-mentioned topics in one
evidence record; `used_in` from topics co-mapped to the same past-exam question.

### 5. Exam Model (separate `exam_model.json`)

Kept separate from the Course Knowledge Model. Each ExamPoint:
`topic`, `importance`, `likelihood_estimate`, `confidence`,
`expected_score_range`, `question_types`, `teacher_emphasis`,
`past_exam_frequency`, `learning_cost`, `evidence`, `priority`, `priority_rationale`.

**`likelihood_estimate` is explicitly an ordinal heuristic, NOT a statistical
probability** — documented in the schema and in every rationale string.

### 6. Risk Radar (S/A/B/C, explainable)

Transparent, deterministic score:

```
score = 0.30*exam_value + 0.25*evidence_support + 0.25*mastery_gap
        + 0.15*urgency + 0.05*(1 - learning_cost_norm)
```

Thresholds: S>=0.78, A>=0.62, B>=0.46, else C. Every item carries a full
`priority_rationale` with the actual numbers, so the user can see exactly WHY an
item is S (tested: `test_risk_radar_explainable_priority`).

### 7. Past Exam Intelligence (verified)

Each past-exam file is a separate `PastExamSet` with per-question extraction:
`year`, `question_number`, `question_type`, `score`, `topic`, `subtopics`,
`difficulty`, `methods`, `common_traps`, `solution`, `evidence_ref`.
Bidirectional `Question <-> Topic` mapping:
Topic->Questions via `past_exam_links`, Question->Topics via `topics` list
(tested: `test_question_topic_bidirectional_mapping`).

### 8. Evidence weight differentiation (not hard-coded globally)

`evidence_weight_for` defaults past-exam/answer-key evidence higher than lecture
notes, but a **per-course override table** (`evidence_weights`) can change it
(tested: `test_evidence_weight_past_exam_higher_and_overrideable`).

### 9. Teacher Style (verified, tiered)

Analyzes chapter frequency, question-type frequency, calc vs proof, conceptual vs
procedural, homework reuse, parameter variation, integrated questions, trap style.
Every claim carries an explicit tier:
**Observed / Strongly Inferred / Inferred / Unknown**. No unsupported
"老师特别喜欢考…" claims: `test_teacher_style_unknown_when_no_evidence` asserts the
unknown tier emits zero claims.

### 10. Conflict handling (verified)

Contradictory definitions from different sources are **recorded, never silently
overwritten**. Resolution priority: exam relevance & source authority > recency >
teacher material. Different-language definition pairs are flagged as likely
translation pairs needing user confirmation. `conflicts.json` is persisted and
`resolved=False` until the user confirms.

### 11. Exam Coverage Report (verified)

Answers "我这些资料够不够?" with concrete numbers: material coverage, chapter
coverage, past-exam coverage, answer coverage, unresolved documents,
low-confidence topics, and a fail-closed verdict (`insufficient: ...` when evidence
is missing — never a fake "adequate").

## CLI

`workspace build --dir <ws> --course <id> [--days-to-exam N]` builds and persists
knowledge_graph.json, exam_model.json, risk_radar.json, conflicts.json,
coverage_report.json, and prints a summary (topics, exam points, past exam sets,
conflicts, coverage verdict, risk radar).

## Schemas

Updated: `knowledge_graph.schema.json` (topic-centric), `exam_model.schema.json`
(separate exam model + evidence weights), `risk_radar.schema.json` (explainable).
New: `conflicts.schema.json`, `coverage_report.schema.json`. All validated in
`test_knowledge_schemas.py`.

## QA coverage vs. required list

| Required | Covered by |
|---|---|
| 跨文件 Topic fusion | `test_cross_language_topic_fusion`, `test_knowledge_edges_relations` |
| 中英文 Topic fusion | `test_cross_language_topic_fusion`, `test_no_false_merging_of_different_concepts` |
| citation preservation | `test_citation_preservation` |
| past exam mapping | `test_past_exam_sets_modeled_per_file`, `test_question_topic_bidirectional_mapping` |
| formula evidence | `test_formula_evidence_preserved` |
| teacher-style evidence | `test_teacher_style_tiers`, `test_teacher_style_unknown_when_no_evidence` |
| conflict resolution | `test_conflict_detected_not_silently_overwritten`, `test_same_language_contradiction_flags_real_conflict` |
| hallucination guard | `test_no_hallucination_without_evidence`, `test_citation_preservation` |

## Test results

* Full suite: **95 passed, 1 skipped** (Round 2 baseline 70 + 25 new knowledge tests).
* New knowledge tests: 25 across `test_knowledge_topic.py`,
  `test_knowledge_exam.py`, `test_knowledge_risk_conflict_coverage.py`,
  `test_knowledge_schemas.py`.

## Naming note

The v3 `Topic`/`ExamPoint` dataclasses were renamed to `KnowledgeTopic`/
`ExamPointModel` because the shared `models.py` still carries the v0
`Topic`/`ExamPoint` used by the legacy batch pipeline (removed in a later round).

Commit: `feat: add evidence-grounded course and exam intelligence`
