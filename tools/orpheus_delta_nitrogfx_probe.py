#!/usr/bin/env python3
"""Run upstream pret/pokeplatinum NitroGFX on unapproved Desert Scarab source assets.

This is actual native NCGR/NCLR construction and pixel-index readback, but *not*
a validated Platinum Pokemon NARC member order, animation, shiny/icon package,
species binding or ROM insertion.
"""
from pathlib import Path
from PIL import Image
import hashlib, json, os, re, shutil, subprocess, tempfile

ROOT=Path("report/orpheus_delta_native80_preflight")
DATA=ROOT/"family"
QAPATH=ROOT/"preflight_qa.json"
qa=json.loads(QAPATH.read_text())
assert qa["schema"]=="mercury-orpheus-sixview-pt-battle-source-preflight-v1"
assert qa["nativeBattleFrame"]==[80,80] and qa["expectedTwoFrames"]==[160,80]
assert len(qa["views"])==6 and qa["normalViewCount"]==6
assert qa["allApproved"] is False and qa["notROMIntegrated"] is True
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def run(args,cwd=None,timeout=150):
    p=subprocess.run([str(x) for x in args],cwd=str(cwd) if cwd else None,
                     text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                     timeout=timeout)
    if p.returncode:raise RuntimeError(
       f"Command failed ({p.returncode}): {args}\nstdout:\n{p.stdout[-3500:]}\nstderr:\n{p.stderr[-3500:]}")
    return p
