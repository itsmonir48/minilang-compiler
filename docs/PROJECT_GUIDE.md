# MiniLang Compiler Studio: Project Guide

- **Course:** CIT 412 Compiler Design and Automata Theory Sessional
- **Textbook:** Aho, Lam, Sethi, Ullman, *Compilers: Principles, Techniques, and Tools*,
  2nd ed. (the "Dragon Book"). Section numbers below (3.2, 4.4, ...) refer to this book.
- **Repository:** https://github.com/itsmonir48/minilang-compiler

This guide explains what the project does, how each part works, and why it was built
this way. Section 13 lists likely viva questions with short answers.

Status when this guide was written (2026-11-25): Phases 0, 1, 2, 3 and 3.5 of
[ROADMAP.md](../ROADMAP.md) are finished. Phases 4 to 8 (main parser, semantic checks,
three-address code, LR parsers, Yacc calculator, final report) are planned, not built.
Every "planned" item below is marked as such.

---

## 1. The project in one paragraph

The project is a small C-like language, **MiniLang**, and a compiler for it written
in Python. Next to the compiler sits a **grammar workbench** that runs the Chapter 2,
3 and 4 algorithms step by step. Everything is shown in a **web interface** called
*MiniLang Compiler Studio*: you type code, an expression or a grammar in the browser
and see tokens, transition diagrams, the buffer pair, parse trees, FIRST/FOLLOW sets,
LL(1) tables and parser traces as pictures and tables. The same engine also has a
command-line tool, `minilang`, which the automated tests use. Every lab topic from the
three question files is one module of this single tool, not a separate exercise file.

## 2. Why build it this way

- **One connected tool instead of separate programs.** In a real compiler the lexer
  feeds the parser, the parser feeds the tree, and so on. Building one pipeline shows
  how the chapters fit together. For example, the Phase 3.5 parse-tree generator uses
  the Phase 1 lexer, and the Phase 3 derivation search checks the Phase 3.5 trees.
- **Show the steps, not only the answer.** The lab problems ask for traces: stack
  contents, derivations, FIRST/FOLLOW passes, backtracking. So every algorithm records
  its steps, and the web pages let you move through them with a slider.
- **Write the algorithms by hand.** No parser library is used (PLY is planned only for
  the Yacc phase, because the lab asks for a Yacc-style tool there). This way every
  algorithm in the textbook has a matching function in the code.
- **Check the results automatically.** Every module has tests, and several tests
  compare the output with answers printed in the textbook (Section 10).

## 3. The MiniLang language

```c
// examples/factorial.mini   (expected output: 120)
int n; int fact;
n = 5; fact = 1;
while (n > 1) {
    fact = fact * n;
    n = n - 1;
}
if (fact >= 100 && !(n == 0)) print(fact); else print(0);
```

- **Types:** `int` and `float` declarations.
- **Statements:** assignment, `if / else`, `while`, `{ }` blocks (nested scopes), and
  `print(expr)`.
- **Operators:**
  - arithmetic `+ - * /` and unary `-`
  - relational `< <= > >= == !=`
  - logical `&& || !`
- **Comments:** `//` and `/* */`.
- **Semantics:** C-like. `int / int` is integer division (truncates toward zero),
  division by zero is a runtime error, and `else` belongs to the nearest unmatched `if`.

The full grammar (EBNF) is in [ROADMAP.md](../ROADMAP.md), Section 2.

Today the lexer handles the full language. The parser, checker and interpreter for
whole programs come in Phases 4 and 5.

## 4. Architecture

```
                         MiniLang compiler pipeline
source.mini ─► Lexer ─► Parser ─► AST ─► Semantic check ─► Three-address code ─► Run
              (Ch 3)   (Ch 2/4)  (2.8)   (2.7 symbol table)     (2.8)          (interpreter)
               done    planned  planned      planned           planned           planned

                         Workbench (done)
  Strings & regex (3.3) · Translators (Ch 2) · Grammar workbench (4.2–4.4)
  Top-down parsing (4.4) · Expression → parse tree (2.2, 4.1, 4.2)
  Bottom-up / LR parsing (4.5–4.8): planned
```

Folder layout:

| Folder / file | What it holds |
|---|---|
| `minilang/` | the engine (pure Python, no web code) |
| `minilang/grammar/` | the Chapter 4 grammar workbench |
| `app/` | the web interface (Streamlit): `Home.py` and `pages/` |
| `lex/` | Flex programs (3.5) and a Makefile |
| `grammars/` | textbook grammars as text files |
| `examples/` | MiniLang programs, valid and with errors |
| `tests/` | pytest tests; `tests/expected/` holds golden outputs |
| `scripts/` | the buffer-size experiment |
| `docs/` | this guide and the experiment report |
| `ROADMAP.md` | the plan, phase by phase, with checkboxes |

