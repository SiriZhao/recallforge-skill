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

Not yet completed. Real Codex host E2E must be run in a separate Codex session by a maintainer using [Release Host Verification Protocol](manual-verification.md). The machine-readable evidence template is at [verification/host-verification-template.json](../verification/host-verification-template.json).
