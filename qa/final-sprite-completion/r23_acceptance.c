/* R23 isolated acceptance harness. Never call from a live screen. */
#if defined(R23_REAL_SDK)
#include <nitro.h>
#else
typedef unsigned int u32;
typedef unsigned char u8;
extern u32 OS_DisableInterrupts(void), OS_RestoreInterrupts(u32), OS_GetProcMode(void);
extern void DC_FlushRange(const void *,u32);
extern void GX_BeginLoadTex(void), GX_EndLoadTex(void), GX_BeginLoadTexPltt(void), GX_EndLoadTexPltt(void);
extern void GX_LoadTex(const void *,u32,u32), GX_LoadTexPltt(const void *,u32,u32);
extern int GX_GetBankForTex(void), GX_GetBankForTexPltt(void);
#define GX_VRAM_TEX_0_A 1
#define GX_VRAM_TEXPLTT_01_FG 96
#endif
/* Result bits: 1 texture transfer returned, 2 palette transfer returned,
 * 4 bank mappings restored. No claim of rendered pixels or readback. */
static volatile u32 busy;
static u32 last_epoch;
static u32 scratch[128] __attribute__((aligned(32)));
static int enter(u32 epoch){
    if(OS_GetProcMode()!=0x1fu) return 0; /* system mode only */
    u32 irq=OS_DisableInterrupts();
    int ok=!busy && epoch && epoch>last_epoch;
    if(ok){busy=1;last_epoch=epoch;}
    OS_RestoreInterrupts(irq);
    return ok;
}
static void leave(void){u32 irq=OS_DisableInterrupts();busy=0;OS_RestoreInterrupts(irq);}
u32 r23_acceptance(u32 epoch){
#if defined(R23_ISOLATED_HARNESS) && (defined(R23_REAL_SDK) || defined(R23_HOST_MOCK))
    /* Caller must own an isolated, display-off, non-rendering test context,
       with no other GX/DMA users and banks A/F/G explicitly reserved for it.
       This intentionally writes scratch at address zero, never a live PC. */
    if(!enter(epoch))return 0;
    u32 result=0;
    if(GX_GetBankForTex()==GX_VRAM_TEX_0_A && GX_GetBankForTexPltt()==GX_VRAM_TEXPLTT_01_FG){
        for(u32 i=0;i<128;i++)scratch[i]=0x12345678u^(i*0x01010101u);
        DC_FlushRange(scratch,512);
        GX_BeginLoadTex();GX_LoadTex(scratch,0,512);GX_EndLoadTex();result|=1;
        for(u32 i=0;i<8;i++)scratch[i]=0x001f0000u+i;
        DC_FlushRange(scratch,32);
        GX_BeginLoadTexPltt();GX_LoadTexPltt(scratch,0,32);GX_EndLoadTexPltt();result|=2;
        if(GX_GetBankForTex()==GX_VRAM_TEX_0_A && GX_GetBankForTexPltt()==GX_VRAM_TEXPLTT_01_FG)result|=4;
        for(u32 i=0;i<128;i++)scratch[i]=0;
    }
    leave();return result;
#else
    (void)epoch; (void)enter; (void)leave; (void)scratch; return 0;
#endif
}
#ifdef R23_HOST_MOCK
#include <stdio.h>
#include <stdlib.h>
static u32 irq,mode=0x1f,phase,epoch,tex=1,pal=96,cases,bytes;
static const u32 *pending;
static void check(int ok){if(!ok)exit(1);}
u32 OS_GetProcMode(void){return mode;}
u32 OS_DisableInterrupts(void){u32 old=irq;irq=1;return old;}
u32 OS_RestoreInterrupts(u32 old){u32 prev=irq;irq=old;return prev;}
int GX_GetBankForTex(void){return (int)tex;}
int GX_GetBankForTexPltt(void){return (int)pal;}
void DC_FlushRange(const void *p,u32 n){check(!irq&&p==scratch&&((phase==0&&n==512)||(phase==3&&n==32)));phase++;}
void GX_BeginLoadTex(void){check(phase==1&&!irq);tex=0;check(!r23_acceptance(epoch+1));phase++;}
void GX_LoadTex(const void *p,u32 a,u32 n){check(phase==2&&a==0&&n==512);pending=p;}
void GX_EndLoadTex(void){check(phase==2&&pending);for(u32 i=0;i<128;i++)check(pending[i]==(0x12345678u^(i*0x01010101u)));bytes+=512;pending=0;tex=1;phase++;}
void GX_BeginLoadTexPltt(void){check(phase==4&&!irq);pal=0;phase++;}
void GX_LoadTexPltt(const void *p,u32 a,u32 n){check(phase==5&&a==0&&n==32);pending=p;}
void GX_EndLoadTexPltt(void){check(phase==5&&pending);for(u32 i=0;i<8;i++)check(pending[i]==0x001f0000u+i);bytes+=32;pending=0;pal=96;phase=0;}
int main(void){for(epoch=1;epoch<=64;epoch++){check(r23_acceptance(epoch)==7&&!busy&&!irq&&!phase);check(!r23_acceptance(epoch));cases++;}mode=0x12;check(!r23_acceptance(65));mode=0x1f;tex=0;check(!r23_acceptance(65)&&!busy);tex=1;pal=0;check(!r23_acceptance(66)&&!busy);pal=96;check(r23_acceptance(67)==7);cases++;printf("%u isolated harness mock sequences; %u fenced bytes; wrong-bank/IRQ/reentry/stale-epoch gates PASS\n",cases,bytes);return 0;}
#endif
