# MiniLang Compiler & Parser Workbench

[![tests](https://github.com/itsmonir48/minilang-compiler/actions/workflows/tests.yml/badge.svg)](https://github.com/itsmonir48/minilang-compiler/actions/workflows/tests.yml)

A small C-like language and a complete mini-compiler written in Python
(lexer → parser → AST → semantic check → three-address code → interpreter),
plus a grammar workbench for FIRST/FOLLOW, LL(1), SLR, CLR and LALR,
with step-by-step top-down and bottom-up parse traces.

CIT 412 Compiler Design and Automata Theory Sessional.

Status: Phase 3.5 (expression → parse tree) done. See [ROADMAP.md](ROADMAP.md). Full explanation of the project: [docs/PROJECT_GUIDE.md](docs/PROJECT_GUIDE.md).

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
minilang translate '9-5+2' --tree --trace          # infix -> postfix/prefix, annotated tree, 2.5 trace
minilang translate '95-2+' --from postfix          # postfix -> infix/prefix
minilang roman MCMXCIV --tree                      # Roman <-> integer (direction is detected)
minilang check div3 --table 6                      # num -> 11 | 1001 | num 0 | num num
minilang check brackets '([]){}'                   # balanced brackets
minilang grammar expr --remove-left-recursion --ll1 # grammar workbench (grammars/*.txt)
minilang grammar expr_ll1 --first-follow --ll1      # FIRST / FOLLOW, LL(1) table
minilang derive expr_ambiguous 'id+id*id'           # 2 parse trees: ambiguous
minilang derive ab_equal --language 4               # strings of L(G) up to length 4
minilang topdown backtrack cad --method backtrack   # try, fail, backtrack
minilang topdown expr_ll1 'id+id*id'                # Stack | Input | Action
minilang parsetree 'a + b * (c - 2)' --all         # parse tree, derivations, AST
minilang parsetree '9-5+2' --dot tree.dot           # Graphviz file (add --png if dot is installed)
make -C lex demo                                 # Flex programs (needs flex + gcc)
python scripts/buffer_experiment.py              # writes docs/buffer_experiment.md
```

## Layout

| Path | Contents |
|---|---|
| `minilang/` | the compiler and workbench package (engine) |
| `app/` | web interface (Streamlit), started with `minilang ui`: `Home.py` (navigation by chapter), `overview.py` (home page), `pages/`, `static/logo.svg` |
| `examples/` | sample `.mini` programs; `*.expected` holds the expected output of valid programs |
| `tests/` | pytest tests; `tests/expected/` holds golden outputs (`pytest --update-golden` rewrites them) |
| `grammars/` | grammar files for the workbench |
| `lex/` | Flex programs (`make -C lex demo`) |
| `scripts/` | experiment scripts; results go to `docs/` |
| `docs/` | lab mapping and report |
