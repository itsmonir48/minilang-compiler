"""Grammar transformations for top-down parsing (4.3.3, 4.3.4).

Each function returns the new grammar and a list of human-readable steps.
"""

from minilang.grammar.first_follow import compute_first
from minilang.grammar.grammar import EPS, Grammar, Production


def _fmt(prods: list[Production]) -> str:
    if not prods:
        return ""
    head = prods[0].head
    return f"{head} → " + " | ".join(p.body_text() for p in prods)


# ---------------------------------------------------------------------------
# detection


def nullable_set(g: Grammar) -> set[str]:
    first, _ = compute_first(g)
    return {a for a, f in first.items() if EPS in f}


def left_recursive(g: Grammar) -> dict[str, list[str]]:
    """Nonterminals A with A ⇒+ A α, and a cycle that shows it, e.g. ['S', 'A', 'S'].

    B is a "left corner" of A if A → γ B δ where γ can derive ε (so B can come first).
    """
    nullable = nullable_set(g)
    corners: dict[str, list[str]] = {a: [] for a in g.nonterminals}
    for p in g.productions:
        for sym in p.body:
            if g.is_nonterminal(sym):
                if sym not in corners[p.head]:
                    corners[p.head].append(sym)
                if sym in nullable:
                    continue
            break
    found: dict[str, list[str]] = {}
    for a in g.nonterminals:
        # breadth-first search from a over left corners, back to a
        prev: dict[str, str] = {}
        queue = list(corners[a])
        for b in queue:
            prev.setdefault(b, a)
        seen = set(queue)
        while queue:
            b = queue.pop(0)
            if b == a:
                path = [a]
                cur = prev[a]
                while cur != a:
                    path.append(cur)
                    cur = prev[cur]
                path.append(a)
                found[a] = list(reversed(path))
                break
            for c in corners[b]:
                if c not in seen:
                    seen.add(c)
                    prev[c] = b
                    queue.append(c)
    return found


def has_cycles_or_eps(g: Grammar) -> tuple[bool, bool]:
    """(has a cycle A ⇒+ A, has an ε-production) — the preconditions of Algorithm 4.19."""
    has_eps = any(not p.body for p in g.productions)
    nullable = nullable_set(g)
    # unit-like edges A -> B where A → α B β with α, β nullable
    edges: dict[str, set[str]] = {a: set() for a in g.nonterminals}
    for p in g.productions:
        for i, sym in enumerate(p.body):
            if g.is_nonterminal(sym) and all(s in nullable for s in p.body[:i] + p.body[i + 1:]):
                edges[p.head].add(sym)

    def reaches(a: str) -> bool:
        stack, seen = list(edges[a]), set()
        while stack:
            b = stack.pop()
            if b == a:
                return True
            if b not in seen:
                seen.add(b)
                stack.extend(edges[b])
        return False

    return any(reaches(a) for a in g.nonterminals), has_eps


# ---------------------------------------------------------------------------
# left recursion


def _remove_immediate(prods: list[Production], g_names: set[str], head: str
                      ) -> tuple[list[Production], str | None]:
    """A → A α1 | ... | A αm | β1 | ... | βn  becomes
    A → β1 A' | ... | βn A',  A' → α1 A' | ... | αm A' | ε."""
    rec = [p.body[1:] for p in prods if p.body[:1] == (head,)]
    other = [p.body for p in prods if p.body[:1] != (head,)]
    if not rec:
        return prods, None
    new = head + "'"
    while new in g_names:
        new += "'"
    out = [Production(head, beta + (new,)) for beta in other]
    out += [Production(new, alpha + (new,)) for alpha in rec if alpha]
    out.append(Production(new, ()))
    return out, new


def remove_immediate_left_recursion(g: Grammar) -> tuple[Grammar, list[str]]:
    """Remove A → A α for every A (4.3.3), without substitution."""
    names = set(g.nonterminals) | set(g.terminals)
    steps: list[str] = []
    out: list[Production] = []
    for a in g.nonterminals:
        prods = g.prods_of(a)
        new_prods, new = _remove_immediate(prods, names, a)
        if new:
            names.add(new)
            steps.append(f"{_fmt(prods)}   ⇒   "
                         f"{_fmt([p for p in new_prods if p.head == a])};  "
                         f"{_fmt([p for p in new_prods if p.head == new])}")
            if any(p.body == (a,) for p in prods):
                steps.append(f"note: {a} → {a} is a cycle; it is dropped (it adds no strings)")
        out += new_prods
    if not steps:
        steps.append("no immediate left recursion")
    return Grammar(out, g.start), steps


