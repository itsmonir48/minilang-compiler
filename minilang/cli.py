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


def _syntax_failure(err, text: str) -> int:
    print(err.format(text), file=sys.stderr)
    return 1


def cmd_translate(args: argparse.Namespace) -> int:
    """Infix / postfix / prefix translation with an annotated parse tree (2.3, 2.5)."""
    from minilang import translators as tr
    from minilang.errors import CompileError
    from minilang.tree import render_ascii

    try:
        t = tr.translate(args.expr, args.source)
    except CompileError as e:
        return _syntax_failure(e, args.expr)
    print(f"input ({t.notation}): {t.source}")
    print(f"infix          : {t.infix}")
    print(f"postfix        : {t.postfix}")
    print(f"prefix         : {t.prefix}")
    value = t.value if t.value is not None else f"- ({t.value_note})"
    print(f"value          : {value}")
    if args.scheme:
        print()
        print("translation scheme:")
        for line in tr.SCHEMES[t.notation]:
            print(f"  {line}")
    if args.tree:
        print()
        print("annotated parse tree:")
        print(render_ascii(t.tree))
    if args.trace:
        print()
        if not t.trace:
            print("(the call trace is recorded for the infix translator of 2.5 only)")
        else:
            rows = [["  " * s.depth + s.action, s.output] for s in t.trace]
            print(render_table(["Call / action", "Output so far"], rows, args.md))
    return 0


def cmd_roman(args: argparse.Namespace) -> int:
    """Roman numeral <-> integer (2.2 grammar, 2.3 scheme); the direction is detected."""
    from minilang import translators as tr
    from minilang.errors import CompileError
    from minilang.tree import render_ascii

    text = args.value
    try:
        if text.strip().isdigit():
            result, tree = tr.int_to_roman(text)
            scheme = tr.INT_TO_ROMAN_SCHEME
        else:
            result, tree = tr.roman_to_int(text)
            scheme = tr.ROMAN_GRAMMAR
    except CompileError as e:
        return _syntax_failure(e, text)
    print(f"{text.strip()} = {result}")
    if args.scheme:
        print()
        for line in scheme:
            print(f"  {line}")
    if args.tree:
        print()
        print(render_ascii(tree))
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    """Membership + parse tree for the small grammars of the 2.2 exercises."""
    from minilang import translators as tr
    from minilang.errors import CompileError
    from minilang.tree import render_ascii

    if args.grammar == "div3" and args.table:
        rows = tr.div3_table(args.table)
        members = [r for r in rows if r["in L(G)"]]
        print(f"grammar: {tr.DIV3_GRAMMAR}")
        print(render_table(["String", "Value", "In L(G)", "Divisible by 3"],
                           [[r["string"], r["value"], "yes" if r["in L(G)"] else "no",
                             "yes" if r["divisible by 3"] else "no"] for r in rows], args.md))
        print()
        print(f"{len(rows)} strings of length 1..{args.table}; {len(members)} in L(G); "
              f"in L(G) but not divisible by 3: "
              f"{sum(not r['divisible by 3'] for r in members)}; divisible by 3 but not in "
              f"L(G): {sum(r['divisible by 3'] and not r['in L(G)'] for r in rows)}")
        return 0
    if args.input is None:
        print("minilang check: an input string is needed (or --table N for div3)",
              file=sys.stderr)
        return 2
    text = args.input
    grammar = {"div3": tr.DIV3_GRAMMAR, "brackets": tr.BRACKETS_GRAMMAR,
               "left-list": tr.LIST_GRAMMARS["left"],
               "right-list": tr.LIST_GRAMMARS["right"]}[args.grammar]
    print(f"grammar: {grammar}")
    try:
        if args.grammar == "div3":
            tree = tr.div3_tree(text)
            if tree is None:
                print(f"{text!r} is not in L(G)")
                return 1
        elif args.grammar == "brackets":
            tree = tr.brackets_tree(text)
        else:
            tree = tr.comma_list_tree(text, args.grammar.split("-")[0])
    except CompileError as e:
        return _syntax_failure(e, text)
    print(f"{text!r} is in L(G)")
    print()
    print(render_ascii(tree))
    return 0


