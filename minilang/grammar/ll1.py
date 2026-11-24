"""LL(1) parsing table (Algorithm 4.31) and the table-driven predictive parser (4.4.4).

The parser records one Step per move: stack, remaining input, action, and a copy of the
parse tree so far (it grows from the root down, in leftmost-derivation order).
"""

from dataclasses import dataclass, field

from minilang.errors import CompileError
from minilang.grammar.first_follow import Sets, first_follow, first_of_seq
from minilang.grammar.grammar import END, EPS, Grammar, Production
from minilang.tree import Node


@dataclass
class LL1Table:
    grammar: Grammar
    sets: Sets
    table: dict[tuple[str, str], list[Production]]

    @property
    def conflicts(self) -> list[tuple[str, str, list[Production]]]:
        """Multiply-defined entries M[A, a]."""
        return [(a, t, ps) for (a, t), ps in self.table.items() if len(ps) > 1]

    @property
    def is_ll1(self) -> bool:
        return not self.conflicts

    def columns(self) -> list[str]:
        return list(self.grammar.terminals) + [END]

    def entry(self, a: str, t: str) -> list[Production]:
        return self.table.get((a, t), [])


def build_ll1(g: Grammar, sets: Sets | None = None) -> LL1Table:
    """Algorithm 4.31: for A → α, add it to M[A, a] for a in FIRST(α); if ε is in
    FIRST(α), also for every b in FOLLOW(A) ($ included)."""
    sets = sets or first_follow(g)
    table: dict[tuple[str, str], list[Production]] = {}
    for p in g.productions:
        f = first_of_seq(p.body, sets.first)
        targets = f - {EPS}
        if EPS in f:
            targets |= sets.follow[p.head]
        for t in targets:
            cell = table.setdefault((p.head, t), [])
            if p not in cell:
                cell.append(p)
    return LL1Table(g, sets, table)


# ---------------------------------------------------------------------------
# steps shared by every top-down parser


@dataclass
class Step:
    action: str
    kind: str                       # expand | match | try | fail | backtrack | accept | error | call | return
    pos: int                        # number of input tokens consumed
    tree: Node                      # copy of the parse tree after this step
    active: tuple[int, ...] | None  # path (child indexes) of the node this step works on
    depth: int = 0                  # call depth (recursive-descent parsers)
    stack: list[str] | None = None  # table-driven parser only (top at the right)


@dataclass
class ParseRun:
    method: str
    tokens: list[tuple[str, int]]
    steps: list[Step] = field(default_factory=list)
    accepted: bool = False
    error: CompileError | None = None
    tree: Node | None = None
    truncated: bool = False         # stopped at the step limit


def clone(node: Node) -> Node:
    return Node(node.symbol, [clone(c) for c in node.children], node.lexeme)


def node_at(root: Node, path: tuple[int, ...] | None) -> Node | None:
    if path is None:
        return None
    node = root
    for i in path:
        node = node.children[i]
    return node


def input_text(tokens: list[tuple[str, int]], pos: int) -> str:
    return " ".join([t for t, _ in tokens[pos:]] + [END])


def _col(tokens: list[tuple[str, int]], pos: int) -> int:
    if pos < len(tokens):
        return tokens[pos][1]
    return tokens[-1][1] + len(tokens[-1][0]) if tokens else 1


def _found(tokens, pos) -> str:
    return repr(tokens[pos][0]) if pos < len(tokens) else "end of input ($)"


def ll1_parse(t: LL1Table, tokens: list[tuple[str, int]], max_steps: int = 5000) -> ParseRun:
    """Table-driven predictive parsing (Algorithm 4.34) with a trace.

    Each step shows the stack and the input before the move (as in Fig. 4.21) and the
    parse tree after it.
    """
    g = t.grammar
    run = ParseRun("ll1", tokens)
    root = Node(g.start)
    # stack entries: (symbol, path of its tree node); END has no node
    stack: list[tuple[str, tuple[int, ...] | None]] = [(END, None), (g.start, ())]
    pos = 0

    while True:
        if len(run.steps) >= max_steps:
            run.truncated = True
            run.error = CompileError("parser", f"stopped after {max_steps} steps")
            return run
        before = [s for s, _ in stack]
        start_pos = pos

        def log(action: str, kind: str, active) -> None:
            run.steps.append(Step(action, kind, start_pos, clone(root), active, stack=before))

        x, path = stack[-1]
        a = tokens[pos][0] if pos < len(tokens) else END
        if x == END and a == END:
            run.accepted = True
            run.tree = root
            log("accept", "accept", None)
            return run
        if x == END or not g.is_nonterminal(x):
            if x == a:
                stack.pop()
                pos += 1
                log(f"match {a}", "match", path)
                continue
            run.error = CompileError("parser", f"expected {x!r}, found {_found(tokens, pos)}",
                                     1, _col(tokens, pos))
            log(f"error: expected {x}, found {a}", "error", path)
            return run
        cell = t.entry(x, a)
        if not cell:
            expected = [b for b in t.columns() if t.entry(x, b)]
            run.error = CompileError(
                "parser", f"no rule for {x} on {_found(tokens, pos)}; expected one of: "
                f"{', '.join(expected)}", 1, _col(tokens, pos))
            log(f"error: M[{x}, {a}] is empty", "error", path)
            return run
        p = cell[0]
        stack.pop()
        node_at(root, path).children = [Node(s) for s in p.body] or [Node(EPS)]
        for i in range(len(p.body) - 1, -1, -1):
            stack.append((p.body[i], path + (i,)))
        log(f"output {p}", "expand", path)
