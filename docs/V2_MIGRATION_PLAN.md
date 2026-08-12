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

## Round 3 — Course Knowledge Model + Exam Intelligence + Student Model

Scope (next):

1. Build the per-course knowledge graph from evidence (concept nodes + edges,
   evidence-linked, `inferred` flagging, semantic dedup reusing terminology maps).
2. Exam Intelligence from structured exam evidence (frequency = real question count,
   evidence-derived confidence).
3. Student Model + wrongbook from real answer sessions only.
4. CLI: `workspace ingest` already creates evidence; add knowledge/exam/student
   build steps.

Acceptance:

* Every concept/exam point has >= 1 evidence ref or `inferred=true`.
* No keyword garbage (no `Slide`/`答案` topics).
* Student model mutates only from recorded sessions.

## Round 2 — Multimodal Ingestion + Evidence Store + Course Knowledge Model

Scope:

1. Multimodal ingestion: render PDF pages / PPTX slides / images and send to the
   multimodal provider; structured evidence output (text/table/formula/diagram/
   handwriting). Local OCR kept only as low-confidence fallback.
2. Evidence Store: persist evidence units with stable IDs, checksums, language tags,
   and course scoping.
3. Course Knowledge Model: concept graph with evidence-linked nodes/edges; semantic
   deduplication; `inferred` flagging.
4. Remove keyword-bag `index_course.py` from the active pipeline; migrate tests to
   assert evidence-linked concepts (no `Slide`/`答案` garbage).

Acceptance:

* A bilingual fixture course produces evidence-grounded concepts with no keyword
  garbage (test asserts topic quality on the golden fixture).
* Every concept has ≥1 evidence ref or `inferred=true`.

Commit: `feat: multimodal ingestion, evidence store, and knowledge model`

## Round 3 — Exam Intelligence + Student Model + Wrongbook (real answers)

Scope:

1. Exam Intelligence: real past-exam question extraction; frequency = real question
   count; evidence-derived confidence; no fabricated traps/variants.
2. Student Model: mastery updated only from real answer outcomes; derived
   weak/strong points; per-concept statistics.
3. Wrongbook: only real wrong answers; remove the fabricated-entry path.
4. CLI: `session practice` command that accepts answers and records diagnosis.

Acceptance:

* No exam point without evidence (or `inferred=true`).
* Student model cannot be mutated except through a recorded session.
* Wrongbook contains zero fabricated entries.

Commit: `feat: exam intelligence, real student model, and truthful wrongbook`

## Round 4 — Practice Engine + Tutor + Diagnosis loop

Scope:

1. Practice Engine: evidence-grounded question generation (real past-exam questions +
   evidence-derived variants); answer recording; grading; wrong-reason classification.
2. Diagnosis → Student Model → Wrongbook → **replanning** loop.
3. Tutor: evidence-grounded, level-adaptive explanation for a target concept.

Acceptance:

* A practice session updates the student model and triggers a changed plan (test).
* Questions/answers resolve to evidence (traceability test).

Commit: `feat: practice, tutor, and the diagnosis-replanning loop`

## Round 5 — Exam Week Orchestrator + Adaptive Planner + Cram

Scope:

1. Exam Week Orchestrator: exam calendar, global time allocation, and the global
   "next most worthwhile thing to study" decision across courses.
2. Adaptive Planner: per-course plan rebuilt from knowledge + exam + student models.
3. Cram Engine: evidence-based, multi-course-aware time tiers.
4. `course report` / `workspace report` commands.

Acceptance:

* Multi-course fixture: orchestrator allocates time and orders cram correctly
  (orchestration tests).
* No cross-course knowledge leakage (integrity test).

Commit: `feat: exam week orchestrator and global adaptive planning`

## Round 6 — i18n completion, QA/Benchmark, packaging, release v2.0.0

Scope:

1. Full bilingual output (en/zh catalogs, locale-neutral filenames, per-evidence
   language preservation); snapshot tests.
2. QA/Benchmark harness: golden fixtures, state-integrity, traceability, i18n, and
   orchestration suites; CI matrix (3.10/3.11/3.12).
3. Packaging: clean `pyproject.toml` (v2.0.0), scripts, local release artifact
   (wheel/sdist), `SKILL.md`/`README.md` rewrite for the v2 workflow.
4. Regression: full old `run` command removed or replaced by v2 commands; no batch
   fallback that writes mock state.

Acceptance:

* Full test suite passes in CI and locally.
* Local release artifact builds; `pip install` from the artifact works.
* No mock data can reach any real state file (end-to-end test).
* Version `2.0.0`.

Commit: `feat: v2.0.0 release - bilingual, orchestrated, evidence-grounded`

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
