typedef unsigned int u32;
typedef int s32;
_Static_assert(sizeof(u32)==4,"word");
/* Host/ARM9 arithmetic only: no SDK or DMA invocation. */
int r20_transfer_ok(u32 addr,u32 size,u32 lo,u32 hi){return lo<=hi && addr>=lo && addr<=hi && size!=0 && (addr&3u)==0 && (size&3u)==0 && size<=hi-addr;}
u32 r20_scroll(u32 start,s32 direction,u32 update){if(start>511u || (direction!=1 && direction!=-1) || update>30u)return 0xffffffffu; s32 target=(s32)start*4096+direction*184*4096; s32 delta=(direction*184*4096)/30; s32 pos=update==30?target:(s32)start*4096+(s32)update*delta; return ((u32)pos>>12)&511u;}
#ifdef HOST_TEST
#include <stdio.h>
int main(void){unsigned count=0;for(unsigned start=0;start<512;start++)for(int d=-1;d<=1;d+=2)for(unsigned i=0;i<=30;i++){int p=i==30?(int)start*4096+d*184*4096:(int)start*4096+(int)i*(d*184*4096/30);int floor=p>=0?p/4096:-((-p+4095)/4096);if(r20_scroll(start,d,i)!=((unsigned)floor&511u))return 1;count++;}if(!r20_transfer_ok(32768,512,32768,131072)||!r20_transfer_ok(192,32,192,32768)||!r20_transfer_ok(130560,512,32768,131072)||r20_transfer_ok(0,512,32768,131072)||r20_transfer_ok(131068,8,32768,131072)||r20_transfer_ok(32769,512,32768,131072)||r20_transfer_ok(32768,0xffffffffu,32768,131072)||r20_transfer_ok(32768,0,32768,131072))return 2;printf("%u scroll cases; 8 bounds cases PASS\n",count);return 0;}
#endif
