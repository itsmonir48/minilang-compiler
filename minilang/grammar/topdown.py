"""Top-down parsing visualizer (4.4): three parsers on the same grammar and input.

* backtracking recursive descent (4.4.1): tries the alternatives in order and backs up
  when one fails; needs a grammar without left recursion
* predictive recursive descent: one procedure per nonterminal, the alternative is chosen
  by the lookahead through the LL(1) table; needs an LL(1) grammar
* table-driven LL(1) (Algorithm 4.34): explicit stack; see ll1.py

Every parser returns a ParseRun whose steps hold a copy of the tree, so the tree can be
shown growing from the root down.
"""

from dataclasses import dataclass

from minilang.errors import CompileError
from minilang.grammar.grammar import EPS, Grammar
from minilang.grammar.ll1 import (LL1Table, ParseRun, Step, _col, _found, build_ll1, clone,
                                  ll1_parse, node_at)
from minilang.grammar.transforms import left_recursive, prepare_for_ll1
from minilang.tree import Node

METHODS = {
    "backtrack": "Backtracking recursive descent",
    "predictive": "Predictive recursive descent",
    "ll1": "Table-driven LL(1)",
}


@dataclass
class Refusal:
    reason: str
    suggestion: Grammar | None       # a transformed grammar that may work
    suggestion_steps: list[str]
    suggestion_ok: bool              # the suggestion is LL(1) (or free of left recursion)


def check(g: Grammar, method: str) -> Refusal | None:
    """None if the method can run on g; otherwise why not and a transformed grammar."""
    rec = left_recursive(g)
    if rec:
        a, cycle = next(iter(rec.items()))
        chain = " ⇒ ".join([cycle[0]] + [f"{x} …" for x in cycle[1:]])
        why = (f"the grammar is left-recursive ({chain}; left-recursive: {', '.join(rec)}); "
               f"a top-down parser would loop forever: {a}() reaches {a}() again without "
               "reading any input")
    elif method != "backtrack":
        t = build_ll1(g)
        if t.is_ll1:
            return None
        a, b, ps = t.conflicts[0]
        why = (f"the grammar is not LL(1): M[{a}, {b}] has {len(ps)} productions "
               f"({'  |  '.join(str(p) for p in ps)}), so one lookahead symbol cannot choose"
               + (f"; {len(t.conflicts)} conflicting entries in all"
                  if len(t.conflicts) > 1 else ""))
    else:
        return None
    new, steps = prepare_for_ll1(g)
    ok = not left_recursive(new) and (method == "backtrack" or build_ll1(new).is_ll1)
    if new == g:
        new = None
    return Refusal(why, new, steps, ok)


# ---------------------------------------------------------------------------
# backtracking recursive descent


def backtrack_parse(g: Grammar, tokens: list[tuple[str, int]],
                    max_steps: int = 3000) -> ParseRun:
    """Recursive descent with full backtracking (generators yield every way a symbol can
    match). Assumes no left recursion (call check() first)."""
    run = ParseRun("backtrack", tokens)
    root = Node(g.start)
    syms = [t for t, _ in tokens]
    n = len(syms)
    furthest = [0]

    class Stop(Exception):
        pass

    def log(action: str, kind: str, pos: int, path, depth: int) -> None:
        if len(run.steps) >= max_steps:
            run.truncated = True
            raise Stop
        run.steps.append(Step(action, kind, pos, clone(root), path, depth))

    def parse_sym(sym: str, pos: int, path: tuple[int, ...], depth: int):
        node = node_at(root, path)
        if not g.is_nonterminal(sym):
            if pos < n and syms[pos] == sym:
                furthest[0] = max(furthest[0], pos + 1)
                log(f"match {sym}", "match", pos, path, depth)
                yield pos + 1
            else:
                got = syms[pos] if pos < n else "$"
                log(f"fail: expected {sym}, found {got}", "fail", pos, path, depth)
            return
        prods = g.prods_of(sym)
        for k, p in enumerate(prods):
            node.children = [Node(s) for s in p.body] or [Node(EPS)]
            log(f"{sym}: try {p}" + (f"  (alternative {k + 1} of {len(prods)})"
                                       if len(prods) > 1 else ""), "try", pos, path, depth)
            for end in parse_seq(p.body, 0, pos, path, depth + 1):
                yield end
                log(f"{sym}: back in {p}, look for another way", "backtrack", pos, path, depth)
            node.children = []
            if k + 1 < len(prods):
                log(f"{sym}: {p} failed, reset input to position {pos + 1}, try the next "
                    "alternative", "backtrack", pos, path, depth)
            else:
                log(f"{sym}: no alternative left, {sym} fails", "fail", pos, path, depth)

    def parse_seq(body, k: int, pos: int, path, depth: int):
        if k == len(body):
            yield pos
            return
        for mid in parse_sym(body[k], pos, path + (k,), depth):
            yield from parse_seq(body, k + 1, mid, path, depth)

    try:
        for end in parse_sym(g.start, 0, (), 0):
            if end == n:
                run.accepted = True
                run.tree = clone(root)
                log("accept: the whole input is matched", "accept", end, None, 0)
                break
            log(f"{g.start} matched only {end} of {n} tokens; backtrack", "backtrack", end,
                (), 0)
    except Stop:
        run.error = CompileError("parser", f"stopped after {max_steps} steps")
        return run
    if not run.accepted:
        p = furthest[0]
        run.error = CompileError("parser", f"no way to derive the input; the furthest match "
                                 f"stopped at {_found(tokens, p)}", 1, _col(tokens, p))
        log("reject", "error", p, None, 0)
    return run


