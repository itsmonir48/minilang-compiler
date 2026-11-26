"""Helpers shared by the Streamlit pages."""

import html
from pathlib import Path

import streamlit as st

from minilang.errors import CompileError
from minilang.tokens import Token, TokenType as T

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "examples"

CSS = """
<style>
.ml-code {font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 14px;
  line-height: 1.55; background: #f8f9fa; color: #212529; border: 1px solid #dee2e6;
  border-radius: 8px; padding: 12px 14px; white-space: pre; overflow-x: auto;}
.ml-code .ln {color: #adb5bd; user-select: none; display: inline-block; width: 2.5em;}
.tk-kw {color: #7048e8; font-weight: 600;}
.tk-id {color: #1864ab;}
.tk-num {color: #d9480f;}
.tk-op {color: #c2255c;}
.tk-punct {color: #495057;}
.tk-com {color: #868e96; font-style: italic;}
.tk-err {background: #ffe3e3; text-decoration: underline wavy #e03131;}
.tk-sel {outline: 2px solid #f08c00; border-radius: 3px; background: #fff3bf;}
.legend span {margin-right: 14px; font-size: 13px;}
.stTextArea textarea {font-family: ui-monospace, Menlo, Consolas, monospace !important; font-size: 14px !important;}
.buf {border-collapse: collapse; font-family: ui-monospace, Menlo, Consolas, monospace;}
.buf td {border: 1px solid #ced4da; min-width: 24px; height: 28px; text-align: center;
  font-size: 13px; color: #212529; background: #fff;}
.buf td.sent {background: #343a40; color: #fff; font-size: 10px;}
.buf td.lex {background: #fff3bf; font-weight: 700;}
.buf td.empty {background: #f1f3f5; color: #adb5bd;}
.buf tr.idx td {border: none; font-size: 10px; color: #868e96; height: 14px; background: transparent;}
.buf tr.ptr td {border: none; font-size: 11px; color: #d9480f; font-weight: 700; background: transparent;}
.tr-line {display: block;}
.tr-match {color: #2b8a3e;}
.tr-fail {color: #c92a2a;}
.tr-back {color: #e8590c;}
.tr-acc {color: #2b8a3e; font-weight: 700;}
.tr-future {color: #ced4da;}
.tr-cur {outline: 2px solid #f08c00; border-radius: 3px; background: #fff3bf;}
table.ll1 {border-collapse: collapse; font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 13px;}
table.ll1 th, table.ll1 td {border: 1px solid #dee2e6; padding: 4px 8px; text-align: left; color: #212529;}
table.ll1 th {background: #f1f3f5;}
table.ll1 td.conflict {background: #ffe3e3; color: #c92a2a; font-weight: 600;}
table.ll1 td.hit {background: #fff3bf; outline: 2px solid #f08c00;}
/* ---- layout and page chrome ---- */
.block-container {padding-top: 3.4rem; max-width: 1280px;}
.page-head {padding: 0 0 14px; margin: 0 0 18px; border-bottom: 1px solid #e2e7ef;}
.page-head .eyebrow {font-size: 12px; font-weight: 700; letter-spacing: .13em;
  text-transform: uppercase; color: #2b5fb3;}
.page-head .ph-title {font-size: 2.05rem; font-weight: 700; color: #0f1f3d;
  line-height: 1.2; margin: 4px 0 6px; letter-spacing: -0.01em;}
.page-head .ph-desc {color: #5b6474; font-size: 1rem; margin: 0 0 10px; max-width: 900px;}
.chip {display: inline-block; padding: 2px 10px; margin: 0 6px 4px 0; border-radius: 999px;
  background: #eef3fb; color: #2b5fb3; border: 1px solid #d6e2f5; font-size: 12px;
  font-weight: 600;}
.hero {background: linear-gradient(120deg, #0f1f3d 0%, #1d3a70 60%, #2b5fb3 100%);
  border-radius: 14px; padding: 30px 34px 26px; color: #e8eef8; margin-bottom: 18px;}
.hero .eyebrow {font-size: 12px; font-weight: 700; letter-spacing: .15em;
  text-transform: uppercase; color: #8cb4ff;}
.hero .h-title {font-size: 2.5rem; font-weight: 750; color: #ffffff; margin: 6px 0 8px;
  letter-spacing: -0.015em; line-height: 1.15;}
.hero .h-text {font-size: 1.05rem; color: #c9d6ea; max-width: 820px; margin: 0 0 18px;
  line-height: 1.55;}
.hero .stats {display: flex; gap: 34px; flex-wrap: wrap; border-top: 1px solid #34507f;
  padding-top: 14px;}
.hero .stat .v {font-size: 1.6rem; font-weight: 700; color: #ffffff; line-height: 1.1;}
.hero .stat .l {font-size: 12px; color: #9fb3d4; text-transform: uppercase;
  letter-spacing: .08em;}
.card-tag {font-size: 11px; font-weight: 700; letter-spacing: .1em; text-transform: uppercase;
  color: #2b5fb3;}
.card-title {font-size: 1.12rem; font-weight: 700; color: #0f1f3d; margin: 2px 0 4px;}
.card-text {font-size: 0.92rem; color: #5b6474; min-height: 4.2em; line-height: 1.5;}
.section-title {font-size: 1.15rem; font-weight: 700; color: #0f1f3d; margin: 8px 0 2px;}
.section-sub {font-size: 0.92rem; color: #5b6474; margin-bottom: 10px;}
.buf tr.half td {border: none; font-size: 11px; color: #495057; background: transparent;}
</style>
"""

