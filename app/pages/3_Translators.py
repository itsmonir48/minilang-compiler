"""Syntax-directed translators page (Chapter 2.2, 2.3, 2.5)."""

import html

import streamlit as st

from minilang import translators as tr
from minilang.errors import CompileError
from minilang.tree import to_dot
from ui_common import setup_page

setup_page("Translators")
st.title("Syntax-Directed Translators")
st.caption("Chapter 2 · grammars and parse trees (2.2) · translation schemes and annotated "
           "parse trees (2.3) · the infix → postfix translator (2.5)")


def show_error(e: CompileError, text: str) -> None:
    st.error(e.message)
    st.code(e.format(text), language=None)


def tree_chart(node, attrs: bool = True) -> None:
    st.graphviz_chart(to_dot(node, attrs=attrs))


def scheme_block(lines: list[str], title: str = "Translation scheme") -> None:
    with st.expander(title):
        st.code("\n".join(lines), language=None)


def trace_html(trace: list[tr.TraceStep], current: int) -> str:
    rows = []
    for i, step in enumerate(trace):
        text = html.escape("  " * step.depth + step.action)
        if i == current:
            rows.append(f'<span class="tk-sel">{text}</span>')
        elif i > current:
            rows.append(f'<span class="tk-com">{text}</span>')
        elif step.action.startswith("print"):
            rows.append(f'<span class="tk-num">{text}</span>')
        else:
            rows.append(text)
    return '<div class="ml-code">' + "\n".join(rows) + "</div>"


tab_expr, tab_roman, tab_grammars = st.tabs(
    ["Infix · postfix · prefix", "Roman numerals", "Grammar checkers"])

# --------------------------------------------------------------------------- expressions
EXPR_DEFAULTS = {"infix": "9-5+2", "postfix": "95-2+", "prefix": "+-952"}

with tab_expr:
    c1, c2 = st.columns([1, 2], gap="large")
    with c1:
        notation = st.segmented_control(
            "Input notation", list(EXPR_DEFAULTS), default="infix", required=True,
            key="tr_notation")
        text = st.text_input("Expression", value=EXPR_DEFAULTS[notation],
                             key=f"tr_expr_{notation}")
        st.caption("Operators `+ - * /`, identifiers and numbers. In postfix and prefix, "
                   "unary minus is written `~`. Without blanks, postfix and prefix are read "
                   "one character per token (`95-2+`); with blanks, `12 3 +` works.")
        show_attrs = st.toggle("Show attributes in the tree", value=True, key="tr_attrs")
    try:
        t = tr.translate(text, notation)
    except CompileError as e:
        with c2:
            show_error(e, text)
        t = None
    if t is not None:
        with c2:
            value = t.value if t.value is not None else f"– ({t.value_note})"
            st.code(f"infix   : {t.infix}\npostfix : {t.postfix}\nprefix  : {t.prefix}\n"
                    f"value   : {value}", language=None)
            scheme_block(tr.SCHEMES[notation])
        st.subheader("Annotated parse tree")
        st.caption({
            "infix": "Grammar of 2.5 with * / ( ) and unary signs. Each node carries its "
                     "synthesized attributes post (postfix), pre (prefix) and val.",
            "postfix": "Grammar E → E E op | E ~ | id | num. Attributes: in (infix), "
                       "pre (prefix), val.",
            "prefix": "Grammar E → op E E | ~ E | id | num. Attributes: in (infix), "
                      "post (postfix), val.",
        }[notation])
        tree_chart(t.tree, show_attrs)

        if t.trace:
            st.subheader("▶ Step through the 2.5 translator")
            st.caption("expr(), term() and factor() are called recursively. The print "
                       "actions write the postfix output one symbol at a time.")
            k = st.slider("Step", 1, len(t.trace), len(t.trace), key="tr_step") - 1
            s1, s2 = st.columns([1.3, 1], gap="large")
            with s1:
                st.markdown(trace_html(t.trace, k), unsafe_allow_html=True)
            with s2:
                st.markdown(f"**Step {k + 1} of {len(t.trace)}:** `{t.trace[k].action}`")
                st.markdown("**Output so far**")
                st.code(t.trace[k].output or " ", language=None)

