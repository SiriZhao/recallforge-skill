# V2 Architecture — exam-review-skill v2.0.0

> Frozen during Round 0. Every v2 round must conform to this document. It is written
> from the real v0.1.0 codebase (see `V2_RESTART_AUDIT.md`) and replaces the batch
> generator with a persistent, multi-course, evidence-grounded learning loop.

## 0. Product Definition

An Exam Review Agent that understands course materials, exams, and the student, and —
across a multi-course exam week — continuously decides **what to study next**.

Closed loop:

```
Materials
  → Multimodal Understanding
  → Course Knowledge Model
  → Exam Intelligence
  → Student Model
  → Exam Week Orchestrator
  → Adaptive Study Plan
  → Tutor → Practice → Diagnosis
  → Wrongbook → Replanning → Cram → Exam
```

Non-negotiable principles (from the master instruction):

* Score improvement > generic summarization
* Structure understanding > long-text stacking
* Course evidence > model guessing
* Native multimodal > local OCR
* Real state > mock data
* Cross-file fusion > single-file summary
* Persistent student model > re-guessing level every time
* Active practice > passive reading
* Error diagnosis > only providing answers
* Multi-course global optimization > per-course time fighting
* True bilingual > simple UI translation

---

## 1. State Hierarchy: Workspace / Course / Session

V2 enforces **three strict levels**. Knowledge content is **never** shared across
courses. The workspace level owns only time, priority, the global plan, and the exam
calendar.

```
Workspace  (整个考试周)
├── workspace.json            # courses, exam calendar, global time budget,
│                             # global plan, locale, provider config
├── courses/
│   └── <course_id>/
│       ├── course.json       # metadata + knowledge model refs
│       ├── knowledge.json    # concept graph (course-scoped)
│       ├── exam.json         # exam intelligence (course-scoped)
│       ├── student.json      # student model (course-scoped)
│       ├── wrongbook.json    # real wrong answers only
│       ├── plan.json         # per-course adaptive plan
│       └── evidence/         # evidence store for this course
└── sessions/
    └── <course_id>/
        └── <session_id>.json # one study behavior
```

Rules:

* **Workspace** may only reference `course_id` + time/priority/calendar/global-plan
  fields. It never stores topic knowledge.
* **Course** owns all knowledge, exam, student, and wrongbook data for exactly one
  course. Mixing probability-theory topics into an organic-chemistry knowledge base is
  a hard failure.
* **Session** records a single behavior (practice, quiz, review, tutor, cram): items,
  answers, diagnosis, time, and links to course model nodes. Sessions are the only
  input that may mutate the student model.

## 2. Multimodal Ingestion

**Replace local-OCR-only with native multimodal understanding.**

* Primary path: send rendered pages (PDF pages, PPTX slides, scanned images, DOCX
  embedded images) to a multimodal provider that returns structured content:
  text, tables, formulas, diagrams, and handwriting — each as structured evidence with
  position (page/slide), heading path, and language.
* Local OCR (`pytesseract`) is demoted to an **offline fallback** that emits
  `low_confidence` evidence only and is never the source of high-confidence claims.
* Output: a list of `Evidence` units (see §3).
* Failure is graceful and recorded; no fabricated content on failure.

## 3. Evidence Store

Single source of truth for everything downstream. Every claim in every artifact must
resolve to evidence IDs.

```json
{
  "evidence_id": "EV-2026-0001",
  "course_id": "chem101",
  "source_file": "lecture_03.pdf",
  "page_or_slide": "12",
  "doc_type": "lecture_slide",
  "chapter": "第一章 标准溶液与滴定分析",
  "heading": "标准溶液的概念",
  "modality": "text | table | formula | diagram | image | handwriting",
  "content": "标准溶液是已知准确浓度的溶液，用于滴定分析。",
  "image_ref": "optional absolute path or null",
  "language": "zh",
  "confidence": 0.0-1.0,
  "checksum": "sha256 of source bytes",
  "created_at": "ISO-8601"
}
```

## 4. Course Knowledge Model

Per-course **concept graph**, not a keyword bag.

* Nodes: `Concept {concept_id, name, aliases, chapter, definitions, formulas,
  examples, evidence_refs[], language}`.
* Edges: `prerequisite`, `part_of`, `related`, `contrast` — inferred from structural
  understanding (heading hierarchy, cross-file mentions) plus LLM, each edge carrying
  `evidence_refs`.
