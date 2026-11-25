# Project Proposal: MiniLang Compiler Studio


## 1. Introduction

A compiler is built from several phases: lexical analysis, syntax analysis,
syntax-directed translation, semantic analysis and intermediate code generation.
Chapters 2 to 4 of *Compilers: Principles, Techniques, and Tools* (Aho, Lam, Sethi,
Ullman; the "Dragon Book") describe these phases with algorithms such as transition
diagrams, FIRST and FOLLOW sets, LL(1) tables and LR parsing tables.

This project proposes MiniLang Compiler Studio: a compiler for a small C-like
language, MiniLang, written in Python. Next to the compiler is a grammar workbench that
runs the Chapter 2–4 algorithms step by step. Both are used through a web interface in
the browser and through a command-line tool, `minilang`.

## 2. Problem statement

The lab problems of CIT 412 ask for many separate tasks:

- tokenizing input;
- buffer pairs;
- regular definitions;
- translation schemes;
- left recursion removal;
- FIRST/FOLLOW sets;
- LL(1) and LR tables;
- stack traces;
- a Yacc calculator.

Solved as separate small programs, these tasks have three weaknesses:

1. They do not show how the phases of a compiler connect. The lexer's output should be
   the parser's input, and the parser's tree should be the input of code generation.
2. They usually print only the final answer, while the lab problems ask for the steps:
   stack contents, derivations, the passes of FIRST/FOLLOW, backtracking.
3. Their answers are rarely checked against the textbook, so errors in a table or a
   trace go unnoticed.

The project addresses all three with one connected tool that shows each algorithm
step by step and is checked by automated tests.

## 3. Objectives

1. Design a small C-like language, MiniLang, and build a working compiler for it:
   - lexer;
   - parser with error recovery;
   - abstract syntax tree;
   - scoped symbol table and semantic checks;
   - three-address code;
   - an interpreter that runs the generated code.
2. Implement the Chapter 3 lexical-analysis topics:
   - tokens and attributes;
   - buffer pairs with sentinels;
   - regular definitions;
   - transition diagrams;
   - Flex programs.
3. Implement the Chapter 2 translators:
   - infix, postfix and prefix conversion;
   - Roman numerals;
   - annotated parse trees;
   - the small grammars of the exercises.
4. Implement the Chapter 4 parsing algorithms as a grammar workbench:
   - derivations and ambiguity;
   - left recursion removal and left factoring;
   - FIRST/FOLLOW and the LL(1) table;
   - top-down parsers;
   - LR(0), SLR, canonical LR(1) and LALR tables;
   - bottom-up parsers;
   - a Yacc-style calculator.
5. Show every algorithm step by step in a web interface, with pictures of trees,
   diagrams and tables.
6. Verify the results with automated tests, including answers printed in the textbook.

## 4. Scope

**In scope**

- **The MiniLang language:**
  - `int` and `float` variables, assignment;
  - `+ - * /` and unary `-`;
  - relational operators `< <= > >= == !=`;
  - logical operators `&& || !`;
  - `if / else`, `while`, nested `{ }` blocks, `print`, and comments.
- **Lab topics:** all topics of the three question files: Chapter 2, Chapter 3 and Chapter 4
  (sections 4.1 to 4.9).
- **Interfaces:** a web interface and a command-line interface over the same engine.

**Out of scope**

- **Machine code:** generating machine code or assembly. The compiler stops at
  three-address code, which an interpreter runs.
- **Optimization:** code optimization beyond simple constant folding, which is optional.
- **Larger language features:** functions, arrays, strings and pointers in MiniLang.

## 5. Proposed system

### 5.1 Architecture

```
                         MiniLang compiler pipeline
source.mini ─► Lexer ─► Parser ─► AST ─► Semantic check ─► Three-address code ─► Run
              (Ch 3)   (Ch 2/4)  (2.8)   (2.7 symbol table)     (2.8)        (interpreter)

                         Grammar workbench
  Strings & regex (3.3) · Translators (Ch 2) · Derivations and ambiguity (4.2)
  Grammar transformations (4.3) · FIRST/FOLLOW, LL(1) (4.4) · Top-down parsing (4.4)
  Expression → parse tree (2.2, 4.1) · LR(0)/SLR/CLR/LALR and bottom-up parsing (4.5–4.8)
  Yacc-style calculator (4.9)
```

The engine is a plain Python package. The web pages and the command line both call it,
so the same code is tested and demonstrated.

### 5.2 Modules

