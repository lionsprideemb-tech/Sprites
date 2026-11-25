typedef unsigned short u16;
_Static_assert(sizeof(u16)==2,"16-bit word");
/* Exact result of pinned PC ov19_021D78C8 for tint 0x057f, factor 8. */
u16 mercury_pc_shade(u16 color) {
    unsigned r = ((color & 31u) + 31u) / 2u;
    unsigned g = (((color >> 5) & 31u) + 11u) / 2u;
    unsigned b = (((color >> 10) & 31u) + 1u) / 2u;
    return (u16)((b << 10) | (g << 5) | r);
}
#ifdef HOST_TEST
#include <stdio.h>
#include <stdint.h>
static u16 reference(u16 c) {
    int v[3], t[3];
    for (int i=0;i<3;i++){v[i]=((c>>(i*5))&31)<<8; t[i]=((0x57f>>(i*5))&31)<<8;v[i]+=((t[i]-v[i])/16)*8;v[i]=(v[i]>>8)&31;}
    return (u16)(v[0]|v[1]<<5|v[2]<<10);
}
int main(void){uint32_t hash=2166136261u; for(unsigned i=0;i<32768;i++){u16 a=mercury_pc_shade(i); if(a!=reference(i))return 1; hash=(hash^(a&255))*16777619u;hash=(hash^(a>>8))*16777619u;}printf("32768 colors PASS; FNV1a=%08x; black=%04x white=%04x tint=%04x\n",hash,mercury_pc_shade(0),mercury_pc_shade(32767),mercury_pc_shade(0x57f));return 0;}
#endif
