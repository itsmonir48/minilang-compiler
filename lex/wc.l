/* The classic wc: count characters, words and lines (Dragon Book 3.5). */
%option noyywrap
%{
#include <stdio.h>
static long chars = 0, words = 0, lines = 0;
%}
%%
[^ \t\n]+   { words++; chars += yyleng; }
\n          { lines++; chars++; }
.           { chars++; }
%%
int main(int argc, char **argv) {
    if (argc > 1 && !(yyin = fopen(argv[1], "r"))) { perror(argv[1]); return 2; }
    yylex();
    printf("lines %ld  words %ld  chars %ld\n", lines, words, chars);
    return 0;
}
