# Contributing to RecallForge

Thanks for helping make exam review more useful and trustworthy.

## Setup

Fork the repository, clone your fork, and create a focused branch:

```bash
git clone https://github.com/YOUR_USERNAME/recallforge-skill.git
cd recallforge-skill
git switch -c feature/short-description
python -m pip install -e ".[test]"
python -m compileall recallforge
python -m pytest
```

Use `fix/`, `docs/`, `feature/`, or `refactor/` prefixes where helpful. Keep commits concise and imperative, for example `docs: clarify manual installation`.

## What to contribute

- Bug fixes with regression tests.
- Safe, self-authored examples; never upload private, leaked, paid, or unauthorized course material.
- Documentation improvements in English or Chinese.
- Prompt/Skill improvements that preserve evidence boundaries and academic integrity.
- New parsers, providers, reports, or planning behavior with tests and clear failure modes.

## Pull requests

Before opening a PR, run the relevant tests and update documentation when user behavior changes. Explain what changed, why, and exactly how you tested it. Do not commit keys, `.env` files, personal data, course records, or generated workspaces.

See [Architecture](docs/architecture.md) for module boundaries and [Security](SECURITY.md) for reporting sensitive concerns.
