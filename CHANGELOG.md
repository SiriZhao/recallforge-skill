# Changelog

## 2.0.0

- Final release of the v2 Exam Review Agent.
- Internationalization completion:
  - Catalog key parity between zh-CN and en-US enforced by a parity test (no
    Chinese-only features, no English-only translation).
  - Localized diagnosis explanations, formula-ambiguity signals, and mistake-type
    labels (previously hard-coded Chinese).
  - Three output modes: Chinese / English / Bilingual (Chinese main text + English
    key terms, never full duplication), via `OutputMode` / `render_bilingual`.
  - Terminology maps keep technical terms unified across languages (no on-the-fly
    machine translation).
- User experience:
  - First-use material report (`workspace material-report`): material inventory,
    course structure, exam situation, material gaps, current risk, next steps.
  - Exam Week text dashboard (`workspace dashboard`): per-course exam proximity,
    risk, honest readiness (Unknown / Insufficient evidence until enough data),
    today's allocation, and "what should I do now?".
  - On-demand reports (`workspace report`): course-overview, exam-risk-radar,
    past-exam-analysis, teacher-style, formula-sheet, wrongbook, 7-day-plan,
    mock-exam, 1-hour-cram, 30-min-rescue, dashboard, welcome.
  - Export: Markdown (default), DOCX, PDF, Anki CSV, JSON - export failure never
    affects the main learning flow (clean error, Markdown always available).
- Rewrote README with What it is / Why not ChatGPT / Architecture / Multimodal /
  Multi-course / Chinese-English / Installation / Configuration / Examples /
  Privacy / Limitations / Testing.
- Added 5 runnable example scenarios (Chinese final, English course, mixed-language
  course, four-course exam week, 24-hour cram).
- Acceptance audit: no TODO/placeholder/coming-soon in v2 code; mock references are
  only the intentional contamination guard.
- Full suite: 169 tests green (1 skipped: OCR-engine-present branch on this machine).

## 0.6.0

- Added the complete learning loop (`exam_review_skill/tutor/`).
- Tutor: course-first structured explanation (Intuition/Definition/Core
  Formula/Principle/Conditions/Method/Example/Common Mistake/Check Question),
  subject-adaptive, model additions marked "Supplementary explanation".
- Quiz Engine with 8 modes (diagnostic / s-priority / weak-topic / past-exam-style /
  mixed / wrongbook / speed-run / cram) and adaptive difficulty L1-L4.
- Question provenance (derived_from / source_question / topic / variation_type) on
  every past-exam variant.
- Grading with process analysis (multiple choice / fill-blank / short answer /
  calculation / derivation / essay / diagram, bilingual zh/en answers).
- Diagnosis taxonomy (13 categories) with prerequisite-gap detection and
  prerequisite-fix topic ids.
- Wrongbook entries that drive mastery, risk, planner, future quizzes, and cram;
  fabricated content rejected.
- Retry scheduling from mistake type / severity / repeat count / mastery / exam
  proximity.
- Cram engine with genuinely distinct modes (7d/3d/24h/3h/1h/30m), strict 30-minute
  rescue, and multi-course cram coordination through the orchestrator.
- Independent question_language / explanation_language control (English questions
  with Chinese explanations supported).
- CLI: `workspace tutor`, `workspace quiz`, `workspace cram`.
- New schemas: quiz_question, cram_plan, wrongbook_v2.

## 0.5.0

- Added persistent per-course Student Model (`exam_review_skill/student/`):
  composite mastery (accuracy + difficulty + independence/hints + recency + repeat
  errors + transfer + question-type coverage), per-topic stats, forgetting risk;
  no data -> `unknown` (never a pretend 0.5); only real answer sessions mutate it.
- Added session answer recording + wrongbook entries (real wrong answers only,
  fabricated content rejected).
- Added 10-20 minute diagnostic test selection by knowledge-graph coverage
  (unknown/weak topics first).
- Added single-course adaptive planner with topic-level Study Blocks
  (course / topic / duration / reason / task / practice / completion criterion).
- Upgraded the Exam Week Orchestrator to a real scheduler: cross-course priority
  (urgency / score gain / risk / target gap / learning cost / forgetting /
  maintenance), never a mechanical time average, with anti-starvation minimum
  maintenance + cram mode.
- Added dynamic replan events (quiz_completed, wrong_answer, topic_mastered,
  new_material, new_past_exam, exam_rescheduled, hours_changed, target_changed,
  course_completed); exam-day completion releases a course's future time to others.
- Added bilingual natural-language user control (zh/en): skip / pin / reduce /
  change target / change hours; user override always beats the planner.
- Added CLI commands: `workspace diagnostic`, `workspace answer`, `workspace
  plan-v4`, `workspace replan`, `workspace nl`.
- Updated schemas: course student state (v4 per-topic mastery) and global study
  plan (topic-level blocks).

