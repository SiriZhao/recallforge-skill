# Local OCR verification

RecallForge’s default path is native extraction → host vision → explicit unresolved. Local OCR is an optional fallback, not a core requirement.

## Verified engines (reference run)

Reference environment: Windows 11, Python 3.14.3, Intel64 Family 6 Model 197, CPU only. Ten self-authored fixtures: English clean, Chinese clean, mixed Chinese-English, low-resolution, rotated, two-column, exam paper, formula context, table, annotation overlap.

| Metric | Tesseract 5.5.0 | RapidOCR 1.2.3 (ONNX CPU) |
|---|---|---|
| Mean CER | 0.2578 | 0.2492 |
| Median CER | 0.2630 | 0.1503 |
| Mean WER (where meaningful) | 0.1956 | 0.1490 |
| Fixtures completed | 10/10 | 10/10 |
| Total elapsed | 5.15 s | 51.59 s |
| Pages/sec | 1.94 | 0.19 |
| Cold start | not separated (first call ~0.4–0.7 s) | 0.78 s |
| Install footprint | ~90 MB system binary + language data | ~190 MB in a Python venv |
| Chinese clean CER | 0.2759 | 0.1379 |
| Mixed Chinese-English CER | 0.2979 | 0.6383 |
| Exam paper CER | 0.3810 | 0.1111 |
| Formula context CER | 0.5417 | 0.8125 |
| Table CER | 0.2500 | 0.0000 |
| Annotation overlap CER | 0.1600 | 0.1200 |

Full machine-readable results: [benchmarks/results/ocr-windows-reference.json](../benchmarks/results/ocr-windows-reference.json).

## What these numbers mean

- Both engines recover clean printed text, but neither is good enough to be treated as verified understanding. Formula symbols and mixed-language math punctuation are especially weak; host vision or user verification is still required.
- RapidOCR is stronger on clean Chinese text, tables, exam pages, and annotations in this fixture set, but much slower on CPU.
- Tesseract is lighter and faster, with stronger mixed Chinese-English and formula-context text in this run, but its Chinese quality is weaker than RapidOCR.
- Two-column reading order is not reliably restored by either engine; this is a layout problem, not a character-recognition problem.
- An annotation such as `B?` is recognized as separate text. RecallForge still labels handwriting as user/unknown annotation, never as a printed answer key.

## Recommended processing matrix

| Material | Recommended path |
|---|---|
| Digital PPTX | Native + host vision when needed |
| Digital PDF | Native + selective host vision |
| Clean scan | Host vision first |
| Large clean scan batches | Optional local OCR + host vision verification |
| Formula-heavy scan | Host vision first; local OCR only for surrounding text |
| Diagram-heavy material | Host vision first |
| Past paper | Native/OCR + host vision structure recovery |

## Conclusion

Local OCR remains an optional experimental fallback. It is **not** the preferred Chinese document path, and it must never be used alone for formulas, diagrams, tables, or exam structure. `OCR_QUALITY` is not treated as a blocker because the product’s recommended path is host vision; the OCR data above is published as real evidence rather than as a supported quality claim.
