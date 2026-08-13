# Tested environment

## CI matrix (passing)

GitHub Actions `Validate` workflow passes on:

- Ubuntu 24.04, Python 3.10 and 3.11
- Windows Server 2025 (windows-latest), Python 3.11
- macOS (macos-latest), Python 3.11

Each job runs the full automated suite, package build, clean-room ZIP/Plugin install checks, native Material Intelligence benchmark, official Skill/Plugin validation, and branding/placeholder scan.

## Local OCR reference

Windows 11, Python 3.14.3, Intel64 Family 6 Model 197, CPU only:

- Tesseract 5.5.0 with official `eng` + `chi_sim` traineddata
- RapidOCR 1.2.3 (ONNX Runtime CPU)

Full results: [benchmarks/results/ocr-windows-reference.json](../benchmarks/results/ocr-windows-reference.json) and [Local OCR verification](ocr.md).

## Package verification

- Official Skill validator: pass
- Official Plugin validator: pass
- Clean-room ZIP install to a temporary target: pass
- Clean-room Plugin extraction and relative-reference check: pass
- SHA256SUMS reproducibility: pass

## Host verification

Completed in an independent Codex session on Windows 11 by the maintainer (EXTERNAL_MANUAL):

- Codex 0.147.0
- RecallForge commit `1856c66`
- Candidate ZIP, user-level Skill installation
- `/skills` discovery: pass
- `$recallforge self-test`: pass (`Status: READY`)
- `$recallforge multimodal-test`: pass (`Status: MULTIMODAL_READY`)
- Functional test: pass
- Real material E2E: pass (16 lecture decks + 30-page scanned past-paper PDF; 1047 slide/page units + 30 exam pages catalogued)
- Weakness feedback loop: pass (diagnostic recall → weakness detection → corrective teaching → follow-up practice, including a user-requested switch from diagnostic to from-scratch teaching)

Full machine-readable evidence: [verification/host-verification-template.json](../verification/host-verification-template.json).