The engine never imports the web code. The web pages and the command line both call
the same functions, so the tests of the engine also cover what the pages show.

## 5. How to run it

One-time setup (already done on this machine):

```bash
cd ~/Downloads/"Compiler Design lab"/"Masud Sir"/MiniLang_Compiler
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

Each time:

```bash
cd ~/Downloads/"Compiler Design lab"/"Masud Sir"/MiniLang_Compiler
source .venv/bin/activate
minilang ui          # opens http://localhost:8501 ; stop with Ctrl+C
```

When Streamlit asks for an email on its first run, leave the field blank and press
Enter.

Command-line examples (each prints tables or trees in the terminal):

```bash
minilang tokens examples/factorial.mini              # token table + name table
minilang tokens examples/lexer_errors.mini           # 4 lexical errors with line:col
minilang tokens --buffer-size 8 --stats examples/scopes.mini
minilang strings banana                              # prefixes, suffixes, ...
minilang regex no_abb abab abba                      # regular definitions
minilang translate '9-5+2' --tree --trace            # infix → postfix/prefix (2.5)
minilang roman MCMXCIV --tree                        # Roman ↔ integer
minilang check div3 --table 6                        # num → 11 | 1001 | num 0 | num num
minilang grammar expr --remove-left-recursion --ll1  # grammar workbench
minilang derive expr_ambiguous 'id+id*id'            # two parse trees → ambiguous
minilang topdown backtrack cad --method backtrack    # try, fail, backtrack
minilang topdown expr_ll1 'id+id*id'                 # Stack | Input | Action
minilang parsetree 'a + b * (c - 2)' --all           # parse tree, derivations, AST
make -C lex demo                                     # all Flex programs
.venv/bin/pytest -q                                  # all tests
```

Every table command also takes `--md`, which prints the table as Markdown for a report.

## 6. The web interface (MiniLang Compiler Studio)

| Page | What you can do |
|---|---|
| **Home** | A picture of the compiler pipeline (finished stages in green), links to every page, and the example program. |
| **Lexer** | See the [Lexer page](#lexer-page) below. |
| **Strings & Regex** | Prefixes, suffixes, substrings and subsequences of a string, with their counts compared to the formulas. Test strings against the regular definitions from the lab sheet. |
| **Translators** | Type an expression in infix, postfix or prefix and get the other two notations, its value and the **annotated parse tree** (attributes such as `post`, `pre`, `val` on every node). Step through the 2.5 translator: each `expr()`, `term()`, `factor()` call and each `print`. Roman numerals ↔ integers with their trees. Grammar checkers: binary numbers divisible by 3, balanced brackets, left- vs right-associative lists. |
| **Grammar Workbench** | See the [Grammar Workbench page](#grammar-workbench-page) below. |
| **Top-Down Parsing** | See the [Top-Down Parsing page](#top-down-parsing-page) below. |
| **Parse Tree** | Type an expression: the parse tree and the syntax tree (AST) side by side. A slider walks through the leftmost or rightmost derivation and shows the tree half built at each step. A `.dot` file can be downloaded. |

### Lexer page

- Write or load MiniLang code. The source is shown with keywords, identifiers, numbers
  and operators in colour, and errors are underlined.
- **Step through** the tokens one by one. For each token the page shows:
  - the path it took through its **transition diagram**, e.g. `9 → 10 → 10 → 11*`;
  - the **buffer pair** with both halves, the `eof` sentinels and the `lexemeBegin` and
    `forward` pointers.
- Tabs: Token table, Name table, Errors, and all three transition diagrams.

### Grammar Workbench page

Load a textbook grammar or type your own, then use the tabs:

- **Derivations & ambiguity:** how many parse trees a string has; the first two trees
  side by side, with leftmost and rightmost derivations.
- **Language L(G):** every string of the grammar up to length n.
- **Left recursion:** Algorithm 4.19, or immediate removal only, with every step.
- **Left factoring:** Algorithm 4.21 with every step.
- **FIRST / FOLLOW:** the sets, the nullable flag, and every pass of the fixed-point loop.
- **LL(1) table:** conflicts (multiply-defined entries) in red.

### Top-Down Parsing page

- Three methods on the same grammar and input: backtracking, predictive recursive
  descent, and table-driven LL(1).
- A slider moves through the steps. The parse tree grows from the root down:
  - the current node is orange;
  - nonterminals not expanded yet are dashed grey.
- The table-driven method shows the stack and the input, and outlines the LL(1) table
  cell used in that step.
- If the grammar is left-recursive or not LL(1), the page says why and offers the
  transformed grammar.
- A table compares the three methods.

## 7. The modules and their algorithms

For each part: the problem, the idea, how the code does it, and where to find it.

### 7.1 Errors (`minilang/errors.py`)

- **Problem:** every phase must report errors the same way, with a position.
- **How:** one `CompileError(kind, message, line, col)` class. It prints the source line
  and a caret under the column:
  ```
  error[lexer] line 3, col 7: illegal character '@'
      a = 5 @ 3;       // illegal character '@'
            ^
  ```
  `ErrorList` collects many errors, so one run can report all of them.

### 7.2 Tokens and the lexer (Chapter 3.1, 3.4; `tokens.py`, `lexer.py`)

- **Problem:** turn characters into tokens `<token name, attribute>`.
- **Idea:** the textbook's transition diagrams.
  - **Identifiers and keywords** (Fig. 3.14): states 9 → 10 → 11*. The `*` means
    *retract*: the last character read is not part of the lexeme, so `forward` moves
    back by one.
    Keywords are found by reading an identifier first and then looking it up in a
    keyword table. So `while` becomes a keyword token, but `whilex` stays an identifier.
  - **Numbers** (Fig. 3.16): states 12–21, covering integers, reals and exponents
    (`1.5E+3`). Two parts are errors: a `.` without a digit after it, and an exponent
    without digits.
  - **Relational operators** (Fig. 3.13, extended for C): `<`, `<=`, `>`, `>=`, `==`,
    `!=`, plus `=` (assignment) and `!` (not), which share the first character.
- **Attributes:**
  - for an identifier: its index in the **name table** (each name is stored once);
  - for a number: its value;
  - for a relop: which operator it is (LT, LE, ...).
- **Longest match:** the lexer always takes the longest possible lexeme, e.g. `<=` and
  not `<` followed by `=`.
- **Errors:** an illegal character, a malformed number or an unterminated comment is
  reported with its line and column. The lexer then keeps going, so one run finds every
  lexical error. `examples/lexer_errors.mini` has 4 errors and all 4 are reported.
- **Where:** `Lexer._scan`, `_id_or_keyword`, `_number`, `_relop`. Each token records
  its state path, which the web page draws on the diagram.

### 7.3 Input buffering (Chapter 3.2; `buffer.py`)

- **Problem:** reading one character at a time from a file is slow, and the lexer must
  sometimes look ahead and then go back.
- **Idea:** a **buffer pair** (Fig. 3.3), with a **sentinel** `eof` at the end of each
  half (Fig. 3.5).
  - The buffer is two halves of N characters each.
  - `lexemeBegin` marks the start of the lexeme; `forward` scans ahead.
  - When `forward` reaches the end of a half, the other half is loaded with the next
    chunk.
- **Why the sentinel:**
  - Without it, each character needs two tests: "end of buffer?" and "which character
    is it?".
  - With it, the check is one test, "is this `eof`?", and only then the lexer asks
    whether it is the end of a half or the real end of the input.
- **Limit:** only the half that `forward` moves into is reloaded, so a lexeme must fit
  in one half. A longer lexeme is reported as an error ("lexeme longer than the buffer
  half size").
- **Experiment:** `scripts/buffer_experiment.py` measured reloads and time for different
  N. The results, hardware and the explanation are in
  [buffer_experiment.md](buffer_experiment.md).
  - The number of reloads falls in proportion to 1/N.
  - In this Python program the time changes much less than the reload count.
  - The smallest working N equals the longest lexeme of the input.

### 7.4 Strings and regular expressions (Chapter 3.3; `regex_tools.py`)

- String terms: prefixes, suffixes, proper prefixes/suffixes, substrings and
  subsequences.
- The counts are compared with the formulas for a string of n distinct characters, e.g.
  2ⁿ subsequences. Repeated characters make the real counts smaller.
- Regular definitions from the lab sheet:

| Name | Language | Pattern |
|---|---|---|
| `vowels` | letters with the five vowels in order | `[b-df-hj-np-tv-z]*a(...|a)*e...u(...|u)*` |
| `ascending` | letters in ascending order | `a*b*c*...z*` |
| `comment` | `/* ... */` without `*/` inside | `/\*([^*]|\*+[^*/])*\*+/` |
| `no_abb` | a/b strings without the substring `abb` | `b*(a|ab)*` |
| `no_abb_subseq` | a/b strings without the subsequence `abb` | `b*a*b?a*` |
| `chess` | moves such as `p-k4`, `kbp*qn` | `[kq]?[rbn]?[kqrbnp](-[kq]?[rbn]?[1-8]|\*[kq]?[rbn]?[kqrbnp])` |
| `sql_select` | `SELECT` in any letter case | `[Ss][Ee][Ll][Ee][Cc][Tt]` |
| `no_repeat_digit`, `one_repeat_digit` | digit strings with no / at most one repeated digit | checked by a function |

(The full `vowels` pattern is printed by `minilang regex`.)

### 7.5 Flex programs (Chapter 3.5; `lex/`)

| File | What it does |
|---|---|
| `minilang.l` | the MiniLang scanner in Flex. It prints the same tokens, positions and name table as the Python lexer; a test checks this on every example file. |
| `wc.l` | counts characters, words and lines |
| `numbers.l` | writes numbers digit by digit in words (`42` → `four-two`); words such as `cit412` are left unchanged |
| `urls_emails.l` | finds URLs and e-mail addresses |
| `strip_comments.l` | removes C comments |

Build and run everything with `make -C lex demo`. The Flex tests are skipped if Flex
is not installed. GitHub Actions installs Flex, so they run there.

### 7.6 Chapter 2 translators (`translators.py`, `tree.py`)

- **Syntax-directed translation (2.3):**
  - Each grammar rule has a semantic rule that computes **synthesized attributes** from
    the children, e.g. `expr.post = expr₁.post ‖ term.post ‖ '+'`.
  - The result is an **annotated parse tree**, where every node shows its attribute
    values.
- **Infix → postfix (2.5):**
  - A recursive-descent translator with `expr()`, `term()`, `factor()`. Left recursion
    is replaced by a loop.
  - Extended with `* /`, parentheses and unary `+ -`. Every call and every `print`
    action is recorded.
- **Other directions:**
  - Postfix input is read with a stack (grammar `E → E E op`).
  - Prefix input is read by recursive descent (`E → op E E`).
  - Unary minus is written `~` in postfix and prefix, because there `-` is always binary.
- **Infix output with the fewest parentheses:**
  - a left operand needs `( )` if it binds weaker than the operator;
  - a right operand also needs them if it binds equally, because all four operators are
    left-associative. So `a-(b-c)` keeps its parentheses.
- **Roman numerals (2.2, 2.3):**
  - Grammar: `romanNum → thousand hundred ten digit`, and each level has the forms
    `small | one five | five small | one ten`. It covers 1–3999.
  - Invalid numerals (`IIII`, `IC`, `VX`) are rejected with the column of the bad letter.
  - The integer → Roman scheme writes the number with 4 digits, and each digit position
    maps to its Roman letters.
- **Grammar checkers (2.2):**
  - `num → 11 | 1001 | num 0 | num num`: every string it generates is divisible by 3.
    - The proof is by induction on the parse tree: `11` = 3 and `1001` = 9, `num 0`
      doubles the value, and `num₁ num₂` = num₁·2^|num₂| + num₂. Each rule keeps "a
      multiple of 3".
    - The page annotates every node with `val mod 3 = 0`.
    - The page also shows that the converse is false: some multiples of 3 are not
      generated, e.g. `10101` (21).
  - Balanced brackets: `S → ( S ) S | [ S ] S | { S } S | ε`.
  - Left- vs right-associative comma lists: `list → list , id` against
    `list → id , list`. Same strings, trees that lean opposite ways.

### 7.7 Grammars (Chapter 4.2; `grammar/grammar.py`, `grammars/`)

- Grammars are plain text: `E -> E + T | T`, with `ε` or `eps` for the empty string.
- The first head is the start symbol. Heads are nonterminals; every other symbol is a
  terminal.
- An input string is split into terminals by longest match, so `id+id*id` works without
  blanks.
- Textbook grammars in `grammars/`:

| File | Grammar |
|---|---|
| `expr.txt` | expression grammar (4.1), left-recursive |
| `expr_ll1.txt` | the same without left recursion (4.28) |
| `expr_ambiguous.txt` | `E → E + E \| E * E \| ( E ) \| id` (4.3) |
| `dangling_else.txt` | if-then-else, ambiguous (4.14) |
| `dangling_else_fixed.txt` | matched / open statements (4.3.2) |
| `backtrack.txt` | `S → c A d`, `A → a b \| a` (Example 4.29) |
| `indirect_left_rec.txt` | `S → A a \| b`, `A → A c \| S d \| ε` (4.18, Example 4.20) |
| `left_factor.txt` | `S → i E t S \| i E t S e S \| a` (4.23) |
| `balanced.txt`, `ab_equal.txt`, `prefix.txt` | small grammars for "describe L(G)" exercises |

### 7.8 Derivations and ambiguity (Chapter 4.2; `grammar/derivation.py`)

- **Problem:** give leftmost and rightmost derivations, and show that a grammar is
  ambiguous.
- **Idea:** each **leftmost derivation corresponds to exactly one parse tree**. So two
  different leftmost derivations of one string prove that the grammar is ambiguous.
- **How:**
  - A depth-first search over sentential forms always expands the leftmost nonterminal.
  - It prunes a form when:
    - its terminals before the first nonterminal do not match the input;
    - its terminals after the last nonterminal do not match the end of the input;
    - the shortest string it can still derive is longer than the input.
  - Forms known to lead nowhere are remembered.
  - The search has a budget, and it reports whether it finished. That is why it says
    "exactly 2" or "at least 10".
- **From the tree:** the rightmost derivation of the same tree is read off by walking
  the tree right to left.
- **L(G) up to length n:** the same expansion, collecting every all-terminal form.
- **Results:**
  - `id+id*id` has 2 trees in the ambiguous grammar and 1 in `expr.txt`.
  - `if cond then if cond then other else other` has 2 trees in the dangling-else
    grammar and 1 in the fixed grammar.

### 7.9 Left recursion and left factoring (Chapter 4.3; `grammar/transforms.py`)

- **Why left recursion is a problem for top-down parsing:** with `E → E + T`, the
  procedure `E()` calls `E()` again before reading any input, so it loops forever.
- **Immediate left recursion:**
  ```
  A → A α | β    becomes    A → β A',   A' → α A' | ε
  ```
- **Algorithm 4.19 (general):**
  1. Order the nonterminals A1…An.
  2. For each Ai, substitute the bodies of every earlier Aj into rules `Ai → Aj γ`.
  3. Then remove the immediate left recursion of Ai.

  This also removes **indirect** recursion such as `S ⇒ A a ⇒ S d a`. The algorithm is
  only guaranteed for grammars without cycles or ε-productions; the tool prints a
  warning when that is not the case.
- **Detection:** the tool finds left recursion also when it is hidden behind nullable
  symbols, e.g. `A → B A x` with `B ⇒ ε`.
- **Left factoring (Algorithm 4.21):**
  ```
  A → α β1 | α β2    becomes    A → α A',   A' → β1 | β2
  ```
  This repeats until no two alternatives share a first symbol. It helps a predictive
  parser choose with one lookahead symbol.
- **Results:** they match the textbook.
  - `expr.txt` becomes `expr_ll1.txt` (4.28).
  - Example 4.20 becomes `A → b d A' | A'`, `A' → c A' | a d A' | ε`.
  - `left_factor.txt` becomes `S → i E t S S' | a`, `S' → e S | ε`.

