/* Isolated native-facing transfer ownership core. Caller supplies actual DMA hooks. */
typedef unsigned int u32;
typedef unsigned char u8;
_Static_assert(sizeof(u32)==4,"word");
enum { IDLE, OWNED, DRAINING, CLOSED };
typedef struct {u32 state,epoch,serial,addr,len; _Alignas(4) u8 data[1024];} R21;
int r21_init(R21 *s,u32 epoch){if(!s||!epoch)return 0;s->state=IDLE;s->epoch=epoch;s->serial=0;s->addr=0;s->len=0;return 1;}
int r21_stage(R21 *s,u32 addr,const u8 *src,u32 len,u32 lo,u32 hi){if(!s||!src||s->state!=IDLE||s->serial==0xffffffffu||lo>hi||addr<lo||addr>hi||!len||len>1024||len>hi-addr||(addr&3u)||(len&3u))return 0;for(u32 i=0;i<len;i++)s->data[i]=src[i];s->addr=addr;s->len=len;s->serial++;s->state=OWNED;return 1;}
int r21_fence(R21 *s,u32 epoch,u32 serial){if(!s||(s->state!=OWNED&&s->state!=DRAINING)||epoch!=s->epoch||serial!=s->serial)return 0;s->state=s->state==DRAINING?CLOSED:IDLE;s->len=0;return 1;}
int r21_close(R21 *s){if(!s)return 0;if(s->state==OWNED)s->state=DRAINING;else if(s->state==IDLE)s->state=CLOSED;return s->state==CLOSED;}
#ifdef HOST_TEST
#include <stdio.h>
int main(void){R21 s;u8 a[1024];u32 cases=0;for(u32 n=1;n<=256;n++){if(!r21_init(&s,n))return 1;for(u32 j=0;j<1024;j++)a[j]=(u8)(j+n);if(!r21_stage(&s,32768,a,n*4,32768,131072))return 2;for(u32 j=0;j<n*4;j++){a[j]=0;if(s.data[j]!=(u8)(j+n))return 3;cases++;}if(r21_stage(&s,32768,a,4,32768,131072)||r21_close(&s)||r21_fence(&s,n+1,s.serial)||r21_fence(&s,n,s.serial+1)||!r21_fence(&s,n,s.serial)||!r21_close(&s)||r21_fence(&s,n,s.serial)||r21_stage(&s,32768,a,4,32768,131072))return 4;}
if(!r21_init(&s,999)||r21_stage(&s,0,a,4,32768,131072)||r21_stage(&s,131068,a,8,32768,131072)||r21_stage(&s,32769,a,4,32768,131072)||r21_stage(&s,32768,a,0,32768,131072)||r21_stage(&s,32768,a,0xffffffffu,32768,131072)) {return 5;}
printf("256 lifetime cases; %u owned bytes; 5 bounds rejections PASS\n",cases);return 0;}
#endif
