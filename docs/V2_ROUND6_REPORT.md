# Round 6 Report — 国际化收口 + 用户体验 + 报告系统 (v2.0.0)

> Scope per the master instruction: do NOT change the quantitative / core
> algorithms. This round is specifically about making the actual user experience
> good: full zh/en equivalence, terminology-driven terms, three output modes,
> first-use experience, exam-week dashboard, on-demand reports, export formats,
> README rewrite, examples, and the acceptance audit.

## 1. Chinese and English fully equivalent (verified)

The catalog-parity test (`tests/test_i18n_parity.py`) asserts **every catalog key
exists in BOTH zh-CN and en-US** with equal counts. No Chinese-only features, no
English-only translation. Current catalogs: 130+ keys in each locale (was 92 at the
start of this round).

## 2. Terminology, not machine translation (verified)

The per-course `terminology_map.json` (Round 1) is used to unify technical terms
across languages (`Bayes' theorem` = `贝叶斯公式` = `Bayes公式`). The new
`render_bilingual` accepts a `term_map` + `term_key` so bilingual output uses the
course's own terminology - never ad-hoc machine translation.

## 3. Three output modes (verified)

`OutputMode` supports `chinese` / `english` / `bilingual`.

**Bilingual means Chinese main text + English key term** - never every sentence
twice. `render_bilingual` appends only the other-language *term* (short, from the
terminology map); a long sentence is never duplicated
(`test_render_bilingual_does_not_duplicate_long_sentences`). `primary` can flip the
arrangement (Chinese main + English terms, or English main + Chinese term).

## 4. First-use experience (verified)

`workspace material-report` returns - after upload - exactly what the instruction
asks for, instead of dumping files:

```
一、材料盘点      (files, evidence, topics, unresolved pages)
二、课程结构      (chapters -> topic counts)
三、考试情况      (exam date, target, estimate or "unknown")
四、资料缺口      (missing answers, missing past exams, low-confidence topics)
五、当前风险      (mastery counts, or "no data, not fabricated")
六、下一步建议    (diagnostic, fill gaps, plan, tutor)
```

Both zh and en verified (`test_first_use_report_has_all_sections`,
`test_first_use_report_english`).

## 5. Exam Week Dashboard (verified)

Text-based overview (`workspace dashboard`), per course:

```
## 概率论
考试：明天考试
风险：HIGH
准备度：57%
今日：1.8 小时
```

**Readiness is honest**: it only shows a number when there is enough real answer
data; otherwise it shows `Unknown / Insufficient evidence` - never fabricated
(`test_dashboard_honest_readiness`). Exam proximity reads from the calendar with a
manifest fallback; risk is derived from the S/A share of the exam model.

## 6. What should I do now? (verified)

The dashboard ends with a "接下来做什么 / What should I do now?" section listing the
top 3 plan blocks with **topic, duration, why, and done-when** - user-facing, not
internal JSON.

## 7. On-demand reports (verified)

`workspace report --type <name>`:

`course-overview`, `exam-risk-radar`, `past-exam-analysis`, `teacher-style`,
`formula-sheet`, `wrongbook`, `7-day-plan`, `mock-exam`, `1-hour-cram`,
`30-min-rescue`, `dashboard`, `welcome`.

All 12 render and are tested (`test_all_report_types_render`).

## 8. Output formats (verified)

Markdown (default), DOCX, PDF, Anki CSV, JSON. **Export failure never affects the
main learning flow**: `export_report` returns `(ok, message)` and the caller keeps
the Markdown. Verified live: PDF export with reportlab uninstalled reports a clean
"导出失败（不影响主流程）" while MD/DOCX/JSON exports succeed
(`test_export_failure_isolated`).

## 9. README rewritten

Covers: What it is, Why not just upload everything to ChatGPT, Architecture,
Multimodal workflow, Multi-course exam week, Chinese/English support, Installation,
Configuration (providers, OCR fallback, user control), Examples, Privacy,
Limitations, Testing.

## 10. Examples added

Five runnable scenarios in `examples/` with a shared fixture helper
(`examples/examples_common.py`) and per-scenario README:

| Example | Exercises |
|---|---|
| chinese-final-exam | zh-CN course, tutor/quiz/cram |
| english-course | en-US UI, English questions + Chinese explanations |
| mixed-language-course | zh PPT + en textbook fused into one topic model |
| four-course-exam-week | multi-course orchestrator, anti-starvation, dashboard |
| 24-hour-cram | distinct 24h/3h/1h/30m tiers + multi-course coordination |

Verified by `tests/test_examples.py`.

## 11. Acceptance audit (search + per-item check)

| Pattern | Result |
|---|---|
| TODO | 0 hits in v2 code |
| placeholder | 0 hits |
| coming soon | 0 hits |
| not implemented / FIXME | 0 hits |
| mock | 4 hits, ALL in `state/isolation.py` - the intentional contamination guard that **rejects** mock/sandbox content from real state (by design, must stay) |
| hard-coded Chinese | 180 string-literal hits audited: ~90% are content-recognition regexes (exam/chapter/teacher markers - must be bilingual to parse both languages) + intentional catalogs. The genuinely user-facing hard-coded strings were localized this round: diagnosis explanations, formula-ambiguity signals, mistake-type labels. The rest are locale-branched (zh/en) |
| hard-coded English | None found in v2 user-facing paths; all user-facing text is locale-branched or catalog-driven |

Legacy v0 batch modules remain in the repo (not part of the v2 flow) - they are
documented as legacy and will be removed in a dedicated cleanup, not mixed into this
UX round (which must not change core behavior).

## 12. Test results

* Full suite: **169 passed, 1 skipped** (Round 5 baseline 146 + 23 new Round 6
  tests). The 1 skipped test is the unchanged Round 2 OCR-engine-present branch
  (tesseract binary not installed on this machine).
* Version bumped to **2.0.0**.

Commit: `feat: complete bilingual exam review user experience`
