"""Home page of MiniLang Compiler Studio."""

import streamlit as st

from minilang import __version__
from minilang.grammar.grammar import grammar_names
from ui_common import EXAMPLES, example_names, setup_page

setup_page("Home")

# compiler stages and whether they are built yet (see ROADMAP.md)
STAGES = [
    ("Lexer", "Ch 3", True),
    ("Parser", "Ch 2.4 / 4", False),
    ("AST", "Ch 2.8", False),
    ("Semantic check", "Ch 2.7", False),
    ("Three-address code", "Ch 2.8", False),
    ("Run", "TAC interpreter", False),
]

CARDS = [
    ("pages/1_Lexer.py", "Lexer", ":material/data_object:", "Chapter 3.1–3.4",
     "Tokens, the name table and lexical errors; the transition-diagram path of every "
     "token and the buffer pair with its pointers."),
    ("pages/2_Strings_and_Regex.py", "Strings & Regex", ":material/text_fields:",
     "Chapter 3.3",
     "Prefixes, suffixes, substrings and subsequences; test strings against the regular "
     "definitions of the lab sheet."),
    ("pages/3_Translators.py", "Translators", ":material/swap_horiz:", "Chapter 2.2–2.5",
     "Infix, postfix and prefix with annotated parse trees, the 2.5 translator step by "
     "step, Roman numerals and small grammars."),
    ("pages/6_Parse_Tree.py", "Parse Tree", ":material/account_tree:", "Chapter 2.2 · 2.8 · 4.2",
     "Expression → parse tree and syntax tree side by side; leftmost and rightmost "
     "derivations step by step."),
    ("pages/4_Grammar_Workbench.py", "Grammar Workbench", ":material/schema:",
     "Chapter 4.2–4.4",
     "Ambiguity, L(G), left recursion removal, left factoring, FIRST and FOLLOW, and the "
     "LL(1) table with its conflicts."),
    ("pages/5_Top_Down_Parsing.py", "Top-Down Parsing", ":material/south:", "Chapter 4.4",
     "Backtracking, predictive and table-driven LL(1) parsing, with the parse tree growing "
     "from the root down."),
]


def pipeline_dot() -> str:
    lines = ['digraph G { rankdir=LR; bgcolor=transparent; nodesep=0.3;',
             'node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=12,'
             ' margin="0.18,0.08", penwidth=1.2];',
             'edge [color="#9aa7bd", arrowsize=0.7];',
             'src [label="source.mini", shape=note, fillcolor="#f4f6fa", color="#c3cddd"];']
    prev = "src"
    for i, (name, chapter, done) in enumerate(STAGES):
        if done:
            style = 'fillcolor="#2b5fb3", color="#2b5fb3", fontcolor="white"'
        else:
            style = 'fillcolor="#ffffff", color="#c3cddd", fontcolor="#5b6474", style="rounded,dashed,filled"'
        lines.append(f'n{i} [label="{name}\\n{chapter}", {style}];')
        lines.append(f"{prev} -> n{i};")
        prev = f"n{i}"
    lines.append("}")
    return "\n".join(lines)


n_pages = len(CARDS)
n_grammars = len(grammar_names())
n_examples = len(example_names())
st.markdown(f"""
<div class="hero">
  <div class="eyebrow">CIT 412 · Compiler Design and Automata Theory Sessional</div>
  <div class="h-title">MiniLang Compiler Studio</div>
  <div class="h-text">A compiler for a small C-like language, MiniLang, and a workbench
  that runs the algorithms of Chapters 2–4 of the Dragon Book step by step: tokens,
  transition diagrams, translation schemes, parse trees, FIRST/FOLLOW, LL(1) tables and
  parser traces.</div>
  <div class="stats">
    <div class="stat"><div class="v">{n_pages}</div><div class="l">Interactive pages</div></div>
    <div class="stat"><div class="v">3</div><div class="l">Textbook chapters</div></div>
    <div class="stat"><div class="v">{n_grammars}</div><div class="l">Textbook grammars</div></div>
    <div class="stat"><div class="v">{n_examples}</div><div class="l">Example programs</div></div>
    <div class="stat"><div class="v">v{__version__}</div><div class="l">Version</div></div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="section-title">Explore</div>'
            '<div class="section-sub">Each page covers one group of lab topics. Type your '
            'own input or load an example, then step through the algorithm.</div>',
            unsafe_allow_html=True)
for i in range(0, len(CARDS), 3):
    cols = st.columns(3, gap="medium")
    for col, (path, label, icon, tag, text) in zip(cols, CARDS[i:i + 3]):
        with col, st.container(border=True):
            st.markdown(f'<div class="card-tag">{tag}</div>'
                        f'<div class="card-title">{label}</div>'
                        f'<div class="card-text">{text}</div>', unsafe_allow_html=True)
            st.page_link(path, label=f"Open {label}", icon=icon)

st.markdown('<div class="section-title">Compiler pipeline</div>'
            '<div class="section-sub">Blue: built. Dashed: planned in the next phases '
            '(see ROADMAP.md).</div>', unsafe_allow_html=True)
with st.container(border=True):
    st.graphviz_chart(pipeline_dot(), width="stretch")

left, right = st.columns([1.2, 1], gap="large")
with left:
    st.markdown('<div class="section-title">MiniLang in one example</div>'
                '<div class="section-sub">examples/factorial.mini, expected output 120</div>',
                unsafe_allow_html=True)
    st.code((EXAMPLES / "factorial.mini").read_text(), language="c", wrap_lines=True)
with right:
    st.markdown('<div class="section-title">The language</div>'
                '<div class="section-sub">C-like, small enough to compile by hand</div>',
                unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown(
            "- **Types:** `int`, `float`\n"
            "- **Statements:** assignment, `if / else`, `while`, `{ }` blocks, `print`\n"
            "- **Operators:** arithmetic `+ - * /` and unary `-`; relational `< <= > >= == !=`; "
            "logical `&& || !`\n"
            "- **Comments:** `//` and `/* */`\n"
            "- **Semantics:** `int / int` truncates; division by zero is a runtime "
            "error; `else` binds to the nearest `if`")
