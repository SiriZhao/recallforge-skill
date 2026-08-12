from __future__ import annotations

import argparse

from .workspace_cli import add_workspace_parser


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="exam-review-skill",
        description="Exam Review Agent: from course materials to a scoring path.",
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
