"""Expression → parse tree generator (2.2, 4.1, 4.2).

The expression is tokenized by the Phase 1 lexer and parsed with the textbook grammar

    E → E + T | E - T | T
    T → T * F | T / F | F
    F → ( E ) | id | num

by recursive descent on its left-recursion-free form (a loop per level, as in 2.5); the
tree is built in the left-recursive shape above, so it matches the textbook drawings.
Every interior node remembers its production (meta["prod"]), so the leftmost and
rightmost derivations of the same tree come from grammar/derivation.py.
"""

from dataclasses import dataclass

from minilang.errors import CompileError
from minilang.grammar import derivation as dv
from minilang.grammar.grammar import Grammar, Production
from minilang.lexer import Lexer
from minilang.tokens import Token, TokenType as T
from minilang.tree import Node

ParseNode = Node      # the name used in the roadmap

EXPR_GRAMMAR_TEXT = """\
E -> E + T | E - T | T
T -> T * F | T / F | F
F -> ( E ) | id | num
"""
EXPR_GRAMMAR = Grammar.parse(EXPR_GRAMMAR_TEXT)

_OPS = {T.PLUS: "+", T.MINUS: "-", T.STAR: "*", T.SLASH: "/", T.LPAREN: "(",
        T.RPAREN: ")"}


@dataclass
class ExprTree:
    source: str
    tokens: list[Token]
    tree: Node          # concrete parse tree
    ast: Node           # abstract syntax tree of the same expression

    @property
    def leftmost(self) -> list[Production]:
        return leftmost_sequence(self.tree)

    @property
    def rightmost(self) -> list[Production]:
        return dv.rightmost_sequence(self.tree)


def _prod(head: str, *body: str) -> Production:
    p = Production(head, tuple(body))
    assert p in EXPR_GRAMMAR.productions, p
    return p


def _node(head: str, children: list[Node]) -> Node:
    body = [c.symbol for c in children]
    n = Node(head, children)
    n.meta["prod"] = _prod(head, *body)
    return n


def _terminal(tok: Token) -> str:
    if tok.type is T.ID:
        return "id"
    if tok.type in (T.NUM, T.REAL):
        return "num"
    return _OPS.get(tok.type, tok.lexeme)


def tokenize_expression(source: str) -> list[Token]:
    """Phase 1 lexer; only tokens that can appear in an expression are allowed."""
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    if lexer.errors:
        raise lexer.errors.errors[0]
    for tok in tokens:
        if tok.type is not T.EOF and tok.type not in _OPS and tok.type not in (T.ID, T.NUM,
                                                                              T.REAL):
            raise CompileError("parser", f"{tok.lexeme!r} cannot appear in an expression "
                               "(only + - * / ( ), identifiers and numbers)", tok.line, tok.col)
    return tokens


class _Parser:
    def __init__(self, tokens: list[Token]):
        self.toks = tokens
        self.i = 0

    @property
    def look(self) -> Token:
        return self.toks[self.i]

    def found(self) -> str:
        t = self.look
        return "end of input" if t.type is T.EOF else repr(t.lexeme)

    def error(self, message: str) -> CompileError:
        return CompileError("parser", message, self.look.line, self.look.col)

    def leaf(self) -> Node:
        tok = self.look
        self.i += 1
        sym = _terminal(tok)
        return Node(sym, lexeme=tok.lexeme if sym in ("id", "num") else None)

    def parse(self) -> Node:
        if self.look.type is T.EOF:
            raise self.error("empty expression")
        e = self.expr()
        if self.look.type is not T.EOF:
            hint = " (missing operator?)" if self.look.type in (T.ID, T.NUM, T.REAL,
                                                                 T.LPAREN) else ""
            if self.look.type is T.RPAREN:
                raise self.error("unmatched ')'")
            raise self.error(f"unexpected {self.found()} after the expression{hint}")
        return e

    def _level(self, head: str, sub_head: str, sub, ops: tuple[T, ...]) -> Node:
        node = _node(head, [sub()])                      # E → T
        while self.look.type in ops:
            op = self.leaf()
            node = _node(head, [node, op, sub()])        # E → E + T (left-recursive shape)
        return node

    def expr(self) -> Node:
        return self._level("E", "T", self.term, (T.PLUS, T.MINUS))

    def term(self) -> Node:
        return self._level("T", "F", self.factor, (T.STAR, T.SLASH))

    def factor(self) -> Node:
        t = self.look
        if t.type is T.LPAREN:
            open_ = self.leaf()
            inner = self.expr()
            if self.look.type is not T.RPAREN:
                raise self.error(f"expected ')' to close '(' at line {t.line}, column "
                                 f"{t.col}, found {self.found()}")
            return _node("F", [open_, inner, self.leaf()])
        if t.type in (T.ID, T.NUM, T.REAL):
            return _node("F", [self.leaf()])
        if t.type is T.MINUS:
            raise self.error("unary minus is not in this grammar; write (0 - x)")
        raise self.error(f"expected an operand (id, number or '('), found {self.found()}")


