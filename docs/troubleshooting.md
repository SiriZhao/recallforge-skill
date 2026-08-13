# Troubleshooting

## RecallForge does not appear in Skills or `$recallforge` fails

Check that the final path is exactly `.../.agents/skills/recallforge/SKILL.md`, not `recallforge/recallforge/SKILL.md`. Start a new Codex turn after copying it. Confirm you installed it in the user directory or in the project where Codex was launched. If explicit `$recallforge self-test` works, installation is correct even if automatic invocation did not occur.

## `recallforge` is not recognized

Run `python -m recallforge --help` from the installed folder. If it works, the package is installed but your Python scripts directory is not on PATH; keep using `python -m recallforge`, or repair your Python installation. On Windows, try `py -m recallforge --help`.

## Installation fails

Confirm Python 3.10+ with `python --version`. Upgrade pip with `python -m pip install --upgrade pip`, then repeat `python -m pip install .`. Do not run the installer in a protected directory such as Program Files; use a folder you own.

## The command cannot find a workspace or course

Use the same `--dir` used with `workspace init`, and verify the course ID with `recallforge workspace list --dir ./my-review`. IDs are not display names.

## PDF, slides, images, formulas, or Chinese text

Install `python -m pip install ".[ingestion]"`. Text extraction may work without external services; scanned/image-heavy pages need a configured provider. Formula ambiguity and OCR output remain low confidence until verified. Keep filenames and text in UTF-8 where possible.

## Large files or long output

Start with relevant chapters and past-paper sections. Ingest smaller batches, build after each batch, and use topic-specific tutor/quiz commands rather than asking for every output at once.

## Prompt or skill discovery did not work

RecallForge’s guaranteed interface is the CLI. `SKILL.md` provides host-readable instructions, but each AI client decides how it discovers local skills. Use the commands directly if your client does not surface it.

## Update and uninstall

Download the new release and rerun `python -m pip install .`. To uninstall the package, run `python -m pip uninstall recallforge-skill`. Delete review workspaces separately only if you want to remove local study state.

## Installer script error

Run it from the extracted RecallForge directory and supply a writable `--target` path. The scripts only copy this release; they do not install Python, modify PATH, or request secrets. Then run `python -m pip install .` in the target directory.
