#!/usr/bin/env python3
"""Read-only cross-repository Mercury Delta Flygon integration collision audit.

Reads local read-only clones of Mercury-redux-dex, platinum-modern-ds, and
pret/pokeplatinum. Writes only report outputs on Sprites research branch.
Nothing in the three inspected repositories can be changed by this script.
"""
from __future__ import annotations
import argparse, base64, collections, gzip, hashlib, json, re, subprocess
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument("--dex",type=Path,required=True)
p.add_argument("--platinum",type=Path,required=True)
p.add_argument("--upstream",type=Path,required=True)
p.add_argument("--sprites",type=Path,default=Path("."))
p.add_argument("--output",type=Path,default=Path("report/mercury_delta_readonly_gate"))
a=p.parse_args()
out=a.output
out.mkdir(parents=True,exist_ok=True)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def gitblob(path):
    data=path.read_bytes()
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
def commit(path):
    return subprocess.check_output(["git","-C",str(path),"rev-parse","HEAD"],text=True).strip()
def jsonfile(path):return json.loads(path.read_text())
def gzjson(path):return json.loads(gzip.decompress(base64.b64decode(path.read_text().strip())))
def allstrings(obj):
    if isinstance(obj,str):
        yield obj
    elif isinstance(obj,dict):
        for k,v in obj.items():
            yield str(k)
            yield from allstrings(v)
    elif isinstance(obj,list):
        for v in obj:yield from allstrings(v)
def summary_record(rec,source):
    keys=("key","id","species","constant","name","displayName","form","formId","form_id","nationalDex","nationalDexNumber","dexNumber","types","type1","type2","evolutions","evolution","retired","status","planned")
    return {"source":source,**{k:v for k,v in rec.items() if k in keys}}
R={"schema":"mercury-delta-flygon-readonly-crossrepo-collision-audit-v1",
   "auditScope":"Actual checked-out public GitHub repository files; no game modifications or ID assignment",
   "sources":{
       "SpritesResearchHead":commit(a.sprites),
       "MercuryReduxDexMain":commit(a.dex),
       "PlatinumModernDSMain":commit(a.platinum),
       "pretPokeplatinumMain":commit(a.upstream)},
   "allUnapproved":True,"noRomChanges":True,"noDexChanges":True,
   "noHistoricalVoteChanges":True,"noIDAssigned":True,"noPaletteAllocated":True}
# 1. Immutable creative vote ledger and currently authoritative roster decision.
backup=a.sprites/"review/user-iphone-decisions-2026-10-23.json"
decisions=jsonfile(backup)
assert gitblob(backup)=="61c5e53c6ec81b74d192cd62a4c52c970cea15ce"
assert (decisions["count"],decisions["keepCount"],decisions["cutCount"])==(166,154,12)
overlay=a.sprites/"review/final-artwork-approval-overlay-2026-10-24.json"
assert gitblob(overlay)=="89f328b4471f1531520305e54f63efdbc6251a50"
roster=a.sprites/"review/flygon-roster-plan-2026-11-09.json"
assert gitblob(roster)=="e2c29dcbb27c5354f00a594a9ffbb466cc962e85"
plan=jsonfile(roster)["plannedStructure"]
assert plan["deltaFamily"]["newSpeciesOrFormSlots"]==3
assert plan["deltaMega"]["numberOfMegaSlots"]==0
assert plan["ordinaryMega"]["numberOfMegaSlots"]==1
R["historicalVotes"]={"source":str(backup),"blobSHA":gitblob(backup),"count":166,
     "keep":154,"cut":12,"finalApprovalOverlayBlobSHA":gitblob(overlay),
     "rosterPlanBlobSHA":gitblob(roster)}
# 2. Main registry: this is NOT a list of available game slots.
regpath=a.platinum/"data/canonical_species_1025.txt"
canonical=[s.strip() for s in regpath.read_text().splitlines() if s.strip() and not s.lstrip().startswith("#")]
assert len(canonical)==1025 and len(set(canonical))==1025
assert [(n,canonical[n-1]) for n in (328,329,330)]==[
 (328,"SPECIES_TRAPINCH"),(329,"SPECIES_VIBRAVA"),(330,"SPECIES_FLYGON")]
assert canonical[-1]=="SPECIES_PECHARUNT"
assert not any("DELTA" in sp or "REDUX" in sp for sp in canonical)
speciesmap=(a.platinum/"tools/build_ds_species_id_map.py").read_text()
assert "EGG_INTERNAL_ID = CANONICAL_SPECIES_COUNT + 1" in speciesmap
assert "BAD_EGG_INTERNAL_ID = CANONICAL_SPECIES_COUNT + 2" in speciesmap
assert "return national_dex" in speciesmap
# Detect actual installed production constants, not narrative docs.
production_roots=[
 a.platinum/"data/canonical_species_1025.txt",
 a.platinum/"platinum-overlay/generated",
 a.platinum/"platinum-overlay/src",
 a.platinum/"engine-overlay",
 a.platinum/"tools"]
