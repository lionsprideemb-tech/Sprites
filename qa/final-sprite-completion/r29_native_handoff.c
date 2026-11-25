/* Host-only symbolic QA. Never link into the playable ROM. No species IDs. */
#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>

typedef struct { const char *key; const char *parent; const char *target; bool source_verified; } Route;
static bool eq(const char *a, const char *b) { return a && b && strcmp(a,b)==0; }
static const Route *inspect(const Route *rows, size_t n, const char *key, const char *purpose) {
    if (!rows || !key || !eq(purpose,"QA_INSPECT")) return NULL;
    const Route *found=NULL;
    for (size_t i=0;i<n;i++) if (eq(rows[i].key,key)) {
        if (found) return NULL;
        found=&rows[i];
    }
    return found;
}
static bool native_binding_allowed(const Route *route) { (void)route; return false; }

static const char *const forms[]={"SPECIES_ORICORIO_BAILE","SPECIES_ORICORIO_POM_POM","SPECIES_ORICORIO_PAU","SPECIES_ORICORIO_SENSU"};
static const char mega[]="SPECIES_ORICORIO_MEGA";
typedef struct { unsigned long generation; bool active; const char *origin[2][6]; } Battle;
static bool valid(Battle *b,unsigned long generation,unsigned owner,unsigned slot) {
    return b && b->active && generation && b->generation==generation && owner<2 && slot<6;
}
static bool begin(Battle *b,unsigned long generation) {
    if (!b || b->active || !generation || generation<=b->generation) return false;
    b->generation=generation; b->active=true; return true;
}
static const char *enter(Battle *b,unsigned long generation,unsigned owner,unsigned slot,const char *species,const char *item,bool transformed) {
    if (!valid(b,generation,owner,slot)||transformed||!eq(item,"ITEM_ORICORIONITE")||b->origin[owner][slot]) return NULL;
    for (size_t i=0;i<4;i++) if (eq(species,forms[i])) { b->origin[owner][slot]=forms[i]; return mega; }
    return NULL;
}
static const char *restore(Battle *b,unsigned long generation,unsigned owner,unsigned slot,const char *species,const char *event,bool transformed) {
    if (!valid(b,generation,owner,slot)||transformed||!eq(species,mega)||(!eq(event,"FAINT")&&!eq(event,"END_BATTLE"))) return NULL;
    const char *origin=b->origin[owner][slot];
    if (!origin) return NULL;
    b->origin[owner][slot]=NULL; return origin;
}
static bool finish(Battle *b,unsigned long generation) {
    if (!valid(b,generation,0,0)) return false;
    for(unsigned o=0;o<2;o++) for(unsigned s=0;s<6;s++) if(b->origin[o][s]) return false;
    b->active=false; return true;
}
static unsigned checks;
#define CHECK(x) do { assert(x); checks++; } while(0)
int main(void) {
    const Route rows[]={{"verified","P","T",true},{"held","P",NULL,false},{"duplicate","P","A",true},{"duplicate","P","B",true}};
    CHECK(inspect(rows,4,"verified","QA_INSPECT")==&rows[0]);
    CHECK(inspect(rows,4,"held","QA_INSPECT")==&rows[1]);
    CHECK(!inspect(rows,4,"duplicate","QA_INSPECT")); CHECK(!inspect(rows,4,"unknown","QA_INSPECT"));
    CHECK(!inspect(rows,4,"verified","PRODUCTION")); CHECK(!inspect(rows,4,"verified","SAVE_WRITE"));
    CHECK(!inspect(rows,4,NULL,"QA_INSPECT")); CHECK(!inspect(NULL,4,"verified","QA_INSPECT"));
    for(size_t i=0;i<4;i++) CHECK(!native_binding_allowed(&rows[i]));
    CHECK(!native_binding_allowed(NULL));
    for(unsigned f=0;f<4;f++) for(unsigned e=0;e<2;e++) {
        Battle b={0}; unsigned long g=1; const char *event=e?"END_BATTLE":"FAINT";
        CHECK(begin(&b,g)); CHECK(eq(enter(&b,g,0,0,forms[f],"ITEM_ORICORIONITE",false),mega));
        CHECK(!finish(&b,g)); CHECK(!enter(&b,g,0,0,forms[(f+1)%4],"ITEM_ORICORIONITE",false));
        CHECK(eq(restore(&b,g,0,0,mega,event,false),forms[f])); CHECK(!restore(&b,g,0,0,mega,event,false));
        CHECK(finish(&b,g)); CHECK(!begin(&b,g)); CHECK(begin(&b,g+1)); CHECK(!restore(&b,g,0,0,mega,event,false)); CHECK(finish(&b,g+1));
    }
    Battle b={0}; CHECK(!begin(&b,0)); CHECK(begin(&b,7)); CHECK(!begin(&b,8));
    CHECK(!enter(&b,7,0,0,forms[0],"ITEM_NONE",false)); CHECK(!enter(&b,7,0,0,forms[0],"ITEM_ORICORIONITE",true));
    CHECK(!enter(&b,7,0,0,"SPECIES_TATSUGIRI","ITEM_ORICORIONITE",false)); CHECK(!enter(&b,7,2,0,forms[0],"ITEM_ORICORIONITE",false));
    CHECK(!enter(&b,7,0,6,forms[0],"ITEM_ORICORIONITE",false)); CHECK(!restore(&b,7,0,0,mega,"FAINT",false));
    CHECK(enter(&b,7,0,0,forms[0],"ITEM_ORICORIONITE",false)); CHECK(enter(&b,7,1,0,forms[1],"ITEM_ORICORIONITE",false));
    CHECK(enter(&b,7,0,1,forms[2],"ITEM_ORICORIONITE",false)); CHECK(!restore(&b,6,0,0,mega,"FAINT",false));
    CHECK(!restore(&b,7,0,0,mega,"SWITCH_OUT",false)); CHECK(!restore(&b,7,0,0,mega,"FAINT",true));
    CHECK(!restore(&b,7,0,0,forms[0],"FAINT",false)); CHECK(!restore(&b,7,0,2,mega,"FAINT",false));
    CHECK(eq(restore(&b,7,1,0,mega,"FAINT",false),forms[1])); CHECK(eq(restore(&b,7,0,1,mega,"END_BATTLE",false),forms[2]));
    CHECK(!finish(&b,7)); CHECK(eq(restore(&b,7,0,0,mega,"END_BATTLE",false),forms[0])); CHECK(finish(&b,7));
    printf("PASS: %u host C checks; production bindings disabled\n",checks); return 0;
}
