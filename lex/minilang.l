/* Flex scanner for MiniLang (Dragon Book 3.5).
 * Same tokens and attributes as minilang/lexer.py.
 * Output: one line per token:  line:col  token  lexeme  attribute
 */
%option noyywrap yylineno
%{
#include <stdio.h>
#include <string.h>

static int col = 1;
static int errors = 0;
static char *names[1024];
static int n_names = 0;

static int install_id(const char *s) {
    for (int i = 0; i < n_names; i++)
        if (strcmp(names[i], s) == 0) return i;
    if (n_names == 1024) { fprintf(stderr, "name table full\n"); return -1; }
    names[n_names] = strdup(s);
    return n_names++;
}

#define EMIT(tok, attr) printf("%d:%d\t%s\t%s\t%s\n", yylineno, col, tok, yytext, attr)
#define ADVANCE() (col += yyleng)
%}

delim     [ \t\r]
letter    [A-Za-z_]
digit     [0-9]
id        {letter}({letter}|{digit})*
num       {digit}+
real      {digit}+(\.{digit}+)?([Ee][+-]?{digit}+)?
%x COMMENT

%%
{delim}+            { ADVANCE(); }
\n                  { col = 1; }
"//".*              { ADVANCE(); }
"/*"                { ADVANCE(); BEGIN(COMMENT); }
<COMMENT>"*/"       { ADVANCE(); BEGIN(INITIAL); }
<COMMENT>\n         { col = 1; }
<COMMENT>.          { ADVANCE(); }
<COMMENT><<EOF>>    { fprintf(stderr, "error: unterminated comment\n"); errors++; return 0; }

"int"|"float"|"if"|"else"|"while"|"print"  { EMIT(yytext, "-"); ADVANCE(); }
{id}                { char a[32]; snprintf(a, sizeof a, "name #%d", install_id(yytext)); EMIT("id", a); ADVANCE(); }
{num}               { EMIT("num", yytext); ADVANCE(); }
{real}              { EMIT("real", yytext); ADVANCE(); }
{digit}+\.          |
{digit}+(\.{digit}+)?[Ee][+-]?  {
                      fprintf(stderr, "%d:%d error: malformed number '%s'\n", yylineno, col, yytext);
                      errors++; ADVANCE(); }

"<="                { EMIT("relop", "LE"); ADVANCE(); }
">="                { EMIT("relop", "GE"); ADVANCE(); }
"=="                { EMIT("relop", "EQ"); ADVANCE(); }
"!="                { EMIT("relop", "NE"); ADVANCE(); }
"<"                 { EMIT("relop", "LT"); ADVANCE(); }
">"                 { EMIT("relop", "GT"); ADVANCE(); }
"&&"|"||"|[-+*/=!(){};,]  { EMIT(yytext, "-"); ADVANCE(); }

.                   { fprintf(stderr, "%d:%d error: illegal character '%s'\n", yylineno, col, yytext);
                      errors++; ADVANCE(); }
%%

int main(int argc, char **argv) {
    if (argc > 1 && !(yyin = fopen(argv[1], "r"))) { perror(argv[1]); return 2; }
    yylex();
    printf("-- name table --\n");
    for (int i = 0; i < n_names; i++) printf("%d\t%s\n", i, names[i]);
    if (errors) fprintf(stderr, "%d lexical error(s)\n", errors);
    return errors ? 1 : 0;
}
