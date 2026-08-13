from __future__ import annotations

import argparse

from .workspace_cli import add_workspace_parser


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="recallforge",
        description="RecallForge — AI Exam Review Skill: forge course materials into exam-ready knowledge.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    add_workspace_parser(sub)
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
