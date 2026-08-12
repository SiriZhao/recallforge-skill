# exam-review-skill

**Input course materials, output a scoring path. 输入课程资料，输出提分路径。**

exam-review-skill is an Exam Review Agent: it understands your course materials, your exams, and **you**, then continuously decides what to study next across a multi-course exam week. It is a Codex Skill + a Python package.

- 中文文档简介：这是一个考试复习智能体，能理解课程资料、理解考试、理解学生，并在多门考试并行的考试周中持续决定"下一步最值得学什么"。

## What it is

A source-grounded, evidence-first exam review system. It does not summarize your materials - it builds:

- a **Course Knowledge Model** (evidence-linked topics, cross-language fusion)
- an **Exam Intelligence Model** (real past-exam frequency, teacher style, risk radar)
- a **persistent Student Model** (composite mastery, never raw accuracy)
- a **multi-course Exam Week Orchestrator** (global daily plan, anti-starvation)
- a **Tutor + Quiz + Diagnosis + Wrongbook + Cram** learning loop

## Why not just upload everything to ChatGPT

| Generic chat with a pile of files | exam-review-skill |
|---|---|
| Context limit eats long courses | Evidence Store + topic model keeps files/chunks/references |
| No memory of what you know | Persistent per-course student model |
| One course at a time | Multi-course exam-week orchestration |
| Answers are generic | Every claim traces to a source evidence id |
| No scoring priority | S/A/B/C risk radar with full rationale |
| Wrong answers vanish | Wrongbook drives mastery, risk, planner, quiz, and cram |
| Chinese OR English | True bilingual (catalogs, terminology maps, mixed-language fusion) |

## Architecture

```text
Workspace (one exam week)
├── workspace_state.json        # locale, daily hours, course list
├── exam_calendar.json          # global exam calendar
├── global_study_plan.json      # daily global plan
├── overrides.json              # user control (skip/pin/reduce/target/hours)
└── courses/<course_id>/
    ├── course_manifest.json
    ├── evidence_store.json     # evidence units (course-scoped)
    ├── knowledge_graph.json    # topic-centric knowledge model
    ├── exam_model.json         # exam intelligence (separate from course model)
    ├── risk_radar.json         # explainable S/A/B/C
    ├── student_state.json      # persistent student model
    ├── wrongbook.json          # real wrong answers only
    ├── study_plan.json / sessions.jsonl / terminology_map.json / conflicts.json
    └── coverage_report.json
```

Core loop:

```text
Materials → Multimodal Understanding → Course Knowledge Model → Exam Intelligence
→ Student Model → Exam Week Orchestrator → Adaptive Plan → Tutor → Practice
→ Diagnosis → Wrongbook → Replanning → Cram → Exam
```

## Multimodal workflow

Native multimodal first; local OCR is a disabled-by-default fallback.

```text
File → Classifier → Native Parser (text layer/boxes/paragraphs)
→ Visual Renderer → Multimodal Understanding → Structured Evidence
```

- Text PDFs, PPTX text boxes, DOCX paragraphs are read natively (preserving file / page / slide / heading / question number).
- Scanned / image-only pages, formulas, tables, diagrams, handwriting, and exam papers route to a multimodal provider (openai / deepseek / synthetic for tests).
- Cheap routing: vision is only called when a page actually needs it.
- Formula ambiguity (subscript/superscript/fraction/chemical equation) forces a visual re-check; unconfirmed formulas stay low-confidence. **Never guessed.**
- OCR fallback: `extraction_method=ocr_fallback`, low confidence, never supports high-confidence conclusions.

## Multi-course exam week

```bash
# create the workspace (one per exam week)
python -m exam_review_skill workspace init --dir ./week --locale zh-CN --daily-hours 6

# add courses (each is fully isolated)
python -m exam_review_skill workspace add-course --dir ./week --course probability --name "概率论" --exam-date 2026-06-19 --target-score 85
python -m exam_review_skill workspace add-course --dir ./week --course organic-chemistry --name "有机化学" --exam-date 2026-06-20 --target-score 80
python -m exam_review_skill workspace add-course --dir ./week --course botany --name "植物学" --target-score 70

# ingest materials into a course (native multimodal first)
python -m exam_review_skill workspace ingest --dir ./week --course probability --input ./probability_materials --provider openai

# build the exam brain (topics, exam model, risk radar, coverage)
python -m exam_review_skill workspace build --dir ./week --course probability --days-to-exam 3

# first-use report + dashboard (what the user sees after upload)
python -m exam_review_skill workspace material-report --dir ./week --course probability
python -m exam_review_skill workspace dashboard --dir ./week

# the formal global daily plan (topic-level, not a time average)
python -m exam_review_skill workspace plan-v4 --dir ./week --date 2026-06-18
```

The orchestrator never mechanically splits time evenly: it weighs urgency, score gain opportunity, risk, target gap, learning cost, forgetting, and course maintenance - while every active course keeps a minimum spaced-review allocation (anti-starvation). Exam-day completion releases a course's future time to others.

## Chinese / English support

- **zh-CN and en-US are fully equivalent**: the catalog-parity test asserts every key exists in both locales (no Chinese-only features).
- **Three output modes** (Chinese / English / Bilingual). Bilingual means Chinese main text with English key terms - never every sentence twice.
- **terminology_map.json** per course unifies technical terms across languages (`Bayes' theorem` = `贝叶斯公式` = `Bayes公式`), so we never machine-translate terms on the fly.
- **Mixed-language materials** (Chinese PPT + English textbook) fuse into one topic with aliases and fusion confidence.
- **question_language and explanation_language** are independently controlled (e.g. English questions with Chinese explanations).

