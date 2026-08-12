# Release Notes — exam-review-skill v2.0.0

**Exam Review Agent — From materials to marks. 输入课程资料，输出提分路径。**

## What's new in v2.0.0

v2.0.0 is the complete rewrite from the v0.1.0 batch generator to a persistent,
evidence-grounded, multi-course Exam Review Agent. Highlights:

- **Native multimodal first** — text layers (PDF/PPTX/DOCX) read natively; scanned /
  image-only pages, formulas, tables, diagrams, handwriting, and exam papers route
  to a multimodal provider. Local OCR is disabled by default and never supports
  high-confidence conclusions. Formula ambiguity forces a visual re-check.
- **Evidence grounding** — every topic, exam point, and answer carries source
  evidence ids; a contamination guard rejects synthetic/mock content from real
  state. No fabricated citations, probabilities, mastery, or teacher statements.
- **Persistent course model** — topic-centric knowledge graph with cross-language
  fusion (CLT / 中心极限定理 / Bayes公式 unify via terminology maps).
- **Exam intelligence** — real past-exam frequency, explainable S/A/B/C risk radar
  (full rationale), teacher style with Observed/Strongly-Inferred/Inferred/Unknown
  tiers, exam coverage report, conflict detection.
- **Student model** — composite mastery (accuracy + difficulty + independence +
  hints + recency + repeat errors + transfer + type coverage); no data -> unknown,
  never a pretend 0.5. Only real answer sessions mutate it.
- **Exam Week Orchestrator** — one coordinated global daily plan across courses;
  urgency / score-gain / risk / target-gap / learning-cost / forgetting /
  maintenance; anti-starvation; exam-day completion releases time to other courses.
- **Adaptive planning** — single-course plans with topic-level study blocks
  (course / topic / duration / reason / task / practice / completion criterion);
  replans after every quiz, wrong answer, new material, or rescheduled exam.
- **Tutor / quiz / diagnosis** — course-first structured tutor; 8 quiz modes;
  adaptive difficulty L1-L4; grading with process analysis; 13-category diagnosis
  with prerequisite-gap detection.
- **Wrongbook** — real wrong answers only; drives mastery, risk, planner, future
  quiz, and cram; retry scheduling from mistake type / severity / repeats / mastery
  / exam proximity.
- **Cram** — genuinely distinct 7d / 3d / 24h / 3h / 1h / 30m modes; the 30-minute
  rescue keeps only S-level core items; multi-course cram coordinated.
- **zh-CN / en-US** — fully equivalent (catalog parity tested); three output modes
  (Chinese / English / Bilingual); English questions with Chinese explanations.
- **Naive baseline benchmark** — the Skill is measurably better than a one-shot
  naive workflow on source grounding, cross-document fusion, past-exam mapping,
  hallucination control, personalization, adaptive planning, and multi-course
  scheduling (see `docs/V2_FINAL_ACCEPTANCE_REPORT.md`).

## Installation

From the source distribution:

```bash
pip install -e ".[test]"        # dev / tests
pip install -e ".[ingestion]"   # document parsing + multimodal rendering
```

Or install the wheel:

```bash
pip install dist/exam_review_skill-2.0.0-py3-none-any.whl
```

Verify checksums:

```bash
cd dist
sha256sum -c SHA256SUMS.txt     # macOS/Linux
Get-FileHash exam-review-skill-v2.0.0.zip  # Windows
```

## Quick start

```bash
python -m exam_review_skill workspace init --dir ./week --locale zh-CN --daily-hours 6
python -m exam_review_skill workspace add-course --dir ./week --course probability --name "概率论" --exam-date 2026-06-19 --target-score 85
python -m exam_review_skill workspace ingest --dir ./week --course probability --input ./materials --provider openai
python -m exam_review_skill workspace build --dir ./week --course probability
python -m exam_review_skill workspace dashboard --dir ./week
python -m exam_review_skill workspace plan-v4 --dir ./week --date 2026-06-18
```

## Configuration

- Multimodal provider: `OPENAI_API_KEY` / `DEEPSEEK_API_KEY` (+ optional
  `EXAM_REVIEW_OPENAI_VISION_MODEL` / `EXAM_REVIEW_DEEPSEEK_VISION_MODEL`). The
  pipeline fails closed when unset.
- OCR fallback: disabled by default; enable with `EXAM_REVIEW_OCR_FALLBACK=1` only
  when native multimodal is unavailable.
- Locale / daily hours: set at `workspace init`.

## Notes for this environment

- No remote Git repository is configured, so nothing was pushed (no fake publish).
- The scanned-material multimodal path was validated with the synthetic provider in
  demo mode (no API key in this environment); real multimodal requires a configured
  provider.
- OCR engine (tesseract binary) is not installed here; the OCR-fallback path is
  covered by tests and degrades to `unresolved` (never fabricates).

## Files

- `dist/exam-review-skill-v2.0.0.zip` — source distribution
- `dist/exam_review_skill-2.0.0-py3-none-any.whl` — wheel
- `dist/SHA256SUMS.txt` — checksums