KEYWORD_TYPES = {T.INT, T.FLOAT, T.IF, T.ELSE, T.WHILE, T.PRINT}
OP_TYPES = {T.RELOP, T.PLUS, T.MINUS, T.STAR, T.SLASH, T.ASSIGN, T.AND, T.OR, T.NOT}


LOGO = Path(__file__).resolve().parent / "static" / "logo.svg"


def setup_page(title: str) -> None:
    st.set_page_config(page_title=f"{title} · MiniLang Compiler Studio",
                       page_icon=":material/terminal:", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)


def page_header(eyebrow: str, title: str, description: str,
                chips: list[str] | None = None) -> None:
    """The same header on every page: chapter label, title, one-line description and the
    textbook sections the page covers."""
    chip_html = "".join(f'<span class="chip">{html.escape(c)}</span>' for c in chips or [])
    st.markdown(
        f'<div class="page-head"><div class="eyebrow">{html.escape(eyebrow)}</div>'
        f'<div class="ph-title">{html.escape(title)}</div>'
        f'<div class="ph-desc">{html.escape(description)}</div>{chip_html}</div>',
        unsafe_allow_html=True)


def example_names() -> list[str]:
    return sorted(p.stem for p in EXAMPLES.glob("*.mini"))


def source_editor(key: str, default: str = "factorial", height: int = 300) -> str:
    """Example picker + editable text area. Returns the current source text."""
    names = example_names()
    choice = st.selectbox(
        "Load an example", names, index=names.index(default) if default in names else 0,
        key=f"{key}_example",
    )
    if st.session_state.get(f"{key}_loaded") != choice:
        st.session_state[f"{key}_src"] = (EXAMPLES / f"{choice}.mini").read_text()
        st.session_state[f"{key}_loaded"] = choice
    return st.text_area("Source code (edit freely)", key=f"{key}_src", height=height)


def token_class(tok: Token) -> str:
    if tok.type in KEYWORD_TYPES:
        return "tk-kw"
    if tok.type is T.ID:
        return "tk-id"
    if tok.type in (T.NUM, T.REAL):
        return "tk-num"
    if tok.type in OP_TYPES:
        return "tk-op"
    return "tk-punct"


def _offsets(source: str) -> list[int]:
    starts = [0]
    for i, c in enumerate(source):
        if c == "\n":
            starts.append(i + 1)
    return starts