def _load_grammar_arg(name: str):
    from minilang.grammar.grammar import load_grammar

    try:
        return load_grammar(name)
    except FileNotFoundError:
        from minilang.grammar.grammar import grammar_names
        raise SystemExit(f"minilang: no grammar {name!r} (a file, or one of: "
                         f"{', '.join(grammar_names())})")


def _tokens_arg(g, text: str):
    from minilang.grammar.grammar import tokenize_input

    return tokenize_input(g, text)


def cmd_grammar(args: argparse.Namespace) -> int:
    """Grammar workbench (4.2-4.4): print, transform, FIRST/FOLLOW, LL(1) table."""
    from minilang.errors import CompileError
    from minilang.grammar import transforms as tf
    from minilang.grammar.first_follow import first_follow, fmt_set
    from minilang.grammar.ll1 import build_ll1

    try:
        g = _load_grammar_arg(args.file)
    except CompileError as e:
        print(e.format(), file=sys.stderr)
        return 1
    print(g.to_text())
    print(f"\nstart: {g.start}   nonterminals: {' '.join(g.nonterminals)}   "
          f"terminals: {' '.join(g.terminals)}")
    rec = tf.left_recursive(g)
    if rec:
        print("left-recursive: " + ", ".join(rec))
    for flag, title, fn in ((args.augment, "augmented grammar", None),
                            (args.remove_left_recursion, "left recursion removed (Algorithm 4.19)",
                             tf.remove_left_recursion),
                            (args.left_factor, "left factored (Algorithm 4.21)", tf.left_factor)):
        if not flag:
            continue
        print(f"\n{title}:")
        if fn is None:
            print(g.augmented().to_text())
            continue
        g2, steps = fn(g)
        for s in steps:
            print(f"  {s}")
        print(g2.to_text())
    if args.first_follow or args.ll1:
        sets = first_follow(g)
        rows = [[a, fmt_set(sets.first[a], g), fmt_set(sets.follow[a], g)]
                for a in g.nonterminals]
        print()
        print(render_table(["Nonterminal", "FIRST", "FOLLOW"], rows, args.md))
    if args.ll1:
        t = build_ll1(g)
        cols = t.columns()
        rows = [[a] + [" / ".join(str(p) for p in t.entry(a, c)) for c in cols]
                for a in g.nonterminals]
        print()
        print(render_table(["M"] + cols, rows, args.md))
        if t.is_ll1:
            print("\nLL(1): yes, no multiply-defined entries")
        else:
            n = len(t.conflicts)
            print(f"\nLL(1): no, {n} multiply-defined {'entry' if n == 1 else 'entries'}:")
            for a, b, ps in t.conflicts:
                print(f"  M[{a}, {b}] = {' | '.join(str(p) for p in ps)}")
    return 0


def cmd_derive(args: argparse.Namespace) -> int:
    """Leftmost / rightmost derivations and the number of parse trees (4.2)."""
    from minilang.errors import CompileError
    from minilang.grammar import derivation as dv
    from minilang.tree import render_ascii

    g = _load_grammar_arg(args.file)
    if args.language is not None:
        lang = dv.language(g, args.language)
        print(f"strings of L(G) with at most {args.language} terminals"
              + ("" if lang.complete else " (search stopped early, list may be incomplete)")
              + f": {len(lang.strings)}")
        for s in lang.strings:
            print("  " + (" ".join(s) or "ε"))
        if args.input is None:
            return 0
    if args.input is None:
        print("minilang derive: give an input string or --language N", file=sys.stderr)
        return 2
    try:
        toks = [t for t, _ in _tokens_arg(g, args.input)]
    except CompileError as e:
        print(e.format(args.input), file=sys.stderr)
        return 1
    d = dv.derive(g, toks, max_trees=args.trees)
    n = len(d.sequences)
    print(f"input: {' '.join(toks) or 'ε'}")
    print(f"parse trees: {d.count_text}"
          + (" (search budget reached)" if d.budget_hit else ""))
    if n == 0:
        return 1
    if n > 1:
        print("the grammar is ambiguous: this string has more than one parse tree")
    for k, seq in enumerate(d.sequences[:args.show], start=1):
        tree = dv.tree_from_leftmost(g, seq)
        print(f"\n--- tree {k} ---")
        print(render_ascii(tree))
        print("\nleftmost : " + dv.derivation_text(g, seq, True))
        print("rightmost: " + dv.derivation_text(g, dv.rightmost_sequence(tree), False))
    return 0


