# Manual host verification (2–3 minutes)

Use a fresh Codex turn after installing the candidate Skill.

1. Run `/skills` and record whether `recallforge` appears.
2. Run `$recallforge self-test`. Pass only if the response ends with `Status: READY` and includes the required probability topics, recall question, practice item, and next step.
3. Attach `skill/recallforge/assets/self-test/multimodal/probability-slide.svg` and run `$recallforge multimodal-test`.
4. Pass the multimodal step only if the host identifies `P(A|B) = P(A ∩ B) / P(B)`, distinguishes independent from mutually exclusive events in the table, explains the arrow as normalization by `P(B)`, asks one source-grounded recall question, and ends with `Status: MULTIMODAL_READY`.
5. If the host cannot inspect the asset, record `HOST_CAPABILITY_UNAVAILABLE`; do not mark the Skill itself failed.
6. Upload one self-authored scan and run `$recallforge inspect-materials`. Confirm unreadable areas are reported rather than invented.

Record: host/version, OS, date, text result, multimodal result, and any recognition warning. Never include private study material or credentials.
