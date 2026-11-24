"""Command-line entry point.

Subcommands are added phase by phase (see ROADMAP.md, Phase 8 for the full list).
"""

import argparse

from minilang import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="minilang",
        description="MiniLang compiler and parser workbench",
    )
    parser.add_argument("--version", action="version", version=f"minilang {__version__}")
    parser.add_subparsers(dest="command", metavar="<command>")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
    return 0
