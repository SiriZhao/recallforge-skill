# V2 Restart Audit — exam-review-skill

> Round 0 audit report. Freezes the baseline understanding of the current `v0.1.0`
> implementation before the v2 rebuild. Written from source code, schemas, tests,
> fixtures, generated examples, and git history — **not** from README claims.

## 摘要 (Executive Summary)

当前仓库是 `v0.1.0` 的单轮 batch generator：上传资料 → 规则/占位模型生成 15 个
Markdown 文件 → 结束。没有持续学生模型、没有真实 LLM、没有多课程工作区、没有原生
多模态、错误本会写入伪造条目。本轮已确认全部旧版问题，并把 v2 架构冻结在
[`V2_ARCHITECTURE.md`](V2_ARCHITECTURE.md)。迁移路线见
[`V2_MIGRATION_PLAN.md`](V2_MIGRATION_PLAN.md)。

---

## 1. Repository State

| Item | Evidence |
|---|---|
| Git | `main` branch, single commit `af7c731 Initial release: exam-review-skill`, tag `v0.1.0`, **no remote** |
| Version | `0.1.0` (`pyproject.toml`, `exam_review_skill/__init__.py`) |
| Test baseline | 4 tests, all PASS (`pytest 9.1.1`, Python 3.14.3, workspace `.venv`) |
| Encoding | All inspected files are clean **UTF-8 without BOM**; Chinese decodes correctly. Console shows GBK mojibake only as a display artifact (environment codepage) |
| Working tree | Clean; `examples/output/*` are gitignored generated artifacts (only `.gitkeep` tracked) |

## 2. Component Classification

| Component | Verdict | Evidence / Reason |
|---|---|---|
| `models.py` | **REFACTOR** | Dataclasses are flat; no Workspace/Course/Session layers; hard-coded zh defaults (`RiskItem.review_action`, `ReviewPlan.strategy`, `StudentState.course_name="课程"`); no Evidence Store entity |
| `config.py` | **REFACTOR** | `RunConfig` defined but **never used**; `EXAM_REVIEW_PROVIDER` env var is ignored; no provider config loading or validation |
| `cli.py` | **REFACTOR** | Batch `run` hard-codes `MockLLMProvider()`; no session/answer/feedback commands; `cram`/`plan`/`quiz` reload one flat `student_state.json` |
| `ingest.py` | **REFACTOR** | Text/PDF/DOCX/PPTX/image ingestion preserves file/page/heading metadata; image path delegates to local OCR; no multimodal understanding |
| `ocr.py` | **REPLACE** | `pytesseract` local OCR, `lang="chi_sim+eng"`; fixed confidence constants (`0.7` cache, `0.65` fresh); no math/formula/table/PPT-diagram/scanned-paper/handwriting support; no native multimodal path |
| `classify.py` | **REFACTOR** | Keyword heuristic; zh + chemistry-specific keywords; filename/extension assumptions |
| `chunk.py` | **REFACTOR** | Regex splitting; chemistry-specific keyword list (`滴定`, `标准溶液`, `有效数字`…); source metadata preserved (good); no semantic boundaries; token-limit naive |
| `index_course.py` | **REPLACE** | Keyword-bag topic aggregation; `related_topics`/`prerequisite_topics` = **adjacent list neighbors** (fake graph); produces garbage topics such as `Slide`, `答案`, `重点`, `必考`, sentence fragments |
| `build_exam_graph.py` | **REPLACE** | Rule heuristic `frequency = len(past)+len(teacher)+…`; **fabricated confidence** (`0.85`/`0.55`); `common_traps`/`possible_variants` are template strings |
| `risk_radar.py` | **REPLACE** | Weighted score over garbage topics; fabricated `exam_probability` (`0.25+0.12*freq`); most items rank S/A regardless of real exam evidence |
| `plan_review.py` | **REPLACE** | Batch day-slicing of the risk list; no adaptation from student model; no replanning after sessions |
| `adaptive_quiz.py` | **REPLACE** | Questions parrot the topic name back (`说明或计算：{topic} 的考试核心要求是什么？`); answers are generic boilerplate; not grounded in evidence |
| `generate_variants.py` | **REPLACE** | Template variant prose; no derivation from real past-exam questions |
| `generate_review_pack.py` | **REPLACE** | Template prose for chapter review / predictions |
| `generate_cram_pack.py` | **REFACTOR** | Tiered cram concept (3d/1d/3h/1h/30m/10m) is sound; content is template; not multi-course aware |
| `diagnose_mastery.py` | **REPLACE** | Writes **keyword-garbage `weak_points`** (e.g. `Slide`, `必考`, `重点`) into `student_state.json`; mastery left `"unknown"` (honest but non-functional) |
| `teacher_style.py` | **REFACTOR** | Heuristic chunk counting; low signal; confidence fabricated (`0.75`/`0.45`) |
| `wrongbook.py` | **REPLACE** | **Fabricates a fake example wrong entry** (`user_answer="示例：未作答"`) and persists it into `wrongbook.json` — P0 contamination |
| `export_pack.py` | **REFACTOR** | DOCX export is line-based and naive; PDF export is a **no-op stub**; Anki CSV is basic |
| `state_manager.py` | **REFACTOR** | Flat single-file JSON; no Workspace/Course/Session hierarchy; `load_student_state` defaults `course_name="课程"` |
| `quality_guard.py` | **REFACTOR** | Only checks output-file existence and JSON validity; does **not** enforce evidence traceability end-to-end; `REQUIRED_OUTPUTS` hard-codes zh filenames |
| `llm_provider.py` | **REPLACE** | `MockLLMProvider` is the default and **fabricates content that enters real outputs/state**; `OpenAIProvider`/`DeepSeekProvider`/`ClaudeProvider` are **empty placeholders**; interface too narrow for multimodal |
| `templates/*.j2` (13) | **REMOVE** | **Dead code** — `jinja2` is never imported/used; all rendering is in `render_*` functions |
| `schemas/*.json` (7) | **REFACTOR** | Mirror the flat v0 state; need new v2 schemas (workspace/course/session/evidence) |
| `tests/` (4) | **KEEP + EXPAND** | Pass; need state-integrity, traceability, i18n, and multi-course tests |
| `examples/input/*` | **KEEP** | `lecture_sample.txt`, `notes_sample.txt`, `past_exam_sample.txt` — usable fixtures (Experimental Chemistry) |
| `examples/output/*` | **KEEP (gitignored)** | Generated artifacts; demonstrate current quality problems |
| `pyproject.toml` deps | **REFACTOR** | `jinja2`, `pydantic` declared but **never used**; `requirements.txt` mixes runtime + `pytest` |
| `.github/workflows/tests.yml` | **KEEP** | Python 3.10/3.11 CI, compile + pytest |
| `.env.example` | **REFACTOR** | Declares keys but nothing reads them |