### 7.10 FIRST and FOLLOW (Chapter 4.4.2; `grammar/first_follow.py`)

- **FIRST(α):** the terminals that can begin a string derived from α, plus ε if α can
  derive the empty string.
- **FOLLOW(A):** the terminals that can appear right after A in some sentential form,
  plus `$` (end of input) if A can be last.
- **Rules for FOLLOW:**
  1. `$ ∈ FOLLOW(S)`.
  2. For `A → α B β`, everything in FIRST(β) except ε is in FOLLOW(B).
  3. If β can derive ε, everything in FOLLOW(A) is in FOLLOW(B).
- **How:** both sets are computed by repeating the rules until nothing changes (a fixed
  point). Every pass is saved, and the web page shows them.

### 7.11 LL(1) table and parser (Chapter 4.4.3–4.4.4; `grammar/ll1.py`)

- **Table (Algorithm 4.31):** for each production `A → α`:
  - put it in `M[A, a]` for each terminal a in FIRST(α);
  - if ε ∈ FIRST(α), also put it in `M[A, b]` for each b in FOLLOW(A).
- **LL(1):** a grammar is LL(1) exactly when no cell holds two productions. Such cells
  are reported as conflicts ("multiply-defined entries").
- **Parser (Algorithm 4.34):** a stack starting with `$ S`. On each move:
  - if the top is a terminal, it must match the input;
  - if the top is a nonterminal, it is replaced by the body of `M[top, lookahead]`;
  - an empty cell is a syntax error. The message lists the expected terminals and
    gives the column.