hits=[]
pat=re.compile(r"\b(?:SPECIES_[A-Z0-9_]*(?:DELTA|REDUX)[A-Z0-9_]*(?:TRAPINCH|VIBRAVA|FLYGON)|SPECIES_(?:TRAPINCH|VIBRAVA|FLYGON)_[A-Z0-9_]*(?:DELTA|REDUX)[A-Z0-9_]*)\b")
for root in production_roots:
    paths=[root] if root.is_file() else (root.rglob("*") if root.is_dir() else [])
    for file in paths:
        if not file.is_file() or file.stat().st_size>500_000 or file.suffix not in {".py",".c",".h",".txt",".json",".md"}:continue
        for lineno,line in enumerate(file.read_text(errors="replace").splitlines(),1):
            if pat.search(line):
                hits.append({"file":str(file.relative_to(a.platinum)),"line":lineno,
                   "preview":line.strip()[:250]})
R["speciesRegistry"]={
 "file":"platinum-modern-ds/data/canonical_species_1025.txt",
 "sha256":sha(regpath),"canonicalUniqueCount":len(canonical),
 "occupiedBaseSpeciesIDRange":[1,1025],
 "vanillaTrapinchVibravaFlygon":[
  {"species":canonical[i-1],"speciesID":i} for i in (328,329,330)],
 "sentinels":{"SPECIES_NONE":0,"SPECIES_EGG":1026,"SPECIES_BAD_EGG":1027},
 "deltaConstantsInCanonical":[],
 "deltaLikeReferencesInPlatinumProduction":hits,
 "noCollisionFreeDeltaIDAllocated":True,
 "doNotAssumeNextIntegerUnallocatedByCustomMercuryRuntime":True
}
# 3. Dex live source: all compressed shards and overlays; don't assume roster row
# keys are game-native species IDs or that raw original shard == active final.
idxpath=a.dex/"data/pokedex/index.json"
index=jsonfile(idxpath);folder=idxpath.parent
shards=index["shards"];overlays=index["overlays"]
allrows=[]
shardcounts=[]
for source in shards:
    doc=gzjson(folder/source)
    rows=doc.get("pokemon") if isinstance(doc,dict) else doc
    assert isinstance(rows,list),(source,type(rows))
    allrows += [(source,entry) for entry in rows if isinstance(entry,dict)]
    shardcounts.append({"file":source,"pokemonRows":len(rows),"sha256":sha(folder/source)})
overlay_docs=[]
for source in overlays:
    data=gzjson(folder/source)
    keys=list(data) if isinstance(data,dict) else []
    overlay_docs.append({"file":source,"sha256":sha(folder/source),"topLevelKeys":keys,
         "patchCount":len(data.get("patches",[])) if isinstance(data,dict) else 0,
         "additions":len(data.get("additions",[])) if isinstance(data,dict) else 0,
         "removeKeysCount":len(data.get("removeKeys",[])) if isinstance(data,dict) else 0})
    if isinstance(data,dict):
        for k in ("patches","additions","updates","records","pokemon","entries"):
            for ent in data.get(k,[]) if isinstance(data.get(k,[]),list) else []:
                if isinstance(ent,dict):allrows.append((source+":"+k,ent))
target=re.compile(r"(?:trapinch|vibrava|flygon)",re.I)
delta=re.compile(r"\b(?:delta[\s_\-]*(?:trapinch|vibrava|flygon)|(?:trapinch|vibrava|flygon)[\s_\-]*delta)\b",re.I)
matching=[]
deltaMatches=[]
for source,entry in allrows:
    identity=" ".join(str(entry.get(k,"")) for k in ("key","id","species","constant","name","displayName","form","formId","form_id"))
    if target.search(identity):
        record=summary_record(entry,source)
        matching.append(record)
        if delta.search(identity):deltaMatches.append(record)
