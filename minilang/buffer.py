"""Input buffering with a buffer pair and sentinels (Dragon Book 3.2, Fig. 3.3 and 3.5).

Layout of the buffer (N = half size):

    index:  0 .. N-1      N        N+1 .. 2N     2N+1
            [ half 0 ] [ eof ]    [ half 1 ]   [ eof ]

Each half ends with the sentinel character EOF_CHAR. When `forward` reaches a
sentinel there are two cases (Fig. 3.5):
  * the sentinel is at the end of a half  -> load the other half and continue
  * the sentinel is inside a half         -> real end of input

Only the half that `forward` moves into is ever reloaded, so `lexeme_begin`
must stay in the half that is not reloaded. A lexeme longer than N characters
is therefore an error, exactly as in the textbook.
"""

import io
from bisect import bisect_right
from typing import TextIO

from minilang.errors import CompileError

EOF_CHAR = "\0"


class BufferPair:
    def __init__(self, source: str | TextIO, half_size: int = 4096):
        if half_size < 1:
            raise ValueError("half_size must be at least 1")
        self.stream: TextIO = io.StringIO(source) if isinstance(source, str) else source
        self.n = half_size
        self.buf: list[str] = [EOF_CHAR] * (2 * half_size + 2)
        self.half_chunk = [-1, -1]   # which chunk of the input each half holds
        self.next_chunk = 0          # next chunk number to read from the stream
        self.reloads = 0             # number of times a half was (re)filled
        self.forward = 0             # index of the next character to read
        self.lexeme_begin = 0
        self.overrun = 0             # how many times next_char() returned EOF
        self.pos = 0                 # absolute offset of `forward` in the input
        self.begin_pos = 0           # absolute offset of `lexeme_begin`
        self._newlines: list[int] = []   # offsets of '\n' seen so far
        self._max_pos_seen = -1
        self._load(0)

    # ---------------------------------------------------------------- loading
    def _half_start(self, half: int) -> int:
        return 0 if half == 0 else self.n + 1

    def _half_of(self, index: int) -> int:
        return 0 if index <= self.n else 1

    def _begin_half(self) -> int:
        """Half that holds the first character of the lexeme.

        lexeme_begin may sit on a sentinel slot at the end of a half; the
        lexeme then really starts at the beginning of the other half.
        """
        if self.lexeme_begin == self.n:
            return 1
        if self.lexeme_begin == 2 * self.n + 1:
            return 0
        return self._half_of(self.lexeme_begin)

    def _load(self, half: int) -> None:
        data = self.stream.read(self.n)
        if EOF_CHAR in data:
            raise CompileError("lexer", "input contains the NUL character used as sentinel")
        start = self._half_start(half)
        self.buf[start:start + len(data)] = list(data)
        self.buf[start + len(data)] = EOF_CHAR     # sentinel after the data
        self.half_chunk[half] = self.next_chunk
        self.next_chunk += 1
        self.reloads += 1

    def _enter_other_half(self, half: int) -> None:
        """Move `forward` from the end of `half` to the start of the other half."""
        other = 1 - half
        needed = self.half_chunk[half] + 1
        if self.half_chunk[other] != needed:      # not loaded yet: reload it
            if self._begin_half() == other and self.begin_pos < self.pos:
                raise CompileError(
                    "lexer",
                    f"lexeme longer than the buffer half size ({self.n})",
                )
            self._load(other)
        self.forward = self._half_start(other)

    # ---------------------------------------------------------------- reading
    def next_char(self) -> str:
        """Return the next character and advance; return '' at end of input."""
        if self.overrun:
            self.overrun += 1
            return ""
        while True:
            c = self.buf[self.forward]
            if c != EOF_CHAR:
                break
            half = self._half_of(self.forward)
            end_of_half = self.forward == self._half_start(half) + self.n
            if not end_of_half:                    # sentinel inside a half
                self.overrun = 1
                return ""
            self._enter_other_half(half)
        self.forward += 1
        if self.pos > self._max_pos_seen:
            self._max_pos_seen = self.pos
            if c == "\n":
                self._newlines.append(self.pos)
        self.pos += 1
        return c

    def retract(self, k: int = 1) -> None:
        """Move `forward` back by k characters (the '*' states of a transition diagram)."""
        for _ in range(k):
            if self.overrun:
                self.overrun -= 1
                continue
            if self.pos <= self.begin_pos:
                raise ValueError("cannot retract before lexeme_begin")
            self.forward -= 1
            if self.forward == self.n:             # stepped onto sentinel of half 0
                self.forward = self.n - 1
            elif self.forward < 0:                 # wrap from half 0 to end of half 1
                self.forward = 2 * self.n
            self.pos -= 1

    def begin_lexeme(self) -> None:
        """Start a new lexeme at the current `forward` position."""
        self.lexeme_begin = self.forward
        self.begin_pos = self.pos

    def lexeme(self) -> str:
        """Text between `lexeme_begin` and `forward` (may cross the two halves)."""
        out = []
        i = self.lexeme_begin
        for _ in range(self.pos - self.begin_pos):
            if i == self.n or i == 2 * self.n + 1:    # skip a sentinel slot
                i = 0 if i == 2 * self.n + 1 else self.n + 1
            out.append(self.buf[i])
            i += 1
        return "".join(out)

    # --------------------------------------------------------------- position
    def line_col(self, offset: int | None = None) -> tuple[int, int]:
        """1-based (line, column) of an absolute offset (default: `forward`)."""
        if offset is None:
            offset = self.pos
        line_index = bisect_right(self._newlines, offset - 1)
        line_start = self._newlines[line_index - 1] + 1 if line_index else 0
        return line_index + 1, offset - line_start + 1
