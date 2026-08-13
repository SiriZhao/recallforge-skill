# Material ingestion benchmark

Run `python scripts/material_benchmark.py` from the repository environment. It creates 11 small self-authored fixtures at runtime and reports the native structural scan only; host vision and optional OCR are intentionally excluded.

Reference run on 2026-08-13:

- Windows 11, Python 3.14.3
- Intel64 Family 6 Model 197
- 11 files / 12 pages or slides
- 0.2191 seconds / 54.771 pages or slides per second
- 2 native-route units / 10 vision-route units / 0 unrouted units

This is a tiny routing benchmark, not an OCR-quality or end-to-end host benchmark. It must not be generalized to other machines or large courses. CER/WER are not reported because no real OCR engine ran in this reference environment.
