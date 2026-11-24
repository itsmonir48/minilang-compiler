# MiniLang Compiler & Parser Workbench

[![tests](https://github.com/itsmonir48/minilang-compiler/actions/workflows/tests.yml/badge.svg)](https://github.com/itsmonir48/minilang-compiler/actions/workflows/tests.yml)

A small C-like language and a complete mini-compiler written in Python
(lexer → parser → AST → semantic check → three-address code → interpreter),
plus a grammar workbench for FIRST/FOLLOW, LL(1), SLR, CLR and LALR,
with step-by-step top-down and bottom-up parse traces.

CIT 412 Compiler Design and Automata Theory Sessional.

Status: Phase 1 (lexical analyzer) done. See [ROADMAP.md](ROADMAP.md).

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install -e .
.venv/bin/pytest -q
.venv/bin/minilang --version
```

## Try it

```bash
minilang ui                                      # web interface in the browser (MiniLang Compiler Studio)
minilang tokens examples/factorial.mini          # Lexeme | Token | Attribute table
minilang tokens examples/lexer_errors.mini       # 4 lexical errors with line:col
minilang tokens --buffer-size 8 --stats examples/scopes.mini
minilang strings abcd                            # prefixes, suffixes, substrings, ...
minilang regex                                   # list the regular definitions
minilang regex no_abb abab abba
make -C lex demo                                 # Flex programs (needs flex + gcc)
python scripts/buffer_experiment.py              # writes docs/buffer_experiment.md
```

## Layout

| Path | Contents |
|---|---|
| `minilang/` | the compiler and workbench package (engine) |
| `app/` | web interface (Streamlit), started with `minilang ui` |
| `examples/` | sample `.mini` programs; `*.expected` holds the expected output of valid programs |
| `tests/` | pytest tests; `tests/expected/` holds golden outputs (`pytest --update-golden` rewrites them) |
| `grammars/` | grammar files for the workbench |
| `lex/` | Flex programs (`make -C lex demo`) |
| `scripts/` | experiment scripts; results go to `docs/` |
| `docs/` | lab mapping and report |