## 0.4.0

- Added the exam brain (`exam_review_skill/knowledge/`): topic-centric Course
  Knowledge Model where `KnowledgeTopic` is the core object and evidence is the proof.
- Full topic schema: localized names, aliases, chapter, prerequisites, definitions,
  formulas, concepts, methods, common mistakes, question types, evidence citations,
  teacher emphasis, past-exam links, fusion/source confidence.
- Cross-language topic fusion (e.g. CLT / 中心极限定理 / Central Limit Theorem)
  with aliases and fusion confidence; no false merging; no generic-heading garbage.
- Evidence-grounded knowledge graph with real `prerequisite` edges (never adjacency)
  plus `related_to` / `part_of` / `often_confused_with` / `used_in`.
- Separate `exam_model.json` with exam points (importance, likelihood_estimate as an
  explicit ordinal heuristic, confidence, expected score range, question types,
  teacher emphasis, past-exam frequency, learning cost, evidence).
- Explainable S/A/B/C risk radar with full per-item rationale.
- Past-exam intelligence: per-file exam sets, per-question extraction, and
  bidirectional Question<->Topic mapping.
- Evidence-weight differentiation with per-course override (not hard-coded).
- Teacher style with Observed/Strongly Inferred/Inferred/Unknown tiers and no
  unsupported claims.
- Conflict handling: contradictions are recorded, never silently overwritten, ranked
  by authority/recency/exam-relevance, and require user confirmation.
- Exam coverage report answering "do I have enough materials?" with concrete numbers
  and a fail-closed verdict.
- CLI `workspace build`; updated/new JSON schemas (knowledge graph, exam model, risk
  radar, conflicts, coverage report).

## 0.3.0

- Rebuilt ingestion around native multimodal understanding
  (`exam_review_skill/ingestion/`): File -> Classifier -> Native Parser ->
  Visual Renderer -> Multimodal Understanding -> Structured Evidence.
- Native-first parsing: PDF text layer, PPTX text boxes, DOCX paragraphs preserve
  file/page/slide/heading/question_number; images and scanned pages route to vision.
- Cheap routing: vision only for formula-heavy, table, diagram, handwriting,
  image-only, and exam-paper pages.
- `MultimodalProvider` abstraction with capability flags and a runtime registry
  (openai / deepseek / synthetic); no single-vendor hard-coding; fail closed when
  unconfigured.
- Local OCR is disabled by default; allowed only as explicit fallback; output is
  `extraction_method=ocr_fallback` with low confidence and never fabricates content.
- Formula verification: subscript/superscript/fraction/chemical-equation ambiguity
  forces visual re-view; unconfirmed formulas stay low-confidence.
- Exam-paper structure preserved field-by-field (question_number, options, score,
  subquestions, answer_area, handwritten_annotation).
- Per-course `evidence_store.json` with content-hash cache, incremental ingestion,
  and dedup; JSON schema added.
- Synthetic (mock/test) records are rejected from real state; CLI `workspace ingest`
  reports a clean fail-closed error.
- CLI: `workspace ingest --input <path> --course <id> [--provider ...] [--ocr]
  [--offline] [--demo]`.

## 0.2.0

- Added multi-course workspace state layer (`workspace init`, `add-course`, `list`,
  `calendar`, `exam`, `override`, `term`, `plan` commands).
- Added per-course isolated state: manifest, document index, knowledge graph, exam
  model, student state, wrongbook, study plan, sessions, terminology map.
- Added Exam Week Orchestrator: transparent heuristic cross-course daily planner
  with anti-starvation (minimum maintenance allocation, per-course caps, cram
  urgency) and per-block rationale (why / risk / goal / done-when).
- Added per-date user overrides (skip course, change hours, move exam, change target)
  with automatic re-planning.
- Added i18n foundation: stable English schema keys, zh-CN/en-US catalogs with
  runtime locale registration and language-level fallback, LanguageProfile
  (UI / source / output languages), per-course bilingual terminology maps, and
  mixed-language topic normalization.
- Added sandbox/mock contamination guard: mock/sandbox content is rejected before it
  can be written to real workspace/course state.
- Added 13 JSON schemas for v2 state and schema-validation tests.
- Removed dead `templates/*.j2` and unused `jinja2`/`pydantic` dependencies; v2 core
  is stdlib-only; requirements/CI cleaned up.

## 0.1.0

- Initial open-source release.
- Added independent Codex Skill metadata in `SKILL.md`.
- Added runnable CLI with `run`, `cram`, `variants`, `plan`, and `quiz` commands.
- Added MockLLMProvider so demos and tests work without API keys.
- Added rule-based ingestion, classification, chunking, course index, exam graph, risk radar, review plan, quiz generation, variants, wrongbook, cram pack, teacher style report, exports, and quality guard.
- Added examples and pytest smoke tests.
