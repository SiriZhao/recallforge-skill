# Changelog

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