## 3. Old-Version Problem Confirmation

### 3.1 Batch generator — CONFIRMED (P0)

`python -m exam_review_skill run` performs: ingest → chunk → course index → exam graph
→ risk radar → review pack → variants → diagnosis → plan → quiz → wrongbook → cram →
teacher style → exports → report. It writes 15 Markdown files + JSON state and exits.
The only "state" is a flat `student_state.json` that is re-loaded and overwritten on
each run. There is **no session record, no answer feedback, no replanning, no
continuous learning loop**. This directly violates the v2 product definition
("在多门考试并行的考试周中持续决定'下一步最值得学什么'").

### 3.2 "All documents concatenated into one big prompt" — NOT PRESENT (latent risk)

No prompt is ever constructed and no real LLM is ever called. `generate_json`,
`generate_markdown`, and `extract_topics` are **defined but never invoked**. The only
used provider method is `MockLLMProvider.generate_questions`, which is pure rule-based
fabrication. The "big prompt" anti-pattern does not exist today only because there is
no LLM at all; v2 must design evidence-level prompting to prevent it.

### 3.3 Local OCR dependency — CONFIRMED (P0)

`ocr.py` uses `pytesseract` with `chi_sim+eng` and fixed confidence constants. It
cannot handle math formulas, tables, PPT diagrams, low-quality scanned papers, or
handwritten annotations. Image files fall back to OCR or empty text with warnings.
This violates "原生多模态 > 本地 OCR".

### 3.4 Mock data contamination — CONFIRMED (P0)

1. **`wrongbook.py` fabricates a wrong-question entry** with `user_answer="示例：未作答"`
   and writes it to `wrongbook.json` (real state). Confirmed in
   `examples/output/wrongbook.json`.
2. **`MockLLMProvider.generate_questions` fabricates questions and answers** that are
   written into `11_专项训练题.md` / mock-exam outputs. Answers are generic boilerplate
   ("围绕 X 写出定义、关键步骤、公式适用条件…").
3. **Keyword garbage enters the knowledge layer**: topics such as `Slide`, `答案`,
   `重点`, `必考`, `老师说到这里容`, and sentence fragments appear in
   `course_index.json`, `exam_graph.json`, and `risk_radar.json`
   (confirmed in `examples/output/03_考试风险雷达.md`).
4. **Fabricated confidence**: fixed constants (`0.65`, `0.7`, `0.75`, `0.85`, `0.55`,
   `0.45`) are assigned as if measured.
5. **`diagnose_mastery.py` writes fabricated `weak_points`** (keyword list) into
   `student_state.json`.

These synthetic artifacts can enter real course state → **P0**.

### 3.5 End-to-end source tracking — PARTIAL (P1)

`SourceRef` propagates from chunk → topic → exam point → question **nominally**:
`source_refs` lists are carried through, and `source_file`/`page_or_slide`/`heading`
are preserved at ingestion. However:

