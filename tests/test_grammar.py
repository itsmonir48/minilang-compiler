"""Grammar workbench: loader, transforms, FIRST/FOLLOW, LL(1), derivations, top-down."""

import random

import pytest

from minilang.cli import main
from minilang.errors import CompileError
from minilang.grammar import derivation as dv
from minilang.grammar import topdown as td
from minilang.grammar import transforms as tf
from minilang.grammar.first_follow import first_follow
from minilang.grammar.grammar import (END, EPS, Grammar, Production, grammar_names,
                                      load_grammar, tokenize_input)
from minilang.grammar.ll1 import build_ll1, input_text, ll1_parse
from minilang.tree import render_ascii


def toks(g, s):
    return [t for t, _ in tokenize_input(g, s)]


# ---------------------------------------------------------------- loader

def test_parse_format():
    g = Grammar.parse("# c\nA -> a A | eps\n  | b\nB → ε | A\n")
    assert g.start == "A"
    assert g.nonterminals == ["A", "B"]
    assert g.terminals == ["a", "b"]
    assert [str(p) for p in g.productions] == ["A → a A", "A → ε", "A → b", "B → ε", "B → A"]


@pytest.mark.parametrize("text, line", [
    ("E E -> x", 1), ("E -> a\nF x", 2), ("| a", 1), ("", 0), ("eps -> a", 1),
])
def test_parse_errors(text, line):
    with pytest.raises(CompileError) as info:
        Grammar.parse(text)
    assert info.value.line == line


def test_every_grammar_file_loads():
    names = grammar_names()
    assert "expr" in names and "dangling_else_fixed" in names
    for n in names:
        assert load_grammar(n).productions


def test_augment_and_tokenize():
    g = load_grammar("expr")
    a = g.augmented()
    assert a.start == "E'" and a.productions[0] == Production("E'", ("E",))
    assert tokenize_input(g, "id+ (id)") == [("id", 1), ("+", 3), ("(", 5), ("id", 6),
                                             (")", 8)]
    with pytest.raises(CompileError) as info:
        tokenize_input(g, "id+x")
    assert info.value.col == 4


# ---------------------------------------------------------------- FIRST / FOLLOW, LL(1)

def test_first_follow_example_4_30():
    g = load_grammar("expr_ll1")
    s = first_follow(g)
    assert s.first == {"E": {"(", "id"}, "E'": {"+", EPS}, "T": {"(", "id"},
                       "T'": {"*", EPS}, "F": {"(", "id"}}
    assert s.follow == {"E": {")", END}, "E'": {")", END}, "T": {"+", ")", END},
                        "T'": {"+", ")", END}, "F": {"+", "*", ")", END}}


def test_ll1_table_fig_4_17():
    t = build_ll1(load_grammar("expr_ll1"))
    got = {(a, b): str(ps[0]) for (a, b), ps in t.table.items()}
    assert got == {
        ("E", "id"): "E → T E'", ("E", "("): "E → T E'",
        ("E'", "+"): "E' → + T E'", ("E'", ")"): "E' → ε", ("E'", END): "E' → ε",
        ("T", "id"): "T → F T'", ("T", "("): "T → F T'",
        ("T'", "+"): "T' → ε", ("T'", "*"): "T' → * F T'", ("T'", ")"): "T' → ε",
        ("T'", END): "T' → ε",
        ("F", "id"): "F → id", ("F", "("): "F → ( E )",
    }
    assert t.is_ll1


def test_ll1_conflicts():
    t = build_ll1(load_grammar("dangling_else"))
    assert not t.is_ll1
    assert [(a, b) for a, b, _ in t.conflicts] == [("stmt", "if")]
    t = build_ll1(tf.left_factor(load_grammar("left_factor"))[0])
    assert [(a, b) for a, b, _ in t.conflicts] == [("S'", "e")]     # dangling else


def test_ll1_trace_golden(golden):
    g = load_grammar("expr_ll1")
    run = ll1_parse(build_ll1(g), tokenize_input(g, "id+id*id"))
    assert run.accepted
    rows = [f"{' '.join(s.stack):<14}{input_text(run.tokens, s.pos):>16}   {s.action}"
            for s in run.steps]
    golden("ll1_id+id*id", "\n".join(rows) + "\n\n" + render_ascii(run.tree) + "\n")