* Semantic identity deduplication (aliases/paraphrases), not string-key matching.
* Strict course boundary: concepts are scoped to one course.
* Every concept keeps at least one evidence ref; concepts without evidence are marked
  `inferred=true` with lowered confidence and never masquerade as sourced facts.

## 5. Exam Intelligence Model

Per-course analysis of **how the exam actually tests the material**.

* Inputs: past-exam questions, teacher hints, syllabus, exercise/answer keys.
* Outputs: `ExamPoint {exam_point_id, concept_ids[], exam_forms[], real_question_refs[],
  frequency (count of real questions), score_potential, difficulty, common_traps,
  possible_variants, evidence_refs[], confidence}`.
* `frequency` is a **count of real past-exam questions**, never a heuristic score.
* `confidence` is derived from evidence count + provenance, never a fixed constant.
* No exam point without at least one evidence ref (or explicit `inferred=true`).

## 6. Student Model

Persistent per-course student state updated **only from real answer outcomes**.

```json
{
  "student_id": "student-default",
  "course_id": "chem101",
  "mastery": { "concept_id|exam_point_id": { "level": "unknown|novice|developing|proficient",
                                             "correct": 3, "attempts": 5,
                                             "last_seen": "ISO-8601" } },
  "wrong_patterns": [ "unit_error", "condition_omitted", "concept_confused" ],
  "weak_points": [], "strong_points": [],   // derived from real data only
  "review_history": [ { "date": "...", "event": "...", "detail": {} } ],
  "last_updated": "ISO-8601"
}
```

* Level is `unknown` until at least one real attempt exists.
* `weak_points`/`strong_points` are **derived** from mastery statistics; never seeded
  with keywords.
* Provides the per-concept signal consumed by the planner and tutor.

## 7. Wrongbook

* Contains **only real wrong answers**: `{question_id, question_text, user_answer,
  correct_answer, concept_id/exam_point_id, wrong_reason (classified), trap_type,
  fix_strategy, next_review_date, variant_questions, evidence_refs}`.
* No fabricated "示例：未作答" entries. No wrongbook entry without a real user answer.
* Linked to the Student Model for spaced repetition; feeds the practice engine and cram
  engine.

## 8. Adaptive Planner

Per-course planning from Knowledge + Exam + Student models:

* Choose the next concepts by (risk priority) × (mastery gap) × (score potential).
* Decide the action type per item: tutor (learn), practice (verify), re-learn
  (after wrong diagnosis), cram (time-constrained).
* Emit a plan with concrete content, time, question types, and self-test method.
* **Replan after every session** — diagnosis results feed back into the plan.

## 9. Exam Week Orchestrator

Cross-course global decision layer (the only cross-course component):

* Inputs: exam calendar (course → date, weight, format), per-course plans/priorities,
  daily time budget, session outcomes.
* Outputs: a **global "next most worthwhile thing to study"** decision and a global
  daily plan that allocates time across courses by
  `proximity × weight × mastery-gap × score-potential`.
* Must not read course knowledge; only course IDs + priorities.

## 10. Tutor

Interactive, evidence-grounded teaching:

* Given a target concept/exam point + student model, produce an explanation that is
  grounded in evidence (definitions, formulas, examples, common traps) and adapted to
  the student's current level.
* Multimodal-aware: can reference formulas, tables, and diagrams from evidence.
* Bilingual: responds in the student's chosen locale while preserving source language.

## 11. Practice Engine

* Generates questions **from evidence** (real past-exam questions + evidence-derived
  variants), not template parroting.
* Records answers through a session; grades and produces a diagnosis
  (wrong-reason classification: concept confusion, formula error, condition omission,
  unit error, misread, step omission, calculation error, recall weakness, transfer
  failure).
* Writes to Student Model + Wrongbook and triggers replanning.

## 12. Cram Engine

* Time-compressed rescue packs derived from risk radar + wrongbook + student model
  (`3d / 1d / 3h / 1h / 30m / 10m` tiers kept from v0, rebuilt on evidence).
* Multi-course aware: picks which course to cram first from the orchestrator.

## 13. Internationalization

* Locale layer with catalogs (`en`, `zh`); no hard-coded user-facing strings in
  render logic.
