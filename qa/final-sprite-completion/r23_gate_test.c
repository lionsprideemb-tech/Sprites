#include <stdio.h>
extern unsigned r23_acceptance(unsigned);
int main(void){for(unsigned i=0;i<256;i++)if(r23_acceptance(i)!=0)return 1;puts("256 default-gate calls denied; no SDK linkage needed PASS");return 0;}
