/* Host QA only: pinned Platinum API mapping, no native species IDs or ROM linkage. */
#include <assert.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <stddef.h>
#define PARTIES 4
#define SLOTS 6
static unsigned checks;
#define CHECK(x) do { assert(x); ++checks; } while(0)
/* Host representation only. Actual Pokemon uses encrypted BoxPokemon; native
 * adapter must use Pokemon_Copy/GetValue/SetValue/CalcStats, not this layout. */
typedef struct { const char *species; unsigned form, personality, ot, token, hp, maxhp; } Mon;
typedef struct { unsigned count; Mon mon[SLOTS]; } Party;
typedef struct { Party *party; unsigned slot, token, personality, ot, form; const char *species; } Origin;
typedef struct { unsigned generation; bool active; Origin records[PARTIES*SLOTS]; } Tracker;
static bool eq(const char *a,const char *b){return a&&b&&!strcmp(a,b);}
/* Mirrors pinned BattleSystem_GetParty: no inferred flag values. */
static Party *resolve(Party *const p[PARTIES],unsigned battler,bool two_vs_two,bool tag,bool enemy,bool doubles){
    if(!p||battler>=PARTIES)return NULL;
    return p[(two_vs_two||(tag&&enemy))?battler:doubles?(battler&1u):battler];
}
static bool start(Tracker *t,unsigned g){if(!t||t->active||!g||g<=t->generation)return false;t->generation=g;t->active=true;return true;}
static bool valid(Tracker *t,unsigned g,Party *p,unsigned slot){return t&&t->active&&g==t->generation&&p&&p->count<=SLOTS&&slot<p->count&&p->mon[slot].token;}
static Origin *find(Tracker *t,Party *p,unsigned slot){for(size_t i=0;i<PARTIES*SLOTS;i++)if(t->records[i].party==p&&t->records[i].slot==slot)return &t->records[i];return NULL;}
static Origin *free_record(Tracker *t){for(size_t i=0;i<PARTIES*SLOTS;i++)if(!t->records[i].party)return &t->records[i];return NULL;}
static bool same_identity(const Mon *m,const Origin *r){return m->token==r->token&&m->personality==r->personality&&m->ot==r->ot;}
/* No raw form values assumed for Oricorio: supplied symbolic resource contract
 * must prove mapping before native use. These 0..3 values are fixture only. */
