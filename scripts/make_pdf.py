"""Render a Markdown document of docs/ (e.g. PROJECT_PROPOSAL.md) to PDF.

Markdown -> HTML (python-markdown) -> PDF (headless Google Chrome, via the DevTools
protocol, so the footer can carry page numbers).

usage: .venv/bin/python scripts/make_pdf.py [--toc] [--style proposal] [input.md] [output.pdf]
  --toc              add a contents list after the first horizontal rule
  --style proposal   formal layout: header block, numbered sections, outcome cards
  default input: docs/PROJECT_PROPOSAL.md; default output: the same name with .pdf
"""

import asyncio
import base64
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import markdown
import websockets

ROOT = Path(__file__).resolve().parent.parent
REPO = "https://github.com/itsmonir48/minilang-compiler/blob/main"

CSS = """
@page { size: A4; margin: 18mm 17mm 20mm 17mm; }
body { font-family: "Noto Sans", "DejaVu Sans", sans-serif; font-size: 10.3pt;
       line-height: 1.45; color: #1f2328; }
h1 { font-size: 21pt; margin: 0 0 6pt; color: #0b3d91; }
h2 { font-size: 14.5pt; margin: 20pt 0 6pt; padding-bottom: 3pt; color: #0b3d91;
     border-bottom: 1.5px solid #c9d6ea; break-after: avoid; }
h3 { font-size: 12pt; margin: 14pt 0 4pt; color: #1f2328; break-after: avoid; }
p { margin: 4pt 0 6pt; }
ul, ol { margin: 3pt 0 6pt; padding-left: 18pt; }
li { margin: 1.5pt 0; }
a { color: #0b5cad; text-decoration: none; }
code { font-family: "Noto Sans Mono", "DejaVu Sans Mono", monospace; font-size: 8.9pt;
       background: #f2f4f7; padding: 0.5pt 3pt; border-radius: 3px; }
pre { background: #f6f8fa; border: 1px solid #dde2e8; border-radius: 5px;
      padding: 7pt 9pt; font-size: 8.6pt; line-height: 1.35; white-space: pre-wrap;
      break-inside: avoid; }
pre code { background: none; padding: 0; font-size: inherit; }
table { border-collapse: collapse; width: 100%; margin: 6pt 0 10pt; font-size: 9pt;
        break-inside: auto; }
th, td { border: 1px solid #d0d7de; padding: 3.5pt 6pt; text-align: left;
         vertical-align: top; }
th { background: #eaf0f8; }
tr { break-inside: avoid; }
tr:nth-child(even) td { background: #fafbfc; }
hr { border: none; border-top: 1px solid #d0d7de; margin: 12pt 0; }
strong { color: #111; }
.toc { border: 1px solid #dde2e8; border-radius: 5px; padding: 6pt 12pt;
       background: #fbfcfe; margin: 8pt 0 12pt; columns: 2; font-size: 9.5pt; }
.toc strong { display: block; column-span: all; margin-bottom: 3pt; }
.toc ul { margin: 0; padding-left: 0; list-style: none; }
.toc li { margin: 1pt 0; }
/* viva questions: keep each question with its answer */
h2#13-likely-viva-questions ~ p strong:only-child { color: #0b3d91; }
"""


