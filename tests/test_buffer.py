import io
import random

import pytest

from minilang.buffer import BufferPair
from minilang.errors import CompileError


def read_all(b: BufferPair) -> str:
    out = []
    while (c := b.next_char()) != "":
        out.append(c)
        b.begin_lexeme()
    return "".join(out)


@pytest.mark.parametrize("n", [1, 2, 3, 7, 4096])
def test_reads_whole_input(n):
    text = "int x;\nx = 10;\n" * 5
    assert read_all(BufferPair(text, n)) == text


def test_reads_from_file_object():
    text = "while (a < b) a = a + 1;"
    assert read_all(BufferPair(io.StringIO(text), 4)) == text


def test_empty_input():
    b = BufferPair("", 4)
    assert b.next_char() == ""
    assert b.next_char() == ""


def test_reload_count():
    # 20 chars, half size 4 -> chunks of 4,4,4,4,4 and one empty chunk = 6 loads
    b = BufferPair("a" * 20, 4)
    read_all(b)
    assert b.reloads == 6


def test_lexeme_across_halves():
    b = BufferPair("abcdefgh", 4)
    for _ in range(2):
        b.next_char()
    b.begin_lexeme()          # lexeme starts at 'c' (half 0)
    for _ in range(4):
        b.next_char()         # reads c d | e f  (crosses into half 1)
    assert b.lexeme() == "cdef"


def test_retract_across_sentinel():
    b = BufferPair("abcdefgh", 4)
    b.begin_lexeme()
    for _ in range(5):
        b.next_char()         # a b c d | e
    b.retract(2)              # back before 'd'
    assert b.lexeme() == "abc"
    assert b.next_char() == "d"
    assert b.next_char() == "e"     # half 1 is not reloaded a second time
    assert b.next_char() == "f"


def test_retract_after_eof():
    b = BufferPair("ab", 4)
    b.begin_lexeme()
    b.next_char(), b.next_char()
    assert b.next_char() == ""      # lookahead past the end
    b.retract()                     # the '*' retraction of an accepting state
    assert b.lexeme() == "ab"
    assert b.next_char() == ""


def test_cannot_retract_before_lexeme_begin():
    b = BufferPair("abc", 4)
    b.next_char()
    b.begin_lexeme()
    with pytest.raises(ValueError):
        b.retract()


def test_lexeme_longer_than_half_is_error():
    b = BufferPair("abcdefghij", 4)
    b.begin_lexeme()
    with pytest.raises(CompileError, match="longer than the buffer half size"):
        for _ in range(10):
            b.next_char()


def test_lexeme_of_exactly_half_size_starting_at_half_boundary():
    b = BufferPair("abcdefghijkl", 4)
    for _ in range(4):
        b.next_char()
    b.begin_lexeme()                # forward is on the sentinel after half 0
    for _ in range(4):
        b.next_char()               # e f g h fills half 1 exactly
    assert b.next_char() == "i"     # reloading half 0 is allowed here
    b.retract()
    assert b.lexeme() == "efgh"


def test_nul_character_rejected():
    with pytest.raises(CompileError, match="NUL"):
        BufferPair("a\0b", 4)


def test_line_col():
    b = BufferPair("ab\ncd\n\ne", 3)
    read_all(b)
    assert b.line_col(0) == (1, 1)
    assert b.line_col(2) == (1, 3)      # the '\n' itself
    assert b.line_col(3) == (2, 1)
    assert b.line_col(6) == (3, 1)
    assert b.line_col(7) == (4, 1)


def test_random_reads_and_retracts_match_plain_string():
    rng = random.Random(1)
    text = "".join(rng.choice("abc \n") for _ in range(300))
    for n in (3, 5, 8):
        b = BufferPair(text, n)
        pos = 0
        while pos < len(text):
            b.begin_lexeme()
            k = min(rng.randint(1, n), len(text) - pos)   # lexeme length <= n
            got = "".join(b.next_char() for _ in range(k))
            assert got == text[pos:pos + k]
            back = rng.randint(0, k)
            b.retract(back)
            consumed = k - back
            assert b.lexeme() == text[pos:pos + consumed]
            if consumed == 0:
                b.next_char()
                consumed = 1
            pos += consumed