with tempfile.TemporaryDirectory(prefix="mercury-upstream-nitrogfx-") as work:
    refroot=Path(work)/"pokeplatinum"
    # Shallow filtered sparse checkout avoids any copyrighted ROM extraction.
    run(["git","clone","-q","--depth","1","--filter=blob:none","--sparse",
         "https://github.com/pret/pokeplatinum.git",refroot],timeout=240)
    run(["git","sparse-checkout","set","tools/nitrogfx","include/constants",
         "tools/scripts"],cwd=refroot,timeout=180)
    revision=run(["git","rev-parse","HEAD"],cwd=refroot).stdout.strip()
    const=(refroot/"include/constants/graphics.h").read_text()
    script=(refroot/"tools/scripts/make_pl_pokegra.py").read_text()
    assert re.search(r"#define MON_SPRITE_FRAME_WIDTH_TILES\s+10\b",const)
    assert re.search(r"#define MON_SPRITE_FRAME_HEIGHT_TILES\s+10\b",const)
    assert "'-encodefronttoback'" in script and "'-scan'" in script
    assert "pl_pokegra.narc" in script
    # GitHub runner images vary: fail specifically if package install step was skipped.
    run(["pkg-config","--exists","libpng","zlib"],timeout=25)
    run(["make","-j2"],cwd=refroot/"tools/nitrogfx",timeout=150)
    nitro=refroot/"tools/nitrogfx/nitrogfx"
    assert nitro.is_file()
    output=[]
    for rec in qa["views"]:
        key=rec["view"]
        stage,face=key.split("_")
        native=ROOT/rec["nativeImage"]
        strip=ROOT/rec["ntr160Source"]
        pal=ROOT/rec["ntrJASCpalette"]
        assert sha(native)==rec["imageSHA256"]
        assert sha(strip)==rec["stripSHA256"]
        assert strip.with_suffix(strip.suffix+".key").exists()
        outdir=ROOT/"ntr-encoded"/stage
        outdir.mkdir(parents=True,exist_ok=True)
        ncgr=outdir/f"{face}_static_twoframe.NCGR"
        nclr=outdir/f"{face}_normal.NCLR"
        roundtrip=outdir/f"{face}_decoded_160x80.png"
        # Exact same CLI flags as original Platinum build for battle graphics.
        run([nitro,strip,ncgr,"-encodefronttoback","-scan"],timeout=80)
        run([nitro,pal,nclr,"-bitdepth","8","-nopad","-comp","10"],timeout=80)
        assert ncgr.read_bytes().startswith(b"RGCN"),(key,"NCGR signature")
        assert nclr.read_bytes().startswith(b"RLCN"),(key,"NCLR signature")
        assert len(ncgr.read_bytes()) > 6400
        # Decode with upstream NitroGFX; output palette index identity is
        # authoritative even where 8-bit display values are rounded.
        run([nitro,ncgr,roundtrip,"-palette",nclr,
             "-encodefronttoback","-object"],timeout=80)
        original=Image.open(strip)
        decoded=Image.open(roundtrip)
        assert original.size==decoded.size==(160,80),(key,original.size,decoded.size)
        assert original.mode=="P" and decoded.mode=="P",(key,original.mode,decoded.mode)
        orig_idx=list(original.getdata());got_idx=list(decoded.getdata())
        assert orig_idx==got_idx,(key,"NTR source index mismatch",
                                    sum(a!=b for a,b in zip(orig_idx,got_idx)))
        assert orig_idx[:80]==orig_idx[80:160],(key,"static 2frame mismatch")
        assert all(orig_idx[y*160:y*160+80]==orig_idx[y*160+80:y*160+160]
                   for y in range(80))
        assert len(ncgr.read_bytes())>2*3200 and len(nclr.read_bytes())>32
        output.append({
          "view":key,"nitroGfxProducer":"pret/pokeplatinum/tools/nitrogfx",
          "upstreamCommitSHA":revision,
          "commandNCGR":"nitrogfx INPUT.png OUTPUT.NCGR -encodefronttoback -scan",
          "commandNCLR":"nitrogfx INPUT.pal OUTPUT.NCLR -bitdepth 8 -nopad -comp 10",
          "NCGR":str(ncgr.relative_to(ROOT)),"NCLR":str(nclr.relative_to(ROOT)),
          "decoded160":str(roundtrip.relative_to(ROOT)),
          "ncgrBytes":ncgr.stat().st_size,"nclrBytes":nclr.stat().st_size,
          "ncgrSHA256":sha(ncgr),"nclrSHA256":sha(nclr),
          "roundTripIndexPixelMismatch":0,"decoded160IndexExact":True,
          "twoFramesAreIdenticalStaticPlaceholders":True,
          "approved":False,"romIntegrated":False})
        print("NTR_SOURCE_ROUNDTRIP_PASS",key,ncgr.stat().st_size,nclr.stat().st_size)
    report={
      "schema":"mercury-orpheus-pret-platinum-nitrogfx-technical-probe-v1",
      "sourceQAsha256":sha(QAPATH),
      "upstreamRepository":"https://github.com/pret/pokeplatinum",
      "upstreamCommitSHA":revision,
      "platinumSourceFrame":[80,80],"twoFrameSource":[160,80],
      "actualNitroGfxEncoderUsed":True,"ncgrNclrGenerated":True,
      "decodedPixelsExact":True,
      "noSourceArtworkChanges":True,"noUserVotesChanged":True,
      "allUnapproved":True,"platinumUntouched":True,
      "notAProductionNARC":True,"noEngineRuntimeTest":True,
      "noSpeciesFormIDsOrAnimationMetadata":True,
      "missingShinies":6,"gameIconsNotCertified":3,
      "notes":[
        "NCGR/NCLR are encoded actual Nitro SDK-format *standalone members* with upstream tooling.",
        "Palette indices successfully roundtrip through the upstream source encoder and decoder.",
        "160x80 strip duplicates each static 80x80 frame; real battle animation is not authored.",
        "Packaging/insertion requires approval, correct species/form member mapping, shinies/icons, runtime testing."],
      "files":output
    }
    reportpath=ROOT/"nitrogfx_qa.json"
    reportpath.write_text(json.dumps(report,indent=2)+"\n")
    readme=ROOT/"README.md"
    readme.write_text(readme.read_text()+"\n## Real Platinum NitroGFX encoding probe\n\n"
      "Generated six NCGR and six NCLR **standalone files** using the upstream "
      "pret/pokeplatinum NitroGFX encoder with the exact native build flags. "
      "Each was decoded back to its full 160x80 indexed pixel source with **0 index differences**. "
      "This verifies the file-encoding stage only: no approved art, shiny views, "
      "converted icon archive, correct form/species NARC index integration or game runtime proof. "
      "See [nitrogfx QA](nitrogfx_qa.json).\n")
    print("MERCURY_NITROGFX_SIXVIEW_PASS",json.dumps({
      "views":len(output),"upstreamSHA":revision,"ncgrNclr":12,"roundtripMismatches":0,
      "allUnapproved":True,"romIntegrated":False}))
