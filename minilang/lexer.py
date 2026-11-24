"""Lexical analyzer for MiniLang (Dragon Book 3.1, 3.4).

Each token class is recognized by a transition diagram written as an explicit
state machine. State numbers follow the textbook figures where possible:

  relop          Fig. 3.13 (adapted to C operators: < <= > >= == != and = !)
  id / keyword   Fig. 3.14 (states 9-11), keywords found in a table (3.4.3)
  number         Fig. 3.16 (states 12-21): digits (. digits)? (E [+-]? digits)?

A '*' state in the textbook means "retract one character"; here that is
`self.buf.retract()`. All characters are read through the buffer pair in
`buffer.py` (3.2).

Errors (illegal character, malformed number, unterminated comment) are
recorded in `self.errors` and the lexer continues with the next character.
"""

from typing import TextIO

from minilang.buffer import BufferPair
from minilang.errors import CompileError, ErrorList
from minilang.tokens import EQ, GE, GT, KEYWORDS, LE, LT, NE, Token, TokenType

SINGLE_CHAR = {
    "+": TokenType.PLUS,
    "-": TokenType.MINUS,
    "*": TokenType.STAR,
    "(": TokenType.LPAREN,
    ")": TokenType.RPAREN,
    "{": TokenType.LBRACE,
    "}": TokenType.RBRACE,
    ";": TokenType.SEMI,
    ",": TokenType.COMMA,
}
WHITESPACE = " \t\r\n"


def is_letter(c: str) -> bool:
    return c == "_" or ("a" <= c <= "z") or ("A" <= c <= "Z")


def is_digit(c: str) -> bool:
    return "0" <= c <= "9" and c != ""


class NameTable:
    """Table of identifier names; an ID token's attribute is the index here.

    Scopes and types are handled later by the scoped symbol table (2.7).
    """

    def __init__(self) -> None:
        self.names: list[str] = []
        self._index: dict[str, int] = {}

    def install(self, name: str) -> int:
        if name not in self._index:
            self._index[name] = len(self.names)
            self.names.append(name)
        return self._index[name]

    def __getitem__(self, index: int) -> str:
        return self.names[index]

    def __len__(self) -> int:
        return len(self.names)