def highlight_html(source: str, tokens: list[Token], errors: list[CompileError],
                   selected: int | None = None) -> str:
    """Source with tokens coloured, errors underlined and one token outlined."""
    starts = _offsets(source)
    classes: list[list[str]] = [[] for _ in source]

    def mark(line: int, col: int, length: int, cls: str) -> None:
        if line < 1 or line > len(starts):
            return
        begin = starts[line - 1] + col - 1
        for i in range(begin, min(begin + max(length, 1), len(source))):
            classes[i].append(cls)

    # everything that is not a token or whitespace is a comment or an error
    covered = [False] * len(source)
    for i, tok in enumerate(tokens):
        if tok.type is T.EOF:
            continue
        mark(tok.line, tok.col, len(tok.lexeme), token_class(tok))
        if i == selected:
            mark(tok.line, tok.col, len(tok.lexeme), "tk-sel")
        b = starts[tok.line - 1] + tok.col - 1
        for j in range(b, min(b + len(tok.lexeme), len(source))):
            covered[j] = True
    for e in errors:
        length = 1
        if "malformed number" in e.message:
            length = len(e.message.split("'")[1])
        mark(e.line, e.col, length, "tk-err")
        if 0 < e.line <= len(starts):
            b = starts[e.line - 1] + e.col - 1
            for j in range(b, min(b + length, len(source))):
                covered[j] = True
    for i, c in enumerate(source):
        if not covered[i] and not c.isspace():
            classes[i].append("tk-com")

    out, line_no = [], 1
    out.append(f'<span class="ln">{line_no}</span>')
    run_cls, run_text = None, []

    def flush() -> None:
        if run_text:
            text = html.escape("".join(run_text))
            out.append(f'<span class="{run_cls}">{text}</span>' if run_cls else text)
            run_text.clear()

    for i, c in enumerate(source):
        if c == "\n":
            flush()
            run_cls = None
            line_no += 1
            out.append(f'\n<span class="ln">{line_no}</span>')
            continue
        cls = " ".join(classes[i]) or None
        if cls != run_cls:
            flush()
            run_cls = cls
        run_text.append(c)
    flush()
    return f'<div class="ml-code">{"".join(out)}</div>'


LEGEND = (
    '<div class="legend"><span class="tk-kw">keyword</span><span class="tk-id">identifier</span>'
    '<span class="tk-num">number</span><span class="tk-op">operator</span>'
    '<span class="tk-punct">punctuation</span><span class="tk-com">comment</span>'
    '<span class="tk-err">error</span></div>'
)


def show_char(c: str) -> str:
    return {" ": "␣", "\n": "↵", "\t": "⇥", "\r": "␍"}.get(c, c)


def buffer_html(snap: dict, valid: list[bool]) -> str:
    """Draw the buffer pair: half 0 above half 1, each ending in its eof sentinel."""
    n, buf = snap["n"], snap["buf"]
    lb, fw = snap["lexeme_begin"], snap["forward"]
    size = 2 * n + 2

    # cells of the lexeme: walk from lexeme_begin to forward like BufferPair.lexeme()
    lexeme_cells, j = set(), lb
    while j != fw and len(lexeme_cells) < size:
        if j not in (n, 2 * n + 1):
            lexeme_cells.add(j)
        j = (j + 1) % size

    def row(first: int, half: int) -> str:
        cells, idx, ptr = [], [], []
        for i in range(first, first + n + 1):
            if i in (n, 2 * n + 1):
                cells.append('<td class="sent">eof</td>')
            elif not valid[i]:
                cells.append('<td class="empty">·</td>')
            else:
                cls = ' class="lex"' if i in lexeme_cells else ""
                cells.append(f"<td{cls}>{html.escape(show_char(buf[i]))}</td>")
            idx.append(f"<td>{i}</td>")
            marks = [m for m, at in (("lb", lb), ("fwd", fw)) if at == i]
            ptr.append(f"<td>{'↑' + '/'.join(marks) if marks else ''}</td>")
        title = f"half {half} · chunk {snap['half_chunk'][half]}"
        return (f'<tr class="half"><td colspan="{n + 1}" style="text-align:left">{title}</td></tr>'
                f'<tr>{"".join(cells)}</tr><tr class="idx">{"".join(idx)}</tr>'
                f'<tr class="ptr">{"".join(ptr)}</tr>')

    return (f'<div style="overflow-x:auto"><table class="buf">{row(0, 0)}'
            f'<tr class="idx"><td colspan="{n + 1}">&nbsp;</td></tr>{row(n + 1, 1)}</table></div>')


