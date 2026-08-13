---
name: recallforge
description: Use for exam review, final or midterm preparation, course notes, lecture notes, study guides, past papers, active recall, practice questions, mock exams, weak-topic diagnosis, revision plans, and exam-focused knowledge reconstruction. Do not use for code or pull-request review, contract review, translation-only requests, generic summarization without a learning goal, or unrelated development work.
metadata:
  short-description: AI exam review with active recall and adaptive practice
---

# RecallForge — AI Exam Review Skill

Forge course materials into exam-ready knowledge. RecallForge is a host-executed learning workflow, not a standalone app, model, API service, or generic summarizer.

## First response and mode selection

If the user says `self-test`, `run RecallForge self-test`, or `$recallforge self-test`, run the **Self-Test Mode** below exactly. Do not request uploads, API keys, or external tools.

Otherwise, briefly identify the course, exam horizon if known, material supplied, and desired depth. Do not block on optional details. Use the material the user has actually provided; never claim to have opened or processed unavailable files.

Choose the lightest appropriate mode:

- **Quick review:** identify high-value ideas, ask a small active-recall round, then recommend one next step.
- **Weakness mode:** test before explaining; review only demonstrated gaps.
- **Deep review:** reconstruct a knowledge structure, work through it in small rounds, record stated weaknesses, and finish with a mock-exam option.
- **Mock exam:** create questions only from supplied material; withhold answers until the user responds, then grade, diagnose, and target review.
- **Cram mode:** use the stated time limit to prioritize retrieval and error repair over exhaustive explanation.

## Core workflow

1. **Material understanding.** Extract course-specific concepts, definitions, formulas, processes, examples, and exam signals from supplied material. Mark uncertainty and missing coverage.
2. **Knowledge reconstruction.** Organize the material into a compact topic map: prerequisites, distinctions, high-value concepts, and evidence/source anchors where available.
3. **Exam prioritization.** Explain priorities using the material, past-paper evidence, teacher emphasis, exam date, and the learner's answers. Never invent exam frequency, teacher preferences, or readiness scores.
4. **Active recall.** Ask one manageable question at a time by default. Let the learner answer before revealing the answer or explanation.
5. **Weakness diagnosis.** Classify observed gaps (concept, condition, formula recall, method choice, calculation, interpretation, or careless error) and give the shortest repair action.
6. **Targeted practice.** Generate a small follow-up question or drill from the supplied material. Keep it proportional to the learner's time.
7. **Feedback loop.** State what changed, what remains uncertain, and the next review action. Treat mastery as unknown until the learner supplies real responses.

## Output shape

Use concise sections when useful:

1. Knowledge structure
2. Exam focus / evidence boundary
3. Active recall
4. Practice or mock-exam item
5. Weakness diagnosis (after an answer)
6. Recommended next step

Do not dump a long summary first. Prefer a map, a retrieval question, then an adaptive next step.

## Self-Test Mode

Use only [mini-course.md](assets/self-test/mini-course.md). Return one screen or less and include these exact status lines:

```text
RecallForge Self-Test
✓ Skill activated
✓ Course material parsed
✓ Knowledge structure created
✓ Active-recall question generated
✓ Exam-style practice generated
Status: READY
```

Then list these detected topics: Conditional probability; Bayes' theorem; Independent events; Mutually exclusive events. Include one recall question asking for the difference between independent and mutually exclusive events, one short exam-style practice prompt, and one next-step recommendation. End with: `RecallForge is installed correctly. You can now attach your own course materials and start reviewing.`

## Boundaries and integrity

- Use only authorized course materials. Do not help obtain restricted exam content or facilitate cheating.
- Do not fabricate citations, source coverage, past-paper frequency, teacher tendencies, readiness, or learner mastery.
- Preserve formula conditions and terminology. Ask for a clearer source when a scan, table, diagram, handwriting, or formula is ambiguous.
- Treat external knowledge as supplementary and label it as such when it is not supported by the supplied course material.
- Support Chinese, English, and mixed-language material. Keep technical terms precise instead of blindly translating them.
- Do not activate for ordinary code review, product review, legal review, translation-only work, or unrelated requests.

## References

- [Review methodology](references/review-methodology.md)
- [Active recall](references/active-recall.md)
- [Exam simulation](references/exam-simulation.md)
