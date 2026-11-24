"""Context-free grammars (4.2): loading from text, augmenting, printing.

Text format, one or more alternatives per line:

    # comment
    E -> E + T | T
    T -> T * F
       | F
    F -> ( E ) | id
    A -> a A | ε          (ε, eps, epsilon or an empty alternative)

* The head of the first rule is the start symbol.
* Every symbol that appears as a head is a nonterminal; all others are terminals.
* Symbols are separated by blanks; `|` separates alternatives; `->` or `→` is the arrow.
"""

from dataclasses import dataclass
from pathlib import Path

from minilang.errors import CompileError

EPS = "ε"
END = "$"
_EPS_WORDS = {"ε", "ϵ", "eps", "epsilon"}

GRAMMARS_DIR = Path(__file__).resolve().parent.parent.parent / "grammars"


@dataclass(frozen=True)
class Production:
    head: str
    body: tuple[str, ...]

    def __str__(self) -> str:
        return f"{self.head} → {' '.join(self.body) if self.body else EPS}"

    def body_text(self) -> str:
        return " ".join(self.body) if self.body else EPS


class Grammar:
    def __init__(self, productions: list[Production], start: str | None = None):
        if not productions:
            raise CompileError("grammar", "the grammar has no productions")
        self.productions: list[Production] = []
        for p in productions:                       # keep order, drop duplicates
            if p not in self.productions:
                self.productions.append(p)
        self.start = start or self.productions[0].head
        self.nonterminals: list[str] = []
        for p in self.productions:
            if p.head not in self.nonterminals:
                self.nonterminals.append(p.head)
        if self.start not in self.nonterminals:
            raise CompileError("grammar", f"start symbol {self.start!r} has no productions")
        nts = set(self.nonterminals)
        self.terminals: list[str] = []
        for p in self.productions:
            for s in p.body:
                if s not in nts and s not in self.terminals:
                    self.terminals.append(s)

    # ------------------------------------------------------------------ queries
    def is_nonterminal(self, sym: str) -> bool:
        return sym in self.nonterminals

    def prods_of(self, head: str) -> list[Production]:
        return [p for p in self.productions if p.head == head]

    def index(self, p: Production) -> int:
        return self.productions.index(p)

    def fresh_name(self, base: str) -> str:
        """A new nonterminal name: A', A'', ..."""
        name = base + "'"
        taken = set(self.nonterminals) | set(self.terminals)
        while name in taken:
            name += "'"
        return name

    def augmented(self) -> "Grammar":
        """S' → S added in front (4.6.2)."""
        new = self.fresh_name(self.start)
        return Grammar([Production(new, (self.start,))] + self.productions, new)

    # ------------------------------------------------------------------ text
    def rules(self) -> list[tuple[str, list[str]]]:
        """(head, [alternative texts]) in order of the nonterminals."""
        return [(a, [p.body_text() for p in self.prods_of(a)]) for a in self.nonterminals]

    def to_text(self, arrow: str = "→") -> str:
        width = max(len(a) for a in self.nonterminals)
        return "\n".join(f"{a.ljust(width)} {arrow} {' | '.join(alts)}"
                         for a, alts in self.rules())

    def __str__(self) -> str:
        return self.to_text()

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, Grammar) and self.start == other.start
                and set(self.productions) == set(other.productions))

    # ------------------------------------------------------------------ loading
    @classmethod
    def parse(cls, text: str) -> "Grammar":
        prods: list[Production] = []
        head = None
        for lineno, line in enumerate(text.splitlines(), start=1):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            stripped = line.strip()
            if stripped.startswith("|"):
                if head is None:
                    raise CompileError("grammar", "'|' with no rule before it", lineno,
                                       line.index("|") + 1)
                alts_text = stripped[1:].split("|")
            else:
                arrow = "->" if "->" in line else ("→" if "→" in line else None)
                if arrow is None:
                    raise CompileError("grammar", "expected '->' (or '→') in a rule", lineno,
                                       len(line) - len(line.lstrip()) + 1)
                lhs, rhs = line.split(arrow, 1)
                head_syms = lhs.split()
                if len(head_syms) != 1:
                    raise CompileError(
                        "grammar", "the left side of a rule must be one nonterminal",
                        lineno, len(lhs) - len(lhs.lstrip()) + 1)
                head = head_syms[0]
                if head in _EPS_WORDS:
                    raise CompileError("grammar", "ε cannot be a nonterminal", lineno, 1)
                alts_text = rhs.split("|")
            for alt in alts_text:
                syms = [s for s in alt.split() if s not in _EPS_WORDS]
                prods.append(Production(head, tuple(syms)))
        if not prods:
            raise CompileError("grammar", "the grammar has no rules")
        return cls(prods)

    @classmethod
    def load(cls, path: str | Path) -> "Grammar":
        return cls.parse(Path(path).read_text(encoding="utf-8"))


def grammar_names() -> list[str]:
    return sorted(p.stem for p in GRAMMARS_DIR.glob("*.txt"))


def grammar_path(name_or_path: str) -> Path:
    """A file path, or the name of a file in grammars/ (with or without .txt)."""
    p = Path(name_or_path)
    if p.exists():
        return p
    for cand in (GRAMMARS_DIR / name_or_path, GRAMMARS_DIR / f"{name_or_path}.txt"):
        if cand.exists():
            return cand
    raise FileNotFoundError(name_or_path)


def load_grammar(name_or_path: str) -> Grammar:
    return Grammar.load(grammar_path(name_or_path))


def grammar_comment(name_or_path: str) -> str:
    """The leading # comment lines of a grammar file (its description)."""
    lines = []
    for line in grammar_path(name_or_path).read_text(encoding="utf-8").splitlines():
        if not line.startswith("#"):
            break
        lines.append(line[1:].strip())
    return " ".join(lines)


def tokenize_input(g: Grammar, text: str) -> list[tuple[str, int]]:
    """Split an input string into terminals of g by longest match; blanks are skipped.

    `id+id*id` and `id + id * id` both give id + id * id. Returns (terminal, column).
    """
    terms = sorted(g.terminals, key=len, reverse=True)
    out: list[tuple[str, int]] = []
    i = 0
    while i < len(text):
        if text[i].isspace():
            i += 1
            continue
        for t in terms:
            if text.startswith(t, i):
                out.append((t, i + 1))
                i += len(t)
                break
        else:
            raise CompileError("input", f"{text[i]!r} does not start any terminal of the "
                               f"grammar ({' '.join(g.terminals)})", 1, i + 1)
    return out
