#!/usr/bin/env python3
"""Source-faithful nearest-neighbor VISUAL TRIAGE, never game integration.

Creates a separately labeled comparison preview only for oversized and partial
alpha art; never overwrites creative-approved art or existing DS64 candidates.
Audits palette-quantized technical candidates by measuring changed pixels.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from collections import Counter
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
TECH=ROOT/"DS_CUSTOM_LIBRARY/converted/Verified_Source_DS64_Technical_2026_10_23/technical_quality_manifest.json"
DEST=ROOT/"DS_CUSTOM_LIBRARY/comparison/DS64_Visual_Triage_2026_10_23"
MANIFEST=DEST/"comparison_manifest.json"
TARGET={"BLOCKED_OVERSIZE_NO_SCALING","BLOCKED_PARTIAL_ALPHA"}
REQUIRED=Counter({"BLOCKED_OVERSIZE_NO_SCALING":179,"BLOCKED_PARTIAL_ALPHA":17,
                  "PALETTE_QUANTIZED_NEEDS_ART_REVIEW":39,
                  "BLOCKED_UNDECODABLE_OR_UNSUPPORTED_PNG":4,
                  "MISSING_SOURCE":28})


def read(path:Path):return json.loads(path.read_text("utf-8"))
def checksum(data:bytes):return hashlib.sha256(data).hexdigest()

def check_source(relative:str, sha:str)->Path:
    p=(ROOT/relative).resolve()
    if not p.is_relative_to(ROOT) or not p.is_file() or p.suffix.lower()!=".png":
        raise ValueError("Source path missing/outside repository: "+relative)
    if checksum(p.read_bytes()) != sha:
        raise ValueError("SOURCE CHANGED; refusing to make comparison: "+relative)
    return p

def stage_image(im:Image.Image, item:dict):
    rgba=im.convert("RGBA")
    bbox=rgba.getchannel("A").getbbox()
    if not bbox:raise ValueError("Non-empty original artwork required")
    cropped=rgba.crop(bbox)
    w,h=cropped.size
    # Only invert original pixel-exact global 2x duplication. Even alpha here is
    # compared bit-for-bit to avoid inferring whether antialiasing was intended.
    exact2x=False
    if w>64 or h>64:
        if cropped.width%2==0 and cropped.height%2==0:
            half=cropped.resize((w//2,h//2),Image.Resampling.NEAREST)
            if half.resize((w,h),Image.Resampling.NEAREST).tobytes()==cropped.tobytes():
                cropped=half;exact2x=True
    before=cropped.size
    if cropped.width>64 or cropped.height>64:
        cropped.thumbnail((64,64),Image.Resampling.NEAREST)
        operation="NEAREST_NEIGHBOR_DOWNSCALE_COMPARISON_ONLY"
    else:
        operation="CROP_AND_CENTER_COMPARISON_ONLY"
    canvas=Image.new("RGBA",(64,64),(0,0,0,0))
    offset=[(64-cropped.width)//2,64-cropped.height]
    canvas.alpha_composite(cropped,tuple(offset))
    item.update(original_canvas=list(rgba.size),visible_extent=[w,h],
                preview_ink_extent=list(cropped.size),lossless_exact_2x_pixel_dedup=exact2x,
                preview_operation=operation,preview_offset=offset,
                partial_alpha_present=not set(rgba.getchannel("A").getdata()).issubset({0,255}),
                palette_unchanged=True,alpha_preserved=True,no_interpolation=True,
                new_art_created=False,autoApproved=False,gameIntegrationAllowed=False)
    return canvas

def calculate_palette_delta(meta:dict):
    # Compare palette-limited technical preview to source geometry as it stood
    # immediately before palette quantization. Strictly visual, not permission.
    source=check_source(meta["original"],meta["sha256"])
    with Image.open(source) as image:
        image.load()
        rgba=image.convert("RGBA")
    if meta.get("lossless_2x_duplicate_collapse"):
        half=rgba.resize((rgba.width//2,rgba.height//2),Image.Resampling.NEAREST)
        assert half.resize(rgba.size,Image.Resampling.NEAREST).tobytes()==rgba.tobytes()
        rgba=half
    bbox=rgba.getchannel("A").getbbox()
    assert bbox
    cropped=rgba.crop(bbox)
    assert cropped.width<=64 and cropped.height<=64
    expected=Image.new("RGBA",(64,64),(0,0,0,0))
    expected.alpha_composite(cropped,tuple(meta["placement_offset"]))
    preview=ROOT/meta["output"]
    if not preview.is_file() or checksum(preview.read_bytes())!=meta["output_sha256"]:
        raise ValueError("Old technical palette candidate changed")
    with Image.open(preview) as im:
        im.load();actual=im.convert("RGBA")
    assert actual.size==expected.size
    before=list(expected.getdata());after=list(actual.getdata())
    visible=[(a,b) for a,b in zip(before,after) if a[3]>0]
    if not visible:raise ValueError("Empty color comparison")
    if any(a[3]!=b[3] for a,b in zip(before,after)):
        raise ValueError("Palette conversion changed transparency")
    changed=sum(a[:3]!=b[:3] for a,b in visible)
    channel_delta=sum(sum(abs(a[i]-b[i]) for i in range(3)) for a,b in visible)
    return {"originalSource":meta["original"],"sourceSHA256":meta["sha256"],
            "quantizedTechnicalCandidate":meta["output"],
            "candidateSHA256":meta["output_sha256"],"opaquePixels":len(visible),
            "changedOpaquePixels":changed,"changedPixelFraction":round(changed/len(visible),6),
            "averageAbsoluteRGBChannelDelta":round(channel_delta/(len(visible)*3),3),
            "originalOpaqueColors":meta["original_opaque_colors"],
            "technicalOpaqueColors":meta["output_opaque_colors"],
            "requiresExplicitVisualApproval":True,"notCreativeApproved":True,
            "gameIntegrationAllowed":False}

def run(check:bool):
    master=read(TECH)
    assert len(master["designs"])==83
    actual=Counter(s["status"] for d in master["designs"] for s in d["slots"].values())
    assert sum(actual.values())==332
    allowed=set(REQUIRED)|{"PIXEL_PRESERVED_DS64_CANDIDATE",
                           "PIXEL_PRESERVED_EXACT_2X_COLLAPSE_DS64_CANDIDATE"}
    assert set(actual)<=allowed,("Unrecognized source integrity state",actual)
    assert actual["BLOCKED_UNDECODABLE_OR_UNSUPPORTED_PNG"]<=4
    assert actual["MISSING_SOURCE"]==28
    expected_preview_count=sum(actual[k] for k in TARGET)
    expected_palette_count=actual["PALETTE_QUANTIZED_NEEDS_ART_REVIEW"]
    if check:
        result=read(MANIFEST)
        assert result["schema"]=="mercury-original-visual-rescue-comparisons-v1"
        assert len(result["comparisons"])==expected_preview_count
        assert len(result["paletteAudits"])==expected_palette_count
        assert result["sourceSHA256"]==checksum(TECH.read_bytes()),"Visual comparison manifest is stale"
        for item in result["comparisons"]:
            src=check_source(item["original"],item["originalSHA256"])
            out=(ROOT/item["comparisonPath"]).resolve()
            assert out.is_relative_to(ROOT) and out.is_file()
            assert checksum(out.read_bytes())==item["comparisonSHA256"]
            with Image.open(out) as i:
                i.load();assert i.size==(64,64)
                assert i.format=="PNG"
            assert item["gameIntegrationAllowed"] is False
            assert item["autoApproved"] is False
        for p in result["paletteAudits"]:
            assert p["requiresExplicitVisualApproval"]
            assert checksum((ROOT/p["quantizedTechnicalCandidate"]).read_bytes())==p["candidateSHA256"]
        print("PASS:",len(result["comparisons"]),"visual-only previews, 39 palette audits; source and output hashes match")
        return
    DEST.mkdir(parents=True,exist_ok=True)
    result={"schema":"mercury-original-visual-rescue-comparisons-v1",
            "source":str(TECH.relative_to(ROOT)),"sourceSHA256":checksum(TECH.read_bytes()),
            "policy":{"sourceAlwaysPreserved":True,"nearestNeighborComparisonNotDSReady":True,
                      "noFabricatedArt":True,"noNewPokemonSpecies":True,
                      "noOldVotesModified":True,"paletteApprovalNotInferred":True,
                      "neverROMIntegrate":True},
            "comparisons":[],"paletteAudits":[],"missingSource":[],"unrecoverablePNG":[]}
    for design in master["designs"]:
        for slot in ("front","back","shiny_front","shiny_back"):
            meta=design["slots"][slot]
            status=meta["status"]
            if status in TARGET:
                source=check_source(meta["original"],meta["sha256"])
                relative=(DEST/design["key"]/(slot+"_NN_COMPARISON_ONLY.png")).relative_to(ROOT)
                output=ROOT/relative
                entry={"name":design["name"],"family":design["family"],
                       "reviewId":design["reviewId"],"sourceType1":design.get("type1",""),
                       "sourceType2":design.get("type2",""),"key":design["key"],
                       "slot":slot,"originalStatus":status,"original":meta["original"],
                       "originalSHA256":meta["sha256"],"comparisonPath":str(relative),
                       "source":design["source"],"tier":design["tier"]}
                with Image.open(source) as image:
                    image.load()
                    canvas=stage_image(image,entry)
                output.parent.mkdir(parents=True,exist_ok=True)
                canvas.save(output,format="PNG",optimize=False)
                entry["comparisonSHA256"]=checksum(output.read_bytes())
                result["comparisons"].append(entry)
            elif status=="PALETTE_QUANTIZED_NEEDS_ART_REVIEW":
                audit=calculate_palette_delta(meta)
                audit.update({"name":design["name"],"family":design["family"],
                              "reviewId":design["reviewId"],"key":design["key"],
                              "slot":slot,"source":design["source"]})
                result["paletteAudits"].append(audit)
            elif status=="MISSING_SOURCE":
                result["missingSource"].append({"name":design["name"],"key":design["key"],
                   "family":design["family"],"slot":slot,"reviewId":design["reviewId"],
                   "action":"Find matching original creator sprite; do not substitute art"})
            elif status=="BLOCKED_UNDECODABLE_OR_UNSUPPORTED_PNG":
                result["unrecoverablePNG"].append({"name":design["name"],"key":design["key"],
                   "family":design["family"],"slot":slot,"reviewId":design["reviewId"],
                   "original":meta["original"],"sourceSHA256":meta["sha256"],
                   "action":"Recover genuine original pixel stream; no forged replacement"})
    result["counts"]={
        "visualOnlyNearestOrCropComparisons":len(result["comparisons"]),
        "alphaConcernComparisons":sum(x["originalStatus"]=="BLOCKED_PARTIAL_ALPHA" for x in result["comparisons"]),
        "oversizeComparisons":sum(x["originalStatus"]=="BLOCKED_OVERSIZE_NO_SCALING" for x in result["comparisons"]),
        "paletteQuantizedNeedsApproval":len(result["paletteAudits"]),
        "missingOriginals":len(result["missingSource"]),"undecodableOriginals":len(result["unrecoverablePNG"]),
        "noNewGameReadySprites":True}
    assert result["counts"]["visualOnlyNearestOrCropComparisons"]==expected_preview_count
    assert result["counts"]["paletteQuantizedNeedsApproval"]==expected_palette_count
    assert len(result["missingSource"])==28
    assert len(result["unrecoverablePNG"])==actual["BLOCKED_UNDECODABLE_OR_UNSUPPORTED_PNG"]
    MANIFEST.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(result["counts"]))
if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--check",action="store_true")
    run(ap.parse_args().check)
