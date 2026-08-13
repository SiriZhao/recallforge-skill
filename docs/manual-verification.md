# Release Host Verification Protocol

This is the formal v2.2 release gate for real host behavior. The maintainer or a trusted reviewer must run it in a **new, independent Codex session**—not by recursively launching Codex from inside Codex.

## Required tests

1. Run `/skills` and confirm `recallforge` is listed.
2. Run `$recallforge self-test`. PASS only when the response ends with `Status: READY` and includes the required probability topics, one active-recall question, one exam-style item, and a next step.
3. Attach `skill/recallforge/assets/self-test/multimodal/probability-slide.svg` and run `$recallforge multimodal-test`.
   - PASS: the host identifies `P(A|B) = P(A ∩ B) / P(B)`, distinguishes independent and mutually exclusive events in the table, explains the arrow as normalization by `P(B)`, asks one source-grounded recall question, and ends with `Status: MULTIMODAL_READY`.
   - If the host cannot inspect the asset, record `HOST_CAPABILITY_UNAVAILABLE`; do not mark the Skill itself failed.
4. Attach the self-authored `lecture.pptx`, a scanned PDF, and a past-paper PDF, then run:

   ```text
   $recallforge
   Inspect these materials first.
   Then build the course structure and start a short diagnostic review.
   ```

   PASS requires observed material inspection, source structure, knowledge reconstruction, and active recall—not merely that `$recallforge` accepted the string.

## Evidence

Copy [verification/host-verification-template.json](../verification/host-verification-template.json) and fill it in. Record:

- Host name and version
- Operating system
- Date
- RecallForge commit
- Install method
- Each test result and short evidence
- Recognition warnings

Do not include names, emails, local user directories, private paths, credentials, or private study material. Keep the completed file out of the repository unless it has been sanitized and the maintainer decides it is public QA evidence.