R["dex"]={
  "indexSha256":sha(idxpath),"meta":{k:index.get("meta",{}).get(k) for k in ("entries","rosterCount","approvedRosterCount","sourceBoundCount","retiredCount","statusModel")},
  "shardsRead":len(shards),"overlayDocumentsRead":len(overlays),
  "rawShardPokemonRows":sum(x["pokemonRows"] for x in shardcounts),
  "rawPlusOverlayRecordCount":len(allrows),
  "matchingFlygonFamilyRecords":matching[:80],
  "explicitDeltaIdentityMatches":deltaMatches[:50],
  "matchingCount":len(matching),"deltaNameMatchCount":len(deltaMatches),
  "note":"Raw shards and overlay patches/additions inspected; R8 app merges these records. Matching legacy Redux names do not create or approve new game engine species IDs.",
  "shards":shardcounts,"overlayDocuments":overlay_docs
}
# 4. Real upstream icon routing: verify exact hardcoding, not merely palette art.
icon=(a.upstream/"src/pokemon_icon.c").read_text()
mon=(a.upstream/"include/struct_defs/pokemon.h").read_text()
box=(a.upstream/"src/applications/pc_boxes/icon_helper.c").read_text()
party=(a.upstream/"src/applications/party_menu/sprites.c").read_text()
assert "u8 form : 5;" in mon
assert "if (species > NATIONAL_DEX_COUNT)" in icon
assert "return IconTilesIndex(species);" in icon
assert "return sPokemonIconPaletteIndex[species];" in icon
assert "case SPECIES_TRAPINCH" not in icon and "case SPECIES_VIBRAVA" not in icon and "case SPECIES_FLYGON" not in icon
assert "2 + monIcon->plttIndex" in box and "(isSelected ? 6 : 2) + monIcon->plttIndex" in box
assert "SPECIES_ICON_PLTT_SLOT 3" in party
up=a.upstream/"res/pokemon"
palette_records=[]
for file in sorted(up.rglob("data.json")):
    obj=jsonfile(file)
    val=obj.get("icon_palette")
    if isinstance(val,int):palette_records.append((str(file.relative_to(up)),val))
    elif isinstance(val,list):
        for v in val:
            if isinstance(v,list) and len(v)==2 and isinstance(v[1],int):
                palette_records.append((str(file.relative_to(up))+":"+str(v[0]),v[1]))
all_values=collections.Counter(i for _,i in palette_records)
bank3metas=[{"species":n,"index":v} for n,v in palette_records if v==3]
shared=a.upstream/"res/pokemon/.shared/pl_poke_icon.pal"
ls=shared.read_text().splitlines()
assert ls[:3]==["JASC-PAL","0100","256"] and len(ls[3:])==256
colors=[tuple(map(int,x.split())) for x in ls[3:]]
assert all(v==(0,0,0) for v in colors[48:64])
exp=a.sprites/"review/candidates/orpheus-2026-11-09-UNAPPROVED/desert-scarab-sixview-g4-preflight/reserved_icon_bank3_qa.json"
trial=jsonfile(exp)
assert trial["originalSharedPaletteSHA256"]==sha(shared)
assert trial["customPaletteIsNotInstalled"] is True
assert trial["editedEntryCount"]==15
assert trial["allDecodeIndexDifferences"]==0
R["iconBank3"]={
  "sourcePaletteSHA256":sha(shared),
  "sourceGlobalPaletteEntries":256,
  "usedIconPaletteIndexCounts":{str(k):v for k,v in sorted(all_values.items())},
  "sourceMetaBank3Uses":bank3metas[:30],
  "sourceMetaBank3UseCount":len(bank3metas),
  "numberOfParsedSpeciesAndFormPaletteBindings":len(palette_records),
  "bank3Entries48to63AllZeroInSource":True,
  "trialOnlyPaletteChangesEntries49to63":True,
  "experimentalNCLRNotInstalled":True,
  "threeIconNativeRoundtripPixelDifferences":trial["allDecodeIndexDifferences"],
  "routingIssues":[
     "PokeIconSpriteIndex handles selected explicit alternate-form species only; Delta Trapinch/Vibrava/Flygon have no cases, so form ID alone resolves to ordinary icon",
     "BoxPokemon_IconFormOffset switches on selected species only; Delta forms of the Flygon family have no case",
     "PokeIconPaletteIndex also switches only on specific forms, otherwise uses existing species indexed palette; Delta form bank 3 cannot be selected by artwork alone",
     "PC boxes use normal 2+iconPalette and selected 6+iconPalette slots; party uses 3+iconPalette. A bank3 selection yields party slot 6, requiring complete VRAM palette collision testing with existing UI sprites",
     "Even if palette-bank3 metadata is unused upstream, the 256-color file and indexed assets must be inserted and runtime-tested before selection"],
  "evidence":{"upstreamPokemonIcon":"src/pokemon_icon.c",
       "upstreamPokemonIconSHA256":sha(a.upstream/"src/pokemon_icon.c"),
       "upstreamPC":"src/applications/pc_boxes/icon_helper.c",
       "upstreamParty":"src/applications/party_menu/sprites.c",
       "sharedPalette":"res/pokemon/.shared/pl_poke_icon.pal",
       "trialReport":"review/candidates/orpheus-2026-11-09-UNAPPROVED/desert-scarab-sixview-g4-preflight/reserved_icon_bank3_qa.json"}
}
# 5. Actual vanilla evolution data and the planned/blocked Delta graph.
normal=[]
for st in ("trapinch","vibrava","flygon"):
    path=up/st/"data.json"
    obj=jsonfile(path)
    normal.append({"stage":st,"source":str(path.relative_to(a.upstream)),
                   "types":obj.get("types"),"evolutions":obj.get("evolutions"),
                   "iconPalette":obj.get("icon_palette"),"sha256":sha(path)})