def test_ll1_errors():
    g = load_grammar("expr_ll1")
    t = build_ll1(g)
    run = ll1_parse(t, tokenize_input(g, "id+*id"))
    assert not run.accepted and run.error.col == 4
    assert "no rule for T on '*'" in run.error.message
    run = ll1_parse(t, tokenize_input(g, "(id"))
    assert "expected ')'" in run.error.message and run.error.col == 4


# ---------------------------------------------------------------- transforms

def test_remove_left_recursion_expr():
    g, _ = tf.remove_left_recursion(load_grammar("expr"))
    assert g == load_grammar("expr_ll1")
    g, _ = tf.remove_immediate_left_recursion(load_grammar("expr"))
    assert g == load_grammar("expr_ll1")


def test_remove_left_recursion_example_4_20():
    g, steps = tf.remove_left_recursion(load_grammar("indirect_left_rec"))
    assert g == Grammar.parse("S -> A a | b\nA -> b d A' | A'\nA' -> c A' | a d A' | ε")
    assert steps[0].startswith("warning")            # ε-production: no guarantee
    assert not tf.left_recursive(g)


def test_left_recursion_detection():
    assert set(tf.left_recursive(load_grammar("expr"))) == {"E", "T"}
    assert tf.left_recursive(load_grammar("indirect_left_rec"))["S"] == ["S", "A", "S"]
    assert tf.left_recursive(load_grammar("expr_ll1")) == {}
    # hidden: B is nullable, so A → B A x is left-recursive
    assert "A" in tf.left_recursive(Grammar.parse("A -> B A x | y\nB -> ε | b"))


def test_left_factor_4_23():
    g, _ = tf.left_factor(load_grammar("left_factor"))
    assert g == Grammar.parse("S -> i E t S S' | a\nS' -> e S | ε\nE -> b")
    assert g.to_text().splitlines()[1] == "S' → e S | ε"


def test_left_factor_nested():
    g, _ = tf.left_factor(Grammar.parse("A -> a b c | a b d | a e | f"))
    assert g == Grammar.parse("A -> a A' | f\nA' -> b A'' | e\nA'' -> c | d")


def test_transforms_keep_the_language():
    for name in ("expr", "indirect_left_rec", "left_factor", "dangling_else"):
        g = load_grammar(name)
        g2, _ = tf.prepare_for_ll1(g)
        assert dv.language(g, 6).strings == dv.language(g2, 6).strings, name


# ---------------------------------------------------------------- derivations

def test_ambiguity():
    for name, s, n in [("expr_ambiguous", "id+id*id", 2), ("expr", "id+id*id", 1),
                       ("dangling_else", "if cond then if cond then other else other", 2),
                       ("dangling_else_fixed", "if cond then if cond then other else other", 1),
                       ("ab_equal", "abab", 2), ("backtrack", "cd", 0)]:
        g = load_grammar(name)
        d = dv.derive(g, toks(g, s))
        assert d.complete and len(d.sequences) == n, name


def test_ambiguous_count_is_catalan():
    """id+id+id+id+id with E → E + E | id has Catalan(4) = 14 parse trees."""
    g = load_grammar("expr_ambiguous")
    d = dv.derive(g, toks(g, "id+id+id+id+id"), max_trees=100)
    assert d.complete and len(d.sequences) == 14
    assert not dv.derive(g, toks(g, "id+id+id+id+id"), max_trees=3).complete


def test_leftmost_and_rightmost_give_the_same_tree():
    g = load_grammar("expr")
    seq = dv.derive(g, toks(g, "id+id*id")).sequences[0]
    tree = dv.tree_from_leftmost(g, seq)
    lm = dv.forms(g, seq, True)
    rm = dv.forms(g, dv.rightmost_sequence(tree), False)
    assert lm[0] == rm[0] == ("E",)
    assert lm[-1] == rm[-1] == ("id", "+", "id", "*", "id")
    assert len(lm) == len(rm)
    assert rm[1] == ("E", "+", "T") and rm[2] == ("E", "+", "T", "*", "F")


def test_language():
    assert dv.language(load_grammar("balanced"), 4).strings == [
        (), ("(", ")"), ("(", "(", ")", ")"), ("(", ")", "(", ")")]
    strings = dv.language(load_grammar("ab_equal"), 6).strings
    assert all(s.count("a") == s.count("b") for s in strings)
    assert len(strings) == 1 + 2 + 6 + 20          # all balanced a/b strings up to 6


