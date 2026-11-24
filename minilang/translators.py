"""Chapter 2 translators: syntax-directed translation of small notations.

* Expressions in infix, postfix or prefix notation are parsed with a grammar for that
  notation; every parse-tree node gets synthesized attributes computed by the semantic
  rules in SCHEMES (2.3). The result is an annotated parse tree plus the expression in
  the other two notations and its value.
* The infix parser is the recursive-descent translator of 2.5 (expr, term, factor),
  extended with * / ( ) and unary + -. It records a call trace with its print actions.
* Roman numerals <-> integers with grammar-based translators (2.2, 2.3).
* Small grammars from the 2.2 exercises: binary numbers divisible by 3, balanced
  brackets, left- and right-associative comma lists.

All errors are CompileError("syntax" | "range", message, line=1, col).
"""

import re
from dataclasses import dataclass, field
from functools import lru_cache
from itertools import product

from minilang.errors import CompileError
from minilang.tree import Node

# ---------------------------------------------------------------------------
# expression tokens

BINARY_OPS = "+-*/"
UNARY_MINUS = "~"           # unary minus in postfix/prefix: '-' there is always binary
PREC = {"+": 1, "-": 1, "*": 2, "/": 2}
UNARY_PREC = 3
ATOM_PREC = 4


@dataclass(frozen=True)
class Tok:
    kind: str       # id | num | op | ( | ) | end
    text: str
    col: int


_TOKEN_RE = re.compile(r"\s+|[A-Za-z_]\w*|\d+(?:\.\d+)?|[-+*/~()]")


def _error(message: str, col: int, kind: str = "syntax") -> CompileError:
    return CompileError(kind, message, 1, col)


def _make_tok(text: str, col: int) -> Tok:
    if text[0].isalpha() or text[0] == "_":
        return Tok("id", text, col)
    if text[0].isdigit():
        return Tok("num", text, col)
    if text in "()":
        return Tok(text, text, col)
    return Tok("op", text, col)


def scan(text: str, notation: str) -> list[Tok]:
    """Tokens of an expression. Columns are 1-based.

    Postfix and prefix input with an operator but no blank is read one character per
    token, so the textbook style `95-2+` works; with blanks, `12 3 +` has the operands
    12 and 3. A lone operand such as `12` is one token.
    """
    if "\n" in text:
        raise _error("the expression must be on one line", text.index("\n") + 1)
    stripped = text.strip()
    per_char = (notation != "infix" and not any(c.isspace() for c in stripped)
                and any(c in BINARY_OPS + UNARY_MINUS for c in stripped))
    toks: list[Tok] = []
    if per_char:
        for i, c in enumerate(text):
            if not (c.isalnum() or c == "_" or c in BINARY_OPS + UNARY_MINUS + "()"):
                raise _error(f"unexpected character {c!r}", i + 1)
            toks.append(_make_tok(c, i + 1))
    else:
        pos = 0
        while pos < len(text):
            m = _TOKEN_RE.match(text, pos)
            if not m:
                raise _error(f"unexpected character {text[pos]!r}", pos + 1)
            if not m.group().isspace():
                toks.append(_make_tok(m.group(), pos + 1))
            pos = m.end()
    for t in toks:
        if notation == "infix" and t.text == UNARY_MINUS:
            raise _error("'~' is only used in postfix and prefix; write unary minus as '-'",
                         t.col)
        if notation != "infix" and t.kind in "()":
            raise _error(f"parentheses are not used in {notation} notation", t.col)
    toks.append(Tok("end", "end of input", len(text) + 1))
    return toks


def _found(t: Tok) -> str:
    return "end of input" if t.kind == "end" else repr(t.text)


def _number(text: str) -> int | float:
    return float(text) if "." in text else int(text)


# ---------------------------------------------------------------------------
# semantic helpers shared by the three notations


def _apply(op: str, a, b):
    """Value of a op b, with MiniLang semantics (int / int truncates toward zero).

    Returns (value, note); value is None when it cannot be computed.
    """
    if a is None or b is None:
        return None, None
    if op == "+":
        return a + b, None
    if op == "-":
        return a - b, None
    if op == "*":
        return a * b, None
    if b == 0:
        return None, "division by zero"
    if isinstance(a, int) and isinstance(b, int):
        q = abs(a) // abs(b)
        return (q if (a >= 0) == (b >= 0) else -q), None
    return a / b, None


