# MiniLang Compiler & Parser Workbench — Project Roadmap

Course: CIT 412 Compiler Design and Automata Theory Sessional
Language: Python 3 (standard library + `pytest`; `ply` only for Phase 7)

---

## 1. Project idea

Build **MiniLang**, a small C-like language, and a **working mini-compiler for it
in Python**:

```
source.mini ──► Lexer ──► Parser ──► AST ──► Semantic check ──► Three-Address Code ──► TAC interpreter
           (Ch 3)     (Ch 2/4)   (Ch 2.8)   (Ch 2.7 symbol table)   (Ch 2.8)          (runs the program)
```

Next to the compiler, build a **Grammar Workbench**. It reads any grammar from a
text file and shows the Chapter 4 algorithms step by step: left recursion
removal, left factoring, FIRST/FOLLOW, LL(1) table, SLR / CLR / LALR tables,
conflicts and parse traces.

So the project is **one connected tool**, not a set of separate exercise files.
Every lab topic from the question files is one module in it (see Section 9).

## 2. The MiniLang language

```c
// example: examples/factorial.mini
int n; int fact;
n = 5; fact = 1;
while (n > 1) {
    fact = fact * n;
    n = n - 1;
}
if (fact >= 100 && !(n == 0)) print(fact); else print(0);
```

Features: `int` / `float` declarations, assignment, `+ - * /`, unary `-`,
`< <= > >= == !=`, `&& || !`, `if / else`, `while`, `{ }` blocks (nested scopes),
`print(expr)`, `//` and `/* */` comments.

Semantics: C-like. `int / int` is integer division; division by zero is a
runtime error. `else` belongs to the nearest unmatched `if`.

Grammar (EBNF, used by the hand-written parser; a plain BNF version with
left recursion goes in `grammars/minilang.txt` for the workbench):

```
program   → stmt*
stmt      → decl | assign ';' | if | while | block | print ';'
decl      → type id ( ',' id )* ';'
type      → 'int' | 'float'
assign    → id '=' bool
if        → 'if' '(' bool ')' stmt ( 'else' stmt )?
while     → 'while' '(' bool ')' stmt
block     → '{' stmt* '}'
print     → 'print' '(' bool ')'
bool      → join ( '||' join )*
join      → equality ( '&&' equality )*
equality  → rel ( ('=='|'!=') rel )*
rel       → expr ( ('<'|'<='|'>'|'>=') expr )?
expr      → term ( ('+'|'-') term )*
term      → unary ( ('*'|'/') unary )*
unary     → ('!'|'-') unary | factor
factor    → '(' bool ')' | id | num | real
```

## 3. Folder structure (target)

```
MiniLang_Compiler/
├── ROADMAP.md               ← this file
├── README.md                ← how to install / run / demo
├── requirements.txt         ← pinned versions (pytest, ply)
├── pyproject.toml           ← package + `minilang` console command
├── demo.sh                  ← runs all demo commands for the viva
├── .github/workflows/tests.yml  ← CI: pytest on every push
├── minilang/
│   ├── __init__.py
│   ├── __main__.py          makes `python -m minilang ...` work (calls cli.main)
│   ├── errors.py            CompileError + pretty print with source line and caret
│   ├── tokens.py            Token class, TokenType enum
│   ├── buffer.py            buffer pair + sentinel reader (3.2)
│   ├── lexer.py             transition-diagram lexer (3.1, 3.3, 3.4)
│   ├── regex_tools.py       string terms + regular definitions (3.3)
│   ├── report.py            plain-text / Markdown tables (used by every command)
│   ├── ast_nodes.py         AST node classes + tree printer (2.8)
│   ├── parser.py            recursive-descent parser + panic-mode recovery (2.4, 4.1, 4.4)
│   ├── parse_tree.py        expression → concrete parse tree (ASCII + .dot) (2.2, 4.1, 4.2)
│   ├── symtab.py            chained scoped symbol table (2.7)
│   ├── semantic.py          undeclared / redeclared / type checks
│   ├── tac.py               three-address code generator (2.8)
│   ├── interpreter.py       runs TAC (proves the compiler is correct)
│   ├── translators.py       Ch 2 SDT tools: infix↔prefix↔postfix, Roman numerals
│   ├── grammar/
│   │   ├── __init__.py
│   │   ├── grammar.py       Grammar class + loader for grammars/*.txt
│   │   ├── transforms.py    left recursion (immediate + general), left factoring (4.3)
│   │   ├── first_follow.py  FIRST / FOLLOW (4.4)
│   │   ├── ll1.py           LL(1) table, conflicts, stack-trace parser (4.4)
│   │   ├── topdown.py       backtracking + predictive recursive descent, step-by-step tree (4.4)
│   │   ├── derivation.py    leftmost / rightmost derivation, ambiguity demo (4.2)
│   │   ├── lr0.py           LR(0) items, closure, goto, SLR table (4.5, 4.6)
│   │   ├── lr1.py           LR(1) items, canonical LR, LALR merge (4.7)
│   │   ├── lr_parser.py     shared LR driver with trace + precedence rules (4.8)
│   │   ├── bottomup.py      shift-reduce visualizer: handles, tree from leaves up (4.5–4.7)
│   └── cli.py               command-line entry point
├── lex/                     Flex programs (3.5) + Makefile; built into lex/build/
├── scripts/                 buffer_experiment.py → docs/buffer_experiment.md
├── yacc_calc/
│   └── calc.py              PLY (Python Lex-Yacc) calculator with `error` recovery (4.9)
├── grammars/                expr.txt, dangling_else.txt, minilang.txt, lalr_demo.txt …
├── examples/                *.mini sample programs (valid + with errors)
├── tests/                   pytest tests for every module
│   └── expected/            golden outputs for traces and tables
└── docs/
    ├── lab_mapping.md       question topic → file → function → demo command
    └── report.md            final lab report
```

