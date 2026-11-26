"""MiniLang Compiler Studio.  Run:  minilang ui   (or: streamlit run app/Home.py)

This entry script only sets up the navigation (pages grouped by textbook chapter) and
the logo; the home page itself is overview.py.
"""

import streamlit as st

from ui_common import LOGO

PAGES = {
    "Overview": [
        st.Page("overview.py", title="Home", icon=":material/dashboard:", default=True),
    ],
    "Chapter 3 · Lexical analysis": [
        st.Page("pages/1_Lexer.py", title="Lexer", icon=":material/data_object:",
                url_path="lexer"),
        st.Page("pages/2_Strings_and_Regex.py", title="Strings & Regex",
                icon=":material/text_fields:", url_path="strings-regex"),
    ],
    "Chapter 2 · Translation": [
        st.Page("pages/3_Translators.py", title="Translators", icon=":material/swap_horiz:",
                url_path="translators"),
        st.Page("pages/6_Parse_Tree.py", title="Parse Tree", icon=":material/account_tree:",
                url_path="parse-tree"),
    ],
    "Chapter 4 · Syntax analysis": [
        st.Page("pages/4_Grammar_Workbench.py", title="Grammar Workbench",
                icon=":material/schema:", url_path="grammar-workbench"),
        st.Page("pages/5_Top_Down_Parsing.py", title="Top-Down Parsing",
                icon=":material/south:", url_path="top-down"),
    ],
}

st.logo(str(LOGO), size="large")
st.navigation(PAGES).run()