def _infix_of(op: str, left: Node, right: Node) -> tuple[str, int]:
    """Infix text with as few parentheses as keep the same tree.

    A left operand needs ( ) if it binds weaker than op; a right operand also needs them
    if it binds equally (all four operators are left-associative).
    """
    p = PREC[op]
    lt, lp = left.meta["in"], left.meta["prec"]
    rt, rp = right.meta["in"], right.meta["prec"]
    lt = lt if lp >= p else f"({lt})"
    rt = rt if rp > p else f"({rt})"
    return f"{lt} {op} {rt}", p


def _neg_infix(operand: Node) -> str:
    t = operand.meta["in"]
    return f"-{t}" if operand.meta["prec"] == ATOM_PREC else f"-({t})"


def _leaf_meta(node: Node, tok: Tok) -> None:
    val = _number(tok.text) if tok.kind == "num" else None
    node.meta.update({"in": tok.text, "post": tok.text, "pre": tok.text, "prec": ATOM_PREC,
                      "val": val, "note": None if tok.kind == "num" else "identifiers"})


def _binary_meta(node: Node, op: str, left: Node, right: Node) -> None:
    val, note = _apply(op, left.meta["val"], right.meta["val"])
    node.meta["in"], node.meta["prec"] = _infix_of(op, left, right)
    node.meta["post"] = f"{left.meta['post']} {right.meta['post']} {op}"
    node.meta["pre"] = f"{op} {left.meta['pre']} {right.meta['pre']}"
    node.meta["val"] = val
    node.meta["note"] = left.meta["note"] or right.meta["note"] or note


def _unary_meta(node: Node, op: str, operand: Node) -> None:
    """op is '-' or '+' (unary plus changes nothing)."""
    m = operand.meta
    if op == "+":
        node.meta.update(m)
        return
    node.meta.update({
        "in": _neg_infix(operand), "prec": UNARY_PREC,
        "post": f"{m['post']} {UNARY_MINUS}", "pre": f"{UNARY_MINUS} {m['pre']}",
        "val": None if m["val"] is None else -m["val"], "note": m["note"],
    })


def _copy_meta(node: Node, child: Node) -> None:
    node.meta.update(child.meta)


SHOWN = {"infix": ("post", "pre", "val"), "postfix": ("in", "pre", "val"),
         "prefix": ("in", "post", "val")}


def _annotate(node: Node, keys: tuple[str, ...]) -> None:
    """Copy the attributes worth showing from meta to attrs (non-leaf nodes only)."""
    for c in node.children:
        _annotate(c, keys)
    if node.children:
        node.attrs = {k: node.meta[k] for k in keys}


# ---------------------------------------------------------------------------
# translation schemes (shown in the CLI and the web page)

SCHEMES = {
    "infix": [
        "expr → expr₁ + term    { expr.post = expr₁.post ‖ term.post ‖ '+';  expr.pre = '+' ‖ expr₁.pre ‖ term.pre }",
        "expr → expr₁ - term    { same with '-' }",
        "expr → term            { expr.post = term.post;  expr.pre = term.pre }",
        "term → term₁ * factor  { term.post = term₁.post ‖ factor.post ‖ '*';  term.pre = '*' ‖ term₁.pre ‖ factor.pre }",
        "term → term₁ / factor  { same with '/' }",
        "term → factor          { term.post = factor.post;  term.pre = factor.pre }",
        "factor → ( expr )      { factor.post = expr.post;  factor.pre = expr.pre }",
        "factor → - factor₁     { factor.post = factor₁.post ‖ '~';  factor.pre = '~' ‖ factor₁.pre }",
        "factor → + factor₁     { factor.post = factor₁.post;  factor.pre = factor₁.pre }",
        "factor → id | num      { factor.post = factor.pre = lexeme }",
        "(every rule also computes val, e.g. expr.val = expr₁.val + term.val)",
    ],
    "postfix": [
        "E → E₁ E₂ op   { E.in = E₁.in op E₂.in  (with ( ) only where needed);  E.pre = op ‖ E₁.pre ‖ E₂.pre }",
        "E → E₁ ~       { E.in = -E₁.in;  E.pre = '~' ‖ E₁.pre }",
        "E → id | num   { E.in = E.pre = lexeme }",
        "op → + | - | * | /",
    ],
    "prefix": [
        "E → op E₁ E₂   { E.in = E₁.in op E₂.in  (with ( ) only where needed);  E.post = E₁.post ‖ E₂.post ‖ op }",
        "E → ~ E₁       { E.in = -E₁.in;  E.post = E₁.post ‖ '~' }",
        "E → id | num   { E.in = E.post = lexeme }",
        "op → + | - | * | /",
    ],
}


