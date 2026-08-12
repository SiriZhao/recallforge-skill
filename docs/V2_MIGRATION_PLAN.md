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

## Round 1 — Foundation: state layers, provider abstraction, sandbox isolation

Scope:

1. Add `Workspace`, `Course`, `Session` state model + JSON schemas
   (`schemas/workspace.schema.json`, `course.schema.json`, `session.schema.json`,
   `evidence.schema.json`), with a state manager that enforces course isolation.
2. Rework `providers/` abstraction: define the v2 `BaseProvider` interface; add real
   OpenAI (Responses API) and DeepSeek providers with config validation
   (`EXAM_REVIEW_PROVIDER` now honored; fail closed when unset/invalid).
3. Move `MockLLMProvider` behind an explicit `sandbox` flag that never writes to real
   workspace/course state; add a contamination guard test.
4. Remove dead code: `templates/*.j2`, unused `jinja2`/`pydantic` deps; clean
   `requirements.txt` split (runtime vs test).
5. i18n skeleton: locale catalogs (`en`/`zh`) + neutral output filenames.
6. CLI: `workspace init`, `course add/ingest` stubs that create real state files.

Acceptance:

* No mock output can persist into course/student state (automated test).
* `workspace.json` + course dirs + session dirs created by CLI and validated by
  schema tests.
* Existing 4 tests still pass; new state-integrity tests pass.

Commit: `feat: v2 workspace/course/session state and provider isolation`

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