- **Trace:** a `Stack | Input | Action` table, the same format as Fig. 4.21.

### 7.12 Top-down parsing visualizer (Chapter 4.4; `grammar/topdown.py`)

1. **Backtracking recursive descent (4.4.1):**
   - Try the alternatives of a nonterminal in order. If one fails, reset the input
     position and try the next.
   - The implementation uses Python generators, so it can also go back into a part that
     had already succeeded (full backtracking).
   - On `S → c A d`, `A → a b | a` with input `cad`: `A → a b` matches `a` but then
     fails on `d`. The parser backs up, `A → a` succeeds, and the input is accepted.
     `cd` is rejected.
   - The cost can grow exponentially with the input, which is why practical parsers are
     predictive.
2. **Predictive recursive descent:** one procedure per nonterminal. The procedure looks
   at the lookahead and takes `M[A, lookahead]`, so it never backtracks. The trace shows
   the calls, e.g. `E(): lookahead id → use E → T E'`.
3. **Table-driven LL(1):** the same choices made with an explicit stack instead of
   recursion.

- The parse tree is saved after every step, so it can be shown growing from the root
  down in leftmost-derivation order.
- **Refusals:**
  - Before running, the tool checks the grammar. A left-recursive grammar is refused
    with the cycle shown.
  - The predictive methods also refuse a non-LL(1) grammar, showing the conflicting
    cell.
  - In both cases the tool offers the grammar after left-recursion removal and left
    factoring, and says whether that grammar would work.

