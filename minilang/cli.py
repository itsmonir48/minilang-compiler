"""Command-line entry point.

Subcommands are added phase by phase (see ROADMAP.md, Phase 8 for the full list).
"""

import argparse
import sys
from pathlib import Path

from minilang import __version__
from minilang.lexer import Lexer
from minilang.report import render_table
from minilang.tokens import RELOP_TEXT, TokenType


def _read_source(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError as e:
        raise SystemExit(f"minilang: cannot read {path}: {e.strerror}")


def cmd_tokens(args: argparse.Namespace) -> int:
    """Print the Lexeme | Token | Attribute table of a source file (3.1)."""
    source = _read_source(args.file)
    lexer = Lexer(source, half_size=args.buffer_size)
    tokens = lexer.tokenize()
    rows = []
    for tok in tokens:
        if tok.type is TokenType.EOF:
            continue
        if tok.type is TokenType.ID:
            attr = f"name #{tok.value}"
        elif tok.type is TokenType.RELOP:
            attr = f"{tok.value} ({RELOP_TEXT[tok.value]})"
        elif tok.value is not None:
            attr = repr(tok.value)
        else:
            attr = "-"
        rows.append([f"{tok.line}:{tok.col}", tok.lexeme, tok.type.value, attr])
    print(render_table(["Pos", "Lexeme", "Token", "Attribute"], rows, args.md))
    print()
    names = [[i, name] for i, name in enumerate(lexer.names.names)]
    print(render_table(["#", "Name"], names, args.md))
    if args.stats:
        print()
        print(f"buffer half size: {args.buffer_size}, half reloads: {lexer.buf.reloads}")
    if lexer.errors:
        print(lexer.errors.format(source), file=sys.stderr)
        print(f"{len(lexer.errors)} lexical error(s)", file=sys.stderr)
        return 1
    return 0


def cmd_strings(args: argparse.Namespace) -> int:
    """Prefixes, suffixes, substrings, subsequences of a string (3.3.1)."""
    from minilang import regex_tools as rt

    s = args.string
    show = lambda items: ", ".join(repr(x) if x else "ε" for x in items)  # noqa: E731
    print(f"s = {s!r}, length {len(s)}")
    print(f"prefixes          : {show(rt.prefixes(s))}")
    print(f"suffixes          : {show(rt.suffixes(s))}")
    print(f"proper prefixes   : {show(rt.proper_prefixes(s))}")
    print(f"proper suffixes   : {show(rt.proper_suffixes(s))}")
    print(f"substrings        : {show(sorted(rt.substrings(s), key=lambda x: (len(x), x)))}")
    if len(s) <= 12:
        subs = sorted(rt.subsequences(s), key=lambda x: (len(x), x))
        print(f"subsequences      : {show(subs)}")
    actual, formula = rt.string_report(s), rt.count_formulas(len(s))
    rows = [[k, actual[k], formula[k]] for k in actual]
    print()
    print(render_table(["Kind", "Count", "Formula (distinct chars)"], rows, args.md))
    return 0


def cmd_regex(args: argparse.Namespace) -> int:
    """Test strings against the regular definitions of the lab sheet (3.3)."""
    from minilang import regex_tools as rt

    if args.name is None:
        rows = [[d.name, d.description, d.pattern or "(function)"] for d in rt.DEFINITIONS]
        print(render_table(["Name", "Language", "Pattern"], rows, args.md))
        return 0
    if args.name not in rt.BY_NAME:
        print(f"unknown definition {args.name!r}; run `minilang regex` for the list",
              file=sys.stderr)
        return 2
    d = rt.BY_NAME[args.name]
    print(f"{d.name}: {d.description}")
    print(f"pattern: {d.pattern or '(checked by a function)'}")
    if d.note:
        print(f"note: {d.note}")
    rows = [[repr(s), "yes" if d.check(s) else "no"] for s in args.strings]
    if rows:
        print()
        print(render_table(["String", "Match"], rows, args.md))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="minilang",
        description="MiniLang compiler and parser workbench",
    )
    parser.add_argument("--version", action="version", version=f"minilang {__version__}")
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    p = sub.add_parser("tokens", help="show the tokens of a source file (Ch 3)")
    p.add_argument("file")
    p.add_argument("--buffer-size", type=int, default=4096,
                   help="half size N of the buffer pair (default 4096)")
    p.add_argument("--stats", action="store_true", help="also print buffer reload count")
    p.add_argument("--md", action="store_true", help="print tables as Markdown")
    p.set_defaults(func=cmd_tokens)

    p = sub.add_parser("strings", help="prefixes / suffixes / substrings / subsequences (3.3)")
    p.add_argument("string")
    p.add_argument("--md", action="store_true", help="print tables as Markdown")
    p.set_defaults(func=cmd_strings)

    p = sub.add_parser("regex", help="test strings against regular definitions (3.3)")
    p.add_argument("name", nargs="?", help="definition name; omit to list all")
    p.add_argument("strings", nargs="*")
    p.add_argument("--md", action="store_true", help="print tables as Markdown")
    p.set_defaults(func=cmd_regex)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    return args.func(args)