def remove_left_recursion(g: Grammar) -> tuple[Grammar, list[str]]:
    """Algorithm 4.19: order the nonterminals A1..An; for each Ai, substitute the bodies
    of every earlier Aj into Ai → Aj γ, then remove the immediate left recursion of Ai.

    The algorithm is guaranteed only for grammars without cycles or ε-productions; the
    steps say so when that precondition is not met (it often still works, e.g. 4.18).
    """
    steps: list[str] = []
    cycles, eps = has_cycles_or_eps(g)
    if cycles or eps:
        why = " and ".join(w for w, f in (("a cycle", cycles), ("ε-productions", eps)) if f)
        steps.append(f"warning: the grammar has {why}; Algorithm 4.19 is only guaranteed "
                     "without them, so check the result")
    order = list(g.nonterminals)
    steps.append("order: " + ", ".join(f"A{i + 1} = {a}" for i, a in enumerate(order)))
    rules: dict[str, list[Production]] = {a: g.prods_of(a) for a in order}
    names = set(g.nonterminals) | set(g.terminals)
    new_heads: list[str] = []
    for i, ai in enumerate(order):
        for aj in order[:i]:
            changed = False
            out: list[Production] = []
            for p in rules[ai]:
                if p.body[:1] == (aj,):
                    changed = True
                    out += [Production(ai, q.body + p.body[1:]) for q in rules[aj]]
                else:
                    out.append(p)
            if changed:
                old = _fmt(rules[ai])
                rules[ai] = list(dict.fromkeys(out))
                steps.append(f"substitute {aj} into {ai}: {old}   ⇒   {_fmt(rules[ai])}")
        prods, new = _remove_immediate(rules[ai], names, ai)
        if new:
            names.add(new)
            new_heads.append(new)
            before = _fmt(rules[ai])
            rules[ai] = [p for p in prods if p.head == ai]
            rules[new] = [p for p in prods if p.head == new]
            steps.append(f"immediate left recursion of {ai}: {before}   ⇒   "
                         f"{_fmt(rules[ai])};  {_fmt(rules[new])}")
    prods_out: list[Production] = []
    for a in order:
        prods_out += rules[a]
        for n in new_heads:
            if n.rstrip("'") == a and n in rules:
                prods_out += rules.pop(n)
    for n in new_heads:          # any left (should not happen)
        prods_out += rules.get(n, [])
    if len(steps) == 1 + (1 if cycles or eps else 0):
        steps.append("no left recursion")
    return Grammar(prods_out, g.start), steps


# ---------------------------------------------------------------------------
# left factoring


def _common_prefix(bodies: list[tuple[str, ...]]) -> tuple[str, ...]:
    prefix = bodies[0]
    for b in bodies[1:]:
        n = 0
        while n < len(prefix) and n < len(b) and prefix[n] == b[n]:
            n += 1
        prefix = prefix[:n]
    return prefix


def left_factor(g: Grammar) -> tuple[Grammar, list[str]]:
    """Algorithm 4.21: while two alternatives of A start with the same symbol, replace
    A → α β1 | ... | α βn | γ  by  A → α A' | γ,  A' → β1 | ... | βn.

    The alternatives that share a first symbol are factored together, with α their longest
    common prefix; this repeats (also on the new nonterminals) until nothing changes.
    """
    rules: dict[str, list[tuple[str, ...]]] = {a: [p.body for p in g.prods_of(a)]
                                               for a in g.nonterminals}
    order = list(g.nonterminals)
    names = set(g.nonterminals) | set(g.terminals)
    steps: list[str] = []
    work = list(order)
    while work:
        a = work.pop(0)
        bodies = rules[a]
        groups: dict[str, list[tuple[str, ...]]] = {}
        for b in bodies:
            if b:
                groups.setdefault(b[0], []).append(b)
        group = next((grp for grp in groups.values() if len(grp) > 1), None)
        if group is None:
            continue
        alpha = _common_prefix(group)
        new = a + "'"
        while new in names:
            new += "'"
        names.add(new)
        before = " | ".join(" ".join(b) or EPS for b in bodies)
        rest = [b for b in bodies if b not in group]
        first_at = bodies.index(group[0])
        rules[a] = rest[:first_at] + [alpha + (new,)] + rest[first_at:]
        tails = list(dict.fromkeys(b[len(alpha):] for b in group))
        rules[new] = [b for b in tails if b] + [b for b in tails if not b]   # ε last
        order.insert(order.index(a) + 1, new)
        steps.append(
            f"{a} → {before}   ⇒   {a} → "
            + " | ".join(" ".join(b) or EPS for b in rules[a])
            + f";  {new} → " + " | ".join(" ".join(b) or EPS for b in rules[new]))
        work[:0] = [a, new]          # look at both again
    if not steps:
        steps.append("no common prefixes")
    prods = [Production(a, b) for a in order for b in rules[a]]
    return Grammar(prods, g.start), steps


def prepare_for_ll1(g: Grammar) -> tuple[Grammar, list[str]]:
    """Left recursion removal (Algorithm 4.19) followed by left factoring."""
    g1, s1 = remove_left_recursion(g)
    g2, s2 = left_factor(g1)
    return g2, ["— left recursion —"] + s1 + ["— left factoring —"] + s2
