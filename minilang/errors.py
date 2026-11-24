"""One error type for every compiler phase, printed with the source line and a caret."""

from dataclasses import dataclass, field


@dataclass
class CompileError(Exception):
    """An error found while compiling.

    kind:    which phase found it: "lexer", "parser", "semantic", "runtime", ...
    message: human-readable description
    line:    1-based line number (0 if unknown)
    col:     1-based column number (0 if unknown)
    """

    kind: str
    message: str
    line: int = 0
    col: int = 0

    def __post_init__(self) -> None:
        super().__init__(self.message)

    def format(self, source: str | None = None) -> str:
        """Return the message; if the source text is given, add the line and a caret."""
        if self.line <= 0:
            return f"error[{self.kind}]: {self.message}"
        header = f"error[{self.kind}] line {self.line}, col {self.col}: {self.message}"
        if source is None:
            return header
        lines = source.splitlines()
        if self.line > len(lines):
            return header
        text = lines[self.line - 1].expandtabs(4)
        caret = " " * max(self.col - 1, 0) + "^"
        return f"{header}\n    {text}\n    {caret}"


@dataclass
class ErrorList:
    """Collects errors so one run can report many of them (panic-mode style)."""

    errors: list[CompileError] = field(default_factory=list)

    def add(self, error: CompileError) -> None:
        self.errors.append(error)

    def __bool__(self) -> bool:
        return bool(self.errors)

    def __len__(self) -> int:
        return len(self.errors)

    def format(self, source: str | None = None) -> str:
        return "\n".join(e.format(source) for e in self.errors)
