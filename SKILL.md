---
name: exam-review-skill
description: Exam Review Agent that turns course materials into an evidence-grounded, multi-course, adaptive exam-week plan. Use when the user wants to prepare for exams, understand which topics matter and why (with source citations), get a persistent per-course student model, plan a whole exam week across multiple courses, practice with adaptive quizzes, get wrong-answer diagnosis and a wrongbook, or generate time-constrained cram plans. 中英文考试复习智能体：输入课程资料，输出提分路径。
---

# exam-review-skill

An Exam Review Agent: understand the materials, understand the exam, understand the student, and continuously decide what to study next across a multi-course exam week.

核心口号：输入课程资料，输出提分路径。

## When to use

- 用户有一学期的课件、教材、笔记、作业、扫描卷、真题，想复习期末考试。
- The user wants to know which topics are actually tested, with the original source cited.
- The user has multiple final exams in the same week and needs ONE coordinated plan.
- The user answers questions wrong and expects the system to remember, diagnose, and replan.
- The user needs a 30-minute rescue / 1-hour / 3-day cram before an exam.

## Workspace workflow (one exam week)

1. **Init** the workspace for the exam week:

```bash
python -m exam_review_skill workspace init --dir ./week --locale zh-CN --daily-hours 6
```

2. **Add courses** (each fully isolated):

```bash
python -m exam_review_skill workspace add-course --dir ./week --course probability --name "概率论" --exam-date 2026-06-19 --target-score 85
```

3. **Ingest materials** (native multimodal first; provider fails closed):

```bash
python -m exam_review_skill workspace ingest --dir ./week --course probability --input ./materials --provider openai
```

4. **Build the exam brain** (topics, exam model, risk radar, coverage):

```bash
python -m exam_review_skill workspace build --dir ./week --course probability --days-to-exam 3
```

5. **First-use report** (what the user should see after upload - inventory, structure, exam situation, gaps, risks, next steps):

```bash
python -m exam_review_skill workspace material-report --dir ./week --course probability
```

6. **Exam-week dashboard** (honest readiness; Unknown / Insufficient evidence until enough data):

```bash
python -m exam_review_skill workspace dashboard --dir ./week
```

7. **Global daily plan** (topic-level, not a time average):

```bash
python -m exam_review_skill workspace plan-v4 --dir ./week --date 2026-06-18
```

## Learning loop

- **Tutor** a topic (course-first, structured, supplementary-marked): `workspace tutor --course probability --topic central_limit_theorem`
- **Quiz** in any mode (diagnostic / s-priority / weak-topic / past-exam-style / mixed / wrongbook / speed-run / cram): `workspace quiz --mode s-priority --count 10`
- **Record an answer** (only real answers mutate mastery): `workspace answer --topic ... --correct`
- **Diagnosis + wrongbook**: wrong answers are classified into a 13-category taxonomy, stored, and drive mastery/risk/planner/future-quiz/cram.
- **Cram** (7d / 3d / 24h / 3h / 1h / 30m, genuinely distinct): `workspace cram --mode 30m`

## Reports

`workspace report --type course-overview|exam-risk-radar|past-exam-analysis|teacher-style|formula-sheet|wrongbook|7-day-plan|mock-exam|1-hour-cram|30-min-rescue|dashboard|welcome [--out file --format md|docx|pdf|anki|json]`

Export failure never affects the main learning flow.

## Language

- zh-CN and en-US are fully equivalent (catalog-parity tested). All user-facing output localizes.
- Three output modes: Chinese / English / Bilingual (Chinese main text + English key terms).
- Mixed-language materials fuse into one topic via terminology maps.
- English questions with Chinese explanations supported (independent question/explanation language).

## Principles (do not violate)

- 考试提分 > 泛泛总结；结构理解 > 长文本堆叠；课程证据 > 模型猜测。
- Native multimodal first; local OCR is disabled by default and never supports high-confidence conclusions.
- Evidence-grounded: every topic / exam point / answer carries source evidence ids. No fabricated citations.
- Real state > mock data: synthetic/mock content is rejected from real state by the contamination guard.
- Persistent student model; mastery is composite (not raw accuracy); no data -> unknown, never a pretend 0.5.
- Multi-course global optimization; anti-starvation; user overrides always beat the planner.
- likelihood_estimate and readiness are ordinal heuristics, NOT statistical probabilities.