@dataclass
class TraceStep:
    depth: int
    action: str
    output: str      # postfix output printed so far


@dataclass
class Translation:
    source: str
    notation: str
    tree: Node
    infix: str
    postfix: str
    prefix: str
    value: int | float | None
    value_note: str | None
    trace: list[TraceStep] = field(default_factory=list)


# ---------------------------------------------------------------------------
# infix: the 2.5 recursive-descent translator


class _InfixParser:
    """expr → expr + term | expr - term | term
    term → term * factor | term / factor | factor
    factor → ( expr ) | - factor | + factor | id | num

    The left recursion is removed in the code (a while loop, as in 2.5), but the tree is
    built in the left-recursive shape of the grammar above.
    """

    def __init__(self, toks: list[Tok]):
        self.toks = toks
        self.i = 0
        self.depth = 0
        self.out: list[str] = []
        self.trace: list[TraceStep] = []

    @property
    def look(self) -> Tok:
        return self.toks[self.i]

    def log(self, action: str) -> None:
        self.trace.append(TraceStep(self.depth, action, " ".join(self.out)))

    def emit(self, text: str) -> None:
        self.out.append(text)
        self.log(f"print('{text}')")

    def match(self, kind: str, text: str | None = None) -> Tok:
        t = self.look
        if t.kind != kind or (text is not None and t.text != text):
            want = text or kind
            raise _error(f"expected {want!r}, found {_found(t)}", t.col)
        self.log(f"match {t.text!r}")
        self.i += 1
        return t

    def call(self, name: str, fn):
        self.log(f"{name}()")
        self.depth += 1
        node = fn()
        self.depth -= 1
        return node

    def parse(self) -> Node:
        if self.look.kind == "end":
            raise _error("empty expression", 1)
        node = self.call("expr", self.expr)
        if self.look.kind != "end":
            t = self.look
            hint = " (missing operator?)" if t.kind in ("id", "num", "(") else ""
            raise _error(f"unexpected {t.text!r} after the expression{hint}", t.col)
        return node

    def _chain(self, name: str, sub_name: str, sub, ops: str) -> Node:
        first = self.call(sub_name, sub)
        node = Node(name, [first])
        _copy_meta(node, first)
        while self.look.kind == "op" and self.look.text in ops:
            op = self.match("op").text
            right = self.call(sub_name, sub)
            self.emit(op)
            parent = Node(name, [node, Node(op), right])
            _binary_meta(parent, op, node, right)
            node = parent
        return node

    def expr(self) -> Node:
        return self._chain("expr", "term", self.term, "+-")

    def term(self) -> Node:
        return self._chain("term", "factor", self.factor, "*/")

    def factor(self) -> Node:
        t = self.look
        if t.kind == "(":
            self.match("(")
            inner = self.call("expr", self.expr)
            if self.look.kind != ")":
                raise _error(f"expected ')' to close '(' at column {t.col}, "
                             f"found {_found(self.look)}", self.look.col)
            self.match(")")
            node = Node("factor", [Node("("), inner, Node(")")])
            _copy_meta(node, inner)       # redundant ( ) disappear from the infix output
            return node
        if t.kind == "op" and t.text in "+-":
            self.match("op")
            operand = self.call("factor", self.factor)
            if t.text == "-":
                self.emit(UNARY_MINUS)
            node = Node("factor", [Node(t.text), operand])
            _unary_meta(node, t.text, operand)
            return node
        if t.kind in ("id", "num"):
            self.match(t.kind)
            self.emit(t.text)
            leaf = Node(t.kind, lexeme=t.text)
            node = Node("factor", [leaf])
            _leaf_meta(node, t)
            return node
        raise _error(f"expected an operand, found {_found(t)}", t.col)


# ---------------------------------------------------------------------------
# postfix (bottom-up with a stack) and prefix (recursive descent)