assert normal[0]["evolutions"]==[["EVO_LEVEL",35,"SPECIES_VIBRAVA"]]
assert normal[1]["evolutions"]==[["EVO_LEVEL",45,"SPECIES_FLYGON"]]
assert normal[2]["evolutions"]==[]
assert "TYPE_BUG" in (a.platinum/"platinum-overlay/generated/pokemon_types.txt").read_text()
assert "TYPE_GROUND" in (a.platinum/"platinum-overlay/generated/pokemon_types.txt").read_text()
R["evolutions"]={"canonicalSource":normal,
 "plannedDeltaEdges":[["Delta Trapinch","Delta Vibrava"],["Delta Vibrava","Delta Flygon"]],
 "plannedDeltaFinalTyping":["TYPE_BUG","TYPE_GROUND"],
 "initialDeltaStageTyping":{"Delta Trapinch":"Bug required; secondary not explicitly approved",
                            "Delta Vibrava":"Bug required; secondary not explicitly approved"},
 "approvedDeltaEvolutionMethodsAndLevels":None,
 "separateSpeciesVsAlternateFormStorageArchitecture":"UNDECIDED",
 "noDeltaEvolutionDataInPlatinum":len(hits)==0,
 "sourceOrpheusEvolutionDataWarning":"Do not use earlier source PBS Trapinch->Flygon or Vibrava->Lycanroc erroneous evolution records.",
 "normalEvolutionChainPreserved":True}
R["blockers"]=[
 {"id":"ID-01","severity":"blocked","reason":"1025 canonical base species and 1026/1027 sentinels occupy current canonical ID namespace; no independent three-ID collision-free allocation or committed Delta form mapping","gate":"full planned 1599-row roster to game species/form-ID map + runtime code implementation"},
 {"id":"ID-02","severity":"blocked","reason":"The Dex approved roster is larger than the base 1025 registry, so hypothetical 1028+ integers are not proven free","gate":"reconcile all proposed Mercury custom entries, forms, and Megas against namespace/engine IDs"},
 {"id":"FORM-03","severity":"blocked","reason":"5-bit persistent form value and hard-coded icon/form routing; Delta Flygon line not registered","gate":"choose separate species or valid 1-based form scheme, then test full save/battle/party/box behaviour"},
 {"id":"ICON-04","severity":"blocked","reason":"Bank 3 is zero-filled in source, but trial NCLR has not been installed and icon/color routing is absent; party and PC palette slot usage needs runtime collision proof","gate":"shared icon-bank allocation and multiple UI VRAM loading tests"},
 {"id":"EVO-05","severity":"blocked","reason":"Normal evolution levels 35/45 do not establish Delta methods/levels; Delta stage dual types are not finalized","gate":"user-approved Delta methods, first-two-stage types and collision-free directed graph"},
 {"id":"ART-06","severity":"blocked","reason":"Normal views, shiny choices and icon recolors are technically tested but unapproved; battle two-frame sources are static placeholders","gate":"user artwork approval, valid animation assets, rights provenance and ROM runtime checks"}
]
report=out/"delta_form_id_icon_palette_evolution_readonly_QA.json"
report.write_text(json.dumps(R,indent=2,ensure_ascii=False)+"\n")
assert len(R["blockers"])==6 and not R["noRomChanges"] is False
print("MERCURY_READONLY_DELTA_COLLISION_AUDIT",
      json.dumps({"canonical":1025,"dexRaw":R["dex"]["rawShardPokemonRows"],
       "dexFlygonMatches":R["dex"]["matchingCount"],
       "deltaMatches":R["dex"]["deltaNameMatchCount"],
       "bank3UsedInUpstreamMetadata":len(bank3metas),
       "paletteBankCounts":R["iconBank3"]["usedIconPaletteIndexCounts"],
       "blockers":len(R["blockers"]),"approved":False,"platinumTouched":False}))