static const char base[]="ORICORIO", mega[]="ORICORIO_MEGA";
static bool stage(Mon *m,const char *target,unsigned form,unsigned fault){
    if(form>31)return false;
    m->species=target;if(fault==1)return false;
    m->form=form;if(fault==2)return false;
    m->maxhp=target==mega?120:100;
    if(m->hp){if(m->hp>m->maxhp)m->hp=m->maxhp;}
    if(fault==3)return false;
    return eq(m->species,target)&&m->form==form;
}
static bool enter(Tracker *t,unsigned g,Party *p,unsigned slot,unsigned fault){
    if(!valid(t,g,p,slot)||find(t,p,slot))return false;
    Mon *m=&p->mon[slot];Origin *r=free_record(t);
    if(!r||!eq(m->species,base)||m->form>3||!m->hp)return false;
    Mon staged=*m;Origin saved={p,slot,m->token,m->personality,m->ot,m->form,m->species};
    if(!stage(&staged,mega,0,fault))return false;
    *m=staged;*r=saved;return true;
}
static bool restore(Tracker *t,unsigned g,Party *p,unsigned slot,unsigned fault){
    if(!valid(t,g,p,slot))return false;
    Origin *r=find(t,p,slot);Mon *m=&p->mon[slot];
    if(!r||!same_identity(m,r)||!eq(m->species,mega))return false;
    Mon staged=*m;if(!stage(&staged,r->species,r->form,fault))return false;
    *m=staged;*r=(Origin){0};return true;
}
/* Copyback gate only. Caller must run restoration first; no save writes. */
static bool can_copyback(const Tracker *t,unsigned g){if(!t||!t->active||g!=t->generation)return false;for(size_t i=0;i<PARTIES*SLOTS;i++)if(t->records[i].party)return false;return true;}
static bool finish(Tracker *t,unsigned g){if(!can_copyback(t,g))return false;t->active=false;return true;}
static bool same(const Mon *a,const Mon *b){return a->species==b->species&&a->form==b->form&&a->personality==b->personality&&a->ot==b->ot&&a->token==b->token&&a->hp==b->hp&&a->maxhp==b->maxhp;}
int main(void){
    Party p[PARTIES]={0};Party *ptr[PARTIES]={&p[0],&p[1],&p[2],&p[3]};
    for(unsigned mask=0;mask<16;mask++)for(unsigned b=0;b<PARTIES;b++){
        bool two=mask&1,tag=mask&2,enemy=mask&4,doubles=mask&8;
        CHECK(resolve(ptr,b,two,tag,enemy,doubles)==ptr[(two||(tag&&enemy))?b:doubles?b%2:b]);
    }
    CHECK(!resolve(ptr,4,false,false,false,false));CHECK(!resolve(NULL,0,false,false,false,false));
    for(unsigned form=0;form<4;form++)for(unsigned o=0;o<PARTIES;o++)for(unsigned s=0;s<SLOTS;s++){
        Tracker t={0};Party *q=&p[o];q->count=SLOTS;q->mon[s]=(Mon){base,form,10,20,30,90,100};Mon before=q->mon[s];
        CHECK(start(&t,1));CHECK(!start(&t,2));
        for(unsigned f=1;f<=3;f++){CHECK(!enter(&t,1,q,s,f));CHECK(same(&q->mon[s],&before));CHECK(!find(&t,q,s));}
        CHECK(enter(&t,1,q,s,0));CHECK(eq(q->mon[s].species,mega));CHECK(!can_copyback(&t,1));CHECK(!finish(&t,1));
        CHECK(!enter(&t,1,q,s,0));q->mon[s].hp=0;before=q->mon[s];
        for(unsigned f=1;f<=3;f++){CHECK(!restore(&t,1,q,s,f));CHECK(same(&q->mon[s],&before));CHECK(find(&t,q,s)!=NULL);}
        CHECK(!restore(&t,2,q,s,0));q->mon[s].token++;CHECK(!restore(&t,1,q,s,0));q->mon[s].token--;
        CHECK(restore(&t,1,q,s,0));CHECK(eq(q->mon[s].species,base)&&q->mon[s].form==form&&q->mon[s].hp==0);
        CHECK(!restore(&t,1,q,s,0));CHECK(can_copyback(&t,1));CHECK(finish(&t,1));CHECK(!start(&t,1));CHECK(start(&t,2));CHECK(!restore(&t,1,q,s,0));CHECK(finish(&t,2));
    }
    Tracker t={0};CHECK(start(&t,7));for(unsigned o=0;o<PARTIES;o++){p[o].count=SLOTS;for(unsigned s=0;s<SLOTS;s++){p[o].mon[s]=(Mon){base,s%4,10,20,100+o*SLOTS+s,80,100};CHECK(enter(&t,7,&p[o],s,0));}}
    CHECK(!can_copyback(&t,7));CHECK(resolve(ptr,0,false,false,false,true)==resolve(ptr,2,false,false,false,true));CHECK(!enter(&t,7,resolve(ptr,2,false,false,false,true),0,0));
    Mon swap=p[0].mon[0];p[0].mon[0]=p[0].mon[1];p[0].mon[1]=swap;CHECK(!restore(&t,7,&p[0],0,0));CHECK(!restore(&t,7,&p[0],1,0));swap=p[0].mon[0];p[0].mon[0]=p[0].mon[1];p[0].mon[1]=swap;
    for(unsigned o=0;o<PARTIES;o++)for(unsigned s=0;s<SLOTS;s++)CHECK(restore(&t,7,&p[o],s,0));
    CHECK(can_copyback(&t,7));CHECK(finish(&t,7));
    printf("PASS: %u party mapping and copyback host checks; native binding disabled\n",checks);return 0;
}
