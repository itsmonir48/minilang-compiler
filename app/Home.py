"""MiniLang Compiler Studio: home page.  Run:  minilang ui   (or: streamlit run app/Home.py)"""

import streamlit as st

from minilang import __version__
from ui_common import EXAMPLES, setup_page

setup_page("Home")

# phases of the compiler and whether their page exists yet
STAGES = [
    ("Lexer", "Ch 3", True),
    ("Parser", "Ch 2.4 / 4", False),
    ("AST", "Ch 2.8", False),
    ("Semantic check", "Ch 2.7", False),
    ("Three-address code", "Ch 2.8", False),
    ("Run", "TAC interpreter", False),
]


def pipeline_dot() -> str:
    lines = ['digraph G { rankdir=LR; bgcolor=transparent;',
             'node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=12];',
             'src [label="source.mini", shape=note, fillcolor="#f1f3f5"];']
    prev = "src"
    for i, (name, chapter, done) in enumerate(STAGES):
        fill = "#d3f9d8" if done else "#f8f9fa"
        color = "#2b8a3e" if done else "#adb5bd"
        lines.append(f'n{i} [label="{name}\\n{chapter}", fillcolor="{fill}", color="{color}"];')
        lines.append(f"{prev} -> n{i};")
        prev = f"n{i}"
    lines.append("}")
    return "\n".join(lines)


st.title("🛠️ MiniLang Compiler Studio")
st.markdown(
    "A small C-like language **MiniLang** and a complete mini-compiler for it, plus a "
    "**grammar workbench** that shows every Chapter 4 parsing algorithm step by step. "
    f"CIT 412 Compiler Design and Automata Theory Sessional · version {__version__}")

st.subheader("Compiler pipeline")
st.graphviz_chart(pipeline_dot())
st.caption("Green = available now. The other stages are added phase by phase (see ROADMAP.md).")

st.subheader("Pages")
PAGES = [
    ("pages/1_Lexer.py", "Lexer", "🔤",
     "Write MiniLang code and see its tokens, the name table, lexical errors, the "
     "transition-diagram path of every token and the buffer pair with its pointers."),
    ("pages/2_Strings_and_Regex.py", "Strings & Regex", "🔎",
     "Prefixes, suffixes, substrings and subsequences of a string; test strings against "
     "the regular definitions of the lab sheet."),
    ("pages/3_Translators.py", "Translators", "🔁",
     "Infix, postfix and prefix translation with annotated parse trees, the 2.5 translator "
     "step by step, Roman numerals and the small grammars of Chapter 2."),
]
cols = st.columns(3)
for col, (path, label, icon, text) in zip(cols, PAGES):
    with col:
        st.page_link(path, label=label, icon=icon)
        st.caption(text)

st.subheader("MiniLang in one example")
st.code((EXAMPLES / "factorial.mini").read_text(), language="c")