* Stable English schema keys; **content language is preserved per evidence**.
* Output filenames are locale-neutral or catalog-derived (no hard-coded zh filenames).
* Mixed-language materials handled via per-evidence `language` tags.
* All files remain UTF-8 without BOM.

## 14. Provider Abstraction

```python
class BaseProvider:
    name: str
    def multimodal_understand(self, pages: list[PageImage]) -> list[Evidence]: ...
    def build_knowledge(self, course, evidence) -> KnowledgeResult: ...
    def analyze_exam(self, course, evidence) -> ExamResult: ...
    def generate_questions(self, exam_points, mode, count) -> list[Question]: ...
    def tutor_explain(self, target, student) -> TutorResponse: ...
    def diagnose_wrong(self, question, user_answer) -> Diagnosis: ...
```

* Real providers: OpenAI (Responses API), DeepSeek, Claude — configured via environment
  (`EXAM_REVIEW_PROVIDER`, validated at startup).
* **MockProvider exists only in an explicit sandbox/demo mode**: its outputs are
  flagged, excluded from real course state, and never persist to workspace/course
  student models. Default mode requires a real provider (fail closed).

## 15. QA / Benchmark

* Golden fixtures (bilingual, multi-course) + assertion suite.
* State-integrity tests: no cross-course knowledge mixing; no mock data in real state.
* Traceability tests: every exam point / question / answer resolves to evidence.
* i18n snapshot tests (en/zh catalogs, filename neutrality).
* Multi-course orchestration tests (calendar, time allocation, cram ordering).
* CLI end-to-end smoke tests.

## 16. Release Structure (v2.0.0)

```
exam_review_skill/
├── cli.py                  # workspace init, course add/ingest, session practice,
│                           # plan, cram, report, diagnosis
├── ingestion/              # multimodal ingestion
├── evidence/               # evidence store
├── knowledge/              # course knowledge model
├── exam/                   # exam intelligence
├── student/                # student model
├── wrongbook/              # wrongbook
├── planner/                # adaptive planner
├── orchestrator/           # exam week orchestrator
├── tutor/                  # tutor
├── practice/               # practice engine
├── cram/                   # cram engine
├── i18n/                   # locale catalogs
├── providers/              # provider abstraction + real providers + sandbox mock
├── quality/                # QA guards
└── models.py               # shared dataclasses (workspace/course/session/evidence)
schemas/                    # JSON schemas for all v2 state
tests/                      # unit + integrity + traceability + i18n + orchestration
docs/
examples/                   # bilingual fixtures
pyproject.toml              # v2.0.0, cleaned dependencies
SKILL.md / README.md        # updated for v2 workflow
```

## 17. Data Flow (v2)

```
Multimodal Ingestion ──► Evidence Store ──► Course Knowledge Model
                                                  │
                                                  ▼
                                          Exam Intelligence
                                                  │
                                                  ▼
                                          Student Model (persistent)
                                                  │
                   ┌──────────────────────────────┘
                   ▼
          Exam Week Orchestrator (cross-course calendar + time)
                   ▼
          Adaptive Study Plan (per course)
                   ▼
          Tutor / Practice Engine ──► Session ──► Diagnosis
                                                  │
                    ┌─────────────────────────────┤
                    ▼                             ▼
              Wrongbook                      Student Model update
                    │                             │
                    └────────────► Replanning ◄───┘
                                       │
                                       ▼
                                   Cram ──► Exam
```

## 18. Architecture Decisions (ADR Summary)

| # | Decision | Rationale |
|---|---|---|
| ADR-1 | Three-level state (Workspace/Course/Session) | Enforces knowledge isolation; enables multi-course orchestration |
| ADR-2 | Evidence Store is the single source of truth | Guarantees traceability and kills fabricated claims |
| ADR-3 | MockProvider is sandbox-only and never writes real state | Eliminates P0-1 contamination |
| ADR-4 | Native multimodal first; OCR only as low-confidence fallback | Meets "原生多模态 > 本地 OCR" |
| ADR-5 | Student model mutates only from real answer sessions | Meets "真实状态 > Mock 数据" and "持续学生模型" |
| ADR-6 | Orchestrator is the only cross-course component | Meets "多课程全局优化" with a clean boundary |
| ADR-7 | Locale layer + evidence-level language tags | Meets "真正中英双语" |
| ADR-8 | Frequency = count of real past-exam questions | Replaces fabricated heuristics with evidence |