## 4. Phases

Each phase ends with: code + tests passing + one git commit (+ push).
Do not start the next phase until the current one works.

### Phase 0 — Setup (1 day)
- [x] `python3 -m venv .venv`, `.venv/bin/pip install pytest ply`, pin in `requirements.txt`
- [x] `pyproject.toml` + `pip install -e .` → a `minilang` command works from anywhere (`minilang run x.mini` instead of `python -m minilang ...`)
- [x] `minilang/errors.py`: one `CompileError(kind, message, line, col)` used by every phase; printed with the source line and a caret:
      ```
      error[parser] line 3, col 10: expected ';' but found 'n'
          fact = 1 n = 2;
                   ^
      ```
- [x] `git init`, `.gitignore`, first commit, create GitHub repo, push
- [x] GitHub Actions (`.github/workflows/tests.yml`): run `pytest` on every push, green badge in README
- [x] Write 4–5 example programs in `examples/` (valid + one with errors each for lexer, parser, semantic)

### Phase 1 — Lexical analyzer (Chapter 3) (3–4 days)
- [x] `tokens.py`: token types (ID, NUM, REAL, RELOP, keywords, operators, EOF), `Token(type, lexeme, value, line, col)`
- [x] `buffer.py`: two-half buffer with `eof` sentinels, `lexeme_begin` / `forward` pointers, `retract()`; small buffer size option to show reloads (3.2)
- [x] Buffer-size experiment: count reloads and time for sizes 16 … 4096 on one large file; save the table in `docs/` (3.2 trade-offs)
- [x] `lexer.py`: reads characters only through `buffer.py`; transition diagrams as explicit states for **id/keyword**, **num** (int, float, `1.5E-3`), **relop**; skip whitespace and comments; attribute values (index into a simple name table for ids, numeric value for numbers; scopes are handled later in Phase 5) (3.1, 3.4)
- [x] `tokens` command prints a `Lexeme | Token | Attribute` table, which answers "divide this code into lexemes" (3.1)
- [x] Lexical errors: illegal char, unterminated comment, bad number → message with `line:col`, then continue
- [x] `regex_tools.py` (3.3): prefixes / suffixes / substrings / subsequences of a string; Python `re` versions of the regular definitions from the question (vowels in order, ascending letters, no repeated digit, no `abb`, chess moves, case-insensitive SQL keywords, comments)
- [x] `lex/minilang.l`: Flex scanner for MiniLang (token name + attribute), built with `make -C lex`; a test checks that it gives the same tokens and positions as `lexer.py` (skipped without flex)
- [x] Small Flex programs (3.5): `wc.l` (chars/words/lines), `numbers.l` (spell out digits), `urls_emails.l` (extract URLs/emails), `strip_comments.l` (remove C/C++ comments)
- [x] CLI: `tokens file.mini [--buffer-size N] [--stats] [--md]`, `strings abc`, `regex [name] [strings...]`
- [x] Tests: every token type, line/col tracking, buffer reload at the boundary, errors