PROPOSAL_CSS = """
@page { size: A4; margin: 15mm 18mm 17mm 18mm; }
:root { --navy: #14274e; --accent: #2b6cb0; --ink: #23272f; --muted: #5b6474;
        --line: #d9dee7; --tint: #f3f6fb; }
body { font-family: "Noto Serif", "Liberation Serif", serif; font-size: 9.6pt;
       line-height: 1.5; color: var(--ink); margin: 0; }
p { margin: 0 0 5pt; text-align: justify; hyphens: auto; }
em { color: var(--ink); }
code { font-family: "Liberation Mono", "DejaVu Sans Mono", monospace; font-size: 8.3pt;
       color: var(--navy); background: var(--tint); padding: 0 2.5pt; border-radius: 2px; }
strong { font-family: "Inter", sans-serif; font-weight: 600; color: var(--navy); }

/* header block (not a cover page) */
.doc-head { border-bottom: 2.5px solid var(--navy); padding-bottom: 8pt; margin-bottom: 4pt; }
.doc-head .eyebrow { font-family: "Inter", sans-serif; font-size: 8pt; font-weight: 600;
       letter-spacing: 0.22em; text-transform: uppercase; color: var(--accent); }
.doc-head h1 { font-family: "Inter Display", "Inter", sans-serif; font-size: 23pt;
       font-weight: 700; color: var(--navy); margin: 2pt 0 3pt; letter-spacing: -0.01em; }
.doc-head .subtitle { font-style: italic; color: var(--muted); font-size: 10.2pt; margin: 0;
       text-align: left; hyphens: none; }
.doc-head + .rule { border-top: 0.6px solid var(--line); margin: 0 0 6pt; }

/* section headings: number + title */
h2 { font-family: "Inter", sans-serif; font-size: 10.5pt; font-weight: 700;
     text-transform: uppercase; letter-spacing: 0.08em; color: var(--navy);
     margin: 13pt 0 5pt; padding-bottom: 3pt; border-bottom: 0.8px solid var(--line);
     break-after: avoid; display: flex; align-items: baseline; gap: 8pt; }
h2 .num { color: var(--accent); font-size: 10.5pt; min-width: 15pt; }

/* lists */
ul { margin: 2pt 0 5pt; padding-left: 14pt; }
ul li::marker { color: var(--accent); }
ol { list-style: none; counter-reset: item; margin: 2pt 0 5pt; padding-left: 0; }
ol > li { counter-increment: item; position: relative; padding-left: 21pt; margin: 3pt 0; }
ol > li::before { content: counter(item); position: absolute; left: 0; top: 0.5pt;
       width: 13pt; height: 13pt; border-radius: 50%; background: var(--navy); color: #fff;
       font-family: "Inter", sans-serif; font-size: 7.5pt; font-weight: 600;
       display: flex; align-items: center; justify-content: center; }

/* tables */
table { border-collapse: collapse; width: 100%; margin: 4pt 0 7pt;
        font-family: "Inter", sans-serif; font-size: 8.2pt; line-height: 1.35; }
th { background: var(--navy); color: #fff; font-weight: 600; text-align: left;
     padding: 4pt 7pt; letter-spacing: 0.02em; }
td { padding: 3.6pt 7pt; border-bottom: 0.6px solid var(--line); vertical-align: top; }
tr:nth-child(even) td { background: var(--tint); }
td:first-child { font-weight: 600; color: var(--navy); }
tr { break-inside: avoid; }
td code { font-size: 7.8pt; }

/* expected outcomes as cards */
.cards { display: grid; grid-template-columns: 1fr 1fr; gap: 7pt; list-style: none;
         padding: 0; margin: 4pt 0 0; }
.cards li { background: var(--tint); border-left: 3px solid var(--accent);
            border-radius: 3px; padding: 6pt 9pt; margin: 0; text-align: left;
            break-inside: avoid; }
.cards li strong { display: block; font-size: 8.6pt; letter-spacing: 0.04em;
            text-transform: uppercase; margin-bottom: 2pt; }
"""

PROPOSAL_FOOTER = ("<div style='width:100%; margin:0 18mm; padding-top:4px; "
                   "border-top:0.6px solid #d9dee7; display:flex; "
                   "justify-content:space-between; font-family:Inter, sans-serif; "
                   "font-size:7.5px; color:#5b6474; letter-spacing:0.03em;'>"
                   "<span>{title}</span><span>Page <span class='pageNumber'></span> of "
                   "<span class='totalPages'></span></span></div>")


def proposal_layout(body: str) -> str:
    """Header block from the h1 (and an italic subtitle right after it), numbered
    section headings, and the 'Expected outcomes' list as cards."""
    m = re.search(r"<h1[^>]*>(.*?)</h1>\s*(<p><em>(.*?)</em></p>)?", body, re.S)
    if m:
        title = m.group(1)
        eyebrow, _, main = title.partition(":")
        if not main:
            eyebrow, main = "", title
        sub = f'<p class="subtitle">{m.group(3)}</p>' if m.group(3) else ""
        head = (f'<header class="doc-head"><div class="eyebrow">{eyebrow.strip()}</div>'
                f'<h1>{main.strip()}</h1>{sub}</header>')
        body = body[:m.start()] + head + body[m.end():]
    body = re.sub(r"<h2([^>]*)>(\d+)\.\s*(.*?)</h2>",
                  lambda k: f'<h2{k.group(1)}><span class="num">{int(k.group(2)):02d}</span>'
                            f"<span>{k.group(3)}</span></h2>", body)
    body = re.sub(r'(<h2[^>]*>(?:(?!</h2>).)*Expected outcomes(?:(?!</h2>).)*</h2>\s*)<ul>',
                  r'\1<ul class="cards">', body, flags=re.S)
    # card titles: drop the trailing colon of "**Label:**"
    body = re.sub(r'(<ul class="cards">.*?</ul>)',
                  lambda k: re.sub(r"<strong>(.*?):</strong>", r"<strong>\1</strong>",
                                   k.group(1)), body, flags=re.S)
    return body


def fix_links(md_text: str) -> str:
    """Relative links to repository files become GitHub links (they work in a PDF)."""
    def repl(m: re.Match) -> str:
        label, target = m.group(1), m.group(2)
        if target.startswith(("http", "#", "mailto:")):
            return m.group(0)
        path = (ROOT / "docs" / target).resolve().relative_to(ROOT)
        return f"[{label}]({REPO}/{path.as_posix()})"

    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", repl, md_text)