# --------------------------------------------------------------------------- roman
with tab_roman:
    r1, r2 = st.columns(2, gap="large")
    with r1:
        st.subheader("Roman → integer")
        roman = st.text_input("Roman numeral", value="MCMXCIV", key="tr_roman")
        try:
            value, tree = tr.roman_to_int(roman)
            st.success(f"{roman.strip().upper()} = **{value}**")
            tree_chart(tree)
        except CompileError as e:
            show_error(e, roman)
        scheme_block(tr.ROMAN_GRAMMAR, "Grammar with semantic rules")
    with r2:
        st.subheader("Integer → Roman")
        n = st.number_input("Integer (1 to 3999)", min_value=1, max_value=3999, value=2026,
                            key="tr_int")
        result, tree = tr.int_to_roman(int(n))
        st.success(f"{int(n)} = **{result}**")
        tree_chart(tree)
        scheme_block(tr.INT_TO_ROMAN_SCHEME)

# --------------------------------------------------------------------------- grammars
CHECKERS = {
    "div3": "Binary numbers divisible by 3",
    "brackets": "Balanced brackets",
    "lists": "Left- vs right-associative lists",
}

with tab_grammars:
    which = st.segmented_control("Grammar", list(CHECKERS), format_func=CHECKERS.get,
                                 default="div3", required=True, key="tr_grammar")

    if which == "div3":
        st.code(tr.DIV3_GRAMMAR, language=None)
        g1, g2 = st.columns([1, 1.2], gap="large")
        with g1:
            bits = st.text_input("Binary string", value="110011", key="tr_div3")
            tree = tr.div3_tree(bits)
            if tree is None:
                st.warning(f"`{bits}` is not in L(G)."
                           + (f" (Its value {int(bits, 2)} is "
                              f"{'' if int(bits, 2) % 3 == 0 else 'not '}divisible by 3.)"
                              if bits and set(bits) <= {'0', '1'} else ""))
            else:
                st.success(f"`{bits}` is in L(G); value {int(bits, 2)} = 3 × "
                           f"{int(bits, 2) // 3}")
                tree_chart(tree)
        with g2:
            st.markdown(
                "**Why every string of L(G) is divisible by 3** (induction on the parse "
                "tree): `11` = 3 and `1001` = 9; `num 0` doubles the value; "
                "`num₁ num₂` has value num₁ · 2^|num₂| + num₂. Each rule keeps "
                "\"multiple of 3\", so every node of the tree is a multiple of 3, which is "
                "what the `val mod 3` attribute shows.")
            max_len = st.slider("Check every binary string up to length", 1, 10, 6,
                                key="tr_div3_len")
            rows = tr.div3_table(max_len)
            members = [r for r in rows if r["in L(G)"]]
            m1, m2, m3 = st.columns(3)
            m1.metric("Strings", len(rows))
            m2.metric("In L(G)", len(members))
            m3.metric("In L(G), not divisible", sum(not r["divisible by 3"] for r in members))
            missed = [r for r in rows if r["divisible by 3"] and not r["in L(G)"]]
            no_lead = [r for r in missed if r["string"][0] == "1"]
            st.caption(
                f"Divisible by 3 but not in L(G): {len(missed)} strings, so the grammar does "
                f"not generate every multiple of 3. {len(missed) - len(no_lead)} of them start "
                f"with 0 (no string of L(G) does); the others: "
                + (", ".join(f"`{r['string']}` ({r['value']})" for r in no_lead[:6])
                   or "none at this length"))
            only_members = st.toggle("Show only strings in L(G)", value=True,
                                     key="tr_div3_only")
            shown = members if only_members else rows
            st.dataframe(shown, hide_index=True, width="stretch", height=260)

    elif which == "brackets":
        st.code(tr.BRACKETS_GRAMMAR, language=None)
        text = st.text_input("Brackets", value="([]){()}", key="tr_brackets")
        try:
            tree = tr.brackets_tree(text)
            st.success(f"Balanced. Deepest nesting: {tree.attrs['depth']} "
                       "(attribute S.depth = max(S₁.depth + 1, S₂.depth)).")
            tree_chart(tree)
        except CompileError as e:
            show_error(e, text)

    else:
        text = st.text_input("Identifiers separated by commas", value="a, b, c",
                             key="tr_list")
        st.caption("Both grammars generate the same strings, but the trees lean opposite "
                   "ways: the left-recursive one groups (a, b), c and the right-recursive "
                   "one groups a, (b, c), just like left- and right-associative operators.")
        l1, l2 = st.columns(2, gap="large")
        for col, assoc in ((l1, "left"), (l2, "right")):
            with col:
                st.code(tr.LIST_GRAMMARS[assoc], language=None)
                try:
                    tree_chart(tr.comma_list_tree(text, assoc), attrs=False)
                except CompileError as e:
                    show_error(e, text)