| Module | Textbook | What it does |
|---|---|---|
| Lexer and buffer pair | 3.1–3.4 | tokens with attributes, name table, transition diagrams, buffer pair with sentinels, error reporting |
| Strings and regular definitions | 3.3 | prefixes, suffixes, substrings, subsequences; the regular definitions of the lab sheet |
| Flex programs | 3.5 | MiniLang scanner, word count, numbers in words, URLs and e-mails, comment removal |
| Translators | 2.2–2.5 | infix ↔ postfix ↔ prefix with annotated parse trees; Roman numerals; small grammars |
| Grammar workbench | 4.2–4.4 | derivations, ambiguity, L(G), left recursion removal, left factoring, FIRST/FOLLOW, LL(1) table |
| Top-down parsing | 4.4 | backtracking, predictive and table-driven LL(1) parsers with traces |
| Parse tree generator | 2.2, 4.1, 4.2 | expression → parse tree, derivations, syntax tree |
| Parser and AST | 2.4, 2.8, 4.1 | recursive-descent parser for MiniLang with panic-mode error recovery |
| Symbol table and semantics | 2.7 | chained scopes; undeclared, redeclared and type errors |
| Three-address code and interpreter | 2.8 | temporaries and labels; jumps for `if`, `while`, `&&`, `||`, `!`; runs the code |
| Bottom-up parsing | 4.5–4.8 | LR(0) items, SLR, LR(1), LALR, conflicts, precedence; shift-reduce traces with handles |
| Yacc-style calculator | 4.9 | calculator with variables and `error`-token recovery, using PLY |

### 5.3 Web interface

Each module has a page in the browser. On these pages the user can:

- write code, an expression or a grammar;
- see tokens, trees, tables and traces;
- move through the steps of an algorithm with a slider.

Examples of what the pages show:

- the path of each token through its transition diagram;
- the buffer pair with its pointers;
- the parse tree growing from the root (top-down) or from the leaves (bottom-up);
- the LL(1) table cell used at each step.

## 6. Methodology

1. **Phase by phase development.** The work is split into phases (Section 8). Each phase
   ends with working code, its web page, passing tests and a commit.
2. **Algorithms written by hand.** No parser library is used, except PLY in the Yacc
   phase, where the lab asks for a Yacc-style tool. Each textbook algorithm therefore
   has a matching function, and its docstring names the textbook section.
3. **Every algorithm records its steps.** The step records drive both the command-line
   traces and the step-by-step web pages.
4. **One error format.** Every phase reports errors as `kind, message, line, column`,
   printed with the source line and a caret. Lexical and syntax errors do not stop the
   run, so one run reports many errors.
5. **Testing.**
   - Unit tests for every module.
   - Tests that compare the output with textbook answers (for example the LL(1) table of
     Fig. 4.17 and the trace of Fig. 4.21).
   - Property tests on many generated inputs.
   - Golden files for long traces.
   - GitHub Actions runs the tests on every push.

## 7. Tools and technologies

| Tool | Use |
|---|---|
| Python 3 | the compiler, the workbench and the tests |
| Streamlit | the web interface |
| Graphviz (DOT, drawn in the browser) | transition diagrams and trees |
| Flex | Lex programs of Chapter 3.5 |
| PLY (Python Lex-Yacc) | the Yacc-style calculator of Chapter 4.9 (Bison is not installed) |
| pytest | automated tests |
| Git, GitHub, GitHub Actions | version control and continuous testing |

Exact library versions are pinned in `requirements.txt`.

## 8. Work plan

| Phase | Work | Estimate |
|---|---|---|
| 0 | project setup, error format, test setup, continuous integration | 1 day |
| 1 | lexer, buffer pair, regular definitions, Flex programs; Lexer and Strings & Regex pages | 3–4 days |
| 2 | Chapter 2 translators; Translators page | 2–3 days |
| 3 | grammar workbench and top-down parsing; two pages | 4–5 days |
| 3.5 | expression → parse tree generator; Parse Tree page | 1–2 days |
| 4 | MiniLang parser, AST, panic-mode error recovery | 4 days |
| 5 | symbol table, semantic checks, three-address code, interpreter; Compiler page | 4–5 days |
| 6 | LR(0), SLR, LR(1), LALR, bottom-up visualizer, comparison | 5–6 days |
| 7 | Yacc-style calculator with PLY | 2 days |
| 8 | complete command line, demo script, lab mapping, final report | 3 days |

The estimates add up to about six weeks.

**Progress so far (2026-11-25).**

- **Done:** Phases 0, 1, 2, 3 and 3.5. This covers the lexer and Flex programs, the
  translators, the grammar workbench, top-down parsing and the parse tree generator,
  each with its web page.