## Installation

```bash
git clone <your-repo-url> exam-review-skill
cd exam-review-skill
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install the core (stdlib-only runtime; optional extras for document parsing):

```bash
pip install -e .[test]
```

Optional extras:

```bash
pip install -e ".[ingestion]"   # PDF/PPTX/DOCX/image parsing + rendering
pip install -e ".[docx]"        # DOCX export
```

Run the tests:

```bash
python -m compileall exam_review_skill
python -m pytest
```

## Configuration

Create a workspace with your locale and daily time budget:

```bash
python -m exam_review_skill workspace init --dir ./week --locale zh-CN --daily-hours 6
```

### Multimodal provider

The pipeline fails closed when no provider is configured. Set one of:

```env
# OpenAI (Responses API, image input)
OPENAI_API_KEY=...
EXAM_REVIEW_OPENAI_VISION_MODEL=gpt-4o

# DeepSeek (chat completions with image input)
DEEPSEEK_API_KEY=...
EXAM_REVIEW_DEEPSEEK_VISION_MODEL=deepseek-chat
```

Use `--provider synthetic --demo` only for tests/fixtures/CI - synthetic records are rejected from real state by the contamination guard.

### OCR fallback (off by default)

Local OCR is disabled by default. Enable it explicitly only when native multimodal is unavailable:

```bash
set EXAM_REVIEW_OCR_FALLBACK=1   # Windows
export EXAM_REVIEW_OCR_FALLBACK=1  # macOS/Linux
```

OCR output is always `extraction_method=ocr_fallback` with low confidence and can never support high-confidence exam conclusions.

### User control (bilingual natural language)

```bash
# Chinese and English are equivalent
python -m exam_review_skill workspace override --dir ./week --date 2026-06-18 --skip botany
python -m exam_review_skill workspace nl --dir ./week --text "I only have three hours tomorrow"
python -m exam_review_skill workspace nl --dir ./week --text "明天只有3小时"
```

User overrides always beat the planner.

## Examples

| Scenario | What it exercises |
|---|---|
| [Chinese university final exam](examples/chinese-final-exam/README.md) | zh-CN course, evidence ingestion, tutor, quiz, cram |
| [English-language course](examples/english-course/README.md) | en-US course, English questions with Chinese explanations |
| [Mixed-language course](examples/mixed-language-course/README.md) | zh PPT + en textbook fused into one topic model |
| [Four-course exam week](examples/four-course-exam-week/README.md) | multi-course orchestrator, anti-starvation, dashboard |
| [24-hour cram](examples/24-hour-cram/README.md) | genuine 24h/3h/1h/30m rescue tiers |

Each example includes a runnable fixture (or the exact commands to build one) and expected outputs.

## On-demand reports

```bash
python -m exam_review_skill workspace report --dir ./week --type exam-risk-radar --course probability
python -m exam_review_skill workspace report --dir ./week --type formula-sheet --course probability --out formulas.md --format md
python -m exam_review_skill workspace report --dir ./week --type mock-exam --course probability --out mock.json --format json
```

Available reports: `course-overview`, `exam-risk-radar`, `past-exam-analysis`, `teacher-style`, `formula-sheet`, `wrongbook`, `7-day-plan`, `mock-exam`, `1-hour-cram`, `30-min-rescue`, `dashboard`, `welcome`.

Formats: Markdown (default), DOCX, PDF, Anki CSV, JSON. **An export failure never affects the main learning flow** - the Markdown is always produced and the failure is reported cleanly.

## Privacy

- Everything runs locally. Materials and student data stay on your machine unless you configure a cloud multimodal provider (your files/images then travel to that provider for understanding).
- No API keys are committed. Use a local `.env` / environment variables.
- Synthetic (mock/test) content is **never** written to real course state.
- Do not upload private student records, paid textbooks, copyrighted materials, real exam leaks, or restricted course files to public repositories.

## Limitations

- `likelihood_estimate` and readiness percentages are **ordinal heuristics**, not statistical probabilities. Never treated as predictions.
- Readiness shows `Unknown / Insufficient evidence` until there is enough real answer data - the system never fabricates a readiness score.
- Multimodal understanding needs a configured provider; without one, scanned / image-only pages are recorded as `unresolved` (never faked).
- PPTX/DOCX visual rendering requires LibreOffice when installed; otherwise native text is used and visual pages are recorded as unresolved.
- OCR fallback requires the tesseract binary and is disabled by default.
- Teacher-style claims are tiered (Observed / Strongly Inferred / Inferred / Unknown); nothing is asserted without evidence.

## Testing

```bash
python -m pytest
```

The suite covers (167+ tests):

- Workspace / course isolation / contamination guard
- Multimodal ingestion (text PDF, scanned PDF, PPTX, formula, table, exam paper, handwriting, mixed zh/en, provider failure, OCR fallback)
- Knowledge model (cross-language fusion, citation preservation, prerequisite edges, conflict handling, hallucination guard)
- Student model (composite mastery, no-data → unknown, forgetting, sessions)
- Orchestrator (5 realistic scenarios, anti-starvation, replan events, bilingual NL)
- Tutor / quiz / grading / diagnosis / wrongbook / cram + the full learning loop
- i18n (catalog parity zh=en, output modes, terminology)
- Reporting (welcome report, dashboard honesty, report rendering, exports)

## License

MIT License. See [LICENSE](LICENSE).
