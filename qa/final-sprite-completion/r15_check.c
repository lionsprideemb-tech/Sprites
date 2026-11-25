/* Independent host C checker, not Nitro SDK or native runtime. */
#include <stdint.h>
#include <stdio.h>
#include <string.h>
static uint32_t le(const unsigned char *p, unsigned n){uint32_t v=0;for(unsigned i=0;i<n;i++)v|=(uint32_t)p[i]<<(8*i);return v;}
static int header(const unsigned char *p,size_t n,const char *magic,const char *block,unsigned ver){return n>=40&&!memcmp(p,magic,4)&&le(p+4,2)==0xfeff&&le(p+6,2)==ver&&le(p+8,4)==n&&le(p+12,2)==16&&le(p+14,2)==1&&!memcmp(p+16,block,4)&&le(p+20,4)==n-16;}
static int character(const unsigned char *p,size_t n){return n==1072&&header(p,n,"RGCN","RAHC",0x101)&&le(p+24,4)==0xffffffff&&le(p+28,4)==3&&le(p+32,4)==16&&!le(p+36,4)&&le(p+40,4)==1024&&le(p+44,4)==24;}
static int palette(const unsigned char *p,size_t n){if(n!=72||!header(p,n,"RLCN","TTLP",0x100)||le(p+24,4)!=3||le(p+28,4)||le(p+32,4)!=32||le(p+36,4)!=16)return 0;for(unsigned i=0;i<16;i++)if(le(p+40+2*i,2)>32767)return 0;return 1;}
static size_t load(const char *s,unsigned char *p,size_t max){FILE*f=fopen(s,"rb");if(!f)return 0;size_t n=fread(p,1,max,f);fclose(f);return n;}
int main(int argc,char **argv){unsigned char c[1100],p[100];if(argc!=3)return 2;size_t cn=load(argv[1],c,sizeof c),pn=load(argv[2],p,sizeof p);if(!character(c,cn)||!palette(p,pn))return 3;unsigned neg=0;const unsigned co[]={0,4,6,8,12,14,16,20,24,28,32,36,40,44};const unsigned po[]={0,4,6,8,12,14,16,20,24,28,32,36};for(unsigned i=0;i<sizeof co/sizeof *co;i++){c[co[i]]^=1;if(character(c,cn))return 4;c[co[i]]^=1;neg++;}for(unsigned i=0;i<sizeof po/sizeof *po;i++){p[po[i]]^=1;if(palette(p,pn))return 5;p[po[i]]^=1;neg++;}if(character(c,cn-1)||palette(p,pn-1))return 6;neg+=2;unsigned opaque=0;for(unsigned i=48;i<1072;i++){opaque+=(c[i]&15)!=0;opaque+=(c[i]>>4)!=0;}printf("NCGR=%zu NCLR=%zu pixels=2048 opaque=%u negative=%u PASS\n",cn,pn,opaque,neg);return 0;}
