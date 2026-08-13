# Changelog

All notable changes to RecallForge are documented here. This project follows the spirit of [Keep a Changelog](https://keepachangelog.com/) and Semantic Versioning.

## [2.2.0] - 2026-08-13

### Added

- Material Intelligence Layer with page/slide routing, StudyDocument IR, source anchors, material catalog, multimodal self-test, and zero-silent-page-drop status tracking.
- Native PPTX spatial blocks, notes, structured tables, WEBP routing, visual uncertainty handling, self-authored multimodal fixtures, gallery, and bilingual material guides.

### Changed

- Made release archive creation and checksum generation reproducible.
- Frozen the public version to v2.2.0 and published the first multimodal Material Intelligence release.

### Verified

- Full automated suite: 215 passed on Windows 11 / Python 3.14.3 (real Tesseract OCR test included).
- Local OCR benchmark with 10 self-authored fixtures: Tesseract 5.5.0 and RapidOCR 1.2.3, CER/WER recorded.
- Official Skill and Plugin validators pass; clean-room ZIP/Plugin install tests pass.
- GitHub Actions passes on Ubuntu 24.04, Windows, and macOS.
- Real Codex host E2E: skill discovery, text self-test, multimodal self-test, functional test, and a 1047-slide + 30-page scanned past-paper material review all passed (evidence: `verification/host-verification-template.json`).

### Known limitations

- Local OCR is optional and experimental; it is not the preferred Chinese document path and cannot verify formulas, diagrams, tables, or exam structure alone.
- Host vision quality depends on the selected host/model and is not claimed as universally verified.
- Scanned pages with rotation, stitching, handwriting, and legacy PPT visual rendering remain recognition boundaries that are reported rather than silently accepted.

## [2.1.3] - 2026-08-13 (tag only)

Tag-only packaging correction for reproducible archives. No GitHub Release assets were published for this tag.

## [2.1.2] - 2026-08-13

### Added

- First public RecallForge release: evidence-grounded course knowledge reconstruction, exam scope mapping, active recall, adaptive quizzes, diagnosis, wrongbook, multi-course planning, reports, and time-boxed cram plans.
- Chinese, English, bilingual output modes, terminology mapping, and mixed-language course support.
- Safe sample materials, package validation, checksum generation, install scripts, community templates, and bilingual beginner documentation.

### Changed

- Rebranded the project as **RecallForge — AI Exam Review Skill**.
- Consolidated public documentation around supported behavior and removed internal round-by-round development reports.
- Added a host-installable RecallForge Skill, Codex discovery metadata, self-test, trigger cases, and a skills-only Plugin package.

### Security

- Release package excludes secrets, local environments, caches, generated outputs, and user course data.

[2.1.2]: https://github.com/SiriZhao/recallforge-skill/releases/tag/v2.1.2
[2.1.3]: https://github.com/SiriZhao/recallforge-skill/releases/tag/v2.1.3
[2.2.0]: https://github.com/SiriZhao/recallforge-skill/releases/tag/v2.2.0
