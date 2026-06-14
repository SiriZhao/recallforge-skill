# Contributing

Thanks for considering a contribution to exam-review-skill.

## Development Setup

```bash
git clone https://github.com/YOUR_USERNAME/exam-review-skill.git
cd exam-review-skill
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

On Windows, activate with:

```powershell
.venv\Scripts\activate
```

## Before Opening a PR

Run:

```bash
python -m compileall exam_review_skill
python -m pytest
```

## Pull Request Flow

1. Fork the repository.
2. Create a branch, for example `feature/better-risk-radar`.
3. Keep changes focused.
4. Add or update tests when behavior changes.
5. Do not commit API keys, `.env` files, private course materials, scanned real exams, student data, or large generated outputs.
6. Open a PR with a short summary, validation steps, and any known limitations.

## Good First Issues

- Improve example materials.
- Add more parser tests.
- Improve source references in generated reports.
- Improve optional export formats.
- Add provider adapters while keeping mock mode working.
