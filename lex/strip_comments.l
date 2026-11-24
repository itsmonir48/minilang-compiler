/* Remove C/C++ comments; keep everything else, including comment-like text in strings. */
%option noyywrap
%{
#include <stdio.h>
%}
%x BLOCK
%%
\"(\\.|[^"\\\n])*\"     { ECHO; }               /* string literal: keep as is */
\'(\\.|[^'\\\n])*\'     { ECHO; }               /* char literal */
"//"[^\n]*              { }                     /* line comment (newline kept) */
"/*"                    { BEGIN(BLOCK); }
<BLOCK>"*/"             { putchar(' '); BEGIN(INITIAL); }  /* a comment acts as a space */
<BLOCK>\n               { putchar('\n'); }      /* keep line numbers */
<BLOCK>.                { }
.|\n                    { ECHO; }
%%
int main(int argc, char **argv) {
    if (argc > 1 && !(yyin = fopen(argv[1], "r"))) { perror(argv[1]); return 2; }
    yylex();
    return 0;
}