# ---------------------------------------------------------------- top-down

def test_backtracking_textbook_example():
    g = load_grammar("backtrack")
    run = td.backtrack_parse(g, tokenize_input(g, "cad"))
    assert run.accepted
    kinds = [s.kind for s in run.steps]
    assert "backtrack" in kinds and kinds[-1] == "accept"
    assert render_ascii(run.tree) == "S\n├── c\n├── A\n│   └── a\n└── d"
    run = td.backtrack_parse(g, tokenize_input(g, "cd"))
    assert not run.accepted and run.error.col == 2


def test_refusals():
    r = td.check(load_grammar("expr"), "ll1")
    assert "left-recursive" in r.reason and r.suggestion_ok
    assert r.suggestion == load_grammar("expr_ll1")
    r = td.check(load_grammar("dangling_else"), "predictive")
    assert "not LL(1)" in r.reason and not r.suggestion_ok
    assert td.check(load_grammar("dangling_else"), "backtrack") is None
    assert td.check(load_grammar("expr_ll1"), "ll1") is None


def test_definition_of_done_expressions():
    """Top-down accepts id+id*id and rejects id+*id with a clear message."""
    g = td.check(load_grammar("expr"), "ll1").suggestion
    for m in td.METHODS:
        assert td.run_method(g, m, tokenize_input(g, "id+id*id")).accepted
        bad = td.run_method(g, m, tokenize_input(g, "id+*id"))
        assert not bad.accepted and bad.error.col == 4, m


def test_three_parsers_agree():
    """On LL(1) grammars all three parsers accept the same strings with the same tree."""
    rng = random.Random(4)
    tested = []
    for name in ("expr", "expr_ll1", "balanced", "prefix", "dangling_else_fixed"):
        g = load_grammar(name)
        refusal = td.check(g, "ll1")
        if refusal:
            if not refusal.suggestion_ok:
                continue                    # dangling-else: no LL(1) form exists
            g = refusal.suggestion
        tested.append(name)
        members = [s for s in dv.language(g, 7).strings]
        cands = list(members)
        for _ in range(40):                  # random strings, mostly not in L(G)
            cands.append(tuple(rng.choice(g.terminals) for _ in range(rng.randint(1, 6))))
        for s in cands:
            tokens = [(t, i + 1) for i, t in enumerate(s)]
            runs = [td.run_method(g, m, tokens) for m in td.METHODS]
            accepted = {r.accepted for r in runs}
            assert len(accepted) == 1, (name, s)
            assert accepted.pop() == (s in members or bool(dv.derive(g, list(s)).sequences))
            trees = {render_ascii(r.tree) for r in runs if r.accepted}
            assert len(trees) <= 1, (name, s)
    assert tested == ["expr", "expr_ll1", "balanced", "prefix"]


# ---------------------------------------------------------------- CLI

def test_cli_grammar(capsys):
    assert main(["grammar", "expr", "--remove-left-recursion", "--left-factor", "--augment",
                 "--ll1"]) == 0
    out = capsys.readouterr().out
    assert "E' → + T E' | ε" in out and "LL(1): no" in out
    assert main(["grammar", "expr_ll1", "--ll1", "--md"]) == 0
    assert "LL(1): yes" in capsys.readouterr().out
    with pytest.raises(SystemExit):
        main(["grammar", "no_such_grammar"])


def test_cli_derive(capsys):
    assert main(["derive", "expr_ambiguous", "id+id*id"]) == 0
    out = capsys.readouterr().out
    assert "exactly 2" in out and "ambiguous" in out and "⇒rm" in out
    assert main(["derive", "backtrack", "cd"]) == 1
    assert main(["derive", "balanced", "--language", "2"]) == 0
    assert main(["derive", "balanced"]) == 2


def test_cli_topdown(capsys):
    assert main(["topdown", "backtrack", "cad", "--method", "backtrack"]) == 0
    assert "reset input" in capsys.readouterr().out
    assert main(["topdown", "expr_ll1", "id+id*id", "--method", "predictive"]) == 0
    assert main(["topdown", "expr_ll1", "id+*id"]) == 1
    assert main(["topdown", "expr", "id"]) == 2
    assert "left-recursive" in capsys.readouterr().err
