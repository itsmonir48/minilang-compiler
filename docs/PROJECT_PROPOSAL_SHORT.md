# Project Proposal: MiniLang Compiler Studio

## 1. Introduction

Chapters 2 to 4 of *Compilers: Principles, Techniques, and Tools* (Aho, Lam, Sethi,
Ullman) describe the front end of a compiler: lexical analysis, syntax analysis,
syntax-directed translation and intermediate code. This project proposes MiniLang
Compiler Studio, a compiler for a small C-like language, MiniLang, written in Python.
A grammar workbench next to the compiler runs the Chapter 2–4 algorithms step by step.
Both are used through a web interface and a command-line tool.

## 2. Problem statement

The CIT 412 lab problems (tokenizing, buffer pairs, regular definitions, translation
schemes, FIRST/FOLLOW, LL(1) and LR tables, stack traces, a Yacc calculator) are usually
solved as separate small programs. Such programs do not show how the compiler phases
connect, print only final answers while the problems ask for the steps, and are rarely
checked against the textbook. This project solves them in one connected tool that shows
every step and is checked by automated tests.

## 3. Objectives

1. Build a working compiler for MiniLang: lexer, parser with error recovery, syntax
   tree, scoped symbol table, semantic checks, three-address code and an interpreter.
2. Implement the Chapter 3 lexical-analysis topics and the Chapter 2 translators.
3. Implement the Chapter 4 parsing algorithms as a grammar workbench, from FIRST/FOLLOW
   and LL(1) to SLR, canonical LR(1) and LALR.
4. Show every algorithm step by step in the browser, with diagrams, trees and tables.
5. Verify the results with automated tests, including answers printed in the textbook.

## 4. Proposed system

| Module | Textbook | Content |
|---|---|---|
| Lexer, buffer pair, regular definitions, Flex | 3.1–3.5 | tokens and attributes, sentinels, transition diagrams, Lex programs |
| Translators | 2.2–2.5 | infix ↔ postfix ↔ prefix, annotated parse trees, Roman numerals |
| Grammar workbench | 4.2–4.4 | derivations, ambiguity, left recursion, left factoring, FIRST/FOLLOW, LL(1) |
| Top-down parsing, parse trees | 2.2, 4.1, 4.4 | backtracking, predictive and table-driven parsers with traces |
| Parser, symbol table, TAC, interpreter | 2.4, 2.7, 2.8, 4.1 | MiniLang parser with panic-mode recovery, scopes, three-address code |
| Bottom-up parsing | 4.5–4.8 | LR(0), SLR, LR(1), LALR tables, conflicts, shift-reduce traces |
| Yacc-style calculator | 4.9 | variables, precedence, `error`-token recovery (PLY) |

MiniLang has `int` and `float` variables, arithmetic, relational and logical operators,
`if / else`, `while`, nested blocks and `print`. Machine-code generation, functions and
arrays are out of scope.

## 5. Methodology and tools

The work is done phase by phase. Each phase ends with working code, its web page and
passing tests. The algorithms are written by hand, so each textbook algorithm has a
matching function. Every algorithm records its steps, and the web pages replay them
with a slider. All phases report errors in one format, with line and column. Tests
compare the output with textbook answers, such as the LL(1) table of Fig. 4.17, and
GitHub Actions runs them on every push. Tools: Python 3, Streamlit (web interface),
Graphviz DOT (diagrams), Flex, PLY (Python Lex-Yacc), pytest, Git and GitHub.

## 6. Work plan

| Phase | Work | Estimate |
|---|---|---|
| 0–1 | setup; lexer, buffer pair, regular definitions, Flex | 4–5 days |
| 2 | Chapter 2 translators | 2–3 days |
| 3–3.5 | grammar workbench, top-down parsing, parse tree generator | 5–7 days |
| 4–5 | parser and AST, symbol table, semantic checks, TAC, interpreter | 8–9 days |
| 6 | LR(0), SLR, LR(1), LALR, bottom-up visualizer | 5–6 days |
| 7–8 | Yacc-style calculator; demo script, lab mapping, report | 5 days |

## 7. Expected outcomes

- **Compiler:** `minilang run examples/factorial.mini` prints `120`, and a program with
  several errors reports all of them with line numbers.
- **Web interface:** one page per lab topic, with step-by-step views.
- **Parsers:** top-down and bottom-up parsers accept `id+id*id` and reject `id+*id`;
  SLR, canonical LR and LALR tables are compared on one grammar.
- **Coverage and tests:** every lab topic is mapped to a component; all tests pass.
