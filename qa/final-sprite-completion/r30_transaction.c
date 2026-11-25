/* Host-only transaction preflight. No ROM, native IDs, or save writes. */
#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>
typedef struct { const char *key,*review,*hp,*ht,*kind,*req,*sp,*st,*state; bool exact; } Route;
#include "r30_registry_fixture.h"
#define N(a) (sizeof(a)/sizeof((a)[0]))
static bool eq(const char *a,const char *b){return a&&b&&!strcmp(a,b);}
static unsigned checks;
#define CHECK(x) do { assert(x); ++checks; } while(0)
static const Route *lookup(const Route *r,size_t n,const char *key,const char *purpose){
    if(!r||!key||!eq(purpose,"QA_INSPECT")) return NULL;
    const Route *hit=NULL;
    for(size_t i=0;i<n;i++) if(eq(r[i].key,key)){if(hit)return NULL;hit=&r[i];}
    return hit;
}
static bool activate(const Route *r){(void)r;return false;}
static const char *const forms[]={"SPECIES_ORICORIO_BAILE","SPECIES_ORICORIO_POM_POM","SPECIES_ORICORIO_PAU","SPECIES_ORICORIO_SENSU"};
static const char mega[]="SPECIES_ORICORIO_MEGA";
typedef struct { const char *species; unsigned token,stats; } Mon;
typedef struct { const char *origin; unsigned token; } Origin;
typedef struct { unsigned generation; bool active; Mon party[2][6]; Origin origins[2][6]; } Battle;
typedef enum { OK, FAIL_WRITE, FAIL_STATS, FAIL_AFTER_STATS } Fault;
static bool valid(const Battle *b,unsigned g,unsigned o,unsigned s){return b&&b->active&&g&&g==b->generation&&o<2&&s<6;}
static bool begin(Battle *b,unsigned g){if(!b||b->active||!g||g<=b->generation)return false;b->generation=g;b->active=true;return true;}
/* Staged copy models atomic commit. Faults can mutate only the staged copy. */
static bool stage(Mon *m,const char *target,Fault f){m->species=target;if(f==FAIL_WRITE)return false;m->stats++;if(f==FAIL_STATS)return false;return f!=FAIL_AFTER_STATS;}
static bool entry(Battle *b,unsigned g,unsigned o,unsigned s,const char *item,bool transformed,Fault f){
    if(!valid(b,g,o,s)||transformed||!eq(item,"ITEM_ORICORIONITE"))return false;
    Mon *m=&b->party[o][s];Origin *r=&b->origins[o][s];
    if(r->origin||!m->token)return false;
    const char *original=NULL;for(size_t i=0;i<N(forms);i++)if(eq(m->species,forms[i]))original=forms[i];
    if(!original)return false;
    Mon next=*m;if(!stage(&next,mega,f))return false;
    *m=next;*r=(Origin){original,m->token};return true;
}
static bool restore(Battle *b,unsigned g,unsigned o,unsigned s,const char *event,bool transformed,Fault f){
    if(!valid(b,g,o,s)||transformed||(!eq(event,"FAINT")&&!eq(event,"END_BATTLE")))return false;
    Mon *m=&b->party[o][s];Origin *r=&b->origins[o][s];
    if(!r->origin||!m->token||r->token!=m->token||!eq(m->species,mega))return false;
    Mon next=*m;if(!stage(&next,r->origin,f))return false;
    *m=next;*r=(Origin){0};return true;
}
static bool finish(Battle *b,unsigned g){if(!valid(b,g,0,0))return false;for(unsigned o=0;o<2;o++)for(unsigned s=0;s<6;s++)if(b->origins[o][s].origin)return false;b->active=false;return true;}
static bool same(const Battle *a,const Battle *b){
    if(a->active!=b->active||a->generation!=b->generation)return false;
    for(unsigned o=0;o<2;o++)for(unsigned s=0;s<6;s++){
        Mon x=a->party[o][s],y=b->party[o][s];Origin u=a->origins[o][s],v=b->origins[o][s];
        if(x.species!=y.species||x.token!=y.token||x.stats!=y.stats||u.origin!=v.origin||u.token!=v.token)return false;
    }return true;
}
static void registry_tests(void){
    CHECK(N(routes)==71);unsigned exact=0,missing=0,held=0,other=0,kinds[4]={0},reviews=0;
    for(size_t i=0;i<N(routes);i++){
        const Route *r=&routes[i];char key[256];int len=snprintf(key,sizeof key,"%s|%s|%s|%s",r->review,r->hp,r->kind,r->req);
        CHECK(len>0&&(size_t)len<sizeof key&&eq(key,r->key));CHECK(lookup(routes,N(routes),key,"QA_INSPECT")==r);
        CHECK(r->sp&&r->ht&&r->req);CHECK(!activate(r));CHECK(!lookup(routes,N(routes),key,"PRODUCTION"));CHECK(!lookup(routes,N(routes),key,"SAVE_WRITE"));CHECK(!lookup(routes,N(routes),key,"NATIVE_EVOLUTION"));CHECK(!lookup(routes,N(routes),key,NULL));
        bool seen=false;for(size_t j=0;j<i;j++)if(eq(r->review,routes[j].review))seen=true;if(!seen)reviews++;
        CHECK(strlen(r->kind)==1&&r->kind[0]>='0'&&r->kind[0]<='3');kinds[r->kind[0]-'0']++;
        if(r->exact){exact++;CHECK(eq(r->state,"SOURCE_ROUTE_CONFIRMED_QA_ONLY")&&r->st);}else if(!r->st){missing++;CHECK(eq(r->state,"HOLD_MISSING_EXACT_SYMBOL"));}else if(eq(r->state,"HOLD_HISTORICAL_AUTHORITY_COMPARISON"))held++;else{other++;CHECK(eq(r->state,"HOLD_NO_EXACT_CURRENT_ROUTE"));}
    }
    CHECK(reviews==68);CHECK(exact==10&&missing==2&&held==44&&other==15);CHECK(kinds[0]==51&&kinds[1]==16&&kinds[2]==2&&kinds[3]==2);
    Route dup[]={routes[0],routes[0]};CHECK(!lookup(dup,2,dup[0].key,"QA_INSPECT"));CHECK(!lookup(routes,N(routes),"UNKNOWN","QA_INSPECT"));CHECK(!lookup(NULL,0,"UNKNOWN","QA_INSPECT"));CHECK(!activate(NULL));
}
static void transaction_tests(void){
    unsigned char save[4096],baseline[4096];for(size_t i=0;i<N(save);i++)save[i]=(unsigned char)(i%251);memcpy(baseline,save,sizeof save);
    for(unsigned f=0;f<N(forms);f++)for(unsigned e=0;e<2;e++)for(unsigned o=0;o<2;o++)for(unsigned s=0;s<6;s++){
        Battle b={0};CHECK(begin(&b,1));b.party[o][s]=(Mon){forms[f],77,10};Battle before=b;
        for(Fault fault=FAIL_WRITE;fault<=FAIL_AFTER_STATS;fault++){CHECK(!entry(&b,1,o,s,"ITEM_ORICORIONITE",false,fault));CHECK(same(&b,&before));}
        CHECK(entry(&b,1,o,s,"ITEM_ORICORIONITE",false,OK));CHECK(eq(b.party[o][s].species,mega)&&b.party[o][s].stats==11&&eq(b.origins[o][s].origin,forms[f]));before=b;
        CHECK(!finish(&b,1));CHECK(same(&b,&before));CHECK(!entry(&b,1,o,s,"ITEM_ORICORIONITE",false,OK));CHECK(same(&b,&before));
        const char *event=e?"END_BATTLE":"FAINT";
        for(Fault fault=FAIL_WRITE;fault<=FAIL_AFTER_STATS;fault++){CHECK(!restore(&b,1,o,s,event,false,fault));CHECK(same(&b,&before));}
        CHECK(restore(&b,1,o,s,event,false,OK));CHECK(eq(b.party[o][s].species,forms[f])&&b.party[o][s].stats==12&&!b.origins[o][s].origin);CHECK(!restore(&b,1,o,s,event,false,OK));CHECK(finish(&b,1));CHECK(!begin(&b,1));CHECK(begin(&b,2));CHECK(!restore(&b,1,o,s,event,false,OK));CHECK(finish(&b,2));CHECK(!memcmp(save,baseline,sizeof save));
    }
    Battle b={0};CHECK(begin(&b,7));b.party[0][0]=(Mon){forms[0],1,0};b.party[0][1]=(Mon){forms[1],2,0};b.party[1][0]=(Mon){forms[2],3,0};Battle before=b;
    CHECK(!entry(&b,7,0,0,"ITEM_NONE",false,OK));CHECK(!entry(&b,7,0,0,"ITEM_ORICORIONITE",true,OK));CHECK(!entry(&b,7,2,0,"ITEM_ORICORIONITE",false,OK));CHECK(!entry(&b,7,0,6,"ITEM_ORICORIONITE",false,OK));CHECK(same(&b,&before));
    CHECK(entry(&b,7,0,0,"ITEM_ORICORIONITE",false,OK));CHECK(entry(&b,7,0,1,"ITEM_ORICORIONITE",false,OK));CHECK(entry(&b,7,1,0,"ITEM_ORICORIONITE",false,OK));before=b;
    CHECK(!restore(&b,7,0,0,"SWITCH_OUT",false,OK));CHECK(!restore(&b,7,0,0,"FAINT",true,OK));CHECK(!restore(&b,6,0,0,"FAINT",false,OK));CHECK(!restore(&b,7,1,1,"FAINT",false,OK));CHECK(same(&b,&before));
    b.party[0][0].token=99;before=b;CHECK(!restore(&b,7,0,0,"END_BATTLE",false,OK));CHECK(same(&b,&before));CHECK(!finish(&b,7));b.party[0][0].token=1;
    CHECK(restore(&b,7,1,0,"FAINT",false,OK));CHECK(eq(b.party[1][0].species,forms[2]));CHECK(restore(&b,7,0,1,"END_BATTLE",false,OK));CHECK(eq(b.party[0][1].species,forms[1]));CHECK(!finish(&b,7));CHECK(restore(&b,7,0,0,"END_BATTLE",false,OK));CHECK(eq(b.party[0][0].species,forms[0]));CHECK(finish(&b,7));CHECK(!memcmp(save,baseline,sizeof save));
}
int main(void){registry_tests();printf("registry checks: %u\n",checks);unsigned start=checks;transaction_tests();printf("transaction checks: %u\nPASS: %u host checks; production bindings disabled\n",checks-start,checks);return 0;}
