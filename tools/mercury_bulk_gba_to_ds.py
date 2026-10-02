#!/usr/bin/env python3
"""
Mercury Redux bulk GBA-source -> DS-technical sprite staging pipeline.

Important: this is a *technical* converter, not an artistic redraw engine.
It preserves source artwork wherever possible and never overwrites source files.

Pipeline:
- ingest ForwardFeed/ER-nextdex-style flat PNGs
- group front/back/shiny-front/shiny-back by design key
- trim transparent margins
- center artwork on 64x64 DS battle canvases when it fits
- reduce opaque palette to <=15 colors (+ transparency) only when needed
- generate 32x64 two-frame placeholder icons from the staged front sprite
- classify every design:
  * DS_TECH_READY_SOURCE
  * MECHANICAL_CONVERSION
  * NEEDS_ART_REDRAW
  * INCOMPLETE_SOURCE_SET
- emit CSV/JSON reports
"""

from __future__ import annotations

from pathlib import Path
from collections import defaultdict
import argparse
import csv
import hashlib
import json
import shutil

from PIL import Image

SLOTS = {
    "front": "",
    "back": "_BACK",
    "front_shiny": "_SHINY",
    "back_shiny": "_BACK_SHINY",
}

def split_slot(stem: str):
    for slot, suffix in [
        ("back_shiny", "_BACK_SHINY"),
        ("front_shiny", "_SHINY"),
        ("back", "_BACK"),
    ]:
        if stem.endswith(suffix):
            return stem[:-len(suffix)], slot
    return stem, "front"

def transparent_bbox(im: Image.Image):
    rgba = im.convert("RGBA")
    alpha = rgba.getchannel("A")
    return alpha.getbbox()

def opaque_color_count(im: Image.Image) -> int:
    rgba = im.convert("RGBA")
    return len({p[:3] for p in rgba.getdata() if p[3]})

def is_binary_alpha(im: Image.Image) -> bool:
    vals = set(im.convert("RGBA").getchannel("A").getdata())
    return vals.issubset({0, 255})

def center_on_64(im: Image.Image) -> tuple[Image.Image | None, dict]:
    rgba = im.convert("RGBA")
    bbox = transparent_bbox(rgba)
    if not bbox:
        return Image.new("RGBA", (64, 64), (0,0,0,0)), {
            "bbox_w": 0, "bbox_h": 0, "fits_64": True
        }
    cropped = rgba.crop(bbox)
    w, h = cropped.size
    if w > 64 or h > 64:
        return None, {"bbox_w": w, "bbox_h": h, "fits_64": False}
    canvas = Image.new("RGBA", (64, 64), (0,0,0,0))
    x = (64 - w) // 2
    y = 64 - h
    if y < 0:
        y = (64 - h) // 2
    canvas.alpha_composite(cropped, (x, y))
    return canvas, {"bbox_w": w, "bbox_h": h, "fits_64": True}

def quantize_ds_palette(im: Image.Image, max_opaque_colors: int = 15) -> Image.Image:
    """
    Preserve transparent pixels and quantize opaque RGB to <= max_opaque_colors.
    Output remains RGBA for repo review; game-format encoding is a later step.
    """
    rgba = im.convert("RGBA")
    alpha = rgba.getchannel("A")
    opaque_mask = alpha.point(lambda a: 255 if a else 0)

    rgb = Image.new("RGB", rgba.size, (0,0,0))
    rgb.paste(rgba.convert("RGB"), mask=opaque_mask)

    # Quantize only the RGB image. Pixels behind transparency do not matter.
    q = rgb.quantize(colors=max_opaque_colors, method=Image.Quantize.MEDIANCUT).convert("RGB")
    out = Image.new("RGBA", rgba.size, (0,0,0,0))
    out.paste(q, mask=opaque_mask)
    return out

def make_icon(front64: Image.Image) -> Image.Image:
    rgba = front64.convert("RGBA")
    bbox = transparent_bbox(rgba)
    if bbox:
        mon = rgba.crop(bbox)
    else:
        mon = rgba
    mon.thumbnail((30, 30), resample=Image.Resampling.NEAREST)
    frame = Image.new("RGBA", (32, 32), (0,0,0,0))
    x=(32-mon.width)//2
    y=max(0, 30-mon.height)
    frame.alpha_composite(mon, (x,y))
    sheet = Image.new("RGBA", (32,64), (0,0,0,0))
    sheet.alpha_composite(frame, (0,0))
    sheet.alpha_composite(frame, (0,32))
    return sheet

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20), b""):
            h.update(chunk)
    return h.hexdigest()

