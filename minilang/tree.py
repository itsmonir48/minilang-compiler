"""Generic parse-tree node with attributes, plus ASCII and Graphviz renderers.

Used for annotated parse trees (2.3) and, later, for the parse-tree generator.
A leaf is a node without children; its `lexeme` is shown next to the symbol.
"""

from dataclasses import dataclass, field


@dataclass
class Node:
    symbol: str
    children: list["Node"] = field(default_factory=list)
    lexeme: str | None = None
    attrs: dict[str, object] = field(default_factory=dict)   # shown in the tree
    meta: dict[str, object] = field(default_factory=dict, repr=False)  # hidden helpers

    @property
    def is_leaf(self) -> bool:
        return not self.children

    def label(self) -> str:
        if self.lexeme is not None and self.lexeme != self.symbol:
            return f"{self.symbol} ({self.lexeme})"
        return self.symbol

    def leaves(self) -> list["Node"]:
        if self.is_leaf:
            return [self]
        return [leaf for c in self.children for leaf in c.leaves()]

    def count(self) -> int:
        return 1 + sum(c.count() for c in self.children)

    def height(self) -> int:
        return 1 + max((c.height() for c in self.children), default=0)


def _fmt_attrs(node: Node) -> str:
    if not node.attrs:
        return ""
    return "  [" + ", ".join(f"{k} = {_show(v)}" for k, v in node.attrs.items()) + "]"


def _show(v: object) -> str:
    if v is None:
        return "-"
    if isinstance(v, str):
        return v if v else "ε"
    return str(v)


def render_ascii(root: Node, attrs: bool = True) -> str:
    """Tree drawn with box characters, one node per line."""
    lines = [root.label() + (_fmt_attrs(root) if attrs else "")]

    def walk(node: Node, prefix: str) -> None:
        for i, child in enumerate(node.children):
            last = i == len(node.children) - 1
            text = child.label() + (_fmt_attrs(child) if attrs else "")
            lines.append(prefix + ("└── " if last else "├── ") + text)
            walk(child, prefix + ("    " if last else "│   "))

    walk(root, "")
    return "\n".join(lines)


def _html(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def to_dot(root: Node, attrs: bool = True, highlight: set[int] | None = None,
           faded: set[int] | None = None) -> str:
    """Graphviz DOT, top-down. `highlight` holds id()s of nodes to colour; `faded` holds
    id()s of nodes drawn grey and dashed (e.g. nonterminals not expanded yet).

    Labels are Graphviz HTML labels: the symbol, then the attributes in small grey text.
    """
    highlight = highlight or set()
    faded = faded or set()
    lines = [
        "digraph T {",
        "  bgcolor=transparent; nodesep=0.2; ranksep=0.3;",
        '  node [fontname="Helvetica", fontsize=12, shape=plaintext, width=0.3, height=0.2, margin=0.04];',
        "  edge [arrowhead=none, color=\"#868e96\"];",
    ]
    ids: dict[int, str] = {}

    def visit(node: Node) -> str:
        name = f"n{len(ids)}"
        ids[id(node)] = name
        color = "#1864ab" if node.is_leaf else "#212529"
        if id(node) in faded:
            color = "#adb5bd"
        label = f'<font color="{color}"><b>{_html(node.label())}</b></font>'
        if attrs and node.attrs:
            extra = "<br/>".join(_html(f"{k} = {_show(v)}") for k, v in node.attrs.items())
            label += f'<br/><font point-size="9" color="#868e96">{extra}</font>'
        style = ""
        if id(node) in faded:
            style = ', shape=box, style="rounded,dashed", color="#ced4da"'
        if id(node) in highlight:
            style = ', shape=box, style="rounded,filled", fillcolor="#ffe8cc", color="#d9480f"'
        lines.append(f"  {name} [label=<{label}>{style}];")
        for c in node.children:
            lines.append(f"  {name} -> {visit(c)};")
        return name

    visit(root)
    # keep leaves on one line, like a textbook parse tree (yield read left to right)
    leaves = [ids[id(leaf)] for leaf in root.leaves()]
    if len(leaves) > 1:
        lines.append("  { rank=max; " + " ".join(leaves) + " }")
    lines.append("}")
    return "\n".join(lines)
