"""Derivations, parse trees and ambiguity (4.2).

`derive` searches the leftmost derivations of a token string. Each leftmost derivation is
one parse tree, so two of them prove the grammar ambiguous. The search is bounded: it
prunes sentential forms that can no longer produce the input and stops after a node
budget, and it says whether the search finished.
"""

import math
from dataclasses import dataclass, field

from minilang.grammar.grammar import EPS, Grammar, Production
from minilang.tree import Node


def min_lengths(g: Grammar) -> dict[str, float]:
    """Shortest terminal string each nonterminal derives (inf if it derives none)."""
    best = {a: math.inf for a in g.nonterminals}
    changed = True
    while changed:
        changed = False
        for p in g.productions:
            n = sum(best[s] if g.is_nonterminal(s) else 1 for s in p.body)
            if n < best[p.head]:
                best[p.head] = n
                changed = True
    return best


@dataclass
class Derivations:
    tokens: list[str]
    sequences: list[list[Production]] = field(default_factory=list)   # leftmost derivations
    complete: bool = True        # False: stopped at max_trees or at the budget
    budget_hit: bool = False
    explored: int = 0

    @property
    def count_text(self) -> str:
        n = len(self.sequences)
        if self.complete:
            return f"exactly {n}"
        return f"at least {n}"


def derive(g: Grammar, tokens: list[str], max_trees: int = 10,
           budget: int = 200_000) -> Derivations:
    """Leftmost derivations of `tokens` from the start symbol (up to max_trees)."""
    w = tuple(tokens)
    n = len(w)
    ml = min_lengths(g)
    res = Derivations(list(tokens))
    dead: set[tuple[str, ...]] = set()
    on_path: set[tuple[str, ...]] = set()

    def viable(form: tuple[str, ...]) -> bool:
        if sum(ml[s] if g.is_nonterminal(s) else 1 for s in form) > n:
            return False
        nts = [i for i, s in enumerate(form) if g.is_nonterminal(s)]
        if not nts:
            return form == w
        first, last = nts[0], nts[-1]
        if form[:first] != w[:first]:
            return False
        tail = form[last + 1:]
        return not tail or w[n - len(tail):] == tail

    def search(form: tuple[str, ...], seq: list[Production]) -> bool:
        """Returns False if a cycle was cut below (so `dead` would be unsafe)."""
        res.explored += 1
        if res.explored > budget:
            res.budget_hit = True
            res.complete = False
            return False
        i = next((k for k, s in enumerate(form) if g.is_nonterminal(s)), None)
        if i is None:
            if form == w:
                res.sequences.append(list(seq))
            return True
        exact = True
        for p in g.prods_of(form[i]):
            if len(res.sequences) >= max_trees:
                res.complete = False
                return False
            new = form[:i] + p.body + form[i + 1:]
            if new in dead or not viable(new):
                continue
            if new in on_path:
                exact = False
                continue
            before = len(res.sequences)
            on_path.add(new)
            sub_exact = search(new, seq + [p])
            on_path.discard(new)
            if res.budget_hit:
                return False
            exact = exact and sub_exact
            if sub_exact and len(res.sequences) == before:
                dead.add(new)
        return exact

    start = (g.start,)
    if viable(start):
        on_path.add(start)
        search(start, [])
    return res


# ---------------------------------------------------------------------------
# trees and sentential forms


def tree_from_leftmost(g: Grammar, seq: list[Production]) -> Node:
    """Parse tree of a leftmost derivation (productions in preorder)."""
    it = iter(seq)

    def build(sym: str) -> Node:
        if not g.is_nonterminal(sym):
            return Node(sym)
        p = next(it)
        node = Node(sym, [build(s) for s in p.body] or [Node(EPS)])
        node.meta["prod"] = p
        return node

    return build(g.start)


def rightmost_sequence(tree: Node) -> list[Production]:
    """Productions of the rightmost derivation of the same tree (right-to-left preorder)."""
    out: list[Production] = []

    def walk(node: Node) -> None:
        if "prod" in node.meta:
            out.append(node.meta["prod"])
            for c in reversed(node.children):
                walk(c)

    walk(tree)
    return out


def forms(g: Grammar, seq: list[Production], leftmost: bool = True) -> list[tuple[str, ...]]:
    """Sentential forms of a derivation: each step rewrites the leftmost (or rightmost)
    nonterminal with the next production."""
    form: tuple[str, ...] = (g.start,)
    out = [form]
    for p in seq:
        idx = [i for i, s in enumerate(form) if g.is_nonterminal(s)]
        i = idx[0] if leftmost else idx[-1]
        assert form[i] == p.head, (form, p)
        form = form[:i] + p.body + form[i + 1:]
        out.append(form)
    return out


def form_text(form: tuple[str, ...]) -> str:
    return " ".join(form) if form else EPS


def derivation_text(g: Grammar, seq: list[Production], leftmost: bool = True) -> str:
    arrow = " ⇒lm " if leftmost else " ⇒rm "
    return arrow.join(form_text(f) for f in forms(g, seq, leftmost))


# ---------------------------------------------------------------------------
# the language of a grammar


@dataclass
class Language:
    strings: list[tuple[str, ...]]
    complete: bool               # every string up to max_len was found


def language(g: Grammar, max_len: int, budget: int = 200_000) -> Language:
    """All terminal strings of L(G) with at most max_len terminals, shortest first."""
    ml = min_lengths(g)
    found: set[tuple[str, ...]] = set()
    seen = {(g.start,)}
    queue = [(g.start,)]
    steps = 0
    complete = True
    while queue:
        steps += 1
        if steps > budget:
            complete = False
            break
        form = queue.pop()
        i = next((k for k, s in enumerate(form) if g.is_nonterminal(s)), None)
        if i is None:
            found.add(form)
            continue
        for p in g.prods_of(form[i]):
            new = form[:i] + p.body + form[i + 1:]
            if new in seen:
                continue
            if sum(ml[s] if g.is_nonterminal(s) else 1 for s in new) > max_len:
                continue
            seen.add(new)
            queue.append(new)
    return Language(sorted(found, key=lambda t: (len(t), t)), complete)