def cmd_topdown(args: argparse.Namespace) -> int:
    """Top-down parsing trace: backtracking, predictive, table-driven LL(1) (4.4)."""
    from minilang.errors import CompileError
    from minilang.grammar import topdown as td
    from minilang.grammar.ll1 import input_text
    from minilang.tree import render_ascii

    g = _load_grammar_arg(args.file)
    refusal = td.check(g, args.method)
    if refusal:
        print(f"cannot use {td.METHODS[args.method]}: {refusal.reason}", file=sys.stderr)
        if refusal.suggestion is not None:
            print("\ntransformed grammar"
                  + (" (works for this method):" if refusal.suggestion_ok
                     else " (still not suitable):"), file=sys.stderr)
            print(refusal.suggestion.to_text(), file=sys.stderr)
        return 2
    try:
        tokens = _tokens_arg(g, args.input)
    except CompileError as e:
        print(e.format(args.input), file=sys.stderr)
        return 1
    run = td.run_method(g, args.method, tokens)
    print(f"{td.METHODS[args.method]}, input: {args.input}\n")
    if args.method == "ll1":
        rows = [[" ".join(s.stack), input_text(tokens, s.pos), s.action] for s in run.steps]
        print(render_table(["Stack", "Input", "Action"], rows, args.md))
    else:
        rows = [[i, "  " * s.depth + s.action, input_text(tokens, s.pos)]
                for i, s in enumerate(run.steps, start=1)]
        print(render_table(["#", "Action", "Input"], rows, args.md))
    if run.accepted:
        print("\naccepted\n")
        print(render_ascii(run.tree))
        return 0
    print(file=sys.stderr)
    print(run.error.format(args.input), file=sys.stderr)
    return 1


def cmd_parsetree(args: argparse.Namespace) -> int:
    """Expression → parse tree, derivations, AST, Graphviz file (2.2, 4.1, 4.2)."""
    import shutil
    import subprocess

    from minilang.errors import CompileError
    from minilang.parse_tree import EXPR_GRAMMAR, derivation_lines, parse_expression
    from minilang.tree import render_ascii, to_dot

    try:
        r = parse_expression(args.expr)
    except CompileError as e:
        print(e.format(args.expr), file=sys.stderr)
        return 1
    show_all = args.all
    print(f"grammar:\n{EXPR_GRAMMAR.to_text()}\n")
    print("parse tree:")
    print(render_ascii(r.tree, attrs=False))
    if args.derivations or show_all:
        print("\nleftmost derivation:")
        print("    " + "\n⇒lm ".join(derivation_lines(r.tree)))
        print("\nrightmost derivation:")
        print("    " + "\n⇒rm ".join(derivation_lines(r.tree, rightmost=True)))
    if args.ast or show_all:
        print("\nsyntax tree (AST):")
        print(render_ascii(r.ast, attrs=False))
    if args.dot:
        Path(args.dot).write_text(to_dot(r.tree, attrs=False) + "\n", encoding="utf-8")
        print(f"\nwrote {args.dot}")
        if args.png:
            if shutil.which("dot") is None:
                print("Graphviz 'dot' is not installed, so no PNG was made "
                      "(the .dot file can be opened in any Graphviz viewer)", file=sys.stderr)
            else:
                png = str(Path(args.dot).with_suffix(".png"))
                subprocess.run(["dot", "-Tpng", args.dot, "-o", png], check=True)
                print(f"wrote {png}")
    return 0


