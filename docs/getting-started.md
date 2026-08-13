# Getting started

RecallForge runs inside your AI host. The core Skill does not require Python, an API key, or a separate program.

## 1. Install

Quick version: download `recallforge-skill-v2.2.0.zip` from the [latest formal Release](https://github.com/SiriZhao/recallforge-skill/releases/latest), extract it, and copy `recallforge` to `%USERPROFILE%\.agents\skills` on Windows or `~/.agents/skills` on macOS/Linux.

Full platform steps: [RecallForge for Codex](codex.md).

## 2. Verify

Start a new Codex turn and run `$recallforge self-test`. Continue when the response ends in `Status: READY`. If it does not, use [Troubleshooting](troubleshooting.md).

## 3. Add a manageable first set

Attach one chapter, one slide deck, or a small group of past-paper pages. PPTX, digital/scanned PDF, PNG/JPG/JPEG/WEBP, DOCX, TXT, and Markdown have implemented intake paths, but visual and scan-heavy material depends on your host’s vision capability.

Remove unnecessary private information and use only material you are authorized to process.

## 4. Inspect before reviewing

Run:

```text
$recallforge inspect-materials
Inspect the attached materials. Report material types, pages or slides the host can actually count, scan-heavy or visual-heavy content, recognition warnings, and the recommended next action. Do not start review yet.
```

RecallForge must not invent file counts or pretend unreadable pages were processed.

## 5. Build the course structure

```text
$recallforge
Use these materials as the primary course scope. Build a compact, source-grounded course structure. Mark incomplete coverage and conflicting definitions. Do not start with a long summary.
```

## 6. Start diagnostic recall

```text
Test me one question at a time. Let me answer before explaining. Track only weaknesses demonstrated by my answers.
```

## 7. Continue adaptive review

After each answer, RecallForge should classify the gap, give a short repair, and ask a nearby follow-up question. It should not claim mastery without learner responses.

## 8. Run a mock exam

```text
$recallforge
Create a mock exam based only on the supplied materials. Do not reveal answers first. After I respond, grade, explain errors, show source anchors for disputed points, and create a final targeted review.
```

## 9. Fix recognition problems

If a formula, scan, table, or diagram is uncertain, attach a clearer crop or original page. Host vision is preferred; optional local OCR is a fallback for text recovery and is not required for the core Skill. See [Materials](materials.md) and [Multimodal material](multimodal.md).
