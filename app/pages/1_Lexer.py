"""Lexical analyzer page (Chapter 3)."""

import streamlit as st

from diagrams import DIAGRAMS, diagram_for_path, to_dot
from minilang.lexer import Lexer
from minilang.tokens import RELOP_TEXT, TokenType as T
from ui_common import (LEGEND, buffer_html, errors_block, highlight_html, setup_page,
                       source_editor, valid_cells)

setup_page("Lexer")
st.title("Lexical Analyzer")
st.caption("Chapter 3 · tokens, lexemes and attributes (3.1) · buffer pair with sentinels (3.2) "
           "· transition diagrams (3.4)")

left, right = st.columns([1, 1.2], gap="large")
with left:
    source = source_editor("lexer")
    half_size = st.number_input(
        "Buffer half size N", min_value=1, max_value=8192, value=16, step=1,
        help="Each half of the buffer pair holds N characters. A lexeme must fit in one half.",
    )


@st.cache_data(show_spinner=False)
def run_lexer(src: str, n: int):
    lexer = Lexer(src, half_size=n)
    steps = []
    keep_snapshots = n <= 64
    while True:
        tok = lexer.next_token()
        snap = lexer.buf.snapshot() if keep_snapshots else None
        steps.append((tok, list(lexer.path), snap))
        if tok.type is T.EOF:
            break
    return steps, list(lexer.errors.errors), list(lexer.names.names), lexer.buf.reloads


steps, errors, names, reloads = run_lexer(source, int(half_size))
tokens = [s[0] for s in steps]

with right:
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Tokens", len(tokens) - 1)
    m2.metric("Names", len(names))
    m3.metric("Errors", len(errors))
    m4.metric("Half reloads", reloads)
    st.markdown(highlight_html(source, tokens, errors), unsafe_allow_html=True)
    st.markdown(LEGEND, unsafe_allow_html=True)


def attribute(tok) -> str:
    if tok.type is T.ID:
        return f"name #{tok.value}"
    if tok.type is T.RELOP:
        return f"{tok.value} ({RELOP_TEXT[tok.value]})"
    return "-" if tok.value is None else repr(tok.value)


st.divider()
tab_steps, tab_tokens, tab_names, tab_errors, tab_diagrams = st.tabs(
    ["▶ Step through", "Token table", "Name table", "Errors", "Transition diagrams"])

with tab_tokens:
    rows = [{"Pos": f"{t.line}:{t.col}", "Lexeme": t.lexeme, "Token": t.type.value,
             "Attribute": attribute(t)} for t in tokens if t.type is not T.EOF]
    st.dataframe(rows, width="stretch", hide_index=True)

with tab_names:
    st.caption("Each identifier is stored once; its token's attribute is the index here. "
               "Scopes and types come later (symbol table, 2.7).")
    st.dataframe([{"#": i, "Name": n} for i, n in enumerate(names)], hide_index=True)

with tab_errors:
    errors_block(errors, source)

with tab_diagrams:
    for name, (title, _s, _e) in DIAGRAMS.items():
        st.subheader(title)
        st.graphviz_chart(to_dot(name))
    st.caption("A state marked * retracts the forward pointer by one character: the last "
               "character read is not part of the lexeme.")

with tab_steps:
    real = [i for i, t in enumerate(tokens) if t.type is not T.EOF]
    if not real:
        st.info("No tokens.")
    else:
        k = st.slider("Token", 1, len(real), 1, key="lexer_step") - 1
        i = real[k]
        tok, path, snap = steps[i]
        st.markdown(
            f"**Token {k + 1} of {len(real)}:** lexeme `{tok.lexeme}` → "
            f"token **{tok.type.value}**, attribute **{attribute(tok)}**, at line {tok.line}, "
            f"column {tok.col}")
        c1, c2 = st.columns([1, 1.3], gap="large")
        with c1:
            st.markdown(highlight_html(source, tokens, errors, selected=i), unsafe_allow_html=True)
        with c2:
            which = diagram_for_path(path)
            if which:
                st.markdown(f"**Transition diagram:** {DIAGRAMS[which][0]}")
                st.graphviz_chart(to_dot(which, path))
                st.markdown("State path: " + " → ".join(f"`{s}`" for s in path))
            else:
                st.markdown("**Single-character token:** recognized directly, no lookahead "
                            "needed, so there is no diagram to walk.")
        st.markdown("**Buffer pair after this token** (`lb` = lexemeBegin, `fwd` = forward; "
                    "yellow = the lexeme)")
        if snap is None:
            st.info("Set the buffer half size to 64 or less to see the buffer.")
        else:
            st.markdown(buffer_html(snap, valid_cells(snap)), unsafe_allow_html=True)
            st.caption(f"Half reloads so far: {snap['reloads']}. When forward reaches the eof "
                       "at the end of a half, the other half is loaded with the next chunk.")
