# Benchmarks

## Native routing benchmark

Run `python scripts/material_benchmark.py` from the repository environment. It creates 11 small self-authored fixtures at runtime and reports the native structural scan only; host vision and optional OCR are intentionally excluded.

Reference run on 2026-08-13:

- Windows 11, Python 3.14.3
- Intel64 Family 6 Model 197
- 11 files / 12 pages or slides
- 0.2191 seconds / 54.771 pages or slides per second
- 2 native-route units / 10 vision-route units / 0 unrouted units

This is a tiny routing benchmark, not an OCR-quality or end-to-end host benchmark. It must not be generalized to other machines or large courses. CER/WER are not reported because no real OCR engine ran in this reference environment.

## OCR benchmark

Run `python benchmarks/ocr_benchmark.py benchmarks/results/<file>.json` after installing optional engines. Ten self-authored fixtures with ground truth cover English clean, Chinese clean, mixed Chinese-English, low-resolution, rotated, two-column, exam paper, formula context, table, and annotation overlap.

Windows 11 CPU reference (2026-08-13):

- Tesseract 5.5.0: mean CER 0.2578, median CER 0.2630, 1.94 pages/sec, 10/10 fixtures
- RapidOCR 1.2.3: mean CER 0.2492, median CER 0.1503, 0.19 pages/sec (latest run), 10/10 fixtures
- Machine-readable details: `results/ocr-windows-reference.json`

Interpretation and the recommended processing matrix: [docs/ocr.md](../docs/ocr.md).

## Performance categories

- **Native routing performance:** measured above; depends on parser and machine.
- **OCR performance:** measured only on the reference machine above.
- **Host vision performance:** not measured here; it depends on host, model, provider, network, and machine. RecallForge publishes no universal host-vision number.