### 7.13 Expression → parse tree (Chapter 2.2, 2.8, 4.1, 4.2; `parse_tree.py`)

- The expression is tokenized by the Phase 1 lexer and parsed with
  `E → E + T | E - T | T`, `T → T * F | T / F | F`, `F → ( E ) | id | num`.
- The parser is recursive descent with loops, but the tree is built in the
  left-recursive shape above, so it looks like the textbook drawings.
- Outputs:
  - the ASCII tree;
  - the leftmost and rightmost derivations;
  - a Graphviz `.dot` file (and a PNG if Graphviz `dot` is installed);
  - the **AST** of the same expression.
- **Parse tree vs. syntax tree:**
  - The parse tree contains every grammar symbol, including `E → T → F` chains and
    parentheses.
  - The syntax tree keeps only operators and operands. The grouping is the same.
- **Checks:**
  - `9-5+2` leans left (left-associative).
  - In `a+b*c`, `*` is lower than `+` (precedence).
  - In `(a+b)*c`, the parentheses put `+` lower.

## 8. Error handling summary

| Where | Example input | Message |
|---|---|---|
| Lexer | `a = 5 @ 3;` | `illegal character '@'` (and continues) |
| Lexer | `b = 1.5E+;` | `malformed number '1.5E+': expected a digit in the exponent` |
| Lexer | `/* ...` (never closed) | `unterminated comment` at the comment start |
| Translators | `a+*b` | `expected an operand, found '*'` at column 3 |
| Roman | `IIII` | `'I' cannot appear here` at column 4 |
| LL(1) parser | `id+*id` | `no rule for T on '*'; expected one of: (, id` at column 4 |
| Parse tree | `(a+b` | `expected ')' to close '(' at line 1, column 1, found end of input` |
| Grammar file | `E E -> x` | `the left side of a rule must be one nonterminal` with line number |