def widen_indents(md_text: str) -> str:
    """GitHub accepts 2-space nested lists; python-markdown needs 4. Double the leading
    spaces of indented lines outside fenced code blocks."""
    out, fence = [], False
    for line in md_text.splitlines():
        stripped = line.lstrip(" ")
        indent = len(line) - len(stripped)
        if stripped.startswith("```"):
            out.append(" " * (indent * 2) + stripped)
            fence = not fence
            continue
        out.append(" " * (indent * 2) + stripped if indent and not fence else
                   (" " * indent + stripped if fence else line))
    return "\n".join(out) + "\n"


def title_of(md_text: str) -> str:
    for line in md_text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return "Document"


def to_html(md_text: str, toc: bool = False, style: str = "default") -> str:
    md = markdown.Markdown(extensions=["tables", "fenced_code", "toc", "sane_lists"],
                           extension_configs={"toc": {"toc_depth": "2-2"}})
    body = md.convert(widen_indents(fix_links(md_text)))
    body = body.replace("\\|", "|")      # GitHub-style escaped pipes inside table cells
    # contents list after the first horizontal rule (no cover page)
    if not toc:
        md.toc_tokens = []
    items = "".join(f'<li><a href="#{t["id"]}">{t["name"]}</a></li>'
                    for t in md.toc_tokens)
    toc_html = f'<div class="toc"><strong>Contents</strong><ul>{items}</ul></div>'
    if md.toc_tokens:
        body = body.replace("<hr />", toc_html + "\n<hr />", 1)
    css = CSS
    if style == "proposal":
        body = proposal_layout(body)
        css = PROPOSAL_CSS
    return (f"<!doctype html><html><head><meta charset='utf-8'><title>{title_of(md_text)}"
            f"</title><style>{css}</style></head><body>{body}</body></html>")


FOOTER_TEMPLATE = ("<div style='font-size:8px; color:#6e7781; width:100%; padding:0 17mm; "
          "display:flex; justify-content:space-between; font-family:sans-serif;'>"
          "<span>{title}</span>"
          "<span><span class='pageNumber'></span> / <span class='totalPages'></span></span>"
          "</div>")


async def print_pdf(ws_url: str, html_file: Path, footer: str) -> bytes:
    async with websockets.connect(ws_url, max_size=200_000_000) as ws:
        n = 0

        async def call(method, **params):
            nonlocal n
            n += 1
            my = n
            await ws.send(json.dumps({"id": my, "method": method, "params": params}))
            while True:
                msg = json.loads(await ws.recv())
                if msg.get("id") == my:
                    if "error" in msg:
                        raise RuntimeError(msg["error"])
                    return msg.get("result", {})

        await call("Page.enable")
        await call("Page.navigate", url=html_file.as_uri())
        await asyncio.sleep(2)             # local file, fonts: a short wait is enough
        res = await call("Page.printToPDF", printBackground=True, preferCSSPageSize=True,
                         displayHeaderFooter=True, headerTemplate="<span></span>",
                         footerTemplate=footer)
        return base64.b64decode(res["data"])


def main() -> int:
    args = sys.argv[1:]
    toc = "--toc" in args
    style = "default"
    if "--style" in args:
        i = args.index("--style")
        style = args[i + 1]
        del args[i:i + 2]
    args = [a for a in args if a != "--toc"]
    src = Path(args[0]) if args else ROOT / "docs" / "PROJECT_PROPOSAL.md"
    out = Path(args[1]) if len(args) > 1 else src.with_suffix(".pdf")
    md_text = src.read_text(encoding="utf-8")
    template = PROPOSAL_FOOTER if style == "proposal" else FOOTER_TEMPLATE
    footer = template.replace("{title}", title_of(md_text).replace("<", "&lt;"))
    chrome = shutil.which("google-chrome") or shutil.which("chromium")
    if chrome is None:
        print("Google Chrome or Chromium is needed to print the PDF", file=sys.stderr)
        return 2
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        html_file = Path(tmp) / "guide.html"
        html_file.write_text(to_html(md_text, toc, style), encoding="utf-8")
        port = 9334
        proc = subprocess.Popen(
            [chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
             f"--remote-debugging-port={port}", f"--user-data-dir={tmp}/profile",
             "about:blank"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            ws_url = None
            for _ in range(100):
                try:
                    targets = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json"))
                    ws_url = next(t["webSocketDebuggerUrl"] for t in targets
                                  if t["type"] == "page")
                    break
                except Exception:
                    time.sleep(0.1)
            if ws_url is None:
                print("could not connect to Chrome", file=sys.stderr)
                return 1
            out.write_bytes(asyncio.run(print_pdf(ws_url, html_file, footer)))
        finally:
            proc.terminate()
            proc.wait()
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