def process_slot(src: Path, dst: Path):
    try:
        im=Image.open(src)
        im.load()
    except Exception as exc:
        return None, {
            "source_width":0,
            "source_height":0,
            "source_colors":0,
            "binary_alpha":False,
            "bbox_w":0,
            "bbox_h":0,
            "fits_64":False,
            "palette_reduced":False,
            "source_error":f"{type(exc).__name__}: {exc}",
        }
    src_colors=opaque_color_count(im)
    src_size=im.size
    alpha_binary=is_binary_alpha(im)

    staged, meta=center_on_64(im)
    if staged is None:
        return None, {
            "source_width":src_size[0],
            "source_height":src_size[1],
            "source_colors":src_colors,
            "binary_alpha":alpha_binary,
            **meta,
            "palette_reduced":False,
            "source_error":"",
        }

    before=opaque_color_count(staged)
    reduced=False
    if before > 15:
        staged=quantize_ds_palette(staged, 15)
        reduced=True
    after=opaque_color_count(staged)
    dst.parent.mkdir(parents=True, exist_ok=True)
    staged.save(dst)

    return staged, {
        "source_width":src_size[0],
        "source_height":src_size[1],
        "source_colors":src_colors,
        "binary_alpha":alpha_binary,
        **meta,
        "palette_reduced":reduced,
        "staged_colors":after,
        "source_error":"",
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--report-dir", required=True)
    args=ap.parse_args()

    source=Path(args.source)
    output=Path(args.output)
    report_dir=Path(args.report_dir)
    output.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    grouped=defaultdict(dict)
    for p in sorted(source.glob("*.png")):
        key,slot=split_slot(p.stem)
        grouped[key][slot]=p

    design_rows=[]
    slot_rows=[]

    for key, slots in sorted(grouped.items()):
        complete=all(s in slots for s in SLOTS)
        staged={}
        any_conversion=False
        any_redraw=False

        design_dir=output/key.lower()
        if design_dir.exists():
            shutil.rmtree(design_dir)
        design_dir.mkdir(parents=True, exist_ok=True)

        for slot in SLOTS:
            if slot not in slots:
                continue
            dst=design_dir/f"{slot.replace('_','-')}.png"
            staged_im,meta=process_slot(slots[slot],dst)
            if staged_im is None:
                any_redraw=True
            else:
                staged[slot]=staged_im
                if (
                    meta["source_width"] != 64
                    or meta["source_height"] != 64
                    or meta["source_colors"] > 15
                    or not meta["binary_alpha"]
                    or meta["palette_reduced"]
                ):
                    any_conversion=True

            slot_rows.append({
                "key":key,
                "slot":slot,
                "source_path":str(slots[slot]),
                "source_sha256":sha256(slots[slot]),
                **meta,
                "output_path":str(dst) if staged_im is not None else "",
            })

        if "front" in staged:
            icon=make_icon(staged["front"])
            icon.save(design_dir/"icon-generated.png")

        if not complete:
            category="INCOMPLETE_SOURCE_SET"
        elif any_redraw:
            category="NEEDS_ART_REDRAW"
        elif any_conversion:
            category="MECHANICAL_CONVERSION"
        else:
            category="DS_TECH_READY_SOURCE"

        design_rows.append({
            "key":key,
            "category":category,
            "complete_4way":complete,
            "redux_named":"REDUX" in key,
            "mega_named":"MEGA" in key,
            "has_front":"front" in slots,
            "has_back":"back" in slots,
            "has_front_shiny":"front_shiny" in slots,
            "has_back_shiny":"back_shiny" in slots,
            "staged_dir":str(design_dir),
        })

    with (report_dir/"elite_redux_gba_to_ds_design_classification.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=design_rows[0].keys())
        w.writeheader(); w.writerows(design_rows)

    with (report_dir/"elite_redux_gba_to_ds_slot_audit.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=slot_rows[0].keys())
        w.writeheader(); w.writerows(slot_rows)

    counts=defaultdict(int)
    redux_counts=defaultdict(int)
    for r in design_rows:
        counts[r["category"]]+=1
        if r["redux_named"]:
            redux_counts[r["category"]]+=1

    summary={
        "source":str(source),
        "design_keys":len(design_rows),
        "slot_files":len(slot_rows),
        "categories":dict(sorted(counts.items())),
        "redux_named_designs":sum(r["redux_named"] for r in design_rows),
        "redux_named_categories":dict(sorted(redux_counts.items())),
        "policy":{
            "artistic_redraw":"NOT AUTOMATED",
            "source_overwrite":False,
            "battle_canvas":"64x64",
            "opaque_palette_limit":15,
            "icon_output":"32x64 generated two-frame review placeholder",
            "oversize_policy":"do not resize; classify NEEDS_ART_REDRAW",
        }
    }
    (report_dir/"elite_redux_gba_to_ds_summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":
    main()
