"""Plain-text and Markdown tables, used by every command that prints a table."""


def render_table(headers: list[str], rows: list[list[object]], markdown: bool = False) -> str:
    cells = [[str(c) for c in row] for row in rows]
    if markdown:
        def esc(s: str) -> str:
            return s.replace("|", "\\|")

        lines = ["| " + " | ".join(esc(h) for h in headers) + " |",
                 "|" + "|".join("---" for _ in headers) + "|"]
        lines += ["| " + " | ".join(esc(c) for c in row) + " |" for row in cells]
        return "\n".join(lines)
    widths = [len(h) for h in headers]
    for row in cells:
        widths = [max(w, len(c)) for w, c in zip(widths, row)]

    def fmt(row: list[str]) -> str:
        return "  ".join(c.ljust(w) for c, w in zip(row, widths)).rstrip()

    lines = [fmt(headers), "  ".join("-" * w for w in widths)]
    lines += [fmt(row) for row in cells]
    return "\n".join(lines)
