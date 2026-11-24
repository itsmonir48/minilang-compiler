"""Specification of tokens page (Chapter 3.3)."""

import streamlit as st

from minilang import regex_tools as rt
from ui_common import setup_page

setup_page("Strings & Regex")
st.title("Strings and Regular Definitions")
st.caption("Chapter 3.3 · prefixes, suffixes, substrings, subsequences · regular definitions "
           "from the lab sheet")

tab_strings, tab_regex = st.tabs(["String terms", "Regular definitions"])

with tab_strings:
    s = st.text_input("String s", value="banana", max_chars=16)
    show = lambda items: ", ".join(f"`{x}`" if x else "ε" for x in items)  # noqa: E731
    st.markdown(f"**Prefixes:** {show(rt.prefixes(s))}")
    st.markdown(f"**Suffixes:** {show(rt.suffixes(s))}")
    st.markdown(f"**Proper prefixes:** {show(rt.proper_prefixes(s))}")
    st.markdown(f"**Proper suffixes:** {show(rt.proper_suffixes(s))}")
    st.markdown(f"**Substrings:** {show(sorted(rt.substrings(s), key=lambda x: (len(x), x)))}")
    if len(s) <= 12:
        subs = sorted(rt.subsequences(s), key=lambda x: (len(x), x))
        st.markdown(f"**Subsequences:** {show(subs)}")
    else:
        st.caption("Subsequences are listed only for strings of up to 12 characters.")
    actual, formula = rt.string_report(s), rt.count_formulas(len(s))
    st.subheader("Counts")
    st.dataframe(
        [{"Kind": k, "Count for s": actual[k], f"Formula for n = {len(s)} (distinct chars)": formula[k]}
         for k in actual], hide_index=True)
    if len(set(s)) < len(s):
        st.info("s has repeated characters, so some substrings and subsequences coincide and "
                "the counts are below the formula.")

with tab_regex:
    names = [d.name for d in rt.DEFINITIONS]
    labels = {d.name: d.description for d in rt.DEFINITIONS}
    name = st.selectbox("Definition", names, format_func=lambda n: labels[n])
    d = rt.BY_NAME[name]
    if d.pattern:
        st.code(d.pattern, language=None)
    else:
        st.markdown("_Checked by a function, not a written-out expression._")
    if d.note:
        st.caption(d.note)
    samples = {
        "vowels": "facetious\nabstemious\neducation\naeiou",
        "ascending": "abc\nalmost\nba",
        "comment": "/* ok */\n/* a */ b */\n/***/",
        "no_repeat_digit": "1234\n1231",
        "one_repeat_digit": "1121\n1122",
        "no_abb": "abab\nabba\nbbaa",
        "no_abb_subseq": "baab\nabab\nbbba",
        "chess": "p-k4\nkbp*qn\np-k9",
        "sql_select": "select\nSeLeCt\nselects",
    }
    text = st.text_area("Strings to test (one per line)", value=samples.get(name, ""),
                        key=f"regex_{name}")
    rows = [{"String": line, "Match": "✅ yes" if d.check(line) else "❌ no"}
            for line in text.splitlines()]
    if rows:
        st.dataframe(rows, hide_index=True, width="stretch")
