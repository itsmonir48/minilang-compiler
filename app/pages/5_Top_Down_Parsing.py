"""Top-down parsing page (Chapter 4.4): three parsers, step by step."""

import html

import streamlit as st

from minilang.errors import CompileError
from minilang.grammar import topdown as td
from minilang.grammar.grammar import tokenize_input
from minilang.grammar.ll1 import build_ll1, input_text, node_at
from minilang.tree import Node, to_dot
from ui_common import grammar_editor, ll1_table_html, setup_page, trace_html

setup_page("Top-Down Parsing")
st.title("Top-Down Parsing")
st.caption("Chapter 4.4 · backtracking recursive descent (4.4.1) · predictive recursive "
           "descent · table-driven LL(1) parser (4.4.4). The parse tree grows from the root "
           "down, in leftmost-derivation order.")

SAMPLES = {
    "expr": "id+id*id", "expr_ll1": "id+id*id", "expr_ambiguous": "id+id*id",
    "dangling_else": "if cond then if cond then other else other",
    "dangling_else_fixed": "if cond then if cond then other else other",
    "backtrack": "cad", "indirect_left_rec": "bdca", "left_factor": "ibtaea",
    "balanced": "(())()", "ab_equal": "abab", "prefix": "+a*aa",
}

left, right = st.columns([1, 1.2], gap="large")
with left:
    name, _text, g = grammar_editor("td", "expr_ll1")
if g is None:
    st.stop()
with right:
    method = st.segmented_control("Method", list(td.METHODS), format_func=td.METHODS.get,
                                  default="ll1", required=True, key="td_method")
    inp = st.text_input("Input string (terminals may be written without blanks)",
                        value=SAMPLES.get(name, ""), key=f"td_input_{name}")

    refusal = td.check(g, method)
    if refusal:
        st.warning(f"**{td.METHODS[method]} cannot be used:** {refusal.reason}.")
        if refusal.suggestion is None:
            st.info("Removing left recursion and left factoring do not change this grammar. "
                    "Try backtracking, or rewrite the grammar by hand.")
            st.stop()
        st.markdown("Transformed grammar (left recursion removed, then left factored):")
        st.code(refusal.suggestion.to_text(), language=None)
        if not refusal.suggestion_ok:
            st.info("The transformed grammar is still not suitable for this method (e.g. an "
                    "ambiguous grammar never becomes LL(1)). Backtracking may still work.")
            st.stop()
        if not st.toggle("Use the transformed grammar", value=True, key="td_use_fixed"):
            st.stop()
        g = refusal.suggestion

try:
    tokens = tokenize_input(g, inp)
except CompileError as e:
    with right:
        st.error(e.format(inp))
    st.stop()

run = td.run_method(g, method, tokens)

with right:
    if run.accepted:
        st.success(f"Accepted in {len(run.steps)} steps.")
    elif run.error is not None:
        st.error(f"Rejected after {len(run.steps)} steps.")
        st.code(run.error.format(inp), language=None)

if not run.steps:
    st.stop()

st.divider()
k = st.slider("Step", 1, len(run.steps), len(run.steps), key=f"td_step_{method}") - 1
step = run.steps[k]
st.markdown(f"**Step {k + 1} of {len(run.steps)}:** {html.escape(step.action)}")

c1, c2 = st.columns([1.3, 1], gap="medium")
with c1:
    tree = step.tree
    active = node_at(tree, step.active)
    pending: set[int] = set()

    def collect(node: Node) -> None:
        if node.is_leaf and g.is_nonterminal(node.symbol):
            pending.add(id(node))
        for c in node.children:
            collect(c)

    collect(tree)
    st.graphviz_chart(to_dot(tree, attrs=False, highlight={id(active)} if active else None,
                             faded=pending))
    st.caption("Orange: the node this step works on. Dashed grey: a nonterminal not "
               "expanded yet. Blue: terminals.")
with c2:
    if method == "ll1":
        st.markdown(f"**Stack** (top at the right): `{' '.join(step.stack)}`  \n"
                    f"**Input:** `{input_text(tokens, step.pos)}`")
        stacks = [" ".join(s.stack) for s in run.steps]
        inputs = [input_text(tokens, s.pos) for s in run.steps]
        ws, wi = max(map(len, stacks)), max(map(len, inputs))
        lines = [f"{a:<{ws}}  {b:>{wi}}  {s.action.replace('output ', '')}"
                 for a, b, s in zip(stacks, inputs, run.steps)]
    else:
        st.markdown(f"**Input left:** `{input_text(tokens, step.pos)}`")
        lines = ["  " * s.depth + s.action for s in run.steps]
    st.markdown(trace_html(lines, [s.kind for s in run.steps], k), unsafe_allow_html=True)

if method != "backtrack":
    with st.expander("LL(1) table used by the parser"):
        t = build_ll1(g)
        hit = None
        if step.kind in ("expand", "call") and step.active is not None:
            sym = node_at(tree, step.active).symbol
            la = tokens[step.pos][0] if step.pos < len(tokens) else "$"
            hit = (sym, la)
        st.markdown(ll1_table_html(t, hit), unsafe_allow_html=True)
        st.caption("The outlined cell is the entry used in this step.")

with st.expander("Compare the three methods on this grammar and input"):
    rows = []
    for m, label in td.METHODS.items():
        r = td.check(g, m)
        if r:
            rows.append({"Method": label, "Result": "cannot run", "Steps": "",
                         "Why": r.reason[:90] + ("…" if len(r.reason) > 90 else "")})
            continue
        res = td.run_method(g, m, tokens)
        rows.append({"Method": label, "Result": "accepted" if res.accepted else "rejected",
                     "Steps": len(res.steps), "Why": ""})
    st.dataframe(rows, hide_index=True, width="stretch")
    st.caption("Backtracking needs no table but may try (and undo) many alternatives; the "
               "predictive parsers never back up because one lookahead symbol decides.")
