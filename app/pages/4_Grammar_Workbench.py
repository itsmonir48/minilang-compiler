"""Grammar workbench page (Chapter 4.2-4.4)."""

import streamlit as st

from minilang.errors import CompileError
from minilang.grammar import derivation as dv
from minilang.grammar import transforms as tf
from minilang.grammar.first_follow import first_follow, fmt_set
from minilang.grammar.grammar import tokenize_input
from minilang.grammar.ll1 import build_ll1
from minilang.tree import to_dot
from ui_common import grammar_editor, ll1_table_html, setup_page, page_header

setup_page("Grammar Workbench")
page_header('Chapter 4 · Syntax analysis',
            'Grammar Workbench',
            'Load or write a grammar and analyse it: derivations and ambiguity, the language L(G), left recursion, left factoring, FIRST/FOLLOW and the LL(1) table.',
            ['4.2 Derivations and ambiguity', '4.3 Writing a grammar', '4.4 FIRST, FOLLOW, LL(1)'])

SAMPLES = {
    "expr": "id+id*id", "expr_ll1": "id+id*id", "expr_ambiguous": "id+id*id",
    "dangling_else": "if cond then if cond then other else other",
    "dangling_else_fixed": "if cond then if cond then other else other",
    "backtrack": "cad", "indirect_left_rec": "bdca", "left_factor": "ibtaea",
    "balanced": "(())()", "ab_equal": "abab", "prefix": "+a*aa",
}

left, right = st.columns([1, 1.25], gap="large")
with left:
    name, text, g = grammar_editor("gw", "expr")
if g is None:
    st.stop()

sets = first_follow(g)
table = build_ll1(g, sets)
rec = tf.left_recursive(g)

with right:
    m1, m2, m3 = st.columns(3)
    m1.metric("Nonterminals", len(g.nonterminals), border=True)
    m2.metric("Terminals", len(g.terminals), border=True)
    m3.metric("Productions", len(g.productions), border=True)
    m4, m5 = st.columns(2)
    m4.metric("Left-recursive", "yes" if rec else "no", border=True)
    m5.metric("LL(1)", "yes" if table.is_ll1 else f"no ({len(table.conflicts)} conflicts)",
              border=True)
    st.markdown(f"**Start symbol:** `{g.start}` · **Nonterminals:** "
                + " ".join(f"`{a}`" for a in g.nonterminals) + " · **Terminals:** "
                + " ".join(f"`{t}`" for t in g.terminals))
    st.markdown("**Productions**")
    st.dataframe([{"#": i, "Production": str(p)} for i, p in enumerate(g.productions)],
                 hide_index=True, width="stretch", height=min(38 + 35 * len(g.productions), 280),
                 column_config={"#": st.column_config.NumberColumn(width="small")})

st.divider()
tabs = st.tabs(["Derivations & ambiguity", "Language L(G)", "Left recursion", "Left factoring",
                "FIRST / FOLLOW", "LL(1) table"])

# ------------------------------------------------------------------ derivations
with tabs[0]:
    inp = st.text_input("String to derive (terminals may be written without blanks)",
                        value=SAMPLES.get(name, ""), key=f"gw_input_{name}")
    try:
        toks = [t for t, _ in tokenize_input(g, inp)]
    except CompileError as e:
        st.error(e.format(inp))
        toks = None
    if toks is not None:
        d = dv.derive(g, toks, max_trees=10)
        n = len(d.sequences)
        if n == 0:
            msg = f"`{' '.join(toks) or 'ε'}` is not in L(G)"
            (st.warning if d.complete else st.info)(
                msg + ("" if d.complete else " (the search stopped early)") + ".")
        elif n == 1 and d.complete:
            st.success("Exactly one parse tree: this string is unambiguous in this grammar.")
        else:
            st.error(f"{d.count_text.capitalize()} parse trees: the grammar is **ambiguous** "
                     "(one string, more than one tree).")
        shown = d.sequences[:2]
        cols = st.columns(len(shown)) if shown else []
        for k, (col, seq) in enumerate(zip(cols, shown), start=1):
            with col:
                tree = dv.tree_from_leftmost(g, seq)
                st.markdown(f"**Parse tree {k}**")
                st.graphviz_chart(to_dot(tree, attrs=False))
                st.markdown("Leftmost derivation")
                st.code(dv.derivation_text(g, seq, True).replace(" ⇒lm ", "\n⇒lm "),
                        language=None)
                st.markdown("Rightmost derivation")
                st.code(dv.derivation_text(g, dv.rightmost_sequence(tree), False)
                        .replace(" ⇒rm ", "\n⇒rm "), language=None)
        st.caption("Each leftmost derivation gives one parse tree, so two leftmost "
                   "derivations of one string prove the grammar ambiguous. The search "
                   f"explored {d.explored} sentential forms.")