### Phase 2 — Ch 2 translators (2–3 days)
- [ ] `translators.py`: recursive-descent SDT for infix → postfix (2.5), infix → prefix, postfix → infix, postfix → prefix (2.3)
- [ ] Roman numerals ↔ integer with a grammar-based translator (2.2, 2.3)
- [ ] Annotated parse tree printout (node + attribute value) for a given input
- [ ] Small grammar checkers: binary strings divisible by 3, balanced brackets, left- vs right-associative lists
- [ ] Tests

### Phase 3 — Grammar workbench, top-down (Chapter 4.2–4.4) (4–5 days)
- [ ] `grammar.py`: load grammar from text (`E -> E + T | T`, `ε` / `eps`), augment, print
- [ ] `derivation.py`: leftmost / rightmost derivation search for a string (bounded); count parse trees and show two different ones for ambiguous grammars (expr without precedence, dangling-else); list all strings of the language up to length n (helps describe L(G)) (4.2)
- [ ] `transforms.py`: immediate and general (Algorithm 4.19) left-recursion removal; left factoring
- [ ] Dangling-else: textbook matched/open grammar stored in `grammars/dangling_else_fixed.txt`; `derivation.py` shows the old grammar has 2 trees and the fixed one has 1 for `if E then if E then S else S`
- [ ] `first_follow.py`: FIRST of symbols and strings, FOLLOW
- [ ] `ll1.py`: table M[A, a], report multiply-defined entries, table-driven parser that prints `Stack | Input | Action`
- [ ] `topdown.py` — **Top-down parsing visualizer** (4.4), three parsers on the same input:
  - **Backtracking recursive descent** (4.4.1): textbook example `S → c A d`, `A → a b | a` on `cad`; prints every try, failure and backtrack
  - **Predictive recursive descent** (no backtracking): call trace with indentation and current lookahead, e.g. `E() → T() → F() match id(a)`
  - **Table-driven LL(1)**: `Stack | Input | Action` trace (from `ll1.py`)
  - Shows the parse tree **growing from the root down**, one step per expansion (leftmost derivation order)
  - Refuses a left-recursive or non-LL(1) grammar with a clear reason, and offers the transformed grammar from `transforms.py`
- [ ] Tests against the textbook grammar (4.28) answers; backtracking parser accepts `cad`, rejects `cd`

### Phase 3.5 — Expression → Parse Tree generator (Ch 2.2, 4.1, 4.2) (1–2 days)
User gives an expression such as `a + b * (c - 2)`; the tool prints its **parse tree**.
- [ ] `parse_tree.py`: `ParseNode(symbol, children)`; leaves are terminals with their lexeme (`id (a)`, `num (2)`)
- [ ] Expression is tokenized with the Phase 1 lexer, then parsed with the standard grammar
      `E → E + T | E - T | T`, `T → T * F | T / F | F`, `F → ( E ) | id | num`
      (recursive descent on the left-recursion-free form, but the tree is rebuilt in the original left-recursive shape so it matches the textbook)
- [ ] (Trees for other grammars come from `topdown` and `bottomup`; this command is only for expressions.)
- [ ] Output formats:
  - ASCII tree in the terminal (always works)
  - leftmost and rightmost derivation steps of the same tree
  - Graphviz `.dot` file (PNG only if `dot` is installed)
  - AST of the same expression side by side, to show parse tree vs. syntax tree (2.8)
- [ ] Invalid expression (`a + * b`): clear error with the position, no crash
- [ ] Tests: tree shape for `9-5+2` (left-associative), `a+b*c` (precedence), `(a+b)*c` (parentheses), error case

### Phase 4 — Main parser + AST (Ch 2.4, 2.8, 4.1) (4 days)
- [ ] `ast_nodes.py`: `Program, Decl, Assign, If, While, Block, Print, BinOp, UnOp, Id, Num`; ASCII tree printer
- [ ] `parser.py`: recursive descent following Section 2 grammar, builds AST
- [ ] Panic-mode recovery: on error, report, skip tokens to a sync set (`;`, `}`, FOLLOW(stmt)), continue → many errors in one run
- [ ] Tests: valid programs give expected AST; broken programs give the expected error list