def _operand_node(t: Tok) -> Node:
    node = Node("E", [Node(t.kind, lexeme=t.text)])
    _leaf_meta(node, t)
    return node


def _parse_postfix(toks: list[Tok]) -> Node:
    """E → E E op | E ~ | id | num, read left to right with a stack of E's."""
    stack: list[Node] = []
    for t in toks[:-1]:
        if t.kind in ("id", "num"):
            stack.append(_operand_node(t))
        elif t.text == UNARY_MINUS:
            if not stack:
                raise _error("'~' needs one operand before it", t.col)
            e1 = stack.pop()
            node = Node("E", [e1, Node(UNARY_MINUS)])
            _unary_meta(node, "-", e1)
            stack.append(node)
        else:
            if len(stack) < 2:
                raise _error(f"operator {t.text!r} needs two operands before it, "
                             f"found {len(stack)}", t.col)
            e2, e1 = stack.pop(), stack.pop()
            node = Node("E", [e1, e2, Node(t.text)])
            _binary_meta(node, t.text, e1, e2)
            stack.append(node)
    end = toks[-1].col
    if not stack:
        raise _error("empty expression", 1)
    if len(stack) > 1:
        raise _error(f"{len(stack)} operands are left without an operator", end)
    return stack[0]


def _parse_prefix(toks: list[Tok]) -> Node:
    """E → op E E | ~ E | id | num."""
    i = 0

    def e() -> Node:
        nonlocal i
        t = toks[i]
        if t.kind == "end":
            raise _error("expected an operand or operator, found end of input", t.col)
        i += 1
        if t.kind in ("id", "num"):
            return _operand_node(t)
        if t.text == UNARY_MINUS:
            e1 = e()
            node = Node("E", [Node(UNARY_MINUS), e1])
            _unary_meta(node, "-", e1)
            return node
        e1 = e()
        e2 = e()
        node = Node("E", [Node(t.text), e1, e2])
        _binary_meta(node, t.text, e1, e2)
        return node

    if toks[0].kind == "end":
        raise _error("empty expression", 1)
    root = e()
    if toks[i].kind != "end":
        raise _error(f"unexpected {toks[i].text!r} after a complete expression", toks[i].col)
    return root


def translate(text: str, notation: str = "infix") -> Translation:
    """Parse `text` in the given notation and translate it to the other two (2.3, 2.5)."""
    if notation not in SCHEMES:
        raise ValueError(f"unknown notation {notation!r}")
    toks = scan(text, notation)
    trace: list[TraceStep] = []
    if notation == "infix":
        parser = _InfixParser(toks)
        root = parser.parse()
        trace = parser.trace
    elif notation == "postfix":
        root = _parse_postfix(toks)
    else:
        root = _parse_prefix(toks)
    _annotate(root, SHOWN[notation])
    m = root.meta
    note = m["note"]
    if note == "identifiers":
        note = "the expression has identifiers, so it has no value"
    return Translation(text, notation, root, m["in"], m["post"], m["pre"], m["val"], note, trace)


# ---------------------------------------------------------------------------
# Roman numerals (2.2 grammar, 2.3 translation schemes)

ROMAN_GRAMMAR = [
    "romanNum → thousand hundred ten digit   { romanNum.val = thousand.val + hundred.val + ten.val + digit.val }",
    "thousand → M | MM | MMM | ε             { val = 1000 × (number of M) }",
    "hundred → smallHundred | C D | D smallHundred | C M   { val = 100 × (1..3 | 4 | 5 + small | 9) }",
    "smallHundred → C | CC | CCC | ε",
    "ten → smallTen | X L | L smallTen | X C              { val = 10 × (...) }",
    "smallTen → X | XX | XXX | ε",
    "digit → smallDigit | I V | V smallDigit | I X        { val = 1 × (...) }",
    "smallDigit → I | II | III | ε",
]

# (nonterminal, small nonterminal, one, five, ten, unit)
_ROMAN_LEVELS = [
    ("hundred", "smallHundred", "C", "D", "M", 100),
    ("ten", "smallTen", "X", "L", "C", 10),
    ("digit", "smallDigit", "I", "V", "X", 1),
]


