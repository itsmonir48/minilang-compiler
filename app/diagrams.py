"""Transition diagrams of the lexer as Graphviz DOT, with the visited path highlighted.

The edges here must match the state machines in minilang/lexer.py.
Rendered in the browser by st.graphviz_chart (no system Graphviz needed).
"""

HIGHLIGHT = "#d9480f"
VISITED_FILL = "#ffe8cc"

# state -> (label, kind) ; kind: start | normal | accept | retract | error
ID_STATES = {9: ("9", "start"), 10: ("10", "normal"), 11: ("11 *\\nreturn id / keyword", "retract")}
ID_EDGES = [(9, 10, "letter"), (10, 10, "letter | digit"), (10, 11, "other")]

NUM_STATES = {
    12: ("12", "start"), 13: ("13", "normal"), 14: ("14", "normal"), 15: ("15", "normal"),
    16: ("16", "normal"), 17: ("17", "normal"), 18: ("18", "normal"),
    19: ("19 *\\nreturn real", "retract"), 20: ("20 *\\nreturn num", "retract"),
    21: ("21\\nerror", "error"),
}
NUM_EDGES = [
    (12, 13, "digit"), (13, 13, "digit"), (13, 14, "."), (13, 16, "E"), (13, 20, "other"),
    (14, 15, "digit"), (14, 21, "other"),
    (15, 15, "digit"), (15, 16, "E"), (15, 19, "other"),
    (16, 17, "+ | -"), (16, 18, "digit"), (16, 21, "other"),
    (17, 18, "digit"), (17, 21, "other"),
    (18, 18, "digit"), (18, 19, "other"),
]

RELOP_STATES = {
    "r0": ("0", "start"),
    "r1": ("1", "normal"), "r2": ("2\\nrelop LE", "accept"), "r3": ("3 *\\nrelop LT", "retract"),
    "r4": ("4", "normal"), "r5": ("5\\nrelop GE", "accept"), "r6": ("6 *\\nrelop GT", "retract"),
    "r7": ("7", "normal"), "r8": ("8\\nrelop EQ", "accept"), "r9": ("9 *\\nassign", "retract"),
    "r10": ("10", "normal"), "r11": ("11\\nrelop NE", "accept"), "r12": ("12 *\\nnot", "retract"),
}
RELOP_EDGES = [
    ("r0", "r1", "<"), ("r1", "r2", "="), ("r1", "r3", "other"),
    ("r0", "r4", ">"), ("r4", "r5", "="), ("r4", "r6", "other"),
    ("r0", "r7", "="), ("r7", "r8", "="), ("r7", "r9", "other"),
    ("r0", "r10", "!"), ("r10", "r11", "="), ("r10", "r12", "other"),
]

DIAGRAMS = {
    "id": ("Identifiers and keywords (Fig. 3.14)", ID_STATES, ID_EDGES),
    "number": ("Numbers (Fig. 3.16)", NUM_STATES, NUM_EDGES),
    "relop": ("Relational operators, = and ! (Fig. 3.13, C version)", RELOP_STATES, RELOP_EDGES),
}


def diagram_for_path(path: list) -> str | None:
    """Which diagram a token's state path belongs to."""
    if not path:
        return None
    first = path[0]
    if first == 9:
        return "id"
    if first == 12:
        return "number"
    if isinstance(first, str) and first.startswith("r"):
        return "relop"
    return None


def to_dot(name: str, path: list | None = None) -> str:
    _title, states, edges = DIAGRAMS[name]
    path = path or []
    visited = set(path)
    walked = {(a, b) for a, b in zip(path, path[1:])}
    lines = [
        "digraph G {",
        "  rankdir=LR; bgcolor=transparent; forcelabels=true; nodesep=0.35;",
        '  node [fontname="Helvetica", fontsize=11, style=filled, fillcolor=white];',
        '  edge [fontname="Helvetica", fontsize=10];',
        '  start [shape=point, width=0.1];',
    ]
    for s, (label, kind) in states.items():
        shape = "doublecircle" if kind in ("accept", "retract") else "circle"
        name, _, action = label.partition("\\n")     # action text goes beside the node
        attrs = [f'label="{name}"', f"shape={shape}", "fixedsize=true", "width=0.55"]
        if action:
            attrs.append(f'xlabel="{action}"')
        if kind == "error":
            attrs += ['color="#c92a2a"', 'fontcolor="#c92a2a"']
        if s in visited:
            attrs += [f'fillcolor="{VISITED_FILL}"', f'color="{HIGHLIGHT}"', "penwidth=2"]
        lines.append(f'  "{s}" [{", ".join(attrs)}];')
        if kind == "start":
            lines.append(f'  start -> "{s}";')
    for a, b, label in edges:
        attrs = [f'label="{label}"']
        if (a, b) in walked:
            attrs += [f'color="{HIGHLIGHT}"', f'fontcolor="{HIGHLIGHT}"', "penwidth=2.5"]
        lines.append(f'  "{a}" -> "{b}" [{", ".join(attrs)}];')
    lines.append("}")
    return "\n".join(lines)