def valid_cells(snap: dict) -> list[bool]:
    """Cells that hold real data: everything before the first sentinel of each half."""
    n, buf = snap["n"], snap["buf"]
    valid = [False] * (2 * n + 2)
    for start in (0, n + 1):
        for i in range(start, start + n):
            if buf[i] == "\0":
                break
            valid[i] = True
    return valid


def errors_block(errors: list[CompileError], source: str) -> None:
    if not errors:
        st.success("No errors.")
        return
    st.error(f"{len(errors)} error(s)")
    st.code("\n".join(e.format(source) for e in errors), language=None)


# ----------------------------------------------------------------------------- grammars

def grammar_editor(key: str, default: str = "expr"):
    """Grammar picker + editable text. Returns (name, text, Grammar or None)."""
    from minilang.grammar.grammar import (Grammar, grammar_comment, grammar_names,
                                          grammar_path)

    names = grammar_names()
    choice = st.selectbox("Load a grammar", names,
                          index=names.index(default) if default in names else 0,
                          key=f"{key}_grammar")
    if st.session_state.get(f"{key}_gloaded") != choice:
        body = [ln for ln in grammar_path(choice).read_text().splitlines()
                if not ln.startswith("#")]
        st.session_state[f"{key}_gtext"] = "\n".join(body).strip() + "\n"
        st.session_state[f"{key}_gloaded"] = choice
    st.caption(grammar_comment(choice))
    text = st.text_area("Grammar (edit freely; `->`, `|`, `ε` or `eps`)", key=f"{key}_gtext",
                        height=170)
    try:
        return choice, text, Grammar.parse(text)
    except CompileError as e:
        st.error(e.format(text))
        return choice, text, None


TRACE_CLASS = {"match": "tr-match", "fail": "tr-fail", "error": "tr-fail",
               "backtrack": "tr-back", "accept": "tr-acc"}


def trace_html(lines: list[str], kinds: list[str], current: int, before: int = 14,
               after: int = 8) -> str:
    """A window of trace lines around `current`; future lines are faded."""
    lo = max(0, current - before)
    hi = min(len(lines), current + after + 1)
    out = []
    if lo > 0:
        out.append(f'<span class="tr-line tr-future">… {lo} earlier steps</span>')
    for i in range(lo, hi):
        cls = ["tr-line"]
        if i > current:
            cls.append("tr-future")
        else:
            cls.append(TRACE_CLASS.get(kinds[i], ""))
        if i == current:
            cls.append("tr-cur")
        out.append(f'<span class="{" ".join(cls)}">{html.escape(lines[i])}</span>')
    if hi < len(lines):
        out.append(f'<span class="tr-line tr-future">… {len(lines) - hi} more steps</span>')
    return ('<div class="ml-code" style="white-space: pre; font-size: 12.5px;">'
            + "".join(out) + "</div>")


def ll1_table_html(t, hit: tuple[str, str] | None = None) -> str:
    """LL(1) table M[A, a]; multiply-defined entries in red, `hit` outlined."""
    cols = t.columns()
    head = "".join(f"<th>{html.escape(c)}</th>" for c in cols)
    rows = []
    for a in t.grammar.nonterminals:
        cells = []
        for c in cols:
            ps = t.entry(a, c)
            text = "<br>".join(html.escape(str(p)) for p in ps)
            cls = "conflict" if len(ps) > 1 else ""
            if hit == (a, c):
                cls += " hit"
            cells.append(f'<td class="{cls.strip()}">{text}</td>')
        rows.append(f"<tr><th>{html.escape(a)}</th>{''.join(cells)}</tr>")
    return (f'<table class="ll1"><tr><th>M</th>{head}</tr>{"".join(rows)}</table>')