def roman_to_int(text: str) -> tuple[int, Node]:
    """Parse a Roman numeral (1..3999) with the grammar above; return (value, annotated tree)."""
    s = text.strip().upper()
    offset = len(text) - len(text.lstrip()) + 1      # column of s[0]
    if not s:
        raise _error("empty numeral (there is no Roman numeral for 0)", 1)
    pos = 0

    def peek(k: int = 0) -> str:
        return s[pos + k] if pos + k < len(s) else ""

    def small(name: str, one: str, unit: int) -> Node:
        nonlocal pos
        kids = []
        while peek() == one and len(kids) < 3:
            kids.append(Node(one))
            pos += 1
        node = Node(name, kids or [Node("ε")])
        node.attrs["val"] = unit * len(kids)
        return node

    def level(name, small_name, one, five, ten, unit) -> Node:
        nonlocal pos
        if peek() == one and peek(1) in (five, ten):
            pair = peek(1)
            pos += 2
            node = Node(name, [Node(one), Node(pair)])
            node.attrs["val"] = unit * (4 if pair == five else 9)
        elif peek() == five:
            pos += 1
            rest = small(small_name, one, unit)
            node = Node(name, [Node(five), rest])
            node.attrs["val"] = 5 * unit + rest.attrs["val"]
        else:
            rest = small(small_name, one, unit)
            node = Node(name, [rest])
            node.attrs["val"] = rest.attrs["val"]
        return node

    thousand = small("thousand", "M", 1000)
    parts = [thousand] + [level(*lv) for lv in _ROMAN_LEVELS]
    if pos < len(s):
        raise _error(f"{text.strip()[pos]!r} cannot appear here: the numeral is not valid "
                     f"after {s[:pos] or 'the start'!r}", offset + pos)
    value = sum(p.attrs["val"] for p in parts)
    if value == 0:
        raise _error("not a Roman numeral", offset)
    root = Node("romanNum", parts, attrs={"val": value})
    return value, root


INT_TO_ROMAN_SCHEME = [
    "num → th h t u     (the number written with 4 decimal digits)   { num.roman = th.roman ‖ h.roman ‖ t.roman ‖ u.roman }",
    "th → d             { th.roman = R(d, M, -, -) }",
    "h → d              { h.roman = R(d, C, D, M) }",
    "t → d              { t.roman = R(d, X, L, C) }",
    "u → d              { u.roman = R(d, I, V, X) }",
    "R(d, one, five, ten) = ε, one, one one, one one one, one five, five, five one, "
    "five one one, five one one one, one ten   for d = 0..9",
]


def _digit_roman(d: int, one: str, five: str, ten: str) -> str:
    return ["", one, one * 2, one * 3, one + five, five, five + one, five + one * 2,
            five + one * 3, one + ten][d]


def int_to_roman(text: str | int) -> tuple[str, Node]:
    """Integer 1..3999 -> Roman numeral, with an annotated tree of the scheme above."""
    raw = str(text).strip()
    if not raw.isdigit():
        bad = next((i for i, c in enumerate(raw) if not c.isdigit()), 0)
        raise _error("expected a decimal integer", bad + 1)
    n = int(raw)
    if not 1 <= n <= 3999:
        raise _error(f"{n} is out of range: Roman numerals here cover 1 to 3999", 1, "range")
    digits = f"{n:04d}"
    names = [("th", "M", "", ""), ("h", "C", "D", "M"), ("t", "X", "L", "C"),
             ("u", "I", "V", "X")]
    kids = []
    for d, (name, one, five, ten) in zip(digits, names):
        roman = _digit_roman(int(d), one, five, ten)
        kids.append(Node(name, [Node("d", lexeme=d)], attrs={"roman": roman}))
    result = "".join(k.attrs["roman"] for k in kids)
    return result, Node("num", kids, attrs={"roman": result})


# ---------------------------------------------------------------------------
# grammar checkers from the 2.2 exercises

DIV3_GRAMMAR = "num → 11 | 1001 | num 0 | num num"


