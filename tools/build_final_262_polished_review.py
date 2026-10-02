#!/usr/bin/env python3
from pathlib import Path
from collections import defaultdict, Counter
from PIL import Image, ImageFile
import csv, json, re, hashlib, shutil

ImageFile.LOAD_TRUNCATED_IMAGES=True
ROOT=Path("DS_CUSTOM_LIBRARY")
AUD=ROOT/"DS_READY_MASTER"/"final_262_conversion_audit.csv"
REBORN=ROOT/"recovered"/"Reborn_Plates_Legacy"
ER=ROOT/"packs"/"Elite_Redux_ER_nextdex"
VANILLA=ROOT/"packs"/"DrPrettyman_DS_64x64"/"sprites-processed"/"front"
OUT=ROOT/"converted"/"Final_262_Polished"
REPORT=ROOT/"cleanup-audit"/"final_262_polish_audit.csv"
RECOLOR=ROOT/"cleanup-audit"/"final-262-recolor-audit.json"
PAGE=Path("mercury-final-polished-sprite-approval.html")

def norm(s):
    s=str(s).lower().replace("_","-").replace(" ","-").replace("'","")
    s=re.sub(r"[^a-z0-9-]+","-",s)
    return re.sub(r"-+","-",s).strip("-")

def opaque_colors(im):
    return len({p[:3] for p in im.convert("RGBA").getdata() if p[3]})