def to_ast(node: Node) -> Node:
    """Syntax tree (2.8): operators are interior nodes, chain rules and ( ) disappear."""
    kids = node.children
    if node.is_leaf:
        return Node(node.lexeme or node.symbol)
    if len(kids) == 1:                                     # E → T, T → F, F → id
        return to_ast(kids[0])
    if kids[0].symbol == "(":                              # F → ( E )
        return to_ast(kids[1])
    return Node(kids[1].symbol, [to_ast(kids[0]), to_ast(kids[2])])


def parse_expression(source: str) -> ExprTree:
    tokens = tokenize_expression(source)
    tree = _Parser(tokens).parse()
    return ExprTree(source, tokens, tree, to_ast(tree))


# ---------------------------------------------------------------------------
# derivations and partial trees


def leftmost_sequence(tree: Node) -> list[Production]:
    out: list[Production] = []

    def walk(n: Node) -> None:
        if "prod" in n.meta:
            out.append(n.meta["prod"])
            for c in n.children:
                walk(c)

    walk(tree)
    return out


def partial_tree(tree: Node, steps: int, rightmost: bool = False) -> Node:
    """The tree after the first `steps` steps of its leftmost (or rightmost) derivation:
    nonterminals expanded later are leaves without children."""
    order: dict[int, int] = {}

    def number(n: Node) -> None:
        if "prod" in n.meta:
            order[id(n)] = len(order)
            for c in (reversed(n.children) if rightmost else n.children):
                number(c)

    number(tree)

    def copy(n: Node) -> Node:
        new = Node(n.symbol, lexeme=n.lexeme)
        if "prod" in n.meta and order[id(n)] < steps:
            new.children = [copy(c) for c in n.children]
            new.meta["prod"] = n.meta["prod"]
        return new

    return copy(tree)


def derivation_lines(tree: Node, rightmost: bool = False) -> list[str]:
    """Sentential forms; terminals id/num show their lexeme, e.g. id(a)."""
    lexemes = [leaf.lexeme for leaf in tree.leaves() if leaf.lexeme is not None]
    seq = dv.rightmost_sequence(tree) if rightmost else leftmost_sequence(tree)
    forms = dv.forms(EXPR_GRAMMAR, seq, leftmost=not rightmost)
    lines = []
    for f in forms:
        # the terminals id/num of a form are a prefix (leftmost) or suffix (rightmost)
        # of the final string, so their lexemes can be attached in order
        pairs = []
        if rightmost:
            k = sum(1 for s in f if s in ("id", "num"))
            lex = lexemes[len(lexemes) - k:] if k else []
        else:
            lex = lexemes
        it = iter(lex)
        for s in f:
            pairs.append(f"{s}({next(it)})" if s in ("id", "num") else s)
        lines.append(" ".join(pairs))
    return lines