# ---------------------------------------------------------------------------
# predictive recursive descent


def predictive_parse(t: LL1Table, tokens: list[tuple[str, int]],
                     max_steps: int = 5000) -> ParseRun:
    """One procedure per nonterminal: A() looks at the lookahead, takes the production
    M[A, lookahead], and calls / matches its body left to right (4.4.1, Fig. 4.13)."""
    g = t.grammar
    run = ParseRun("predictive", tokens)
    root = Node(g.start)
    syms = [s for s, _ in tokens]
    pos = 0

    class Fail(Exception):
        pass

    def la() -> str:
        return syms[pos] if pos < len(syms) else "$"

    def log(action: str, kind: str, path, depth: int) -> None:
        if len(run.steps) >= max_steps:
            run.truncated = True
            run.error = CompileError("parser", f"stopped after {max_steps} steps")
            raise Fail
        run.steps.append(Step(action, kind, pos, clone(root), path, depth))

    def proc(a: str, path: tuple[int, ...], depth: int) -> None:
        nonlocal pos
        cell = t.entry(a, la())
        if not cell:
            expected = [b for b in t.columns() if t.entry(a, b)]
            run.error = CompileError(
                "parser", f"{a}(): no rule for lookahead {_found(tokens, pos)}; expected "
                f"one of: {', '.join(expected)}", 1, _col(tokens, pos))
            log(f"{a}(): error, M[{a}, {la()}] is empty", "error", path, depth)
            raise Fail
        p = cell[0]
        node_at(root, path).children = [Node(s) for s in p.body] or [Node(EPS)]
        log(f"{a}(): lookahead {la()} → use {p}", "call", path, depth)
        for i, sym in enumerate(p.body):
            if g.is_nonterminal(sym):
                proc(sym, path + (i,), depth + 1)
            elif la() == sym:
                pos += 1
                log(f"match({sym})", "match", path + (i,), depth + 1)
            else:
                run.error = CompileError("parser", f"{a}(): expected {sym!r}, found "
                                         f"{_found(tokens, pos)}", 1, _col(tokens, pos))
                log(f"match({sym}): error, found {la()}", "error", path + (i,), depth + 1)
                raise Fail
        log(f"return from {a}()", "return", path, depth)

    try:
        proc(g.start, (), 0)
        if pos != len(syms):
            run.error = CompileError("parser", f"extra input after a complete "
                                     f"{g.start}: {_found(tokens, pos)}", 1, _col(tokens, pos))
            log("error: input left over", "error", None, 0)
        else:
            run.accepted = True
            run.tree = root
            log("accept: lookahead is $", "accept", None, 0)
    except Fail:
        pass
    return run


def run_method(g: Grammar, method: str, tokens: list[tuple[str, int]]) -> ParseRun:
    """Run one top-down method; call check() first."""
    if method == "backtrack":
        return backtrack_parse(g, tokens)
    t = build_ll1(g)
    if method == "predictive":
        return predictive_parse(t, tokens)
    if method == "ll1":
        return ll1_parse(t, tokens)
    raise ValueError(f"unknown method {method!r}")
