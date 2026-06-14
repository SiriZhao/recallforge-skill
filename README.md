# exam-review-skill

**A powerful AI exam review skill that turns course materials into a scoring path.**

**一个将课程资料转化为提分路径的 AI 期末复习 Skill。**

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://github.com/YOUR_USERNAME/exam-review-skill/actions/workflows/tests.yml/badge.svg)](https://github.com/YOUR_USERNAME/exam-review-skill/actions/workflows/tests.yml)
[![GitHub stars](https://img.shields.io/github/stars/YOUR_USERNAME/exam-review-skill?style=social)](https://github.com/YOUR_USERNAME/exam-review-skill/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/YOUR_USERNAME/exam-review-skill)](https://github.com/YOUR_USERNAME/exam-review-skill/issues)
[![Codex Skill](https://img.shields.io/badge/OpenAI%20Codex-Skill-412991)](SKILL.md)

> Replace `YOUR_USERNAME/exam-review-skill` in badges after publishing the repository.

exam-review-skill is not another document summarizer. It is an exam-oriented review system that converts lecture slides, textbooks, notes, scanned papers, exercises, and past exams into a course index, exam graph, risk radar, adaptive study plan, past-exam variants, wrong-question notebook, and cram pack.

exam-review-skill 不是普通资料总结器，而是面向期末考试的复习效率系统。它可以把课件、教材、笔记、扫描卷和往年题转化为课程知识索引、考试考点图谱、风险雷达、自适应复习计划、真题变式训练、错题本和临考急救包。

**Core slogan:** Input course materials, output a scoring path.  
**核心口号：** 输入课程资料，输出提分路径。

## Why This Exists

Dropping a pile of course files into a generic LLM app often feels magical for five minutes, then messy when you need to actually pass the exam.

| Generic LLM app | exam-review-skill |
|---|---|
| Context limit eats long courses | Source-grounded workflow keeps files, chunks, and references |
| Document structure is easy to lose | Preserves source file, page/slide, heading, and question number where available |
| Citations are unstable | Tracks source refs and confidence |
| Does not know what is likely to be tested | Builds an exam graph from past exams, notes, and teacher hints |
| Does not know your target score | Adapts strategy for passing, 80, or 90+ goals |
| No scoring priority | Generates an S/A/B/C risk radar |
| No persistent mistake tracking | Maintains a wrong-question notebook |
| No time compression | Produces 3-day, 1-day, 3-hour, 1-hour, 30-minute, and 10-minute cram plans |

## Feature Highlights

- **Course Index:** turn raw materials into structured topics.
- **Exam Graph:** infer how each topic may be tested.
- **Risk Radar:** rank what to study first with S/A/B/C priorities.
- **Adaptive Study Plan:** plan by days left, target score, and available hours.
- **Past-Exam Variants:** generate likely variations from previous exams.
- **Cram Pack:** 3-day, 1-day, 3-hour, 1-hour, 30-minute, and 10-minute rescue plans.
- **Wrongbook:** track mistakes and generate targeted retraining.
- **Quality Guard:** flag unsupported, low-confidence, or source-missing outputs.
- **Mock Provider:** works without API keys for testing, demos, and CI.

## Output Structure

```text
ExamReview_Output/
├─ 00_资料来源与解析报告.md
├─ 01_课程知识索引.md
├─ 02_考试考点图谱.md
├─ 03_考试风险雷达.md
├─ 04_章节重点精讲.md
├─ 05_高频考点与命题预测.md
├─ 06_往年题考点映射表.md
├─ 07_真题变式训练.md
├─ 08_自适应复习计划.md
├─ 09_个人薄弱点诊断.md
├─ 10_今日复习任务.md
├─ 11_专项训练题.md
├─ 12_错题本.md
├─ 13_临考急救包.md
├─ 14_老师命题风格报告.md
├─ 15_考前30分钟速救版.md
├─ generation_report.md
├─ course_index.json
├─ exam_graph.json
├─ risk_radar.json
├─ student_state.json
└─ wrongbook.json
```

## Quick Start

```bash
git clone https://github.com/YOUR_USERNAME/exam-review-skill.git
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

Install and run the demo:

```bash
pip install -e .
python -m exam_review_skill run \
  --input examples/input \
  --output examples/output \
  --course "Experimental Chemistry" \
  --target-score 80 \
  --daily-hours 4
```

## CLI Usage

Full run:

```bash
python -m exam_review_skill run --input ./materials --output ./ExamReview_Output --course "课程名称" --exam-date "2026-06-25" --target-score 80 --daily-hours 4
```

Cram pack only:

```bash
python -m exam_review_skill cram --state ./ExamReview_Output/student_state.json --hours-left 3
```

Past-exam variants:

```bash
python -m exam_review_skill variants --input ./materials --output ./ExamReview_Output --count 20
```

Study plan only:

```bash
python -m exam_review_skill plan --state ./ExamReview_Output/student_state.json --days-left 3 --daily-hours 4 --target-score 80
```

S-priority quiz:

```bash
python -m exam_review_skill quiz --state ./ExamReview_Output/student_state.json --mode s-priority --count 20
```

Wrongbook variants:

```bash
python -m exam_review_skill quiz --state ./ExamReview_Output/student_state.json --mode wrongbook --count 10
```

## Supported Inputs

- `.txt`
- `.md`
- `.pdf`
- `.pptx`
- `.docx`
- `.png`
- `.jpg`
- `.jpeg`
- scanned papers
- past exams
- lecture notes
- teacher hints

If OCR or document parsing dependencies are unavailable, the system falls back gracefully and records warnings in `generation_report.md`.

## How It Works

```text
Materials
→ Ingest
→ OCR
→ Classify
→ Chunk
→ Course Index
→ Exam Graph
→ Risk Radar
→ Study Plan
→ Quiz / Variants / Wrongbook
→ Cram Pack
→ Quality Report
```

## Example Output

Risk Radar example:

| Priority | Exam Point | Why it matters | Recommended action |
|---|---|---|---|
| S | Acid-base titration calculation | High past-exam frequency and high score potential | Practice template problems first |
| A | Indicator selection | Common conceptual trap | Memorize decision logic |
| B | Experimental procedure order | Medium frequency | Review before exam |

## Codex Skill Usage

This repository is also a Codex Skill. The root directory contains [`SKILL.md`](SKILL.md), which tells Codex when and how to use the workflow.

Use it as a Codex Skill when a user wants to:

- prepare for a university final exam;
- analyze lecture slides, notes, textbooks, scanned papers, exercises, past exams, or teacher hints;
- build a source-grounded course index;
- identify high-risk exam points;
- generate adaptive study plans, quizzes, variants, wrongbook entries, or cram packs.

To install locally for Codex discovery, copy or link this folder to:

```text
~/.codex/skills/exam-review-skill
```

or on Windows:

```text
%USERPROFILE%\.codex\skills\exam-review-skill
```

## Configuration

By default, exam-review-skill uses `MockLLMProvider`, so demos and tests run without API keys.

Future provider integrations are reserved for:

- OpenAI
- DeepSeek
- Claude

Never commit API keys. Use a local `.env` file and keep it out of Git. This repository only provides `.env.example`.

```env
OPENAI_API_KEY=
DEEPSEEK_API_KEY=
ANTHROPIC_API_KEY=
EXAM_REVIEW_PROVIDER=mock
```

## Development

```bash
python -m compileall exam_review_skill
python -m pytest
```

The CI workflow runs tests on Python 3.10 and 3.11.

## Roadmap

### v0.1.0

- Basic CLI
- Mock provider
- Course index
- Exam graph
- Risk radar
- Cram pack

### v0.2.0

- Better OCR
- Better PPT/PDF parsing
- DOCX export improvements
- Anki export improvements

### v0.3.0

- Real LLM providers
- Interactive mastery diagnosis
- Spaced repetition
- Better wrongbook

### v0.4.0

- Web UI
- Multi-course library
- Collaborative course templates

## Contributing

Contributions are welcome.

1. Fork the repository.
2. Create a feature branch.
3. Run `python -m compileall exam_review_skill` and `python -m pytest`.
4. Submit a pull request with a clear description and screenshots or sample outputs when helpful.

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## Disclaimer

exam-review-skill is a study assistant, not an exam oracle. It does not guarantee prediction accuracy or higher scores. Generated content should be checked against your course syllabus, teacher instructions, and official answers.

Do not use this project to violate school exam rules. Do not upload sensitive personal information, private student records, paid textbooks, copyrighted materials, real exam leaks, or restricted course files to public repositories.

## License

MIT License. See [LICENSE](LICENSE).

## Star

If this project helps you study faster or build better AI learning tools, consider giving it a star.

如果这个项目对你的复习或 AI 学习工具开发有帮助，欢迎点一个 Star。