No input crashes the program. The web pages show the same messages with a caret.
Panic-mode recovery for whole programs (many syntax errors in one run) is part of
Phase 4.

## 9. Design decisions

| Decision | Reason |
|---|---|
| Python | readable code that is close to the textbook pseudocode; the lab sheets allow it |
| Hand-written lexer and parsers | each textbook algorithm has a matching function that can be shown and explained |
| Streamlit web interface | a browser page with pictures, without writing HTML/JavaScript; the graphs are drawn in the browser, so Graphviz need not be installed |
| Engine separate from the web code | the same code is tested from the command line and shown on the pages |
| Every algorithm records its steps | the lab problems ask for traces; the pages replay the steps with a slider |
| Parse trees built in the left-recursive shape | the parser uses loops (no left recursion), but the tree must match the textbook grammar and its associativity |
| Golden-file tests | long outputs (traces, trees) are saved in `tests/expected/`; any change shows up as a test failure |
| Grammars in text files | the same grammar is used by the CLI, the pages and the tests; users can add their own |

## 10. Testing and verification

- **Running the tests:** `.venv/bin/pytest -q`. GitHub Actions runs the whole suite on
  every push, with Python 3.12 and 3.14 and with Flex installed.
- **Test count:** 222 tests passed at the end of Phase 3.5.

| Test file | Tests | What it covers |
|---|---|---|
| `test_lexer.py` | 43 | every token type, line/column, attributes, errors, same tokens for every buffer size |
| `test_buffer.py` | 17 | buffer pair, sentinels, reloads at the boundary, lexeme too long |
| `test_regex_tools.py` | 20 | string terms, formulas, regular definitions |
| `test_flex.py` | 9 | the Flex scanner gives the same tokens as the Python lexer (skipped without Flex) |
| `test_translators.py` | 62 | three notations, Roman numerals, grammar checkers |
| `test_grammar.py` | 30 | loader, transforms, FIRST/FOLLOW, LL(1), derivations, three top-down parsers |
| `test_parse_tree.py` | 17 | tree shapes, derivations, AST, errors |
| `test_app.py` | 12 | every web page runs (Streamlit AppTest), every grammar with every method |
| `test_errors.py`, `test_cli.py`, `test_diagrams.py` | 12 | error format, CLI, diagrams match the lexer |

- **Checked against the textbook:**
  - FIRST and FOLLOW of grammar 4.28 equal Example 4.30.
  - The LL(1) table equals Fig. 4.17 cell by cell.
  - The trace for `id+id*id` has the same moves as Fig. 4.21.
  - Algorithm 4.19 on grammar 4.18 gives the result of Example 4.20.
  - Left factoring of 4.23 gives `S → i E t S S' | a`, `S' → e S | ε`.