def cmd_ui(args: argparse.Namespace) -> int:
    """Start the Streamlit web interface."""
    import subprocess

    home = Path(__file__).resolve().parent.parent / "app" / "Home.py"
    if not home.exists():
        print(f"minilang: web interface not found at {home}", file=sys.stderr)
        return 2
    cmd = [sys.executable, "-m", "streamlit", "run", str(home), "--server.port", str(args.port)]
    if args.headless:
        cmd += ["--server.headless", "true"]
    try:
        return subprocess.call(cmd)
    except KeyboardInterrupt:
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

    p = sub.add_parser("translate", help="infix / postfix / prefix translation (2.3, 2.5)")
    p.add_argument("expr", help="the expression, e.g. '9-5+2' (quote it in the shell)")
    p.add_argument("--from", dest="source", choices=["infix", "postfix", "prefix"],
                   default="infix", help="notation of the input (default infix)")
    p.add_argument("--tree", action="store_true", help="print the annotated parse tree")
    p.add_argument("--trace", action="store_true",
                   help="print the call trace of the 2.5 translator (infix input)")
    p.add_argument("--scheme", action="store_true", help="print the translation scheme")
    p.add_argument("--md", action="store_true", help="print tables as Markdown")
    p.set_defaults(func=cmd_translate)

    p = sub.add_parser("roman", help="Roman numeral <-> integer (2.2, 2.3)")
    p.add_argument("value", help="a Roman numeral (MCMXCIV) or an integer 1..3999")
    p.add_argument("--tree", action="store_true", help="print the annotated parse tree")
    p.add_argument("--scheme", action="store_true", help="print the grammar / scheme")
    p.set_defaults(func=cmd_roman)

    p = sub.add_parser("check", help="small grammars of the 2.2 exercises")
    p.add_argument("grammar", choices=["div3", "brackets", "left-list", "right-list"])
    p.add_argument("input", nargs="?", help="the string to check")
    p.add_argument("--table", type=int, metavar="N",
                   help="div3 only: every binary string up to length N")
    p.add_argument("--md", action="store_true", help="print tables as Markdown")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("grammar", help="grammar workbench: FIRST/FOLLOW, LL(1), transforms (4.2-4.4)")
    p.add_argument("file", help="grammar file, or a name from grammars/ (e.g. expr)")
    p.add_argument("--augment", action="store_true", help="print the augmented grammar")
    p.add_argument("--remove-left-recursion", action="store_true",
                   help="Algorithm 4.19 with its steps")
    p.add_argument("--left-factor", action="store_true", help="Algorithm 4.21 with its steps")
    p.add_argument("--first-follow", action="store_true", help="FIRST and FOLLOW sets")
    p.add_argument("--ll1", action="store_true", help="LL(1) table and its conflicts")
    p.add_argument("--md", action="store_true", help="print tables as Markdown")
    p.set_defaults(func=cmd_grammar)

    p = sub.add_parser("derive", help="derivations, parse trees, ambiguity, L(G) (4.2)")
    p.add_argument("file", help="grammar file, or a name from grammars/")
    p.add_argument("input", nargs="?", help="string to derive, e.g. 'id+id*id'")
    p.add_argument("--trees", type=int, default=10, help="stop after this many trees")
    p.add_argument("--show", type=int, default=2, help="print this many trees (default 2)")
    p.add_argument("--language", type=int, metavar="N",
                   help="list the strings of L(G) with at most N terminals")
    p.set_defaults(func=cmd_derive)

    p = sub.add_parser("topdown", help="top-down parsing trace (4.4)")
    p.add_argument("file", help="grammar file, or a name from grammars/")
    p.add_argument("input", help="string to parse, e.g. 'id+id*id'")
    p.add_argument("--method", choices=["backtrack", "predictive", "ll1"], default="ll1")
    p.add_argument("--md", action="store_true", help="print tables as Markdown")
    p.set_defaults(func=cmd_topdown)

    p = sub.add_parser("parsetree", help="expression -> parse tree (2.2, 4.1, 4.2)")
    p.add_argument("expr", help="e.g. 'a + b * (c - 2)' (quote it in the shell)")
    p.add_argument("--derivations", action="store_true",
                   help="also print the leftmost and rightmost derivations")
    p.add_argument("--ast", action="store_true", help="also print the syntax tree")
    p.add_argument("--all", action="store_true", help="tree, derivations and AST")
    p.add_argument("--dot", metavar="FILE", help="write the tree as a Graphviz .dot file")
    p.add_argument("--png", action="store_true",
                   help="with --dot: also make a PNG if Graphviz 'dot' is installed")
    p.set_defaults(func=cmd_parsetree)

    p = sub.add_parser("ui", help="open the web interface in the browser")
    p.add_argument("--port", type=int, default=8501)
    p.add_argument("--headless", action="store_true", help="do not open a browser")
    p.set_defaults(func=cmd_ui)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    return args.func(args)