- **Tests:** they pass locally and on GitHub Actions.
- **Remaining:** Phases 4 to 8.

The detailed plan with checklists is in `ROADMAP.md` in the repository.

## 9. Expected outcomes and deliverables

1. **A working compiler:** `minilang run examples/factorial.mini` prints `120`. A
   program with several errors reports all of them with line numbers, without
   crashing.
2. **Web interface:** one page per topic, every page working on every example.
3. **Command-line tool:** its commands print the same tables and traces. With
   `--md`, they print as Markdown for the report.
4. **Parser checks:**
   - Top-down and bottom-up parsers both accept `id+id*id` and reject `id+*id` with a
     clear message.
   - The same grammar shows SLR, canonical LR and LALR tables, with a comparison of
     state counts.
5. **Supporting material:**
   - Flex programs with a Makefile;
   - a buffer-size experiment with measured results;
   - a lab mapping document (every question topic → file → demo command);
   - a final report;
   - a demo script for the viva.
6. **Test suite:** automated tests, run on every push.

## 10. Evaluation

The project is complete when the definition of done in `ROADMAP.md` holds:

- **Tests:** all tests pass, locally and on GitHub Actions.
- **Textbook answers are reproduced:**
  - the FIRST/FOLLOW sets of Example 4.30;
  - the LL(1) table of Fig. 4.17 and the trace of Fig. 4.21;
  - the result of Example 4.20;
  - the LR tables of the textbook grammars.
- **Programs run correctly:** every example program prints its expected output, stored
  in `examples/*.expected`.
- **Lab mapping:** every lab topic is shown in `docs/lab_mapping.md`.
- **The demo works:** the web interface opens, and the demo script runs from start to
  end without an error.

## 11. Mapping to the lab questions

| Lab topic | Planned component |
|---|---|
| 2.2 grammars, parse trees, Roman numerals, divisible-by-3 grammar | Translators, Parse Tree |
| 2.3 translation schemes, annotated parse trees | Translators |
| 2.4 recursive descent, left recursion | Top-down parsing, grammar transformations |
| 2.5 infix → postfix translator | Translators |
| 2.7 scoped symbol tables | Symbol table |
| 2.8 syntax trees, three-address code, control flow | Parser and AST, three-address code |
| 3.1–3.4 tokens, buffer pairs, regular definitions, transition diagrams | Lexer, Strings & Regex |
| 3.5 Lex/Flex programs | Flex programs |
| 4.1 error recovery, parse trees | Parser (panic mode), Parse Tree |
| 4.2 derivations, ambiguity, L(G) | Grammar workbench |
| 4.3 left recursion, left factoring, dangling else | Grammar workbench |
| 4.4 FIRST/FOLLOW, LL(1), stack traces, recursive descent | Grammar workbench, Top-down parsing |
| 4.5–4.7 handles, shift-reduce, LR(0)/SLR, LR(1)/LALR | Bottom-up parsing |
| 4.8 precedence and dangling else in LR tables | Bottom-up parsing |
| 4.9 Yacc calculator, `error` token | Yacc-style calculator |

## 12. Risks and how they are handled

| Risk | Handling |
|---|---|
| Bison is not installed on the development machine | the Yacc part uses PLY, a Python implementation of Lex and Yacc |
| Graphviz `dot` is not installed | diagrams and trees are drawn in the browser; `.dot` files are still produced |
| Deciding whether a grammar is ambiguous is impossible in general | the tool checks one string at a time with a bounded search and reports whether the search finished |
| Backtracking parsers can take exponential time | a step limit, and left-recursive grammars are refused with an explanation |
| Large scope for one semester | phase-by-phase plan; each phase is usable on its own; optional extras only if time remains |

## 13. Conclusion

MiniLang Compiler Studio brings the Chapter 2–4 lab topics together in one tool. It
compiles and runs a small language, and it shows every textbook algorithm step by step
in the browser. Automated tests check the results, several of them against answers in
the textbook. The first phases are already working. The remaining phases add the
complete compiler back end and bottom-up parsing.

## References

1. A. V. Aho, M. S. Lam, R. Sethi, J. D. Ullman, *Compilers: Principles, Techniques,
   and Tools*, 2nd ed., Addison-Wesley, 2006.
2. Python documentation, https://docs.python.org/3/
3. Streamlit documentation, https://docs.streamlit.io/
4. Flex, the fast lexical analyzer generator, https://github.com/westes/flex
5. PLY (Python Lex-Yacc), https://github.com/dabeaz/ply