- **Property tests:** the result must hold for many generated inputs.
  - 300 random expressions are translated through all three notations and back, and
    give the same strings and value.
  - All 3999 Roman numerals convert back to the same integer.
  - The three top-down parsers accept exactly the same strings and build the same tree.
  - Removing left recursion and left factoring keep the language the same up to
    length 6.
  - `id+id+id+id+id` has 14 trees in the ambiguous grammar (Catalan(4) = 14).
  - Every string of the divisible-by-3 grammar up to length 10 is divisible by 3.
- **Bugs the tests found:**
  - A crash in the web page when errors were cached (`CompileError` could not be
    pickled).
  - A postfix input such as `12` was read as two tokens.
  - A page test failed when run alone because of the import path.
  - All three are fixed and now have tests.

## 11. Limitations (stated openly)

- **Ambiguity search:** ambiguity of a context-free grammar is undecidable in general.
  The tool only checks one string at a time, with a bounded search. When the budget or
  the tree limit is reached, it says "at least", not "exactly".
- **Backtracking parser:** it can take exponential time. It has a step limit and
  refuses left-recursive grammars.
- **Expression grammar:** the Phase 3.5 grammar has no unary minus (`-a` is an error
  that suggests `(0 - a)`). The Phase 2 translator and the MiniLang grammar do support
  unary minus.
- **Graphviz PNG:** `--png` needs the Graphviz `dot` program, which is not installed on
  the development machine. The `.dot` file is always written, and the web pages draw
  the trees without it.
- **Buffer timing:** the experiment times are from one machine and one Python version
  (listed in the report). They show a trend, not general numbers.

## 12. What comes next (planned, not built yet)

| Phase | Content |
|---|---|
| 4 | MiniLang parser and AST, panic-mode error recovery (many syntax errors in one run) |
| 5 | scoped symbol table (2.7), semantic checks, three-address code (2.8), TAC interpreter; `minilang run examples/factorial.mini` prints `120` |
| 6 | LR(0) items, SLR, canonical LR(1), LALR; shift-reduce visualizer with handles; conflict resolution with precedence; SLR/CLR/LALR comparison |
| 7 | Yacc-style calculator with PLY, including the `error` token |
| 8 | full CLI, `demo.sh`, `docs/lab_mapping.md`, final lab report |

## 13. Likely viva questions

**What is your project?**
A compiler for a small C-like language, MiniLang, plus a workbench that shows the
Chapter 2–4 algorithms step by step in a web interface. Lexing, translators, the
grammar workbench, top-down parsing and parse trees are finished; the full compiler
back end and LR parsing are next.

**What is the difference between a token, a pattern and a lexeme?**
A token is a pair of a name and an optional attribute, e.g. `<id, 0>`. A pattern
describes the form of a token's lexemes, e.g. letter followed by letters or digits.
A lexeme is the actual character sequence in the source, e.g. `fact`.

**Why two buffer halves and why sentinels?**
With one buffer, a lexeme that crosses the end of the buffer would be lost on reload.
With two halves, one half is refilled while the lexeme stays in the other. The sentinel
at the end of each half lets the lexer test for "end of half" and "end of input" with
one comparison per character instead of two.

**What happens if a lexeme is longer than a buffer half?**
It cannot be kept while the other half is reloaded, so it is an error. The tool
reports "lexeme longer than the buffer half size". The experiment shows the smallest
working N is the length of the longest lexeme.

**What does `*` mean on a state of a transition diagram?**
That state needs one character of lookahead that is not part of the lexeme, so the
`forward` pointer is moved back by one (retract) before returning the token.

**How do you separate keywords from identifiers?**
Every word is read with the identifier diagram. Then the lexeme is looked up in the
keyword table: if found, it is that keyword token; otherwise it is an identifier,
installed in the name table.

**What does your lexer do on an error?**
It reports the error with line and column, skips the bad text and continues scanning,
so all lexical errors are found in one run.

**What is a syntax-directed translation scheme?**
A grammar where each production has semantic rules (or actions) that compute
attributes. In the 2.5 translator, `print('+')` placed after `expr + term` produces
postfix output while parsing.

**What is a synthesized attribute?**
An attribute of a node computed only from its children's attributes, e.g.
`E.val = E₁.val + T.val`. All attributes in the Translators page are synthesized.

**Why is `E → E + T` a problem for top-down parsing, and how do you fix it?**
`E()` would call `E()` again without consuming input and loop forever. Rewrite it as
`E → T E'`, `E' → + T E' | ε`. That is immediate left-recursion removal; Algorithm 4.19
also removes indirect left recursion.

**What is left factoring for?**
When two alternatives start with the same symbols, one lookahead token cannot choose
between them. Factoring the common prefix into a new nonterminal delays the choice
until the symbols differ.

