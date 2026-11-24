"""Chapter 2 translators: notations, Roman numerals, small grammars."""

import random

import pytest

from minilang import translators as tr
from minilang.cli import main
from minilang.errors import CompileError
from minilang.tree import render_ascii


# ---------------------------------------------------------------- expressions

@pytest.mark.parametrize("src, notation, infix, post, pre, value", [
    ("9-5+2", "infix", "9 - 5 + 2", "9 5 - 2 +", "+ - 9 5 2", 6),
    ("9-(5+2)", "infix", "9 - (5 + 2)", "9 5 2 + -", "- 9 + 5 2", 2),
    ("a+b*c", "infix", "a + b * c", "a b c * +", "+ a * b c", None),
    ("(a+b)*c", "infix", "(a + b) * c", "a b + c *", "* + a b c", None),
    ("((a))", "infix", "a", "a", "a", None),
    ("-(2+3)*+4", "infix", "-(2 + 3) * 4", "2 3 + ~ 4 *", "* ~ + 2 3 4", -20),
    ("7/2", "infix", "7 / 2", "7 2 /", "/ 7 2", 3),
    ("7/-2", "infix", "7 / -2", "7 2 ~ /", "/ 7 ~ 2", -3),
    ("-7/2", "infix", "-7 / 2", "7 ~ 2 /", "/ ~ 7 2", -3),
    ("7.0/2", "infix", "7.0 / 2", "7.0 2 /", "/ 7.0 2", 3.5),
    ("95-2+", "postfix", "9 - 5 + 2", "9 5 - 2 +", "+ - 9 5 2", 6),
    ("952+-", "postfix", "9 - (5 + 2)", "9 5 2 + -", "- 9 + 5 2", 2),
    ("12", "postfix", "12", "12", "12", 12),
    ("12 3 + 4 *", "postfix", "(12 + 3) * 4", "12 3 + 4 *", "* + 12 3 4", 60),
    ("ab~*", "postfix", "a * -b", "a b ~ *", "* a ~ b", None),
    ("+-952", "prefix", "9 - 5 + 2", "9 5 - 2 +", "+ - 9 5 2", 6),
    ("* + 12 3 4", "prefix", "(12 + 3) * 4", "12 3 + 4 *", "* + 12 3 4", 60),
])
def test_translate(src, notation, infix, post, pre, value):
    t = tr.translate(src, notation)
    assert (t.infix, t.postfix, t.prefix, t.value) == (infix, post, pre, value)


def test_value_notes():
    assert "identifiers" in tr.translate("a+1").value_note
    t = tr.translate("1/0+2")
    assert t.value is None and t.value_note == "division by zero"
    assert tr.translate("1+2").value_note is None


def test_left_associative_tree_shape():
    """9-5+2 groups as (9-5)+2: the root's left child is the expr for 9-5."""
    root = tr.translate("9-5+2").tree
    assert [c.symbol for c in root.children] == ["expr", "+", "term"]
    assert root.children[0].attrs["val"] == 4
    assert [leaf.lexeme or leaf.symbol for leaf in root.leaves()] == list("9-5+2")


def test_precedence_tree_shape():
    """a+b*c: * sits lower in the tree than +."""
    root = tr.translate("a+b*c").tree
    assert root.children[1].symbol == "+"
    term = root.children[2]
    assert [c.symbol for c in term.children] == ["term", "*", "factor"]


def _random_infix(rng: random.Random, depth: int) -> str:
    if depth == 0 or rng.random() < 0.3:
        return rng.choice(["a", "b", "7", "12", "3"])
    r = rng.random()
    if r < 0.1:
        return "-" + _random_infix(rng, depth - 1)
    if r < 0.25:
        return "(" + _random_infix(rng, depth - 1) + ")"
    op = rng.choice("+-*/")
    return _random_infix(rng, depth - 1) + op + _random_infix(rng, depth - 1)


def test_round_trip_between_notations():
    """Any notation translated to another and back gives the same three strings."""
    rng = random.Random(412)
    for _ in range(300):
        t = tr.translate(_random_infix(rng, 5), "infix")
        for notation, text in (("postfix", t.postfix), ("prefix", t.prefix),
                               ("infix", t.infix)):
            u = tr.translate(text, notation)
            assert (u.infix, u.postfix, u.prefix) == (t.infix, t.postfix, t.prefix)
            assert u.value == t.value


def test_trace_prints_postfix_in_order():
    t = tr.translate("9-5+2")
    prints = [s.action for s in t.trace if s.action.startswith("print")]
    assert prints == ["print('9')", "print('5')", "print('-')", "print('2')", "print('+')"]
    assert t.trace[-1].output == t.postfix
    assert tr.translate("95-2+", "postfix").trace == []


@pytest.mark.parametrize("src, notation, col, part", [
    ("a+*b", "infix", 3, "expected an operand, found '*'"),
    ("(a+b", "infix", 5, "expected ')' to close '(' at column 1, found end of input"),
    ("a b", "infix", 3, "missing operator"),
    ("", "infix", 1, "empty expression"),
    ("a+", "infix", 3, "found end of input"),
    ("a$b", "infix", 2, "unexpected character '$'"),
    ("a~b", "infix", 2, "'~' is only used in postfix"),
    ("9+", "postfix", 2, "needs two operands"),
    ("9 5", "postfix", 4, "2 operands are left"),
    ("(95+)", "postfix", 1, "parentheses are not used"),
    ("+9", "prefix", 3, "found end of input"),
    ("+999", "prefix", 4, "after a complete expression"),
])
def test_expression_errors(src, notation, col, part):
    with pytest.raises(CompileError) as info:
        tr.translate(src, notation)
    assert info.value.kind == "syntax"
    assert info.value.col == col
    assert part in info.value.message


