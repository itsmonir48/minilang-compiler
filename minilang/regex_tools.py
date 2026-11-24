"""Specification of tokens (Dragon Book 3.3): string terms and regular definitions.

Part 1: prefixes, suffixes, substrings, subsequences (3.3.1, Exercise 3.3.3).
Part 2: regular definitions from the lab sheet, written as Python `re` patterns
        and always used with re.fullmatch.

Textbook definitions (3.3.1): a *proper* prefix / suffix / substring of s is
one that is neither the empty string nor s itself.
"""

import re
from collections import Counter
from dataclasses import dataclass
from itertools import combinations
from typing import Callable

# ------------------------------------------------------------ Part 1: strings


def prefixes(s: str) -> list[str]:
    """All prefixes, from ε to s (n + 1 of them)."""
    return [s[:i] for i in range(len(s) + 1)]


def suffixes(s: str) -> list[str]:
    """All suffixes, from s to ε (n + 1 of them)."""
    return [s[i:] for i in range(len(s) + 1)]


def proper_prefixes(s: str) -> list[str]:
    return [p for p in prefixes(s) if p not in ("", s)]


def proper_suffixes(s: str) -> list[str]:
    return [p for p in suffixes(s) if p not in ("", s)]


def substrings(s: str) -> set[str]:
    """All distinct substrings, including ε."""
    return {s[i:j] for i in range(len(s) + 1) for j in range(i, len(s) + 1)}


def proper_substrings(s: str) -> set[str]:
    return substrings(s) - {"", s}


def subsequences(s: str) -> set[str]:
    """All distinct subsequences (delete any characters, keep the order), including ε."""
    return {"".join(c) for k in range(len(s) + 1) for c in combinations(s, k)}


def count_formulas(n: int) -> dict[str, int]:
    """Exercise 3.3.3: counts for a string of length n with all characters distinct."""
    return {
        "prefixes": n + 1,
        "suffixes": n + 1,
        "proper prefixes": max(n - 1, 0),
        "substrings": n * (n + 1) // 2 + 1,
        "subsequences": 2 ** n,
    }


def string_report(s: str) -> dict[str, int]:
    """Actual counts for s (equal to count_formulas(len(s)) when all characters differ)."""
    return {
        "prefixes": len(prefixes(s)),
        "suffixes": len(suffixes(s)),
        "proper prefixes": len(proper_prefixes(s)),
        "substrings": len(substrings(s)),
        "subsequences": len(subsequences(s)),
    }


# ----------------------------------------------- Part 2: regular definitions

CONS = "[b-df-hj-np-tv-z]"          # lowercase consonants


@dataclass(frozen=True)
class Definition:
    name: str
    description: str
    pattern: str | None                       # a true regular expression, or None
    check: Callable[[str], bool]
    note: str = ""


def _regex(pattern: str) -> Callable[[str], bool]:
    compiled = re.compile(pattern)
    return lambda s: compiled.fullmatch(s) is not None


def sql_keyword_pattern(word: str) -> str:
    """Case-insensitive keyword without flags: select -> [Ss][Ee][Ll][Ee][Cc][Tt]."""
    return "".join(f"[{c.upper()}{c.lower()}]" if c.isalpha() else re.escape(c) for c in word)


def _no_repeated_digit(s: str) -> bool:
    return s.isdigit() and len(set(s)) == len(s)


def _at_most_one_repeated_digit(s: str) -> bool:
    return s.isdigit() and sum(1 for k in Counter(s).values() if k > 1) <= 1


VOWELS_IN_ORDER = (
    f"{CONS}*a({CONS}|a)*e({CONS}|e)*i({CONS}|i)*o({CONS}|o)*u({CONS}|u)*"
)
ASCENDING = "".join(f"{chr(c)}*" for c in range(ord("a"), ord("z") + 1))
C_COMMENT = r"/\*([^*]|\*+[^*/])*\*+/"
NO_ABB_SUBSTRING = "b*(a|ab)*"
NO_ABB_SUBSEQUENCE = "b*a*b?a*"
# simplified informal chess notation: p-k4, kbp*qn, n-kb3, q*p
_PIECE = "[kq]?[rbn]?[kqrbnp]"
_SQUARE = "[kq]?[rbn]?[1-8]"
CHESS_MOVE = f"{_PIECE}(-{_SQUARE}|\\*{_PIECE})"

DEFINITIONS: list[Definition] = [
    Definition("vowels", "lowercase letters containing the five vowels in order",
               VOWELS_IN_ORDER, _regex(VOWELS_IN_ORDER),
               "a vowel may repeat but never goes back, e.g. 'facetious', 'abstemious'"),
    Definition("ascending", "lowercase letters in ascending lexicographic order",
               ASCENDING, _regex(ASCENDING)),
    Definition("comment", "comments /* ... */ with no '*/' inside",
               C_COMMENT, _regex(C_COMMENT)),
    Definition("no_repeat_digit", "digit strings with no repeated digit",
               None, _no_repeated_digit,
               "regular (the language is finite) but the pure expression lists all "
               "orderings, so it is checked with a function"),
    Definition("one_repeat_digit", "digit strings with at most one repeated digit",
               None, _at_most_one_repeated_digit,
               "regular for the same reason; 'repeated digit' means a digit value "
               "that occurs more than once"),
    Definition("no_abb", "strings of a and b without the substring abb",
               NO_ABB_SUBSTRING, _regex(NO_ABB_SUBSTRING)),
    Definition("no_abb_subseq", "strings of a and b without the subsequence abb",
               NO_ABB_SUBSEQUENCE, _regex(NO_ABB_SUBSEQUENCE)),
    Definition("chess", "chess moves in informal notation (p-k4, kbp*qn)",
               CHESS_MOVE, _regex(CHESS_MOVE), "simplified: legality of the move is not checked"),
    Definition("sql_select", "SQL keyword SELECT in any letter case",
               sql_keyword_pattern("select"), _regex(sql_keyword_pattern("select"))),
]

BY_NAME = {d.name: d for d in DEFINITIONS}


def matches(name: str, s: str) -> bool:
    return BY_NAME[name].check(s)
