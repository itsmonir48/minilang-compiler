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
.buf tr.half td {border: none; font-size: 11px; color: #495057; background: transparent;}
</style>
"""

KEYWORD_TYPES = {T.INT, T.FLOAT, T.IF, T.ELSE, T.WHILE, T.PRINT}
OP_TYPES = {T.RELOP, T.PLUS, T.MINUS, T.STAR, T.SLASH, T.ASSIGN, T.AND, T.OR, T.NOT}


def setup_page(title: str) -> None:
    st.set_page_config(page_title=f"{title} · MiniLang", page_icon="🛠️", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)


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
