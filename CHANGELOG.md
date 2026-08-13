# Changelog

All notable changes to RecallForge are documented here. This project follows the spirit of [Keep a Changelog](https://keepachangelog.com/) and Semantic Versioning.

## [Unreleased]

### Added

- Material Intelligence Layer with page/slide routing, StudyDocument IR, source anchors, material catalog, multimodal self-test, and zero-silent-page-drop status tracking.
- Native PPTX spatial blocks, notes, structured tables, WEBP routing, visual uncertainty handling, self-authored multimodal fixtures, gallery, and bilingual material guides.

### Changed

- Made release archive creation and checksum generation reproducible.
- Prepared v2.2.0 candidate packages without creating a release tag while GitHub authentication remains blocked.

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