# ------------------------------------------------------------------ language
with tabs[1]:
    n = st.slider("Longest string (number of terminals)", 0, 8, 4, key="gw_lang_len")
    lang = dv.language(g, n)
    st.markdown(f"**{len(lang.strings)} strings** of L(G) with at most {n} terminals"
                + ("" if lang.complete else " (search stopped early; the list may be "
                   "incomplete)") + ":")
    st.code("\n".join(" ".join(s) or "ε" for s in lang.strings) or "(none)", language=None)
    st.caption("Looking at the short strings helps to describe L(G) in words, e.g. "
               "'equal numbers of a and b' or 'balanced parentheses'.")

# ------------------------------------------------------------------ left recursion
with tabs[2]:
    if rec:
        st.warning("Left-recursive nonterminals: " + ", ".join(
            f"`{a}` ({' ⇒ '.join([c[0]] + [x + ' …' for x in c[1:]])})" for a, c in rec.items()))
    else:
        st.success("No left recursion (immediate or indirect).")
    mode = st.segmented_control(
        "Method", ["Algorithm 4.19 (general)", "Immediate only"],
        default="Algorithm 4.19 (general)", required=True, key="gw_lr_mode")
    fn = tf.remove_left_recursion if mode.startswith("Algorithm") else \
        tf.remove_immediate_left_recursion
    g2, steps = fn(g)
    st.markdown("**Steps**")
    st.code("\n".join(steps), language=None)
    st.markdown("**Result**")
    st.code(g2.to_text(), language=None)
    still = tf.left_recursive(g2)
    if still:
        st.error("Still left-recursive: " + ", ".join(still) + " (immediate removal does "
                 "not handle indirect recursion; use Algorithm 4.19).")

# ------------------------------------------------------------------ left factoring
with tabs[3]:
    g3, steps = tf.left_factor(g)
    st.markdown("**Steps** (Algorithm 4.21)")
    st.code("\n".join(steps), language=None)
    st.markdown("**Result**")
    st.code(g3.to_text(), language=None)
    t3 = build_ll1(g3)
    if g3 != g:
        st.caption("After left factoring the grammar is "
                   + ("LL(1)." if t3.is_ll1 else
                      f"still not LL(1): {len(t3.conflicts)} conflict(s), e.g. "
                      f"M[{t3.conflicts[0][0]}, {t3.conflicts[0][1]}]. Left factoring removes "
                      "common prefixes, not ambiguity (dangling-else stays ambiguous)."))

# ------------------------------------------------------------------ FIRST / FOLLOW
with tabs[4]:
    st.dataframe([{"Nonterminal": a, "FIRST": fmt_set(sets.first[a], g),
                   "FOLLOW": fmt_set(sets.follow[a], g),
                   "Nullable": "yes" if sets.nullable(a) else ""} for a in g.nonterminals],
                 hide_index=True, width="stretch")
    with st.expander(f"How the sets grow: FIRST took {len(sets.first_passes)} passes, "
                     f"FOLLOW {len(sets.follow_passes)} (the last pass changes nothing)"):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**FIRST**")
            st.dataframe([{"Pass": i + 1, **{a: fmt_set(p[a], g) for a in g.nonterminals}}
                          for i, p in enumerate(sets.first_passes)], hide_index=True)
        with c2:
            st.markdown("**FOLLOW**")
            st.dataframe([{"Pass": i + 1, **{a: fmt_set(p[a], g) for a in g.nonterminals}}
                          for i, p in enumerate(sets.follow_passes)], hide_index=True)
    st.caption("FOLLOW rules (4.4.2): $ ∈ FOLLOW(start); for A → αBβ, FIRST(β) − {ε} ⊆ "
               "FOLLOW(B); if β ⇒* ε, FOLLOW(A) ⊆ FOLLOW(B).")

# ------------------------------------------------------------------ LL(1)
with tabs[5]:
    st.markdown(ll1_table_html(table), unsafe_allow_html=True)
    if table.is_ll1:
        st.success("No multiply-defined entries: the grammar is LL(1).")
    else:
        st.error(f"{len(table.conflicts)} multiply-defined entr"
                 f"{'y' if len(table.conflicts) == 1 else 'ies'} (red): not LL(1).")
        for a, b, ps in table.conflicts:
            st.markdown(f"- M[`{a}`, `{b}`]: " + " · ".join(f"`{p}`" for p in ps))
        if rec:
            st.caption("A left-recursive grammar is never LL(1); see the Left recursion tab.")
    st.caption("Algorithm 4.31: A → α goes into M[A, a] for each a in FIRST(α); if ε ∈ "
               "FIRST(α), also into M[A, b] for each b in FOLLOW(A).")