**Define FIRST and FOLLOW. Why is FOLLOW needed?**
FIRST(α) is the set of terminals that can start a string derived from α. FOLLOW(A) is
the set of terminals that can come right after A. FOLLOW is needed for ε-productions:
`A → ε` should be chosen when the lookahead is something that can follow A.

**When is a grammar LL(1)?**
When its LL(1) table has no multiply-defined entry. Equivalently: for any `A → α | β`,
FIRST(α) and FIRST(β) are disjoint, and if one can derive ε, the other's FIRST is
disjoint from FOLLOW(A).

**Is the dangling-else grammar LL(1)? Does left factoring fix it?**
No. Left factoring removes the common prefix, but the grammar stays ambiguous: after
factoring, the cell `M[stmt', else]` still holds both `stmt' → else stmt` and
`stmt' → ε` (the Grammar Workbench shows this).
In practice, the parser chooses `stmt' → else stmt`, which matches each else with the
nearest then. The unambiguous matched/open grammar solves it in the grammar itself.

**How do you show that a grammar is ambiguous?**
Find one string with two different parse trees, or equivalently two different leftmost
derivations. The tool searches for them and draws both trees. It does this for one
given string; ambiguity of a grammar in general cannot be decided by any algorithm.

**Leftmost vs. rightmost derivation?**
Leftmost always rewrites the leftmost nonterminal, rightmost the rightmost one. For an
unambiguous grammar both give the same parse tree; only the order of the steps
differs. The Parse Tree page shows this with its step slider.

**Parse tree vs. syntax tree?**
A parse tree shows every grammar symbol used. A syntax tree (AST) keeps only the
operators and operands: chain steps like `E → T → F` and parentheses disappear. The
compiler works on the AST.

**How does your grammar make `*` bind tighter than `+`, and `-` left-associative?**
Precedence comes from the levels: `*` is in `T`, which is below `E`, so `*` ends up
lower in the tree. Left associativity comes from left recursion, `E → E - T`, so
`9-5+2` groups as `(9-5)+2`.

**Backtracking vs. predictive parsing?**
Backtracking tries alternatives and undoes failed ones, which can take exponential
time. A predictive parser chooses with one lookahead token through the LL(1) table and
never backs up, so it runs in linear time, but it needs an LL(1) grammar.

**Recursive descent vs. table-driven LL(1)?**
They make the same choices. Recursive descent uses the call stack (one procedure per
nonterminal); the table-driven parser uses an explicit stack and a table. The
Top-Down page shows both on the same input and compares the step counts.

**How did you check that your answers are right?**
Automated tests: textbook answers (Example 4.30, Fig. 4.17, Fig. 4.21, Example 4.20,
grammar 4.23), property tests with random inputs, golden files, and GitHub Actions on
every push. 222 tests pass.

**Why do all strings of `num → 11 | 1001 | num 0 | num num` divide by 3?**
By induction on the parse tree. `11` = 3 and `1001` = 9; appending `0` doubles a
multiple of 3; joining two multiples of 3 gives num₁·2^k + num₂, again a multiple of 3.
The converse is false: `10101` (= 21) is divisible by 3 but is not generated.

## 14. Lab sheet coverage (done so far)

| Lab topic | Where in the project |
|---|---|
| 2.2 grammars, parse trees, postfix grammar, comma lists, Roman numerals, divisible by 3 | `translators.py`, `parse_tree.py`, Translators and Parse Tree pages |
| 2.3 SDT: infix → prefix, postfix → infix, postfix → prefix, Roman ↔ int, annotated trees | `translators.py`, Translators page |
| 2.4 recursive descent, left-recursion removal | `grammar/topdown.py`, `grammar/transforms.py` |
| 2.5 infix → postfix translator | `translators.py` (step-by-step trace) |
| 3.1 tokens, lexemes, attributes | `lexer.py`, Lexer page |
| 3.2 buffer pairs, sentinels, buffer size | `buffer.py`, `docs/buffer_experiment.md` |
| 3.3 string terms, regular definitions | `regex_tools.py`, Strings & Regex page |
| 3.4 transition diagrams | `lexer.py`, `app/diagrams.py`, Lexer page |
| 3.5 Lex/Flex programs | `lex/` |
| 4.1 parse trees | `parse_tree.py`, Parse Tree page |
| 4.2 derivations, ambiguity, L(G) | `grammar/derivation.py`, Grammar Workbench |
| 4.3 left recursion, left factoring, dangling else | `grammar/transforms.py`, `grammars/dangling_else_fixed.txt` |
| 4.4 FIRST/FOLLOW, LL(1) table, stack traces, recursive descent | `grammar/first_follow.py`, `grammar/ll1.py`, `grammar/topdown.py` |
| 2.7, 2.8, 4.1 (error recovery), 4.5–4.9 | planned, Phases 4–7 |
