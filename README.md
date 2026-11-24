# MiniLang Compiler & Parser Workbench

[![tests](https://github.com/itsmonir48/minilang-compiler/actions/workflows/tests.yml/badge.svg)](https://github.com/itsmonir48/minilang-compiler/actions/workflows/tests.yml)

A small C-like language and a complete mini-compiler written in Python
(lexer → parser → AST → semantic check → three-address code → interpreter),
plus a grammar workbench for FIRST/FOLLOW, LL(1), SLR, CLR and LALR,
with step-by-step top-down and bottom-up parse traces.

CIT 412 Compiler Design and Automata Theory Sessional.

Status: Phase 0 (setup) done. See [ROADMAP.md](ROADMAP.md).

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install -e .
.venv/bin/pytest -q
.venv/bin/minilang --version
```

## Layout

| Path | Contents |
|---|---|
| `minilang/` | the compiler and workbench package |
| `examples/` | sample `.mini` programs; `*.expected` holds the expected output of valid programs |
| `tests/` | pytest tests; `tests/expected/` holds golden outputs (`pytest --update-golden` rewrites them) |
| `grammars/` | grammar files for the workbench |
| `lex/` | Flex versions of the scanners |
| `docs/` | lab mapping and report |
