#include <stdio.h>
/* block comment
   on two lines */
int main(void) {
    int x = 1; // line comment
    printf("not a // comment and not a /* comment */\n");
    return x/*inline*/+1;
}
