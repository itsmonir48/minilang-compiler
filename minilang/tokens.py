"""Token types and the Token record (Dragon Book 3.1.2: tokens, patterns, lexemes)."""

from dataclasses import dataclass
from enum import Enum


class TokenType(Enum):
    # names and literals
    ID = "id"
    NUM = "num"          # integer literal, value = int
    REAL = "real"        # floating literal, value = float
    # relational operators share one token; the attribute says which one (Fig. 3.10)
    RELOP = "relop"
    # keywords
    INT = "int"
    FLOAT = "float"
    IF = "if"
    ELSE = "else"
    WHILE = "while"
    PRINT = "print"
    # operators
    PLUS = "+"
    MINUS = "-"
    STAR = "*"
    SLASH = "/"
    ASSIGN = "="
    AND = "&&"
    OR = "||"
    NOT = "!"
    # punctuation
    LPAREN = "("
    RPAREN = ")"
    LBRACE = "{"
    RBRACE = "}"
    SEMI = ";"
    COMMA = ","
    EOF = "EOF"


KEYWORDS: dict[str, TokenType] = {
    "int": TokenType.INT,
    "float": TokenType.FLOAT,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "print": TokenType.PRINT,
}

# attribute values of RELOP
LT, LE, GT, GE, EQ, NE = "LT", "LE", "GT", "GE", "EQ", "NE"
RELOP_TEXT = {LT: "<", LE: "<=", GT: ">", GE: ">=", EQ: "==", NE: "!="}


@dataclass(frozen=True)
class Token:
    """One token.

    value is the attribute value:
      ID    -> index of the name in the lexer's NameTable
      NUM   -> int value, REAL -> float value
      RELOP -> one of LT, LE, GT, GE, EQ, NE
      other -> None
    """

    type: TokenType
    lexeme: str
    value: object = None
    line: int = 0
    col: int = 0

    def __str__(self) -> str:
        if self.value is None:
            return f"<{self.type.value}>"
        return f"<{self.type.value}, {self.value}>"
