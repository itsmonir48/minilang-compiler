/* Spell out every digit of every number: "room 42" -> "room four-two". */
%option noyywrap
%{
#include <stdio.h>
static const char *word[] = {"zero","one","two","three","four",
                             "five","six","seven","eight","nine"};
%}
%%
[0-9]+  { for (int i = 0; i < yyleng; i++)
              printf("%s%s", i ? "-" : "", word[yytext[i] - '0']); }
.|\n    { ECHO; }
%%
int main(int argc, char **argv) {
    if (argc > 1 && !(yyin = fopen(argv[1], "r"))) { perror(argv[1]); return 2; }
    yylex();
    return 0;
}
