#!/usr/bin/env python3
"""Run upstream pret/pokeplatinum NitroGFX on unapproved Desert Scarab source assets.

This is actual native NCGR/NCLR construction and pixel-index readback, but *not*
a validated Platinum Pokemon NARC member order, animation, shiny/icon package,
species binding or ROM insertion.
"""
from pathlib import Path
from PIL import Image
import hashlib, json, os, re, shutil, subprocess, tempfile, struct

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
         "tools/scripts","res/pokemon/.shared"],cwd=refroot,timeout=180)
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
    # Six source-locked optional shiny palettes: technical certification only.
    shinyRoot=Path("review/candidates/orpheus-2026-11-09-UNAPPROVED/delta-shiny-icon-research")
    shinyManifest=json.loads((shinyRoot/"shiny_icon_research_qa.json").read_text())
    assert shinyManifest["allUnapproved"] and shinyManifest["noPlatinumIntegration"]
    assert len(shinyManifest["shinyColorProposals"])==6
    proposals=[]
    def indexed80_from_tiled(data):
        assert len(data)==3200
        idx=[0]*6400;k=0
        for by in range(0,80,8):
            for bx in range(0,80,8):
                for y in range(8):
                    for x in range(0,8,2):
                        value=data[k];k+=1
                        idx[(by+y)*80+bx+x]=value&15
                        idx[(by+y)*80+bx+x+1]=value>>4
        return idx
    for row in shinyManifest["shinyColorProposals"]:
        key=row["view"]
        stage,face=key.split("_")
        pngSource=shinyRoot/row["shiny"]
        tileSource=shinyRoot/row["tile"]
        palSource=shinyRoot/row["palette"]
        for src,expected in ((pngSource,row["shinySHA256"]),
                             (tileSource,row["tileSHA256"]),
                             (palSource,row["paletteSHA256"])):
            assert sha(src)==expected,(key,src)
        tiledIndex=indexed80_from_tiled(tileSource.read_bytes())
        colorWords=struct.unpack("<16H",palSource.read_bytes())
        assert len(colorWords)==16
        # Make exact 4-bit indexed 160x80 horizontally repeated still frames.
        stripIndex=[v for y in range(80) for v in (
                    tiledIndex[y*80:(y+1)*80]*2)]
        assert len(stripIndex)==12800
        outdir=ROOT/"ntr-encoded"/"shiny-proposal"/stage
        outdir.mkdir(parents=True,exist_ok=True)
        pngStrip=outdir/f"{face}_STATIC_shiny_PROPOSAL_160x80.png"
        palStrip=outdir/f"{face}_shiny_PROPOSAL.pal"
        spr=Image.new("P",(160,80))
        spr.putdata(stripIndex)
        def rgb(word):
            return tuple(round(((word>>(5*i))&31)*255/31) for i in range(3))
        spr.putpalette([v for word in colorWords for v in rgb(word)]+[0]*720)
        spr.info["transparency"]=0
        spr.save(pngStrip,optimize=True,bits=4)
        (outdir/f"{face}_STATIC_shiny_PROPOSAL_160x80.png.key").write_bytes(
            struct.pack("<I",0x52A04286))
        palStrip.write_bytes(("JASC-PAL\r\n0100\r\n16\r\n"+
            "\r\n".join(" ".join(str(c) for c in rgb(word)) for word in colorWords)
            +"\r\n").encode("ascii"))
        ncgr=outdir/f"{face}_shiny_PROPOSAL.NCGR"
        nclr=outdir/f"{face}_shiny_PROPOSAL.NCLR"
        decoded=outdir/f"{face}_shiny_decoded.png"
        run([nitro,pngStrip,ncgr,"-encodefronttoback","-scan"],timeout=80)
        run([nitro,palStrip,nclr,"-bitdepth","8","-nopad","-comp","10"],timeout=80)
        run([nitro,ncgr,decoded,"-palette",nclr,"-encodefronttoback","-object"],timeout=80)
        resultIm=Image.open(decoded)
        assert resultIm.size==(160,80) and resultIm.mode=="P"
        diff=sum(a!=b for a,b in zip(resultIm.getdata(),stripIndex))
        assert diff==0,(key,diff)
        proposals.append({"view":key,"fromUnapprovedColorProposal":True,
            "sourceShinySHA256":sha(pngSource),
            "NCGR":str(ncgr.relative_to(ROOT)),"NCLR":str(nclr.relative_to(ROOT)),
            "encodedNCGRSHA256":sha(ncgr),"encodedNCLRSHA256":sha(nclr),
            "ncgrBytes":ncgr.stat().st_size,"nclrBytes":nclr.stat().st_size,
            "zeroPixelIndexDifferences":True,
            "approved":False,"gameIntegrated":False})
        print("NITROGFX_SHINY_PROPOSAL_EXACT",key,sha(ncgr)[:12])
    # Icon study: map real three-stage 32px art to EXISTING global 256-color
    # palette banks and test using actual make_pl_poke_icon.py flags.
    run(["python3","tools/orpheus_delta_shared_palette_icon_qa.py",
         "--upstream",refroot,"--nitrogfx",nitro],timeout=150)
    iconReport=json.loads((ROOT/"shared_icon_palette_qa.json").read_text())
    assert len(iconReport["stageResults"])==3
    assert iconReport["nativeDecoderPixelDifferencesAll"]==0
    assert iconReport["allReservedBanksUntouched"] and iconReport["unapproved"]
    # Source-faithful alternative: use only *currently zero* palette bank 3
    # in a separate trial file, without modifying or registering that bank.
    run(["python3","tools/orpheus_delta_reserved_palette_study.py",
         "--upstream",refroot,"--nitrogfx",nitro],timeout=150)
    bank3Report=json.loads((ROOT/"reserved_icon_bank3_qa.json").read_text())
    assert bank3Report["allDecodeIndexDifferences"]==0
    assert bank3Report["originalSourcePaletteNeverModified"]
    assert bank3Report["existingPaletteBank0to2ByteIdentical"]
    assert bank3Report["reservedBanks4to15ByteIdentical"]
    assert bank3Report["paletteSlot3MustBeVerifiedUnusedBeforeAnyActualAllocation"] is True
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
      "files":output,
      "sixTechnicallyEncodedButUnapprovedShinyColorProposals":proposals,
      "shinyProposalRoundTripsPixelExact":True,
      "shinyProposalNoUserApproval":True,
      "sharedIconPaletteReport":"shared_icon_palette_qa.json",
      "sharedIconNCGRCount":len(iconReport["stageResults"]),
      "sharedIconNitroGfxIndexPixelDifferences":iconReport["nativeDecoderPixelDifferencesAll"],
      "sharedIconArtworkUnapproved":True,
      "reservedBank3AlternativeReport":"reserved_icon_bank3_qa.json",
      "reservedBank3IsNotAllocatedInGame":True,
      "reservedBank3RealIconNCGRCount":len(bank3Report["stageResults"]),
      "allHistoricalPalettesUnchanged":True
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
      "Six separate UNAPPROVED shiny color proposals are also encoded and roundtrip-verified; "
      "they are not final game-ready shinies. See [nitrogfx QA](nitrogfx_qa.json).\n")
    print("MERCURY_NITROGFX_SIXVIEW_PASS",json.dumps({
      "views":len(output),"shinyProposals":len(proposals),"upstreamSHA":revision,"ncgrNclr":24,"roundtripMismatches":0,
      "allUnapproved":True,"romIntegrated":False}))
