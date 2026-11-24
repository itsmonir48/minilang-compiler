"""Expression → parse tree generator (Phase 3.5)."""

import pytest

from minilang.cli import main
from minilang.errors import CompileError
from minilang.grammar import derivation as dv
from minilang.parse_tree import (EXPR_GRAMMAR, derivation_lines, leftmost_sequence,
                                 parse_expression, partial_tree)
from minilang.tree import render_ascii


def shape(node):
    """Compact form: (symbol children...) with leaves as their lexeme or symbol."""
    if node.is_leaf:
        return node.lexeme or node.symbol
    return "(" + node.symbol + " " + " ".join(shape(c) for c in node.children) + ")"


def test_left_associative():
    r = parse_expression("9-5+2")
    assert shape(r.tree) == "(E (E (E (T (F 9))) - (T (F 5))) + (T (F 2)))"
    assert shape(r.ast) == "(+ (- 9 5) 2)"


def test_precedence():
    r = parse_expression("a+b*c")
    assert shape(r.tree) == "(E (E (T (F a))) + (T (T (F b)) * (F c)))"
    assert shape(r.ast) == "(+ a (* b c))"


def test_parentheses():
    r = parse_expression("(a+b)*c")
    assert shape(r.tree) == "(E (T (T (F ( (E (E (T (F a))) + (T (F b))) ))) * (F c)))"
    assert shape(r.ast) == "(* (+ a b) c)"


def test_division_chain_and_reals():
    assert shape(parse_expression("x / y / 2.5").ast) == "(/ (/ x y) 2.5)"


@pytest.mark.parametrize("src, col, part", [
    ("a + * b", 5, "expected an operand"),
    ("(a+b", 5, "expected ')'"),
    ("a b", 3, "missing operator"),
    ("", 1, "empty expression"),
    ("a+b)", 4, "unmatched ')'"),
    ("-a", 1, "unary minus"),
    ("x = 1", 3, "cannot appear in an expression"),
    ("a $ b", 3, "illegal character"),
])
def test_errors(src, col, part):
    with pytest.raises(CompileError) as info:
        parse_expression(src)
    assert info.value.col == col and part in info.value.message


def test_tree_agrees_with_derivation_search():
    """The grammar has exactly one tree per string, and it is the one we build."""
    for src in ("9-5+2", "a+b*c", "(a+b)*c", "a*(b-c)/d+e"):
        r = parse_expression(src)
        toks = [leaf.symbol for leaf in r.tree.leaves()]
        d = dv.derive(EXPR_GRAMMAR, toks)
        assert d.complete and len(d.sequences) == 1
        assert d.sequences[0] == leftmost_sequence(r.tree)


def test_derivations():
    r = parse_expression("a+b*c")
    lm = derivation_lines(r.tree)
    rm = derivation_lines(r.tree, rightmost=True)
    assert lm[0] == rm[0] == "E"
    assert lm[-1] == rm[-1] == "id(a) + id(b) * id(c)"
    assert lm[4] == "id(a) + T" and rm[3] == "E + T * id(c)"
    assert len(lm) == len(rm) == len(leftmost_sequence(r.tree)) + 1


def test_partial_tree():
    r = parse_expression("a+b")
    n = len(leftmost_sequence(r.tree))
    assert render_ascii(partial_tree(r.tree, n)) == render_ascii(r.tree)
    assert render_ascii(partial_tree(r.tree, 0)) == "E"
    assert shape(partial_tree(r.tree, 1)) == "(E E + T)"
    assert shape(partial_tree(r.tree, 2, rightmost=True)) == "(E E + (T F))"


def test_cli_parsetree(capsys, tmp_path):
    assert main(["parsetree", "a+b*c", "--all"]) == 0
    out = capsys.readouterr().out
    assert "⇒lm" in out and "⇒rm" in out and "syntax tree" in out
    dot = tmp_path / "t.dot"
    assert main(["parsetree", "9-5+2", "--dot", str(dot)]) == 0
    assert dot.read_text().startswith("digraph")
    assert main(["parsetree", "a+*b"]) == 1
    assert "col 3" in capsys.readouterr().err


def test_parse_tree_golden(golden):
    r = parse_expression("a + b * (c - 2)")
    text = (render_ascii(r.tree) + "\n\n" + render_ascii(r.ast) + "\n\n"
            + "\n".join(derivation_lines(r.tree)) + "\n")
    golden("parsetree_a+b*(c-2)", text)
