"""Expression → parse tree page (Chapter 2.2, 2.8, 4.1, 4.2)."""

import streamlit as st

from minilang.errors import CompileError
from minilang.parse_tree import (EXPR_GRAMMAR, derivation_lines, parse_expression,
                                 partial_tree)
from minilang.tree import Node, to_dot
from ui_common import setup_page, page_header

setup_page("Parse Tree")
page_header('Chapter 2 · Syntax-directed translation',
            'Expression → Parse Tree',
            'Type an expression and see its parse tree and syntax tree side by side, with the leftmost and rightmost derivations step by step.',
            ['2.2 Parse trees', '2.8 Syntax trees', '4.2 Derivations'])

EXAMPLES = ["a + b * (c - 2)", "9 - 5 + 2", "a + b * c", "(a + b) * c", "x / y / z",
            "a + * b"]

c1, c2 = st.columns([1.3, 1], gap="large")
with c1:
    pick = st.segmented_control("Examples", EXAMPLES, default=EXAMPLES[0], key="pt_pick")
    if pick and st.session_state.get("pt_last_pick") != pick:
        st.session_state["pt_expr"] = pick
        st.session_state["pt_last_pick"] = pick
    st.session_state.setdefault("pt_expr", EXAMPLES[0])
    expr = st.text_input("Expression (tokenized by the Phase 1 lexer)", key="pt_expr")
with c2:
    st.markdown("**Grammar**")
    st.code(EXPR_GRAMMAR.to_text(), language=None)

try:
    r = parse_expression(expr)
except CompileError as e:
    st.error(e.message)
    st.code(e.format(expr), language=None)
    st.stop()

st.markdown("**Tokens:** " + "  ".join(
    f"`{t.lexeme}`" for t in r.tokens if t.lexeme))

t1, t2 = st.columns([1.4, 1], gap="large")
with t1:
    st.subheader("Parse tree")
    st.graphviz_chart(to_dot(r.tree, attrs=False))
    st.caption(f"{r.tree.count()} nodes, height {r.tree.height()}. Every grammar symbol "
               "used is a node; the leaves, read left to right, are the expression.")
    st.download_button("Download .dot", to_dot(r.tree, attrs=False) + "\n",
                       file_name="parse_tree.dot", mime="text/vnd.graphviz")
with t2:
    st.subheader("Syntax tree (AST)")
    st.graphviz_chart(to_dot(r.ast, attrs=False))
    st.caption(f"{r.ast.count()} nodes. Operators are interior nodes; the chain steps "
               "E → T → F and the parentheses are gone, but the grouping is the same.")

st.divider()
st.subheader("Derivations of this tree")
order = st.segmented_control("Order", ["leftmost", "rightmost"], default="leftmost",
                             required=True, key="pt_order")
rightmost = order == "rightmost"
lines = derivation_lines(r.tree, rightmost=rightmost)
k = st.slider("Step", 0, len(lines) - 1, len(lines) - 1, key=f"pt_step_{order}")
d1, d2 = st.columns([1, 1.2], gap="large")
with d1:
    arrow = "⇒rm" if rightmost else "⇒lm"
    shown = []
    for i, line in enumerate(lines):
        prefix = "    " if i == 0 else f"{arrow} "
        mark = "  ◀" if i == k else ""
        shown.append(prefix + line + mark)
    st.code("\n".join(shown), language=None)
with d2:
    part = partial_tree(r.tree, k, rightmost=rightmost)
    pending: set[int] = set()

    def collect(n: Node) -> None:
        if n.is_leaf and EXPR_GRAMMAR.is_nonterminal(n.symbol):
            pending.add(id(n))
        for c in n.children:
            collect(c)

    collect(part)
    st.graphviz_chart(to_dot(part, attrs=False, faded=pending))
    st.caption(f"The tree after {k} step(s). Both derivations build the same tree; they "
               "only expand the nonterminals in a different order (the leftmost or the "
               "rightmost one first).")
