"""FIRST and FOLLOW sets (4.4.2), computed by repeating the rules until nothing changes.

Each pass is recorded, so the web page can show how the sets grow.
"""

from dataclasses import dataclass, field

from minilang.grammar.grammar import END, EPS, Grammar


@dataclass
class Sets:
    first: dict[str, set[str]]          # nonterminal -> FIRST (may contain ε)
    follow: dict[str, set[str]]         # nonterminal -> FOLLOW (may contain $)
    first_passes: list[dict[str, set[str]]] = field(default_factory=list)
    follow_passes: list[dict[str, set[str]]] = field(default_factory=list)

    def nullable(self, sym: str) -> bool:
        return sym in self.first and EPS in self.first[sym]


def first_of_seq(seq: tuple[str, ...] | list[str], first: dict[str, set[str]]) -> set[str]:
    """FIRST of a string of symbols X1 X2 ... Xn (ε if all of them can derive ε)."""
    out: set[str] = set()
    for sym in seq:
        if sym not in first:                 # terminal
            out.add(sym)
            return out
        out |= first[sym] - {EPS}
        if EPS not in first[sym]:
            return out
    out.add(EPS)
    return out


def compute_first(g: Grammar) -> tuple[dict[str, set[str]], list[dict[str, set[str]]]]:
    first: dict[str, set[str]] = {a: set() for a in g.nonterminals}
    passes = []
    changed = True
    while changed:
        changed = False
        for p in g.productions:
            add = first_of_seq(p.body, first)
            if not add <= first[p.head]:
                first[p.head] |= add
                changed = True
        passes.append({a: set(s) for a, s in first.items()})
    return first, passes


def compute_follow(g: Grammar, first: dict[str, set[str]]
                   ) -> tuple[dict[str, set[str]], list[dict[str, set[str]]]]:
    """Rules of 4.4.2: $ in FOLLOW(S); A → αBβ puts FIRST(β) - ε in FOLLOW(B), and
    FOLLOW(A) too if β can derive ε."""
    follow: dict[str, set[str]] = {a: set() for a in g.nonterminals}
    follow[g.start].add(END)
    passes = []
    changed = True
    while changed:
        changed = False
        for p in g.productions:
            for i, sym in enumerate(p.body):
                if sym not in follow:
                    continue
                rest = first_of_seq(p.body[i + 1:], first)
                add = rest - {EPS}
                if EPS in rest:
                    add |= follow[p.head]
                if not add <= follow[sym]:
                    follow[sym] |= add
                    changed = True
        passes.append({a: set(s) for a, s in follow.items()})
    return follow, passes


def first_follow(g: Grammar) -> Sets:
    first, fp = compute_first(g)
    follow, wp = compute_follow(g, first)
    return Sets(first, follow, fp, wp)


def sort_syms(syms: set[str], g: Grammar) -> list[str]:
    """Terminals in grammar order, then $, then ε (stable, readable output)."""
    order = {t: i for i, t in enumerate(g.terminals)}
    order[END] = len(order)
    order[EPS] = len(order) + 1
    return sorted(syms, key=lambda s: (order.get(s, -1), s))


def fmt_set(syms: set[str], g: Grammar) -> str:
    return "{ " + ", ".join(sort_syms(syms, g)) + " }" if syms else "∅"
