"""Smoke tests for the Streamlit pages (skipped if Streamlit is not installed)."""

import sys
from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

APP = Path(__file__).parent.parent / "app"
# `streamlit run app/Home.py` puts app/ on sys.path (for ui_common, diagrams); AppTest of
# a page under app/pages/ does not, so add it here.
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))


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


def test_translators_page_expressions():
    at = run("pages/3_Translators.py")
    at.slider(key="tr_step").set_value(3).run()
    assert not at.exception
    at.text_input(key="tr_expr_infix").set_value("a+*b").run()
    assert not at.exception
    assert at.error, "a syntax error should be shown"


def test_translators_page_postfix_and_grammars():
    at = run("pages/3_Translators.py")
    at.segmented_control(key="tr_notation").set_value("postfix").run()
    assert not at.exception
    at.text_input(key="tr_roman").set_value("IIII").run()
    assert not at.exception
    for g in ("brackets", "lists", "div3"):
        at.segmented_control(key="tr_grammar").set_value(g).run()
        assert not at.exception


def test_grammar_workbench_every_grammar():
    from minilang.grammar.grammar import grammar_names

    at = run("pages/4_Grammar_Workbench.py")
    for name in grammar_names():
        at.selectbox(key="gw_grammar").select(name).run()
        assert not at.exception, name


def test_grammar_workbench_bad_grammar():
    at = run("pages/4_Grammar_Workbench.py")
    at.text_area(key="gw_gtext").set_value("E E -> x").run()
    assert not at.exception
    assert at.error


def test_top_down_every_grammar_and_method():
    from minilang.grammar.grammar import grammar_names

    at = run("pages/5_Top_Down_Parsing.py")
    for method in ("backtrack", "predictive", "ll1"):
        at.segmented_control(key="td_method").set_value(method).run()
        for name in grammar_names():
            at.selectbox(key="td_grammar").select(name).run()
            assert not at.exception, (method, name)


def test_top_down_reject_and_step():
    at = run("pages/5_Top_Down_Parsing.py")
    at.text_input(key="td_input_expr_ll1").set_value("id+*id").run()
    assert not at.exception
    assert at.error
    at.slider(key="td_step_ll1").set_value(2).run()
    assert not at.exception
