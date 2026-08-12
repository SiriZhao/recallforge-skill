# V2 Migration Plan — exam-review-skill v0.1.0 → v2.0.0

> Phased rebuild of the audited `v0.1.0` batch generator into the frozen v2
> architecture (`V2_ARCHITECTURE.md`). Each round ends with a full test pass and a
> commit. No empty shells, no mocked main flow, no fabricated PASS.

## Guiding Rules

* Keep existing user changes; never overwrite unrelated files.
* Real state > mock data: no `MockProvider` output may persist into real course state
  at any round.
* Every round: run the full test suite; only commit when acceptance passes.
* Incremental, reviewable commits per round.

## Round 0 — DONE (this round)

* Full audit of existing implementation (`docs/V2_RESTART_AUDIT.md`).
* v2 architecture frozen (`docs/V2_ARCHITECTURE.md`).
* Migration plan written (this file).
* Commit: `refactor: establish exam review v2 architecture`.

Acceptance: six audit questions answered PASS with source-level evidence; baseline
4 tests still pass.

## Round 1 — DONE (multi-course workspace + bilingual foundation)

Scope delivered per the Round 1 master instruction:

* Workspace layer: `workspace_state.json`, `exam_calendar.json`,
  `global_study_plan.json`, `overrides.json` + schemas.
* True multi-course model: isolated `courses/<id>/` with manifest, document index,
  knowledge graph, exam model, student state, wrongbook, study plan, sessions,
  terminology map.
* Course Manifest with all required fields and exam edge cases.
* Exam Week Orchestrator: transparent heuristic scheduler with anti-starvation,
  daily global plan (per-block why/risk/goal/done-when), user overrides.
* i18n foundation: stable English keys, zh-CN/en-US catalogs (extensible),
  LanguageProfile (UI/source/output), per-course terminology maps, mixed-language
  topic normalization.
* Sandbox/mock contamination guard on every real-state write.
* Dead code removed (`templates/*.j2`, unused jinja2/pydantic); deps cleaned;
  version 0.2.0.

Acceptance (all PASS, tested): multi-course workspace; course isolation; global
exam calendar; cross-course planner skeleton; zh locale; en locale; mixed-language
model; stable internal schemas.

See `docs/V2_ROUND1_REPORT.md`. 48 tests green.

Provider abstraction + real providers were **deferred to Round 2** (multimodal
ingestion is their first consumer).

## Round 2 — DONE (Native Multimodal Document Intelligence)

Scope delivered per the Round 2 master instruction:

* Unified pipeline: File -> Classifier -> Native Parser -> Visual Renderer ->
  Multimodal Understanding -> Structured Evidence (`exam_review_skill/ingestion/`).
* Document types: PDF, PPTX, DOCX, TXT, MD, PNG, JPG, JPEG.
* Native first: PDF text layer, PPTX text boxes, DOCX paragraphs preserve file,
  page, slide, heading, question_number.
* Cheap routing: vision only when needed (scanned/image-only pages, formulas,
  tables, diagrams, handwriting, exam papers).
* `MultimodalProvider` abstraction with capabilities + runtime registry
  (openai / deepseek / synthetic) - no single-vendor hard-coding; fail closed.
* Local OCR disabled by default; `extraction_method=ocr_fallback`, low confidence,
  unresolved on engine failure (never fabricated).
* Formula verification: ambiguity signals force visual re-view; unconfirmed
  ambiguity stays low-confidence.
* Exam-paper structure kept field-by-field (question_number, options, score,
  subquestions, answer_area, handwritten_annotation).
* Evidence objects + per-course `evidence_store.json` with content-hash cache,
  incremental ingestion, dedup.
* Synthetic records rejected from real state; CLI `workspace ingest` with clean
  fail-closed error.
* 22 new ingestion tests (70 total, 1 skipped: tesseract binary absent).

Acceptance (all PASS, tested): see `docs/MULTIMODAL_INGESTION_REPORT.md`.

Commit: `feat: rebuild ingestion around native multimodal understanding`

## Round 3 — DONE (Course Knowledge Model + Exam Intelligence + 真题建模)

Scope delivered per the Round 3 master instruction:

* Topic-centric architecture: `KnowledgeTopic` is the core object; chunks/pages are
  only evidence. Full topic schema (localized names, aliases, chapter,
  prerequisites, definitions, formulas, concepts, methods, common mistakes,
  question types, evidence, teacher emphasis, past-exam links).
* Cross-language topic fusion (CLT / 中心极限定理 / Central Limit Theorem) with
  aliases + fusion confidence; no false merging; no generic-heading garbage.
* Knowledge graph with real `prerequisite` edges (evidence-backed, never adjacency),
  plus `related_to` / `part_of` / `often_confused_with` / `used_in`.
* Separate `exam_model.json`; `likelihood_estimate` explicitly an ordinal heuristic,
  not a statistical probability.
* Explainable S/A/B/C risk radar with full per-item rationale.
* Past-exam intelligence: per-file exam sets, per-question extraction, bidirectional
  Question<->Topic mapping.
* Evidence-weight differentiation with per-course override (not hard-coded).
* Teacher style with Observed/Strongly Inferred/Inferred/Unknown tiers; no
  unsupported claims.
* Conflict handling (record, never silent overwrite; authority/recency/exam-relevance
  ranking; user confirmation).
* Exam coverage report (material/chapter/past-exam/answer coverage, unresolved
  documents, low-confidence topics, fail-closed verdict).
* CLI `workspace build`; schemas for knowledge graph / exam model / risk radar /
  conflicts / coverage.

Acceptance (all PASS, tested): see `docs/V2_ROUND3_REPORT.md`. 95 tests green.