class Lexer:
    def __init__(self, source: str | TextIO, half_size: int = 4096):
        self.source_text = source if isinstance(source, str) else None
        self.buf = BufferPair(source, half_size)
        self.names = NameTable()
        self.errors = ErrorList()
        self._done = False

    # ------------------------------------------------------------ public API
    def next_token(self) -> Token:
        """Return the next token; after the end of input, always EOF."""
        if self._done:
            return self._make(TokenType.EOF, "")
        try:
            return self._scan()
        except CompileError as e:          # e.g. lexeme longer than the buffer
            line, col = self.buf.line_col(self.buf.begin_pos)
            self.errors.add(CompileError("lexer", e.message, line, col))
            self._done = True
            return self._make(TokenType.EOF, "")

    def tokenize(self) -> list[Token]:
        """All tokens up to and including EOF."""
        tokens = []
        while True:
            tok = self.next_token()
            tokens.append(tok)
            if tok.type is TokenType.EOF:
                return tokens

    def __iter__(self):
        return iter(self.tokenize())

    # ------------------------------------------------------------- helpers
    def _make(self, ttype: TokenType, lexeme: str, value: object = None) -> Token:
        line, col = self.buf.line_col(self.buf.begin_pos)
        return Token(ttype, lexeme, value, line, col)

    def _error(self, message: str) -> None:
        line, col = self.buf.line_col(self.buf.begin_pos)
        self.errors.add(CompileError("lexer", message, line, col))

    # ---------------------------------------------------------- main switch
    def _scan(self) -> Token:
        buf = self.buf
        while True:
            buf.begin_lexeme()
            c = buf.next_char()
            if c == "":
                self._done = True
                return self._make(TokenType.EOF, "")
            if c in WHITESPACE:
                continue
            if c == "/":
                kind = self._comment_or_slash()
                if kind is not None:
                    return kind
                continue
            if is_letter(c):
                return self._id_or_keyword()
            if is_digit(c):
                tok = self._number()
                if tok is not None:
                    return tok
                continue
            if c in "<>=!":
                return self._relop(c)
            if c in "&|":
                tok = self._logical(c)
                if tok is not None:
                    return tok
                continue
            if c in SINGLE_CHAR:
                return self._make(SINGLE_CHAR[c], c)
            self._error(f"illegal character {c!r}")

    # ------------------------------------------------------------- comments
    def _comment_or_slash(self) -> Token | None:
        """'/' was read. Return SLASH, or skip a comment and return None."""
        buf = self.buf
        d = buf.next_char()
        if d == "/":                                   # line comment
            while True:
                buf.begin_lexeme()                     # comments may be long
                c = buf.next_char()
                if c in ("\n", ""):
                    return None
        if d == "*":                                   # block comment
            start_pos = buf.begin_pos
            while True:
                buf.begin_lexeme()
                c = buf.next_char()
                if c == "":
                    line, col = buf.line_col(start_pos)
                    self.errors.add(CompileError("lexer", "unterminated comment", line, col))
                    return None
                if c == "*":
                    d2 = buf.next_char()
                    if d2 == "/":
                        return None
                    buf.retract()                      # d2 may be another '*'
        buf.retract()
        return self._make(TokenType.SLASH, "/")

    # --------------------------------------------- Fig. 3.14: id / keyword
    def _id_or_keyword(self) -> Token:
        buf = self.buf
        state = 10                       # state 9 --letter--> 10
        while True:
            if state == 10:
                c = buf.next_char()
                if is_letter(c) or is_digit(c):
                    state = 10
                else:
                    state = 11
            elif state == 11:            # accepting state with retraction (*)
                buf.retract()
                lexeme = buf.lexeme()
                if lexeme in KEYWORDS:
                    return self._make(KEYWORDS[lexeme], lexeme)
                return self._make(TokenType.ID, lexeme, self.names.install(lexeme))

    # ------------------------------------------------ Fig. 3.16: numbers
    def _number(self) -> Token | None:
        buf = self.buf
        state = 13                       # state 12 --digit--> 13
        while True:
            c = buf.next_char() if state not in (19, 20, 21) else None
            if state == 13:              # integer part
                if is_digit(c):
                    state = 13
                elif c == ".":
                    state = 14
                elif c in ("E", "e"):
                    state = 16
                else:
                    state = 20           # accept integer *
            elif state == 14:            # after '.'
                state = 15 if is_digit(c) else 21
                if state == 21:
                    bad = "expected a digit after '.'"
            elif state == 15:            # fraction part
                if is_digit(c):
                    state = 15
                elif c in ("E", "e"):
                    state = 16
                else:
                    state = 19           # accept real *
            elif state == 16:            # after 'E'
                if c in ("+", "-"):
                    state = 17
                elif is_digit(c):
                    state = 18
                else:
                    state, bad = 21, "expected a digit in the exponent"
            elif state == 17:            # after the exponent sign
                if is_digit(c):
                    state = 18
                else:
                    state, bad = 21, "expected a digit in the exponent"
            elif state == 18:            # exponent digits
                if is_digit(c):
                    state = 18
                else:
                    state = 19           # accept real *
            elif state == 19:
                buf.retract()
                lexeme = buf.lexeme()
                return self._make(TokenType.REAL, lexeme, float(lexeme))
            elif state == 20:
                buf.retract()
                lexeme = buf.lexeme()
                return self._make(TokenType.NUM, lexeme, int(lexeme))
            elif state == 21:            # error: drop the malformed lexeme
                buf.retract()
                self._error(f"malformed number {buf.lexeme()!r}: {bad}")
                return None

    # ---------------------------------------------- Fig. 3.13: relop, =, !
    def _relop(self, first: str) -> Token:
        buf = self.buf
        c = buf.next_char()
        if first == "<":
            if c == "=":
                return self._make(TokenType.RELOP, "<=", LE)
            buf.retract()
            return self._make(TokenType.RELOP, "<", LT)
        if first == ">":
            if c == "=":
                return self._make(TokenType.RELOP, ">=", GE)
            buf.retract()
            return self._make(TokenType.RELOP, ">", GT)
        if first == "=":
            if c == "=":
                return self._make(TokenType.RELOP, "==", EQ)
            buf.retract()
            return self._make(TokenType.ASSIGN, "=")
        # first == "!"
        if c == "=":
            return self._make(TokenType.RELOP, "!=", NE)
        buf.retract()
        return self._make(TokenType.NOT, "!")

    def _logical(self, first: str) -> Token | None:
        c = self.buf.next_char()
        if c == first:
            ttype = TokenType.AND if first == "&" else TokenType.OR
            return self._make(ttype, first * 2)
        self.buf.retract()
        self._error(f"illegal character {first!r} (did you mean {first * 2!r}?)")
        return None


def tokenize(source: str, half_size: int = 4096) -> tuple[list[Token], Lexer]:
    """Convenience: tokens of `source` and the lexer (for its errors and name table)."""
    lexer = Lexer(source, half_size)
    return lexer.tokenize(), lexer