* Topic creation from keyword fragments breaks semantic traceability (a fragment is
  not a testable point).
* Answers and explanations are generic boilerplate with no traceable basis.
* `quality_guard` only checks output-file existence, not full traceability.
* No `document → chunk → topic → exam point → question → answer` verification exists.

### 3.6 Single-course only — CONFIRMED (P0)

State is one flat `student_state.json` per output directory; `run --course` accepts a
single value; `cram`/`plan`/`quiz` operate on one state file. There is **no
Workspace / Course / Session hierarchy** and **no cross-course orchestration**
(exam calendar, time allocation, global priority). This violates "多课程全局优化".

### 3.7 i18n — NOT REAL (P1)

* Hard-coded Chinese in nearly every module: default values, prompts, render strings,
  report content, and **output filenames** (`00_资料来源与解析报告.md` …
  `15_考前30分钟速救版.md`, `REQUIRED_OUTPUTS`).
* Hard-coded English in several places (`"Using MockLLMProvider: …"`, `"PDF export is
  optional …"`, `short_answer`, `course_name="课程"`).
* No locale layer, no catalogs, no `locale` parameter; schema field *values* contain
  Chinese content; no mixed-language-material handling (files are clean UTF-8, but
  language is never detected per evidence).

## 4. Problem Register (P0 / P1 / P2)

### P0 — blocks v2 (must be resolved by/within v2)

| # | Problem | Evidence |
|---|---|---|
| P0-1 | **Mock/rule contamination can enter real course state** (fake wrongbook entries, fabricated questions/answers, keyword-garbage topics, fabricated confidence/weak_points) | `wrongbook.py`, `llm_provider.py`, `index_course.py`, `risk_radar.py`, `diagnose_mastery.py`, `examples/output/*` |
| P0-2 | **Batch generator with no continuous learning loop** (no session, no feedback, no replanning) | `cli.py run_pipeline`, `plan_review.py`, `state_manager.py` |
| P0-3 | **No real provider in use; no config wiring** (placeholders only; `EXAM_REVIEW_PROVIDER` ignored; `RunConfig` unused) | `llm_provider.py`, `config.py`, `cli.py` |
| P0-4 | **Local OCR only, no native multimodal understanding** | `ocr.py`, `ingest.py` |
| P0-5 | **Single-course only; no Workspace/Course/Session hierarchy; no multi-course orchestration** | `state_manager.py`, `cli.py`, schemas |

### P1 — must be designed in v2

| # | Problem |
|---|---|
| P1-1 | Course Knowledge Model is a keyword bag with fake graph (adjacent-list relationships) |
| P1-2 | Exam Intelligence is rule-heuristic with fabricated frequency/confidence |
| P1-3 | Student Model cannot receive real answers; mastery always `unknown`/`estimated`; weak_points are keyword garbage |
| P1-4 | No real wrong-question diagnosis (only fabricated entries) |
| P1-5 | i18n absent: hard-coded zh/en strings, zh output filenames, no locale layer, no language detection |
| P1-6 | End-to-end source traceability not enforced (P0-adjacent but non-blocking for architecture freeze) |
| P1-7 | Templates/`jinja2`/`pydantic` dead code; dependency hygiene |
| P1-8 | CLI lacks interactive practice/answer-recording commands (no way to feed real answers back) |

### P2 — polish during v2

| # | Problem |
|---|---|
| P2-1 | DOCX export is line-based; PDF export is a no-op stub |
| P2-2 | `requirements.txt` mixes runtime and test deps; CI lacks lint/type checks |
| P2-3 | Confidence values are uncalibrated constants with no provenance |
| P2-4 | `examples/output` artifacts demonstrate quality problems; should be replaced by v2 fixtures |

## 5. Acceptance Answers (Round 0)

| Item | Verdict |
|---|---|
| Existing implementation understood | **PASS** — all 20 modules, 7 schemas, 13 templates, 4 tests, examples, and git history read; baseline tests run |
| Mock contamination risk known | **PASS** — P0-1 documented with file/line evidence (`wrongbook.py`, `llm_provider.py`, `index_course.py`, `risk_radar.py`, `diagnose_mastery.py`) |
| OCR dependency known | **PASS** — P0-4 documented (`ocr.py` pytesseract-only, fixed confidence) |
| Multi-course gap known | **PASS** — P0-5 documented (flat `student_state.json`, no Workspace/Course/Session) |
| i18n gap known | **PASS** — P1-5 documented (hard-coded zh/en, zh filenames, no locale layer) |
| V2 architecture frozen | **PASS** — `docs/V2_ARCHITECTURE.md` |

No blockers were faked; every PASS above is backed by source-level evidence.

## 6. Artifacts Produced This Round

* `docs/V2_RESTART_AUDIT.md` (this file)
* `docs/V2_ARCHITECTURE.md`
* `docs/V2_MIGRATION_PLAN.md`

Commit: `refactor: establish exam review v2 architecture`
