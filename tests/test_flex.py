"""Builds the Flex programs in lex/ and checks them. Skipped if flex or gcc is missing."""

import shutil
import subprocess
from pathlib import Path

import pytest

from minilang.lexer import tokenize
from minilang.tokens import TokenType

ROOT = Path(__file__).parent.parent
LEX = ROOT / "lex"

pytestmark = pytest.mark.skipif(
    not (shutil.which("flex") and shutil.which("gcc") and shutil.which("make")),
    reason="flex, gcc or make not installed",
)


@pytest.fixture(scope="module")
def build():
    subprocess.run(["make", "-s", "-C", str(LEX)], check=True, capture_output=True)
    return LEX / "build"


def run(prog: Path, arg: Path) -> subprocess.CompletedProcess:
    return subprocess.run([str(prog), str(arg)], capture_output=True, text=True)


@pytest.mark.parametrize("name", ["factorial", "scopes", "parser_errors", "semantic_errors"])
def test_flex_scanner_matches_python_lexer(build, name):
    path = ROOT / "examples" / f"{name}.mini"
    out = run(build / "minilang", path)
    assert out.returncode == 0, out.stderr
    flex_tokens = []
    for line in out.stdout.splitlines():
        if line.startswith("--"):
            break
        pos, _tok, lexeme, _attr = line.split("\t")
        flex_tokens.append((pos, lexeme))
    py_tokens, _ = tokenize(path.read_text())
    expected = [(f"{t.line}:{t.col}", t.lexeme) for t in py_tokens if t.type is not TokenType.EOF]
    assert flex_tokens == expected


def test_flex_scanner_reports_errors(build):
    out = run(build / "minilang", ROOT / "examples" / "lexer_errors.mini")
    assert out.returncode == 1
    assert "4 lexical error(s)" in out.stderr


def test_wc_matches_python(build):
    path = LEX / "samples" / "text.txt"
    text = path.read_text()
    out = run(build / "wc", path).stdout.split()
    assert out == ["lines", str(text.count("\n")), "words", str(len(text.split())),
                   "chars", str(len(text))]


def test_numbers(build):
    out = run(build / "numbers", LEX / "samples" / "text.txt").stdout
    assert out.startswith("Room four-two is on floor three.")


def test_urls_emails(build):
    out = run(build / "urls_emails", LEX / "samples" / "text.txt").stdout.splitlines()
    assert out == [
        "EMAIL\tlab.admin@example.edu",
        "URL\thttps://www.example.org/courses/cit412?id=7",
        "URL\thttp://example.com",
    ]


def test_strip_comments(build):
    out = run(build / "strip_comments", LEX / "samples" / "comments.c").stdout
    assert "block comment" not in out and "line comment" not in out and "inline" not in out
    assert 'printf("not a // comment and not a /* comment */\\n");' in out
    assert out.count("\n") == (LEX / "samples" / "comments.c").read_text().count("\n")
