"""Smoke tests for the Streamlit pages (skipped if Streamlit is not installed)."""

from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

APP = Path(__file__).parent.parent / "app"


def run(page: str) -> AppTest:
    at = AppTest.from_file(str(APP / page), default_timeout=30)
    at.run()
    assert not at.exception, at.exception
    return at


def test_home():
    at = run("Home.py")
    assert "MiniLang Compiler Studio" in at.title[0].value


def test_lexer_page_default_example():
    at = run("pages/1_Lexer.py")
    metrics = {m.label: m.value for m in at.metric}
    assert metrics["Errors"] == "0"
    assert int(metrics["Tokens"]) > 0


def test_lexer_page_with_errors_and_stepping():
    at = run("pages/1_Lexer.py")
    at.selectbox(key="lexer_example").select("lexer_errors").run()
    assert not at.exception
    assert {m.label: m.value for m in at.metric}["Errors"] == "4"
    at.slider(key="lexer_step").set_value(5).run()
    assert not at.exception


def test_lexer_page_tiny_buffer():
    at = run("pages/1_Lexer.py")
    at.number_input[0].set_value(3).run()      # 'factorial' has 4-5 letter lexemes
    assert not at.exception
    assert int({m.label: m.value for m in at.metric}["Errors"]) >= 1


def test_strings_and_regex_page():
    at = run("pages/2_Strings_and_Regex.py")
    at.text_input[0].set_value("abc").run()
    assert not at.exception
