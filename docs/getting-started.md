# Getting Started with RecallForge

RecallForge helps you build an exam-review loop from your own course materials. It is not an exam-answer service and it does not replace checking your course requirements.

## Before you begin

You need Python 3.10 or later. On Windows, install Python from [python.org](https://www.python.org/downloads/) and select **Add Python to PATH** during setup. On macOS/Linux, `python3 --version` should show 3.10 or later.

Use materials you own or are allowed to process: notes, lecture handouts, a syllabus, study guides, small authorized excerpts, and past papers you may use. The core setup works with TXT. PDF, DOCX, PPTX, images, and OCR require the optional ingestion dependencies; scanned and image-heavy documents also need a configured provider.

## Install

1. Open the project’s [Releases page](https://github.com/SiriZhao/recallforge-skill/releases/latest).
2. Download `recallforge-skill-v2.0.4.zip` and extract it.
3. Open a terminal in the extracted folder.
4. Run `python -m pip install .`.
5. Run `recallforge --help`.

If you see a list of `workspace` commands, RecallForge is installed. If Windows says `python` is not found, run `py -m pip install .` and `py -m recallforge --help` instead.

To parse additional formats after the core install, run `python -m pip install ".[ingestion]"`. This installs Python libraries only; it does not configure an API key or upload material.

## Your first review: Probability

Create a folder named `materials` and put a short text file inside it, for example `probability-notes.txt`:

```text
Central Limit Theorem: the standardized sum of many independent random variables is approximately normal under its assumptions. The instructor emphasized checking the assumptions.
```

Then run the following commands from the folder where you want the review workspace:

```bash
recallforge workspace init --dir ./probability-review --locale en-US --daily-hours 3
recallforge workspace add-course --dir ./probability-review --course probability --name "Probability" --exam-date 2026-12-18 --target-score 80
recallforge workspace ingest --dir ./probability-review --course probability --input ./materials
recallforge workspace build --dir ./probability-review --course probability --days-to-exam 7
recallforge workspace material-report --dir ./probability-review --course probability
```

The report is your first check: it lists the material, identifies gaps or unresolved items, and gives evidence-aware next steps. It should not claim you are ready if you have not yet answered questions.

Next, learn and test one topic:

```bash
recallforge workspace tutor --dir ./probability-review --course probability --topic central_limit_theorem
recallforge workspace quiz --dir ./probability-review --course probability --mode mixed --count 3
```

After you answer a question, record the real outcome. Use `--correct` only when it was correct; omit it for an incorrect result and include a brief answer if useful.

```bash
recallforge workspace answer --dir ./probability-review --course probability --topic central_limit_theorem --correct
```

## Recommended rhythm

This is a suggestion, not a required schedule:

1. **Start:** ingest materials and inspect the material report.
2. **Map:** build the knowledge and exam models; check coverage and priorities.
3. **Recall:** use tutor only to repair a gap, then use quizzes to retrieve from memory.
4. **Repair:** record errors, revisit the wrongbook, and let the next plan target weak topics.
5. **Prepare:** use a mock-exam report or `cram` mode near the exam.

For a short review, begin with `workspace diagnostic`, then `workspace quiz --mode weak-topic`. For a multi-course exam week, add each course to the same workspace and use `workspace plan-v4`.

## Common questions

**The skill did not “trigger.”** RecallForge is a local CLI package. Confirm `recallforge --help`; then invoke its commands directly. A host AI tool may read `SKILL.md`, but host-specific automatic discovery is not guaranteed by this repository.

**My PDF is large or scanned.** Start with the relevant chapters or split files into manageable pieces. Install the ingestion extra; configure a supported provider only if you accept its data handling. Unreadable pages will be reported as unresolved.

**Can I use Chinese or English?** Yes. Use `--locale zh-CN` or `--locale en-US`; mixed-language terminology is supported.

**How do I update or uninstall?** Download the newer release and run `python -m pip install .` again. To uninstall the command package, run `python -m pip uninstall recallforge-skill`. Delete any review workspace folders separately if you no longer need their local study state.

Need help? See [Troubleshooting](troubleshooting.md) or open a GitHub issue without keys or private study materials.