### Phase 5 — Symbol table + semantic check + TAC + interpreter (Ch 2.7, 2.8) (4–5 days)
- [ ] `symtab.py`: `Env` with parent link; new env per block; lookup walks outward (2.7)
- [ ] `semantic.py`: undeclared use, redeclaration in same scope, int/float type of expressions, warning for float → int assignment
- [ ] `tac.py`: temps `t1, t2…`, labels `L1, L2…`; assignment, expressions, `if/else`, `while`, short-circuit `&& || !` with jumps; print as quadruples table too
- [ ] `interpreter.py`: execute the TAC list (label map + program counter)
- [ ] Tests: run every example, compare printed output with the expected output file

### Phase 6 — Bottom-up parsing (Ch 4.5–4.8) (5–6 days)
- [ ] `lr0.py`: LR(0) items, CLOSURE, GOTO, canonical collection; SLR ACTION/GOTO with FOLLOW
- [ ] `lr_parser.py`: one LR driver (shift / reduce / accept / error) used by SLR, CLR and LALR tables; it records each step, and `bottomup.py` prints them
- [ ] Conflict report: shift/reduce and reduce/reduce with state + symbol
- [ ] `lr1.py`: LR(1) items, canonical LR(1) table; LALR by merging same-core states; detect new reduce/reduce conflicts after merging
- [ ] Comparison table: number of states and conflicts for SLR / CLR / LALR on the same grammars
- [ ] `bottomup.py` — **Bottom-up parsing visualizer** (4.5–4.7), on an expression the user types:
  - **Shift-reduce trace**: `Stack | Input | Action` with the **handle marked** at every reduce, e.g. `$ E + [T * F]  →  reduce T → T * F`
  - Parse tree **growing from the leaves up** to the start symbol, one step per reduce
  - **Rightmost derivation in reverse** printed from the reduce steps (shows why LR = "rightmost derivation in reverse")
  - Choose the table: `--method slr|clr|lalr` (same driver, different table)
  - When the table has a conflict, show the state, the symbol and both choices (shift/reduce or reduce/reduce), then the result after precedence rules (4.8)
  - Syntax error: show the state, the unexpected token and the expected tokens (the non-empty ACTION entries of that state)
- [ ] `compare` command: LL(1) trace (root → leaves, leftmost derivation, grammar `E → T E'`) next to SLR trace (leaves → root, rightmost derivation in reverse, grammar `E → E + T`) for the same expression
- [ ] Ambiguous grammars (4.8): `%left / %right` style precedence to resolve conflicts in `E → E+E | E*E | (E) | id`; dangling-else resolved by preferring shift
- [ ] Tests on textbook grammars (4.1, 4.49, 4.55)

### Phase 7 — Yacc-style tools (Ch 4.9) (2 days)
- [ ] `yacc_calc/calc.py` with **PLY**: desktop calculator, variables, parentheses, precedence, `error` token panic-mode recovery
- [ ] Explain in the report that PLY = Python Lex/Yacc and is used because Bison is not installed

### Phase 8 — CLI, docs, report, demo (3 days)
- [ ] `cli.py`, run as `python -m minilang <command>`:
  - `tokens file.mini` · `ast file.mini` · `tac file.mini` · `run file.mini`
  - `parsetree "a + b * (c - 2)" [--derivation] [--ast] [--dot out.dot]`
  - `topdown "a + b * c" --method backtrack|recursive|ll1 [--grammar ...]`
  - `bottomup "a + b * c" --method slr|clr|lalr [--grammar ...] [--items] [--table]`
  - `compare "a + b * c"`: top-down and bottom-up traces side by side
  - `grammar grammars/expr.txt --first-follow --ll1 --slr --lalr --clr --trace "id+id*id"`
  - `translate --infix-to-postfix "9-5+2"` · `roman 1994`
  - `repl`: interactive mode; type a statement or expression, see tokens / tree / TAC / result at once
  - global flag `--md`: print any table or trace as Markdown, ready to paste into the report
- [ ] `demo.sh`: runs every demo command in order with a heading for each (one command for the viva)
- [ ] `docs/lab_mapping.md`: every bullet in the three question files → file + function + demo command
- [ ] `README.md` + `docs/report.md` (screenshots / outputs of each command)
- [ ] Final run of all tests; tag `v1.0` on GitHub

## 5. Schedule (about 6 weeks; change if your deadline is different)