def test_annotated_tree_golden(golden):
    t = tr.translate("9-5+2")
    trace = "\n".join("  " * s.depth + s.action + "    | " + s.output for s in t.trace)
    golden("translate_9-5+2", render_ascii(t.tree) + "\n\n" + trace + "\n")


# ---------------------------------------------------------------- Roman numerals

def test_roman_round_trip_all():
    for n in range(1, 4000):
        roman, _ = tr.int_to_roman(n)
        assert tr.roman_to_int(roman)[0] == n


@pytest.mark.parametrize("roman, value", [
    ("I", 1), ("IV", 4), ("IX", 9), ("XIV", 14), ("XLIX", 49), ("XC", 90),
    ("CD", 400), ("MCMXCIV", 1994), ("mmxxvi", 2026), ("MMMCMXCIX", 3999),
])
def test_roman_to_int(roman, value):
    assert tr.roman_to_int(roman)[0] == value


@pytest.mark.parametrize("bad, col", [
    ("IIII", 4), ("IC", 2), ("VX", 2), ("VV", 2), ("MMMM", 4), ("XM", 2), ("ABC", 1),
])
def test_roman_invalid(bad, col):
    with pytest.raises(CompileError) as info:
        tr.roman_to_int(bad)
    assert info.value.col == col


def test_roman_empty_and_range():
    with pytest.raises(CompileError):
        tr.roman_to_int("  ")
    for n in ("0", "4000"):
        with pytest.raises(CompileError) as info:
            tr.int_to_roman(n)
        assert info.value.kind == "range"
    with pytest.raises(CompileError):
        tr.int_to_roman("12a")


def test_roman_tree_attributes():
    value, root = tr.roman_to_int("XIV")
    assert root.attrs["val"] == value == 14
    assert [c.attrs["val"] for c in root.children] == [0, 0, 10, 4]
    roman, root = tr.int_to_roman(1994)
    assert [c.attrs["roman"] for c in root.children] == ["M", "CM", "XC", "IV"]


# ---------------------------------------------------------------- small grammars

def test_div3_members_are_divisible():
    rows = tr.div3_table(10)
    members = [r for r in rows if r["in L(G)"]]
    assert members, "some strings must be in L(G)"
    assert all(r["divisible by 3"] for r in members)


def test_div3_examples():
    for s in ("11", "1001", "110", "1111", "110011"):
        assert tr.div3_tree(s) is not None, s
    for s in ("", "0", "1", "10", "111", "12"):
        assert tr.div3_tree(s) is None, s
    root = tr.div3_tree("110011")
    assert root.attrs["val"] == 51

    def all_mod(node):
        return node.is_leaf or (node.attrs["val mod 3"] == 0
                                and all(all_mod(c) for c in node.children))

    assert all_mod(root)


def test_brackets():
    assert tr.brackets_tree("([]){()}").attrs["depth"] == 2
    assert tr.brackets_tree("").attrs["depth"] == 0
    for bad, col in (("(()", 4), ("())", 3), ("(]", 2), ("( x )", 3)):
        with pytest.raises(CompileError) as info:
            tr.brackets_tree(bad)
        assert info.value.col == col


def test_comma_lists_lean_opposite_ways():
    left = tr.comma_list_tree("a, b, c", "left")
    right = tr.comma_list_tree("a, b, c", "right")
    assert [c.symbol for c in left.children] == ["list", ",", "id"]
    assert [c.symbol for c in right.children] == ["id", ",", "list"]
    assert left.attrs["n"] == right.attrs["n"] == 3
    assert [x.lexeme for x in left.leaves() if x.symbol == "id"] == ["a", "b", "c"]
    assert [x.lexeme for x in right.leaves() if x.symbol == "id"] == ["a", "b", "c"]
    for bad in ("a,,b", "a b", "a,", ""):
        with pytest.raises(CompileError):
            tr.comma_list_tree(bad, "left")


# ---------------------------------------------------------------- CLI

def test_cli_translate(capsys):
    assert main(["translate", "9-5+2", "--tree", "--trace", "--scheme"]) == 0
    out = capsys.readouterr().out
    assert "postfix        : 9 5 - 2 +" in out
    assert "print('+')" in out
    assert main(["translate", "+-952", "--from", "prefix"]) == 0
    assert "9 - 5 + 2" in capsys.readouterr().out
    assert main(["translate", "a+*b"]) == 1
    assert "col 3" in capsys.readouterr().err


def test_cli_roman(capsys):
    assert main(["roman", "MCMXCIV", "--tree"]) == 0
    assert "MCMXCIV = 1994" in capsys.readouterr().out
    assert main(["roman", "2026"]) == 0
    assert "2026 = MMXXVI" in capsys.readouterr().out
    assert main(["roman", "IIII"]) == 1


def test_cli_check(capsys):
    assert main(["check", "div3", "1001"]) == 0
    assert main(["check", "div3", "111"]) == 1
    assert main(["check", "div3", "--table", "4"]) == 0
    assert "in L(G) but not divisible by 3: 0" in capsys.readouterr().out
    assert main(["check", "brackets", "(]"]) == 1
    assert main(["check", "left-list", "a, b"]) == 0
    assert main(["check", "brackets"]) == 2
