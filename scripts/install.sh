#!/usr/bin/env sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
SOURCE="$ROOT/recallforge"
if [ ! -f "$SOURCE/SKILL.md" ]; then SOURCE="$ROOT/skill/recallforge"; fi
TARGET="${HOME}/.agents/skills/recallforge"; FORCE=0
while [ "$#" -gt 0 ]; do case "$1" in --target) TARGET=${2:?missing path}; shift 2;; --force) FORCE=1; shift;; *) echo "Usage: $0 [--target PATH] [--force]" >&2; exit 2;; esac; done
if [ -e "$TARGET" ]; then
  if [ "$FORCE" -ne 1 ]; then echo "RecallForge already exists: $TARGET. Use --force to replace only RecallForge." >&2; exit 1; fi
  BACKUP="${TARGET}.backup-$(date +%Y%m%d%H%M%S)"; mv "$TARGET" "$BACKUP"; echo "Backup created: $BACKUP"
fi
mkdir -p "$TARGET"; cp -R "$SOURCE"/. "$TARGET"
echo "RecallForge installed successfully."
echo "Location: $TARGET"
echo 'Next: open a new Codex turn and run $recallforge self-test.'
