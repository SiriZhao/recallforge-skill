---
name: recallforge
version: 2.0.4
description: RecallForge — AI Exam Review Skill. Use when a learner wants to turn authorized course materials, notes, syllabus items, or past papers into an exam-oriented review workflow: evidence-linked knowledge reconstruction, active recall, adaptive practice, weakness diagnosis, targeted review, multi-course planning, or time-boxed exam simulation. Supports Chinese, English, and mixed-language material.
---

# RecallForge — AI Exam Review Skill

**Forge course materials into exam-ready knowledge.**

RecallForge is an evidence-grounded exam-review workflow, not a generic summarizer. It works from the learner’s authorized materials and should keep claims traceable to those materials.

## Trigger when

- The learner shares or refers to lecture notes, slides, PDFs, DOCX files, syllabus, study guides, question banks, or past papers and wants exam preparation.
- They ask what matters for an exam, which topics are weak, how to practice active recall, how to repair mistakes, or how to plan an exam week.
- They need a diagnostic quiz, targeted review, a mock exam, a wrong-answer review, or a 7-day to 30-minute cram plan.

Do not claim it has processed files that were not supplied or ingested. Do not use it to facilitate cheating, obtain restricted exam content, or process materials without authorization.

## Input and output

Input may include material files, course name, exam date, target score, available time, preferred language, prior answers, and past papers. The CLI’s core runtime natively accepts text files; optional ingestion dependencies and a configured multimodal provider enable PDF, PPTX, DOCX, images, and limited OCR fallback.

Output is proportionate to the evidence available. It may include a material inventory, knowledge map, exam scope map, priority/risk rationale, active-recall questions, answer diagnosis, wrongbook entries, a targeted plan, and an exam-style or cram output. When evidence is insufficient, say so explicitly; readiness remains unknown rather than guessed.

## Workflow

```text
Course materials
  → material understanding and evidence store
  → knowledge reconstruction
  → exam scope mapping and priority
  → active recall and practice
  → weakness detection
  → targeted review and replanning
  → exam simulation or cram
  → feedback from real answers
```

1. **Clarify the review context.** Ask only for missing essentials: course, exam date or horizon, available study time, material location, and output language.
2. **Create an isolated course workspace.** Keep each course’s knowledge and student state separate.
3. **Ingest and inspect material.** Preserve source references. Flag unresolved scans, ambiguous formulas, and missing material; never invent text or citations.
4. **Reconstruct knowledge and exam scope.** Build evidence-linked topics, prerequisites, past-paper mapping, teacher-emphasis tiers, coverage, conflicts, and explainable priorities.
5. **Choose the next learning action.** Prefer active recall and practice over passive recap. Use a diagnostic first when the learner’s mastery is unknown.
6. **Diagnose real responses.** Record only real user answers. Wrong answers can update the student model and wrongbook, then change future practice and plans.
7. **Close the loop.** Replan after new material, completed quizzes, wrong answers, changed time, changed target, or rescheduled exams.

## Behavior boundaries

- Treat course evidence as stronger than model knowledge. Mark helpful general explanations as supplementary.
- Do not fabricate citations, past-exam frequency, teacher tendencies, readiness scores, or mastery.
- Treat likelihood and readiness as ordinal planning heuristics, never statistical predictions.
- Keep OCR output low confidence; if formulas, tables, handwriting, or scans cannot be verified, request a clearer source rather than guessing.
- Respect privacy, copyright, and academic-integrity rules. Do not store API keys, personal student records, restricted exams, or private materials in examples or reports.
- Use Chinese, English, or bilingual terminology as requested. Preserve technical terms and source language when translation would reduce precision.

## CLI path

```bash
recallforge workspace init --dir ./my-review --locale zh-CN --daily-hours 3
recallforge workspace add-course --dir ./my-review --course probability --name "概率论" --exam-date 2026-12-18 --target-score 80
recallforge workspace ingest --dir ./my-review --course probability --input ./materials
recallforge workspace build --dir ./my-review --course probability --days-to-exam 7
recallforge workspace diagnostic --dir ./my-review --course probability
recallforge workspace quiz --dir ./my-review --course probability --mode weak-topic --count 5
recallforge workspace cram --dir ./my-review --course probability --mode 1h
```

For installation and complete command documentation, see [README](README.md), [Getting Started](docs/getting-started.md), and [Usage](docs/usage.md).
