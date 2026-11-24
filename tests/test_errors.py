import pytest

from minilang.errors import CompileError, ErrorList

SOURCE = "int n;\nn = 5;\nfact = 1 n = 2;\n"


def test_format_without_position():
    e = CompileError("runtime", "division by zero")
    assert e.format() == "error[runtime]: division by zero"


def test_format_without_source():
    e = CompileError("parser", "expected ';'", 3, 10)
    assert e.format() == "error[parser] line 3, col 10: expected ';'"


def test_format_with_caret(golden):
    e = CompileError("parser", "expected ';' but found 'n'", 3, 10)
    golden("errors_caret", e.format(SOURCE) + "\n")


def test_caret_column():
    e = CompileError("lexer", "illegal character '@'", 1, 5)
    lines = e.format("int @x;").splitlines()
    assert lines[1] == "    int @x;"
    assert lines[2] == "        ^"


def test_line_out_of_range_keeps_header():
    e = CompileError("parser", "unexpected end of file", 99, 1)
    assert e.format(SOURCE) == "error[parser] line 99, col 1: unexpected end of file"


def test_is_raisable():
    with pytest.raises(CompileError) as info:
        raise CompileError("semantic", "undeclared variable 'x'", 2, 1)
    assert info.value.kind == "semantic"
    assert str(info.value) == "undeclared variable 'x'"


def test_error_list():
    errors = ErrorList()
    assert not errors
    errors.add(CompileError("parser", "a", 1, 1))
    errors.add(CompileError("parser", "b", 2, 1))
    assert len(errors) == 2
    assert errors.format().splitlines() == [
        "error[parser] line 1, col 1: a",
        "error[parser] line 2, col 1: b",
    ]