Note: v3 Topic/ExamPoint renamed to `KnowledgeTopic`/`ExamPointModel` to coexist
with the v0 batch-pipeline classes until Round 6 removes the legacy path.

## Round 4 — DONE (Student Model + 多课程 Adaptive Planner)

Scope delivered per the Round 4 master instruction:

* Persistent per-course Student Model with composite mastery (accuracy + difficulty
  + independence/hints + recency + repeat errors + transfer + type coverage),
  per-topic statistics, forgetting risk. No data -> `unknown`, never a pretend 0.5.
* Diagnostic test (10-20 min) selecting topics by graph coverage, unknown/weak first.
* Single-course adaptive planner (exam date, target, time, risk radar, mastery,
  forgetting, coverage, wrongbook) with topic-level Study Blocks (course / topic /
  duration / reason / task / practice / completion criterion).
* Formal Exam Week Orchestrator: cross-course priority (urgency / score gain / risk /
  target gap / learning cost / forgetting / maintenance), not simple average, with
  anti-starvation minimum maintenance + cram mode.
* Dynamic replan events (quiz_completed, wrong_answer, topic_mastered, new_material,
  new_past_exam, exam_rescheduled, hours_changed, target_changed, course_completed);
  exam-day completion releases the course's future time to others.
* User control wins over the planner: skip / pin / reduce / change target / change
  hours, all parsed from bilingual natural language (zh/en).
* CLI: `workspace diagnostic / answer / plan-v4 / replan / nl`.

Acceptance (all PASS, tested): 5 scenarios (A-E) + composite-mastery / diagnostic /
session / events / NL tests. 121 tests green.

## Round 5 — DONE (Tutor + Quiz + Diagnosis + Wrongbook + Cram)

Scope delivered per the Round 5 master instruction:

* Tutor: course-first structured explanation (Intuition / Definition / Core
  Formula-Principle / Conditions / Method / Example / Common Mistake / Check),
  subject-adaptive (no formula section when the subject has none), model additions
  clearly marked "Supplementary explanation".
* Quiz Engine: diagnostic / s-priority / weak-topic / past-exam-style / mixed /
  wrongbook / speed-run / cram modes, all evidence-grounded.
* Adaptive difficulty L1 Recall / L2 Standard / L3 Variant / L4 Transfer; sustained
  correct raises, repeated errors lower and trigger prerequisite review.
* Question provenance: derived_from / source_question / topic / variation_type on
  every past-exam variant.
* Grading with process analysis (multiple choice / fill-blank / short answer /
  calculation / derivation / essay / diagram, zh/en answers).
* Diagnosis taxonomy (13 categories) with prerequisite-gap detection.
* Wrongbook drives mastery, risk, planner, future quiz, and cram (real entries only).
* Retry scheduling from mistake type / severity / repeat count / mastery / exam
  proximity.
* Cram modes 7d/3d/24h/3h/1h/30m genuinely distinct; 30-minute rescue keeps only
  S-level core items; multi-course cram coordinated by the orchestrator.
* Language: question_language and explanation_language independently controlled.
* Full closed-loop test: plan -> learn -> quiz -> wrong -> diagnosis -> wrongbook ->
  replan -> retry -> mastery update.
* CLI: `workspace tutor / quiz / cram`.

Acceptance (all PASS, tested): 25 new Round 5 tests, 146 total green.

## Round 6 — DONE (国际化收口 + 用户体验 + 报告系统, v2.0.0)

Scope delivered per the Round 6 master instruction:

* zh-CN / en-US fully equivalent (catalog-parity test; 130+ keys each, no
  Chinese-only features).
* Terminology-driven terms via `terminology_map.json`; no on-the-fly machine
  translation.
* Three output modes (Chinese / English / Bilingual) - Bilingual = Chinese main +
  English key terms, never full duplication.
* First-use material report (`workspace material-report`): inventory, structure,
  exam situation, gaps, risk, next steps.
* Exam Week text dashboard with honest readiness (Unknown / Insufficient evidence
  until enough data) and "what should I do now?".
* On-demand reports (12 types) + export (MD/DOCX/PDF/Anki/JSON) with failure
  isolation (export failure never affects the learning flow).
* README rewritten; 5 runnable example scenarios.
* Acceptance audit: no TODO/placeholder/coming-soon; mock hits are only the
  intentional contamination guard; hard-coded user-facing zh localized.

Acceptance: 169 tests green (1 skipped: OCR-engine-present branch). Version 2.0.0.

### Remaining follow-ups (not blockers)

* Remove the legacy v0 batch modules (`index_course.py`, `llm_provider.py`, etc.)
  in a dedicated cleanup round - they are not part of the v2 flow and this round
  must not change core behavior.
* SKILL.md refresh for the v2 workflow.
* CI matrix expansion to Python 3.12.

## Risk Register

| Risk | Mitigation |
|---|---|
| Provider API unavailability during dev | Provider interface + sandbox mock for local tests only; real-state paths fail closed |
| Modal confusion between OCR and native multimodal | Modality field on every evidence unit; low-confidence fallback never promotes claims |
| Multi-course state mixing | Course-isolation tests + schema validation at every write |
| i18n drift | Snapshot tests over catalogs and generated filenames |
| Scope creep into ExamForge AI | Keep repo scoped to exam-review-skill; no unrelated features |

## Definition of Done (v2.0.0)

* All six Round-0 acceptance questions remain honestly PASS.
* Workspace/Course/Session hierarchy enforced and tested.
* Evidence store fully linked: document → chunk/evidence → concept → exam point →
  question → answer.
* Real providers configured and smoke-tested; sandbox mock isolated.
* Bilingual output verified by snapshots.
* Full test suite green locally and in CI; local release artifact built.
