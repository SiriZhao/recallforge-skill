#!/usr/bin/env sh
set -eu

SOURCE=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
TARGET=""
FORCE=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --target) TARGET=${2:?missing path after --target}; shift 2 ;;
    --force) FORCE=1; shift ;;
    *) echo "Usage: $0 [--target PATH] [--force]" >&2; exit 2 ;;
  esac
done

if [ -z "$TARGET" ]; then TARGET="$(pwd)/RecallForge"; fi
if [ -e "$TARGET" ]; then
  if [ "$FORCE" -ne 1 ]; then echo "Target exists: $TARGET. Use --target or --force." >&2; exit 1; fi
  BACKUP="${TARGET}.backup-$(date +%Y%m%d%H%M%S)"
  mv "$TARGET" "$BACKUP"
  echo "Existing RecallForge copied to: $BACKUP"
fi

mkdir -p "$TARGET"
tar --exclude=.git --exclude=.venv --exclude=dist --exclude=build --exclude=.pytest_cache -cf - -C "$SOURCE" . | tar -xf - -C "$TARGET"
echo "RecallForge files copied to: $TARGET"
echo "Next: cd '$TARGET' && python3 -m pip install . && recallforge --help"
