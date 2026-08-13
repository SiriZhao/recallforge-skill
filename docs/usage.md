# Usage

RecallForge commands share a workspace directory (`--dir`) and a course identifier (`--course`). Start with `recallforge --help` and `recallforge workspace --help` for the installed command reference.

| Goal | Command | What to expect |
|---|---|---|
| Fast diagnosis | `workspace diagnostic --minutes 15` | A 10–20 minute coverage-oriented diagnostic plan. |
| Systematic review | `workspace build`, then `workspace plan-v4` | Evidence-linked priorities and daily topic blocks. |
| Active recall | `workspace quiz --mode mixed --count 5` | Questions in the requested mode; record actual outcomes. |
| Weakness repair | `workspace quiz --mode weak-topic` | Practice biased toward real weak or unknown areas. |
| Past-paper review | `workspace quiz --mode past-exam-style` | Evidence-derived past-exam-style prompts when past papers exist. |
| Wrong-answer review | `workspace report --type wrongbook --course <id>` | Recorded real wrong answers and repair direction. |
| Mock output | `workspace report --type mock-exam --course <id>` | A structured exam-style output, not a prediction of a real exam. |
| Time-boxed review | `workspace cram --mode 24h|3h|1h|30m` | A time-constrained priority pack. |

## A complete loop

```bash
recallforge workspace diagnostic --dir ./my-review --course probability --minutes 15
recallforge workspace tutor --dir ./my-review --course probability --topic central_limit_theorem
recallforge workspace quiz --dir ./my-review --course probability --mode weak-topic --count 5
recallforge workspace answer --dir ./my-review --course probability --topic central_limit_theorem --correct
recallforge workspace plan-v4 --dir ./my-review --date 2026-12-11
```

For an incorrect response, omit `--correct` and optionally provide `--question`, `--user-answer`, and `--correct-answer`. This is the path that can create a wrongbook entry and change later planning.

## Material and provider behavior

`workspace ingest` reads TXT without a cloud provider. Optional parsing packages support additional file types. For scan/image interpretation, choose an installed and configured provider; otherwise RecallForge reports unresolved material instead of fabricating evidence. `--ocr` explicitly enables the low-confidence OCR fallback.

## Output language

Create the workspace with `--locale zh-CN` or `--locale en-US`. Several reports also offer `--output-mode chinese|english|bilingual`. Bilingual mode uses Chinese body text and English key terms instead of duplicating every line.

## Multi-course planning

Add every course to one workspace, ingest/build each one, then run `workspace dashboard` and `workspace plan-v4`. The planner coordinates time using exam proximity, risk, target gap, learning cost, forgetting, and maintenance; it does not merge subject knowledge across courses.
