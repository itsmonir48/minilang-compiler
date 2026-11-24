/* Extract URLs and e-mail addresses from text, one per line. */
%option noyywrap
%{
#include <stdio.h>
%}
user      [A-Za-z0-9._%+-]+
domain    [A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}
path      [^ \t\n<>"')]*
%%
https?:\/\/{domain}(:[0-9]+)?(\/{path})?   { printf("URL\t%s\n", yytext); }
{user}@{domain}                            { printf("EMAIL\t%s\n", yytext); }
.|\n                                       { /* skip everything else */ }
%%
int main(int argc, char **argv) {
    if (argc > 1 && !(yyin = fopen(argv[1], "r"))) { perror(argv[1]); return 2; }
    yylex();
    return 0;
}
