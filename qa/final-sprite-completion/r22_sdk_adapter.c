/* Isolated SDK-facing adapter; native gate remains closed until verified allocation. */
typedef unsigned int u32;
typedef unsigned char u8;
_Static_assert(sizeof(u32)==4,"word");
extern void DC_FlushRange(const void *,u32);
extern void GX_BeginLoadTex(void),GX_EndLoadTex(void);
extern void GX_LoadTex(const void *,u32,u32);
extern void GX_BeginLoadTexPltt(void),GX_EndLoadTexPltt(void);
extern void GX_LoadTexPltt(const void *,u32,u32);
enum { R22_CLOSED,R22_IDLE,R22_BUSY };
enum { R22_TEXTURE,R22_PALETTE };
static struct {u32 state,epoch; _Alignas(32) u8 data[1024];} ctx;
int r22_open(u32 epoch){if(ctx.state!=R22_CLOSED||epoch==0||epoch<=ctx.epoch)return 0;ctx.epoch=epoch;ctx.state=R22_IDLE;return 1;}
int r22_close(u32 epoch){if(ctx.state!=R22_IDLE||epoch!=ctx.epoch)return 0;ctx.state=R22_CLOSED;return 1;}
static int allowed(u32 kind,u32 addr,u32 len){
#ifdef HOST_TEST
 u32 lo=kind==R22_TEXTURE?32768u:192u,hi=kind==R22_TEXTURE?131072u:32768u;
 return kind<=R22_PALETTE&&addr>=lo&&addr<=hi&&len&&len<=sizeof(ctx.data)&&len<=hi-addr&&!(addr&3u)&&!(len&3u)&&!(addr&(kind==R22_TEXTURE?7u:15u));
#else
 (void)kind;(void)addr;(void)len;return 0;
#endif
}
int r22_transfer(u32 epoch,u32 kind,u32 addr,const u8 *src,u32 len){if(ctx.state!=R22_IDLE||epoch!=ctx.epoch||!src||!allowed(kind,addr,len))return 0;ctx.state=R22_BUSY;for(u32 i=0;i<len;i++)ctx.data[i]=src[i];DC_FlushRange(ctx.data,len);if(kind==R22_TEXTURE){GX_BeginLoadTex();GX_LoadTex(ctx.data,addr,len);GX_EndLoadTex();}else{GX_BeginLoadTexPltt();GX_LoadTexPltt(ctx.data,addr,len);GX_EndLoadTexPltt();}for(u32 i=0;i<len;i++)ctx.data[i]=0;ctx.state=R22_IDLE;return 1;}
#ifdef HOST_TEST
#include <stdio.h>
#include <stdlib.h>
static u32 phase,kind_expected,addr_expected,len_expected,epoch_expected,cycles,bytes;static const u8 *pending;static u8 src[1024];
static void check(int ok){if(!ok)exit(1);}
void DC_FlushRange(const void *p,u32 n){check(phase==0&&p==ctx.data&&n==len_expected);phase=1;}
static void begin(u32 k){check(phase==1&&k==kind_expected);check(!r22_open(epoch_expected+1)&&!r22_close(epoch_expected)&&!r22_transfer(epoch_expected,k,addr_expected,src,len_expected));phase=2;}
static void load(u32 k,const void *p,u32 a,u32 n){check(phase==2&&k==kind_expected&&a==addr_expected&&n==len_expected&&p==ctx.data);pending=p;for(u32 i=0;i<n;i++)src[i]=0;phase=3;}
static void end(u32 k){check(phase==3&&k==kind_expected);for(u32 i=0;i<len_expected;i++)check(pending[i]==(u8)(i+epoch_expected));bytes+=len_expected;cycles++;pending=0;phase=0;}
void GX_BeginLoadTex(void){begin(0);}void GX_LoadTex(const void*p,u32 a,u32 n){load(0,p,a,n);}void GX_EndLoadTex(void){end(0);}
void GX_BeginLoadTexPltt(void){begin(1);}void GX_LoadTexPltt(const void*p,u32 a,u32 n){load(1,p,a,n);}void GX_EndLoadTexPltt(void){end(1);}
int main(void){for(u32 e=1;e<=412;e++){epoch_expected=e;check(r22_open(e)&&!r22_open(e+1));for(u32 k=0;k<2;k++){kind_expected=k;addr_expected=k?192:32768;len_expected=k?32:512;for(u32 i=0;i<len_expected;i++)src[i]=(u8)(i+e);check(r22_transfer(e,k,addr_expected,src,len_expected));for(u32 i=0;i<len_expected;i++)check(ctx.data[i]==0);}check(!r22_transfer(e,0,0,src,512)&&!r22_transfer(e,1,32752,src,32)&&!r22_transfer(e,0,32772,src,512)&&!r22_transfer(e,0,32768,src,0xffffffffu)&&!r22_transfer(e-1,0,32768,src,512));check(r22_close(e)&&!r22_open(e)&&!r22_transfer(e,0,32768,src,512));}printf("%u SDK mock sequences; %u owned bytes; 412 monotonic epochs PASS\n",cycles,bytes);return 0;}
#endif
