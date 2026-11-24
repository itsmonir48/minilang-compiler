from pathlib import Path

import pytest

from minilang.cli import main
from minilang.lexer import Lexer, tokenize
from minilang.tokens import EQ, GE, GT, LE, LT, NE, TokenType as T

EXAMPLES = Path(__file__).parent.parent / "examples"


def kinds(src: str) -> list[T]:
    tokens, _ = tokenize(src)
    return [t.type for t in tokens]


def test_keywords_and_ids():
    tokens, lexer = tokenize("int float if else while print iff _x x1")
    assert [t.type for t in tokens] == [
        T.INT, T.FLOAT, T.IF, T.ELSE, T.WHILE, T.PRINT, T.ID, T.ID, T.ID, T.EOF]
    assert lexer.names.names == ["iff", "_x", "x1"]


def test_same_name_same_index():
    tokens, _ = tokenize("a b a")
    assert [t.value for t in tokens[:3]] == [0, 1, 0]


@pytest.mark.parametrize("src, ttype, value", [
    ("0", T.NUM, 0),
    ("123", T.NUM, 123),
    ("3.14", T.REAL, 3.14),
    ("1E5", T.REAL, 1e5),
    ("1.5E-3", T.REAL, 1.5e-3),
    ("2.0e+2", T.REAL, 200.0),
])
def test_numbers(src, ttype, value):
    tokens, lexer = tokenize(src)
    assert (tokens[0].type, tokens[0].value, tokens[0].lexeme) == (ttype, value, src)
    assert not lexer.errors


@pytest.mark.parametrize("src, value", [
    ("<", LT), ("<=", LE), (">", GT), (">=", GE), ("==", EQ), ("!=", NE)])
def test_relops(src, value):
    tokens, _ = tokenize(src)
    assert (tokens[0].type, tokens[0].value) == (T.RELOP, value)


def test_operators_and_punctuation():
    assert kinds("+ - * / = ! && || ( ) { } ; ,") == [
        T.PLUS, T.MINUS, T.STAR, T.SLASH, T.ASSIGN, T.NOT, T.AND, T.OR,
        T.LPAREN, T.RPAREN, T.LBRACE, T.RBRACE, T.SEMI, T.COMMA, T.EOF]


def test_longest_match_without_spaces():
    assert kinds("a<=b==c!=!d") == [
        T.ID, T.RELOP, T.ID, T.RELOP, T.ID, T.RELOP, T.NOT, T.ID, T.EOF]
    assert kinds("x=-1") == [T.ID, T.ASSIGN, T.MINUS, T.NUM, T.EOF]


def test_comments_are_skipped():
    src = "a // line comment\n/* block\n * comment **/ b / c"
    assert kinds(src) == [T.ID, T.ID, T.SLASH, T.ID, T.EOF]


def test_line_and_column():
    tokens, _ = tokenize("int x;\n  x = 42;")
    assert [(t.lexeme, t.line, t.col) for t in tokens[:-1]] == [
        ("int", 1, 1), ("x", 1, 5), (";", 1, 6),
        ("x", 2, 3), ("=", 2, 5), ("42", 2, 7), (";", 2, 9)]


@pytest.mark.parametrize("src, message", [
    ("a @ b", "illegal character '@'"),
    ("a & b", "did you mean '&&'"),
    ("x = 1.;", "expected a digit after '.'"),
    ("x = 1.5E+;", "expected a digit in the exponent"),
    ("x = 2Ey;", "expected a digit in the exponent"),
    ("a /* open", "unterminated comment"),
])
def test_errors(src, message):
    _, lexer = tokenize(src)
    assert len(lexer.errors) == 1
    assert message in lexer.errors.errors[0].message


def test_lexer_continues_after_errors():
    tokens, lexer = tokenize("a @ b # c")
    assert [t.lexeme for t in tokens[:-1]] == ["a", "b", "c"]
    assert len(lexer.errors) == 2


def test_lexer_errors_example(golden):
    src = (EXAMPLES / "lexer_errors.mini").read_text()
    _, lexer = tokenize(src)
    assert len(lexer.errors) == 4
    golden("lexer_errors", lexer.errors.format(src) + "\n")


@pytest.mark.parametrize("name", ["factorial", "scopes", "parser_errors", "semantic_errors"])
@pytest.mark.parametrize("n", [5, 8, 64])
def test_small_buffers_give_same_tokens(name, n):
    src = (EXAMPLES / f"{name}.mini").read_text()
    big, _ = tokenize(src)
    small, lexer = tokenize(src, half_size=n)
    assert small == big
    assert not lexer.errors


def test_token_longer_than_buffer_is_reported():
    _, lexer = tokenize("int verylongname;", half_size=4)
    assert "longer than the buffer half size" in lexer.errors.errors[0].message


def test_next_token_after_eof_stays_eof():
    lexer = Lexer("a")
    assert lexer.next_token().type is T.ID
    assert lexer.next_token().type is T.EOF
    assert lexer.next_token().type is T.EOF


def test_tokens_command(capsys, golden):
    assert main(["tokens", str(EXAMPLES / "factorial.mini")]) == 0
    golden("tokens_factorial", capsys.readouterr().out)


def test_tokens_command_markdown(capsys):
    main(["tokens", "--md", str(EXAMPLES / "factorial.mini")])
    out = capsys.readouterr().out
    assert out.startswith("| Pos | Lexeme | Token | Attribute |")
    assert "| 6:20 | \\|\\| |" not in out      # sanity: no stray pipes


def test_tokens_command_errors_exit_code(capsys):
    assert main(["tokens", str(EXAMPLES / "lexer_errors.mini")]) == 1
    assert "4 lexical error(s)" in capsys.readouterr().err