def div3_tree(s: str) -> Node | None:
    """Parse tree of s for num → 11 | 1001 | num 0 | num num, or None if s is not in L.

    Every node is annotated with its binary value; the value is a multiple of 3 at every
    node, which is the induction step of the proof (11 = 3, 1001 = 9, num 0 doubles the
    value, num₁ num₂ = num₁·2^|num₂| + num₂).
    """
    if not s or set(s) - {"0", "1"}:
        return None

    @lru_cache(maxsize=None)
    def derive(i: int, j: int):
        t = s[i:j]
        if t in ("11", "1001"):
            return ("lit",)
        if j - i >= 2 and s[j - 1] == "0" and derive(i, j - 1):
            return ("zero",)
        for k in range(i + 1, j):
            if derive(i, k) and derive(k, j):
                return ("split", k)
        return None

    def build(i: int, j: int) -> Node:
        how = derive(i, j)
        if how[0] == "lit":
            kids = [Node(c) for c in s[i:j]]
        elif how[0] == "zero":
            kids = [build(i, j - 1), Node("0")]
        else:
            kids = [build(i, how[1]), build(how[1], j)]
        v = int(s[i:j], 2)
        return Node("num", kids, attrs={"val": v, "val mod 3": v % 3})

    return build(0, len(s)) if derive(0, len(s)) else None


def div3_table(max_len: int) -> list[dict]:
    """Every binary string of length 1..max_len: its value, membership in L, value mod 3."""
    rows = []
    for n in range(1, max_len + 1):
        for bits in product("01", repeat=n):
            s = "".join(bits)
            v = int(s, 2)
            rows.append({"string": s, "value": v, "in L(G)": div3_tree(s) is not None,
                         "divisible by 3": v % 3 == 0})
    return rows


BRACKETS_GRAMMAR = "S → ( S ) S | [ S ] S | { S } S | ε"
_CLOSE = {"(": ")", "[": "]", "{": "}"}


def brackets_tree(text: str) -> Node:
    """Recursive-descent parse of balanced brackets; blanks are ignored.

    Attribute depth: S.depth = max(S₁.depth + 1, S₂.depth), ε has depth 0.
    """
    toks = [(c, i + 1) for i, c in enumerate(text) if not c.isspace()]
    for c, col in toks:
        if c not in "()[]{}":
            raise _error(f"unexpected character {c!r}; only brackets are allowed", col)
    toks.append(("", len(text) + 1))
    i = 0

    def s() -> Node:
        nonlocal i
        c, col = toks[i]
        if c not in _CLOSE:
            return Node("S", [Node("ε")], attrs={"depth": 0})
        i += 1
        inner = s()
        want = _CLOSE[c]
        got, got_col = toks[i]
        if got != want:
            found = repr(got) if got else "end of input"
            raise _error(f"expected {want!r} to close {c!r} at column {col}, found {found}",
                         got_col)
        i += 1
        rest = s()
        depth = max(inner.attrs["depth"] + 1, rest.attrs["depth"])
        return Node("S", [Node(c), inner, Node(want), rest], attrs={"depth": depth})

    root = s()
    c, col = toks[i]
    if c:
        raise _error(f"unmatched {c!r}", col)
    return root


LIST_GRAMMARS = {
    "left": "list → list , id | id      (left-associative)",
    "right": "list → id , list | id      (right-associative)",
}


def comma_list_tree(text: str, assoc: str) -> Node:
    """Parse tree of `a, b, c` for the left- or right-recursive list grammar.

    Attribute n: the number of identifiers below the node.
    """
    if assoc not in LIST_GRAMMARS:
        raise ValueError(f"assoc must be 'left' or 'right', not {assoc!r}")
    ids: list[tuple[str, int]] = []
    expect_id = True
    for m in re.finditer(r"\s+|[A-Za-z_]\w*|,|.", text):
        tok, col = m.group(), m.start() + 1
        if tok.isspace():
            continue
        if expect_id:
            if not (tok[0].isalpha() or tok[0] == "_"):
                raise _error(f"expected an identifier, found {tok!r}", col)
            ids.append((tok, col))
        elif tok != ",":
            raise _error(f"expected ',', found {tok!r}", col)
        expect_id = not expect_id
    if expect_id:
        raise _error("expected an identifier, found end of input", len(text) + 1)

    def leaf(name: str) -> Node:
        return Node("id", lexeme=name)

    if assoc == "left":
        node = Node("list", [leaf(ids[0][0])], attrs={"n": 1})
        for k, (name, _) in enumerate(ids[1:], start=2):
            node = Node("list", [node, Node(","), leaf(name)], attrs={"n": k})
        return node
    node = Node("list", [leaf(ids[-1][0])], attrs={"n": 1})
    for k, (name, _) in enumerate(reversed(ids[:-1]), start=2):
        node = Node("list", [leaf(name), Node(","), node], attrs={"n": k})
    return node