The phase estimates add up to about 30 working days.

| Week | Phases |
|------|--------|
| 1 | Phase 0, Phase 1 |
| 2 | Phase 2, Phase 3 (start) |
| 3 | Phase 3 (finish), Phase 3.5, Phase 4 (start) |
| 4 | Phase 4 (finish), Phase 5 |
| 5 | Phase 6 |
| 6 | Phase 7, Phase 8, buffer |

## 6. Rules for the code

- Write each algorithm yourself (no parser library) except PLY in Phase 7.
- Every algorithm can print its steps (`--trace`): this is what the teacher wants to see.
- Small functions, docstrings that name the textbook section (e.g. `"""Algorithm 4.31 (LL(1) table)"""`).
- Each module has tests in `tests/`. Run: `.venv/bin/pytest -q`.
- Golden-file tests for traces and tables: the expected output is saved in `tests/expected/*.txt`
  and the test compares it; `pytest --update-golden` rewrites them after an intended change
  (check the diff before committing).
- Every phase's errors go through `errors.py`, so all messages look the same.
- Commit after each finished checklist item group; message like `phase3: FIRST/FOLLOW`.

## 7. Definition of done

- `python -m minilang run examples/factorial.mini` prints `120`.
- A program with 3 errors shows all 3 errors with line numbers (no crash).
- `python -m minilang parsetree "a+b*c"` prints the correct parse tree (`*` lower in the tree than `+`).
- `topdown` and `bottomup` both accept `a+b*c` and reject `a+*b` with a clear message.
- The same grammar shows SLR, CLR and LALR tables plus a state-count comparison.
- All tests pass locally and on GitHub Actions; every question topic is listed in `docs/lab_mapping.md`.
- `./demo.sh` runs from start to end without an error.

## 8. Optional extras (only if time remains)

- Thompson construction (regex → NFA) + subset construction (NFA → DFA) + DFA minimization (Ch 3.7–3.9).
- Basic optimizations: constant folding, dead-code removal after `if (0)`.

## 9. Coverage of the question files

| Question topic | Where |
|---|---|
| 2.2 CFG, parse trees, ambiguity, language of a grammar, grammar design (postfix, comma lists, unary +/-), Roman numerals, divisible-by-3 | `parse_tree.py`, `grammar/derivation.py`, `translators.py`, `grammars/` |
| 2.3 SDT: infix→prefix, postfix→infix, postfix→prefix, Roman ↔ int, annotated trees | `translators.py` |
| 2.4 Recursive descent, left recursion | `parser.py`, `grammar/transforms.py` |
| 2.5 Infix → postfix translator | `translators.py` |
| 2.7 Scoped symbol tables | `symtab.py` |
| 2.8 AST, three-address code, if/while/and/or/not | `ast_nodes.py`, `tac.py` |
| 3.1 Tokens, lexemes, attributes | `lexer.py` |
| 3.2 Buffer pairs + sentinels, buffer-size trade-offs | `buffer.py`, buffer-size experiment |
| 3.3 String terms, regular expressions/definitions | `regex_tools.py` |
| 3.4 Transition diagrams (id, num, relop) | `lexer.py` |
| 3.5 Lex/Flex: wc, spell out numbers, URLs/emails, strip comments, mini-language scanner | `lex/` |
| 4.1 Error recovery, parse trees | `parser.py` (panic mode), `parse_tree.py` |
| 4.2 Derivations, ambiguity, language L(G) | `grammar/derivation.py` |
| 4.3 Left recursion, left factoring, dangling-else | `grammar/transforms.py`, `grammars/dangling_else_fixed.txt` |
| 4.4 Top-down parsing: recursive descent (backtracking + predictive), FIRST/FOLLOW, LL(1) table, stack trace | `grammar/topdown.py`, `grammar/first_follow.py`, `grammar/ll1.py` |
| 4.5 Bottom-up parsing: handles, handle pruning, shift-reduce, conflicts | `grammar/bottomup.py`, `grammar/lr_parser.py` |
| 4.6 LR(0) items, SLR | `grammar/lr0.py` |
| 4.7 LR(1), LALR, comparison | `grammar/lr1.py` |
| 4.8 Precedence/associativity, dangling-else in LR | `grammar/lr_parser.py` |
| 4.9 Yacc calculator, error token, mini-compiler parser | `yacc_calc/calc.py`, whole pipeline |