def run_scale_hint(im):
    im=im.convert("RGBA"); w,h=im.size; px=im.load(); counts=Counter()
    step=max(1,h//24)
    for y in range(0,h,step):
        last=px[0,y]; run=1
        for x in range(1,w):
            p=px[x,y]
            if p==last: run+=1
            else:
                if run<=12: counts[run]+=1
                last=p; run=1
    even=sum(v for k,v in counts.items() if k%2==0)
    odd=sum(v for k,v in counts.items() if k%2==1)
    return 2 if min(w,h)>=128 and even>odd*1.5 else 1

def quant15(im):
    im=im.convert("RGBA"); a=im.getchannel("A")
    rgb=Image.new("RGB",im.size,(0,0,0)); rgb.paste(im.convert("RGB"),mask=a)
    q=rgb.quantize(colors=15,method=Image.Quantize.MEDIANCUT).convert("RGB")
    out=Image.new("RGBA",im.size,(0,0,0,0)); out.paste(q,mask=a)
    return out

def polish(src):
    im=Image.open(src); im.load(); im=im.convert("RGBA")
    flags=[]; factor=run_scale_hint(im)
    if factor==2:
        im=im.resize((im.width//2,im.height//2),Image.Resampling.NEAREST)
        flags.append("2x source de-scaled")
    bbox=im.getchannel("A").getbbox()
    if not bbox:
        return Image.new("RGBA",(64,64),(0,0,0,0)),flags+["empty source"],False,False
    crop=im.crop(bbox); resized=False; reduced=False
    if crop.width>62 or crop.height>62:
        scale=min(62/crop.width,62/crop.height)
        crop=crop.resize((max(1,round(crop.width*scale)),max(1,round(crop.height*scale))),Image.Resampling.NEAREST)
        flags.append("nearest-neighbor fit to DS canvas"); resized=True
    colors=opaque_colors(crop)
    if colors>15:
        crop=quant15(crop); flags.append(f"palette reduced {colors}→15"); reduced=True
    canvas=Image.new("RGBA",(64,64),(0,0,0,0))
    canvas.alpha_composite(crop,((64-crop.width)//2,max(0,62-crop.height)))
    return canvas,flags,resized,reduced

def struct_sig(im):
    im=im.convert("RGBA")
    bbox=im.getchannel("A").getbbox()
    if not bbox: return ""
    im=im.crop(bbox)
    cmap={}; nxt=1; out=bytearray()
    out.extend(im.width.to_bytes(2,"big")); out.extend(im.height.to_bytes(2,"big"))
    for r,g,b,a in im.getdata():
        if a==0: out.extend((0,0)); continue
        k=(r,g,b,a)
        if k not in cmap: cmap[k]=nxt; nxt+=1
        out.extend(cmap[k].to_bytes(2,"big"))
    return hashlib.sha256(out).hexdigest()

def reborn_sources(identity):
    idx={norm(p.name):p for p in REBORN.iterdir() if p.is_dir()}
    d=idx.get(norm(identity))
    if not d: return {}
    names={"front":"front.png","back":"back.png","front-shiny":"shiny_front.png","back-shiny":"shiny_back.png"}
    return {slot:d/name for slot,name in names.items() if (d/name).exists()}

def er_sources(identity):
    key=identity.upper()
    names={"front":f"{key}.png","back":f"{key}_BACK.png","front-shiny":f"{key}_SHINY.png","back-shiny":f"{key}_BACK_SHINY.png"}
    return {slot:ER/name for slot,name in names.items() if (ER/name).exists()}

vanilla_idx={}
if VANILLA.exists():
    for p in VANILLA.iterdir():
        if p.is_file() and p.suffix.lower() in {".png",".gif",".bmp",".jpg",".jpeg",".webp"}:
            vanilla_idx[norm(p.stem)]=p

rows=list(csv.DictReader(AUD.open()))
rows=[r for r in rows if r.get("audit_action")=="NEW_CANDIDATE_IMPORT"]
OUT.mkdir(parents=True,exist_ok=True); REPORT.parent.mkdir(parents=True,exist_ok=True)

audit=[]; cards=[]
for r in rows:
    identity=r["identity"]; species=r.get("species") or re.sub(r"_mega(?:_[xyz])?$","",identity).replace("_"," ").title()
    srcs=reborn_sources(identity) if r["source_family"]=="Reborn_Plates" else er_sources(identity)
    d=OUT/identity
    if d.exists(): shutil.rmtree(d)
    d.mkdir(parents=True,exist_ok=True)
    allflags=[]; resized=False; reduced=False
    for slot,p in srcs.items():
        try:
            im,flags,rs,rd=polish(p)
            im.save(d/f"{slot}.png")
            allflags+=flags; resized|=rs; reduced|=rd
        except Exception as e:
            allflags.append(f"{slot} decode error: {type(e).__name__}")
    front=d/"front.png"
    pure=False; vanilla_match=""
    vp=vanilla_idx.get(norm(species))
    if front.exists() and vp and vp.exists():
        try:
            pure=struct_sig(Image.open(front))==struct_sig(Image.open(vp))
            if pure: vanilla_match=vp.as_posix()
        except Exception: pass
    if pure:
        design_class="PURE_RECOLOR_OF_VANILLA"
    elif resized or reduced:
        design_class="ACTUAL_DESIGN__TECH_CLEANUP_APPLIED"
    else:
        design_class="ACTUAL_DESIGN__SOURCE_GBA_ART_PRESERVED"
    audit.append({
        **r,"species":species,"source_views":"|".join(sorted(srcs)),
        "polished_views":"|".join(sorted(p.stem for p in d.glob("*.png"))),
        "design_class":design_class,"pure_recolor_of_vanilla":pure,
        "vanilla_match":vanilla_match,"polish_notes":" | ".join(sorted(set(allflags))) or "source art preserved"
    })

# family helpers
alias={}
def family(root,*members):
    for x in (root,)+members: alias[x]=root
family("Eevee","Vaporeon","Jolteon","Flareon","Espeon","Umbreon","Leafeon","Glaceon","Sylveon")
for root,members in {
"Pidgey":["Pidgeotto","Pidgeot"],"Vulpix":["Ninetales"],"Poliwag":["Poliwhirl","Poliwrath","Politoed"],
"Abra":["Kadabra","Alakazam"],"Bellsprout":["Weepinbell","Victreebel"],"Geodude":["Graveler","Golem"],
"Slowpoke":["Slowbro","Slowking"],"Gastly":["Haunter","Gengar"],"Onix":["Steelix"],"Happiny":["Chansey","Blissey"],
"Elekid":["Electabuzz","Electivire"],"Magby":["Magmar","Magmortar"],"Larvitar":["Pupitar","Tyranitar"],
"Treecko":["Grovyle","Sceptile"],"Torchic":["Combusken","Blaziken"],"Mudkip":["Marshtomp","Swampert"],
"Ralts":["Kirlia","Gardevoir","Gallade"],"Trapinch":["Vibrava","Flygon"],"Swablu":["Altaria"],
"Bagon":["Shelgon","Salamence"],"Beldum":["Metang","Metagross"],"Turtwig":["Grotle","Torterra"],
"Chimchar":["Monferno","Infernape"],"Piplup":["Prinplup","Empoleon"],"Starly":["Staravia","Staraptor"],
"Shinx":["Luxio","Luxray"],"Shieldon":["Bastiodon"],"Combee":["Vespiquen"],"Buneary":["Lopunny"],
"Gible":["Gabite","Garchomp"],"Skorupi":["Drapion"],"Gligar":["Gliscor"],"Nosepass":["Probopass"],
"Duskull":["Dusclops","Dusknoir"],"Snivy":["Servine","Serperior"],"Tepig":["Pignite","Emboar"],
"Oshawott":["Dewott","Samurott"],"Purrloin":["Liepard"],"Munna":["Musharna"],"Pidove":["Tranquill","Unfezant"],
"Roggenrola":["Boldore","Gigalith"],"Timburr":["Gurdurr","Conkeldurr"],"Petilil":["Lilligant"],
"Sandile":["Krokorok","Krookodile"],"Dwebble":["Crustle"],"Yamask":["Cofagrigus","Runerigus"],
"Tirtouga":["Carracosta"],"Archen":["Archeops"],"Trubbish":["Garbodor"],"Solosis":["Duosion","Reuniclus"],
"Vanillite":["Vanillish","Vanilluxe"],"Karrablast":["Escavalier"],"Ferroseed":["Ferrothorn"],
"Klink":["Klang","Klinklang"],"Tynamo":["Eelektrik","Eelektross"],"Litwick":["Lampent","Chandelure"],
"Shelmet":["Accelgor"],"Mienfoo":["Mienshao"],"Golett":["Golurk"],"Pawniard":["Bisharp","Kingambit"],
"Deino":["Zweilous","Hydreigon"],"Chespin":["Quilladin","Chesnaught"],"Fennekin":["Braixen","Delphox"],
"Froakie":["Frogadier","Greninja"],"Bunnelby":["Diggersby"],"Litleo":["Pyroar"],"Spritzee":["Aromatisse"],
"Binacle":["Barbaracle"],"Skrelp":["Dragalge"],"Clauncher":["Clawitzer"],"Tyrunt":["Tyrantrum"],
"Amaura":["Aurorus"],"Goomy":["Sliggoo","Goodra"],"Noibat":["Noivern"],"Rowlet":["Dartrix","Decidueye"],
"Litten":["Torracat","Incineroar"],"Popplio":["Brionne","Primarina"],"Cutiefly":["Ribombee"],
"Dewpider":["Araquanid"],"Fomantis":["Lurantis"],"Sandygast":["Palossand"],"Jangmo-o":["Hakamo-o","Kommo-o"],
"Grookey":["Thwackey","Rillaboom"],"Scorbunny":["Raboot","Cinderace"],"Sobble":["Drizzile","Inteleon"],
"Arrokuda":["Barraskewda"],"Sizzlipede":["Centiskorch"],"Silicobra":["Sandaconda"],"Venipede":["Whirlipede","Scolipede"],
"Scraggy":["Scrafty"],"Capsakid":["Scovillain"]
}.items(): family(root,*members)

dex={"Pidgey":16,"Vulpix":37,"Poliwag":60,"Abra":63,"Bellsprout":69,"Geodude":74,"Slowpoke":79,"Gastly":92,
"Onix":95,"Eevee":133,"Happiny":173,"Larvitar":246,"Treecko":252,"Torchic":255,"Mudkip":258,"Ralts":280,
"Trapinch":328,"Swablu":333,"Bagon":371,"Beldum":374,"Turtwig":387,"Chimchar":390,"Piplup":393,"Starly":396,
"Shinx":403,"Shieldon":410,"Combee":415,"Buneary":427,"Gible":443,"Snivy":495,"Tepig":498,"Oshawott":501,
"Deino":633,"Chespin":650,"Fennekin":653,"Froakie":656,"Litleo":667,"Goomy":704,"Noibat":714,"Rowlet":722,
"Litten":725,"Popplio":728,"Jangmo-o":782,"Grookey":810,"Scorbunny":813,"Sobble":816}

groups=defaultdict(list)
for a in audit: groups[alias.get(a["species"],a["species"])].append(a)

def esc(s):
    return str(s or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

sections=[]
for fam,items in sorted(groups.items(),key=lambda kv:(dex.get(kv[0],9999),kv[0].lower())):
    inner=[]
    for a in sorted(items,key=lambda x:(x["species"].lower(),x["identity"])):
        ident=a["identity"]; rel=f"DS_CUSTOM_LIBRARY/converted/Final_262_Polished/{ident}"
        types=" / ".join(x for x in [a.get("type1",""),a.get("type2","")] if x) or "Type unknown"
        cls=a["design_class"]
        if cls=="PURE_RECOLOR_OF_VANILLA":
            badge='<div class="recolor pure">PURE RECOLOR OF VANILLA — safe to pass/delete unless you specifically want this palette.</div>'
        elif cls.endswith("SOURCE_GBA_ART_PRESERVED"):
            badge='<div class="recolor design">ACTUAL DESIGN CHANGE — source GBA pixel art preserved. If it still looks rough, that roughness is in the original design.</div>'
        else:
            badge='<div class="recolor tech">ACTUAL DESIGN CHANGE — DS technical cleanup was required. Judge the concept more than tiny pixel details.</div>'
        def img(slot):
            p=d/f"{slot}.png"
            return f"{rel}/{slot}.png" if (OUT/ident/f"{slot}.png").exists() else ""
        inner.append(f"""<article class="card" data-id="{esc(ident)}" data-search="{esc((a['species']+' '+ident+' '+a.get('form_variant','')+' '+types).lower())}">
<div class="head"><div><b>{esc(a['species'])}</b><small>{esc(a.get('form_variant',''))}</small></div><em>{esc(a['source_family'].replace('_',' '))}</em></div>
{badge}
<div class="sprites" data-front="{img('front')}" data-back="{img('back')}" data-front-shiny="{img('front-shiny')}" data-back-shiny="{img('back-shiny')}"><div><label>FRONT</label><img class="front" src="{img('front')}"></div><div><label>BACK</label><img class="back" src="{img('back')}"></div></div>
<div class="meta"><b>{esc(types)}</b><small>{esc(ident)}</small></div>
<div class="views"><button data-view="normal" class="active">Normal</button><button data-view="shiny">Shiny</button></div>
<div class="decision"><button data-decision="Keep">Keep</button><button data-decision="Maybe">Maybe</button><button data-decision="Delete">Delete</button></div>
<div class="role"><span>Role</span><button data-role="Evolution">Evolution</button><button data-role="Mega">Mega</button><button data-role="Delta">Delta</button></div>
<textarea placeholder="Optional note"></textarea></article>""")
    sections.append(f'<section class="family" data-search="{esc(fam.lower())}"><div class="familyhead"><h2>{esc(fam)} family</h2><span>{len(items)} candidate{"s" if len(items)!=1 else ""}</span></div><div class="grid">{"".join(inner)}</div></section>')

css="""*{box-sizing:border-box}body{margin:0;background:#eef2f7;color:#172033;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif}header{position:sticky;top:0;z-index:20;background:#fffffff5;border-bottom:1px solid #ccd6e3;padding:9px}.wrap,main{max-width:1100px;margin:auto}h1{font-size:19px;margin:0}.sub{font-size:12px;color:#657187;line-height:1.35;margin:4px 0 7px}.controls{display:grid;grid-template-columns:1fr auto auto;gap:6px}input,button,textarea{font:inherit;border:1px solid #c7d2e0;border-radius:9px;background:#fff;color:#172033}input{height:38px;padding:0 9px}button{padding:8px 10px;font-weight:750}#export{background:#244a78;color:white}.progress{height:5px;background:#dce5ef;border-radius:99px;overflow:hidden;margin-top:7px}#bar{height:100%;background:#4d78ad;width:0}#summary{font-size:11px;color:#5e6a7c;margin-top:5px}main{padding:10px 9px 60px}.family{background:#fff;border:1px solid #d5dfea;border-radius:14px;margin-bottom:11px;overflow:hidden}.familyhead{display:flex;justify-content:space-between;align-items:center;padding:9px 10px;background:#f9fbfd;border-bottom:1px solid #e5eaf1}.familyhead h2{font-size:16px;margin:0}.familyhead span{font-size:10px;color:#6b7789}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(295px,1fr));gap:8px;padding:8px}.card{border:1px solid #dfe6ee;border-radius:11px;overflow:hidden}.head{display:flex;justify-content:space-between;padding:8px 9px;gap:8px}.head b{font-size:15px}.head small{display:block;color:#69768a;font-size:10px}.head em{font-style:normal;font-size:9px;background:#edf3f9;padding:4px 6px;border-radius:999px;height:max-content}.recolor{margin:0 8px 6px;padding:6px 7px;border-radius:7px;font-size:10px;font-weight:700}.pure{background:#ffe0e0;color:#8c2d2d}.design{background:#e5f3e5;color:#2e6b37}.tech{background:#fff0bd;color:#775e10}.sprites{display:grid;grid-template-columns:1fr 1fr;gap:6px;background:#f6f8fb;padding:7px}.sprites>div{height:132px;background:#fff;border:1px solid #e2e8ef;border-radius:9px;display:flex;align-items:center;justify-content:center;position:relative}.sprites label{position:absolute;top:4px;left:5px;font-size:8px;color:#7d8999;font-weight:800}.sprites img{max-width:118px;max-height:118px;image-rendering:pixelated}.meta{display:flex;justify-content:space-between;gap:8px;padding:6px 9px;font-size:10px}.meta small{color:#7a8798;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.views,.role{display:flex;gap:5px;padding:0 8px 7px;align-items:center;flex-wrap:wrap}.views button,.role button{font-size:10px;padding:5px 8px}.views .active{background:#dfeaf7}.decision{display:grid;grid-template-columns:repeat(3,1fr);gap:5px;padding:0 8px 7px}.decision button{font-size:11px}.decision [data-decision="Keep"].active{background:#dff1df;border-color:#82b58a}.decision [data-decision="Maybe"].active{background:#fff0bd;border-color:#d1b35f}.decision [data-decision="Delete"].active{background:#f7dddd;border-color:#d89797;color:#8a2929}.role button.active{background:#e5dff7;border-color:#9c8bc8}textarea{width:calc(100% - 16px);margin:0 8px 8px;min-height:42px;padding:6px;font-size:11px}.hidden{display:none!important}@media(max-width:600px){.grid{grid-template-columns:1fr}.controls{grid-template-columns:1fr auto}#undecided{display:none}}"""
js="""const STORE='mercury-final-polished-262-v2';let D={},only=false;try{D=JSON.parse(localStorage.getItem(STORE)||'{}')}catch{}const cards=[...document.querySelectorAll('.card')],families=[...document.querySelectorAll('.family')],search=document.getElementById('search'),summary=document.getElementById('summary'),bar=document.getElementById('bar');function view(c,v){let s=c.querySelector('.sprites');c.querySelector('.front').src=v==='shiny'?s.dataset.frontShiny:s.dataset.front;c.querySelector('.back').src=v==='shiny'?s.dataset.backShiny:s.dataset.back;c.querySelectorAll('[data-view]').forEach(b=>b.classList.toggle('active',b.dataset.view===v))}function apply(c){let d=D[c.dataset.id]||{};c.querySelectorAll('[data-decision]').forEach(b=>b.classList.toggle('active',b.dataset.decision===d.decision));c.querySelectorAll('[data-role]').forEach(b=>b.classList.toggle('active',b.dataset.role===d.role));c.querySelector('textarea').value=d.note||'';view(c,d.view||'normal')}function filter(){let q=search.value.trim().toLowerCase();families.forEach(f=>{let n=0;f.querySelectorAll('.card').forEach(c=>{let d=D[c.dataset.id]||{},show=(!q||c.dataset.search.includes(q)||f.dataset.search.includes(q))&&(!only||!d.decision);c.classList.toggle('hidden',!show);if(show)n++});f.classList.toggle('hidden',n===0)})}function stats(){let done=cards.filter(c=>(D[c.dataset.id]||{}).decision).length;summary.textContent=done+' / '+cards.length+' decided';bar.style.width=(done/cards.length*100)+'%';filter()}function save(){localStorage.setItem(STORE,JSON.stringify(D));stats()}cards.forEach(c=>{c.querySelectorAll('[data-decision]').forEach(b=>b.onclick=()=>{D[c.dataset.id]={...(D[c.dataset.id]||{}),decision:b.dataset.decision};save();apply(c)});c.querySelectorAll('[data-role]').forEach(b=>b.onclick=()=>{D[c.dataset.id]={...(D[c.dataset.id]||{}),role:b.dataset.role};save();apply(c)});c.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>{D[c.dataset.id]={...(D[c.dataset.id]||{}),view:b.dataset.view};save();apply(c)});c.querySelector('textarea').onchange=e=>{D[c.dataset.id]={...(D[c.dataset.id]||{}),note:e.target.value};save()};apply(c)});search.oninput=filter;document.getElementById('undecided').onclick=()=>{only=!only;document.getElementById('undecided').textContent=only?'Show all':'Undecided only';filter()};document.getElementById('export').onclick=()=>{let out=[['identity','decision','role','note']];cards.forEach(c=>{let d=D[c.dataset.id]||{};out.push([c.dataset.id,d.decision||'',d.role||'',d.note||''])});let csv=out.map(r=>r.map(v=>'"'+String(v??'').replaceAll('"','""')+'"').join(',')).join('\n'),a=document.createElement('a');a.href=URL.createObjectURL(new Blob([csv],{type:'text/csv'}));a.download='mercury_final_polished_sprite_decisions.csv';a.click()};stats();"""

PAGE.write_text(f'<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>Mercury Final Polished Sprite Approval</title><style>{css}</style></head><body><header><div class="wrap"><h1>Mercury — Final Polished Sprite Approval</h1><div class="sub">Same 262 genuinely new candidates, rebuilt from the original GBA source. Red = pure vanilla recolor (safe to pass/delete). Green = actual design change and the source GBA pixel art was preserved. Gold = actual design change but DS fitting/palette cleanup was needed, so judge the concept more than tiny pixel details.</div><div class="controls"><input id="search" placeholder="Search Pokémon / family / type"><button id="undecided">Undecided only</button><button id="export">Export CSV</button></div><div class="progress"><div id="bar"></div></div><div id="summary"></div></div></header><main>{"".join(sections)}</main><script>{js}</script></body></html>')

with REPORT.open("w",newline="") as f:
    fields=list(audit[0].keys())
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(audit)
RECOLOR.write_text(json.dumps({a["identity"]:{"pure_recolor":a["pure_recolor_of_vanilla"],"class":a["design_class"],"vanilla_match":a["vanilla_match"]} for a in audit},indent=2)+"\n")
print(json.dumps({"candidates":len(audit),"pure_recolors":sum(a["pure_recolor_of_vanilla"] for a in audit),"page":str(PAGE),"out":str(OUT)},indent=2))
