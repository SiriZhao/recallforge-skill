# RecallForge for Codex

RecallForge is a Codex Skill. It needs no runtime dependency: Codex reads `SKILL.md` and uses the supplied references during a conversation.

## Install

### Windows

Download and extract `recallforge-skill-v2.1.2.zip`. In File Explorer, type `%USERPROFILE%\.agents\skills` in the address bar (create the folders if asked), then copy the extracted `recallforge` folder there. The final file must be `%USERPROFILE%\.agents\skills\recallforge\SKILL.md`.

Or open PowerShell in the extracted folder and run `powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1`.

### macOS

In Finder, press Shift-Command-G and enter `~/.agents/skills`. Create it if needed, then copy `recallforge` into it. In Terminal, `~` means your personal home folder:

```bash
mkdir -p ~/.agents/skills
cp -R /path/to/extracted/recallforge ~/.agents/skills/
```

### Linux

```bash
mkdir -p ~/.agents/skills
cp -R /path/to/extracted/recallforge ~/.agents/skills/
```

Or, on macOS/Linux, run `bash ./scripts/install.sh` from the extracted release.

## Verify and run

Start a new Codex turn. Codex discovers local Skills automatically. If your Codex surface provides a Skills picker, confirm that **RecallForge** is listed. Then run:

```text
$recallforge self-test
```

`Status: READY` is the installation check. The Skill picker UI was not available for screenshot capture in this environment, so no UI screenshot is presented as evidence.

## Invocation

Use `$recallforge` explicitly for the most reliable first use. Codex can also invoke it implicitly for exam review language; use explicit invocation if automatic matching does not select it.

## Update and remove

To update, download a new Skill ZIP, replace only `recallforge` in your Skills directory, start a new Codex turn, and rerun self-test. To remove it, delete only the `recallforge` folder—never the entire `.agents/skills` folder. Remove plugins through the host’s Plugin UI if you installed the Plugin ZIP.

## Project-local development

Copy `skill/recallforge` to `<project>/.agents/skills/recallforge`. Codex finds repository Skills from the current working directory, parent directories, and repository root.
