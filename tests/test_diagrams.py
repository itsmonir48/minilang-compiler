"""The UI diagrams must contain every transition the lexer really takes."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from diagrams import DIAGRAMS, diagram_for_path, to_dot  # noqa: E402
from minilang.lexer import Lexer  # noqa: E402

SOURCE = "while x1 _y <= < >= > == = != ! 0 42 3.14 1E5 2.5e-3 7. 8E+ 9.5Ex"


def test_every_lexer_path_is_in_a_diagram():
    lexer = Lexer(SOURCE)
    seen = 0
    while lexer.next_token().type.value != "EOF":
        path = list(lexer.path)
        which = diagram_for_path(path)
        if which is None:
            continue
        _title, states, edges = DIAGRAMS[which]
        edge_set = {(a, b) for a, b, _ in edges}
        for a, b in zip(path, path[1:]):
            assert (a, b) in edge_set, (which, path)
        assert all(s in states for s in path)
        seen += 1
    assert seen >= 15


def test_dot_is_generated():
    for name in DIAGRAMS:
        dot = to_dot(name, [])
        assert dot.startswith("digraph") and dot.endswith("}")
