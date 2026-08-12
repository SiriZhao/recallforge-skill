# Round 1 Report — Core state + multi-course exam week + i18n foundation

> Scope per the master instruction: Workspace layer, true multi-course model,
> Course Manifest, Exam Week Orchestrator, anti-starvation, Daily Global Plan,
> user overrides, i18n foundation (stable keys, locale, three language concepts,
> terminology map, mixed-language materials).

## What was built (all real, tested code — no shells)

### 1. Workspace layer (`exam_review_skill/state/workspace.py`)

```text
<workspace>/
├── workspace_state.json     # workspace_id, user_locale, content_language,
│                            #   output_language, daily_total_hours, courses
├── exam_calendar.json       # global exam calendar (see 3)
├── global_study_plan.json   # latest daily global plan
├── overrides.json           # per-date user overrides (see 7)
└── courses/<course_id>/…    # strictly isolated per-course state (see 2)
```

### 2. True multi-course model (`state/course.py`)

Each course is an isolated directory with its own 9 files:
`course_manifest.json`, `document_index.json`, `knowledge_graph.json`,
`exam_model.json`, `student_state.json`, `wrongbook.json`, `study_plan.json`,
`sessions.jsonl`, `terminology_map.json`. Knowledge content is never shared across
courses; `assert_course_isolation` verifies manifest/dir/payload course_ids match.

### 3. Course Manifest

Supports all required fields: `course_id`, `course_name`, `course_name_localized`,
`source_languages`, `exam_date`, `exam_time`, `target_score`,
`current_estimated_score`, `daily_preference`, `importance_override`,
`material_count`, `topic_count`, `status`. Edge cases supported: no exam date,
two exams on the same day, consecutive multi-day exams, completed exams
(kept as calendar history).

### 4. Exam Week Orchestrator (`orchestrator/calendar.py` + `scheduler.py`)

Global scheduler reads the workspace, exam calendar, and every course manifest, and
produces a daily global plan. Priority is a **transparent heuristic**, not a hidden
formula:

```
expected_gain = 0.35*urgency + 0.30*target_gap + 0.20*risk_signal
              + 0.10*forgetting_risk + 0.05*unfinished_work
```

where urgency = 1/(days_to_exam+1), target_gap = (target-current)/100 (unknown→0.5),
risk_signal = S/A share of exam model, forgetting = days-since-review/7,
unfinished = (planned-logged)/2. The rationale is written into every block so the
user can see exactly why a course was scheduled.

### 5. Anti-starvation

* every active course keeps a minimum maintenance allocation (`MIN_MAINTENANCE_HOURS`);
* courses with no exam date still get spaced-review maintenance (never starved);
* no course exceeds `MAX_SHARE` (60%) of the day, or `CRAM_SHARE` (80%) when within
  `CRAM_DAYS` of an exam;
* user course-hour overrides win; course-switching cost is reduced by clustering
  blocks per course with a 15-minute break and minimum 30-minute blocks.

### 6. Daily Global Plan

Each block carries `start/end/course_id/kind` plus localized
`why` (heuristic numbers), `risk`, `goal`, and `done_when` — matching the required
"为什么安排 / 对应风险 / 目标 / 结束标准" shape.

### 7. User overrides (`state/workspace.py` + scheduler merge)

Per-date `DayOverride` supports: skip a course today, change total hours, set
per-course hours, change a target score, move an exam date. The scheduler merges
stored overrides with inline overrides and re-plans; applied changes are recorded in
`overrides_applied`.

### 8. i18n foundation (`exam_review_skill/i18n/`)

* **Stable internal keys**: all schema keys and JSON fields are English
  (`exam_date`, `mastery`, …); UI/output localize at the boundary.
* **Locale architecture** (`locales.py`): catalogs for `zh-CN` and `en-US`,
  runtime `register_locale` for extensibility, language-level fallback
  (`zh-TW` → zh catalog), fail-closed lookups.
* **Three language concepts** (`languages.py::LanguageProfile`): `ui_locale`,
  `source_languages`, `output_language` are independent (e.g. UI=zh-CN,
  materials=en-US, output=zh-CN) plus `terminology_mode`.
* **Terminology map** (`terminology.py`): per-course `terminology_map.json`
  (`{"conditional probability": {"names": {"zh-CN": …, "en-US": …}, "aliases": […]}}`)
  with a reverse alias index, so `Bayes' theorem` / `贝叶斯公式` / `Bayes公式`
  resolve to one canonical topic without re-translation.
* **Mixed-language normalization**: `normalize_topic()` returns
  `(canonical_key, was_matched)`; unmatched text is never silently merged.

### 9. Schemas

13 new JSON schemas in `schemas/` (workspace, exam_calendar, global_study_plan,
course_manifest, document_index, knowledge_graph, exam_model, course_student_state,
course_wrongbook, course_study_plan, session, terminology_map, overrides). All state
files are validated against them in `test_state_schemas.py`.

### 10. CLI

New `workspace` command tree: `init`, `add-course`, `list`, `calendar`, `exam`,
`override`, `term`, `plan`. Old v0 commands are untouched.

### 11. Hygiene (from the frozen Round 1 plan)

* Removed dead `templates/*.j2` and unused `jinja2`/`pydantic` dependencies
  (v2 core is stdlib-only).
* Split `requirements.txt` to `-e .[test]`; CI now installs `.[test]`.
* Version bumped to `0.2.0`; CHANGELOG updated.

## Test results

* 48 tests pass (8 new test files + existing 4).
* Required i18n test files present: `test_zh_course.py`, `test_en_course.py`,
  `test_mixed_language_course.py`, `test_locale_switch.py`,
  `test_terminology_mapping.py`; plus `test_workspace.py`, `test_orchestrator.py`,
  `test_state_schemas.py`, `test_contamination_guard.py`.

## Acceptance (Round 1)

| Item | Verdict |
|---|---|
| Multi-course workspace | **PASS** — workspace + per-course isolated state, CLI-verified |
| Course isolation | **PASS** — enforced + tested (rejects foreign course_id, mock content) |
| Global exam calendar | **PASS** — no-date / same-day / consecutive / completed covered |
| Cross-course planner skeleton | **PASS** — transparent heuristic, per-block rationale, tested |
| Chinese locale | **PASS** — zh-CN catalog + zh plan rendering tested |
| English locale | **PASS** — en-US catalog + en plan rendering tested |
| Mixed-language model | **PASS** — terminology normalization tested |
| Stable internal schemas | **PASS** — English keys + JSON-schema validation tests |

Deferred (per migration plan): provider abstraction + real providers move to Round 2,
when multimodal ingestion actually needs them.

Commit: `feat: add multi-course workspace and bilingual foundation`
