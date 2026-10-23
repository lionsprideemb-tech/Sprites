#!/usr/bin/env python3
"""Non-destructive 64x64/15-opaque-color DS technical sprite candidate batch.

NO ROM insertion. Native format/artist approval is a separate gate. Original
source PNG/WebP remains untouched; no enlargement, scaling, interpolation,
invented shiny files, generated species, or icon construction.
"""
from __future__ import annotations
from collections import Counter
from pathlib import Path
import argparse
import hashlib
import json
import sys
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT / "review/recovered-approved-legacy-pairs-2026-10-23.json"
EXCEPTION = ROOT / "review/verified-exception-source-pairs-2026-10-23.json"
FURRVA = ROOT / "DS_CUSTOM_LIBRARY/recovered/Pokengine_Mikitari_Furrva_Source/source_manifest.json"
VOTES = ROOT / "review/user-iphone-decisions-2026-10-23.json"
OUT = ROOT / "DS_CUSTOM_LIBRARY/converted/Verified_Source_DS64_Technical_2026_10_23"
SLOTS = ("front", "back", "shiny_front", "shiny_back")


def obj(path: Path) -> dict:
    return json.loads(path.read_text("utf-8"))


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def safe_asset(relative: str) -> Path:
    if not relative or not isinstance(relative, str) or "\\" in relative:
        raise ValueError("missing or invalid source path " + repr(relative))
    item = (ROOT / relative).resolve()
    if not item.is_relative_to(ROOT) or not item.is_file() or item.suffix.lower() != ".png":
        raise ValueError("missing, non-PNG or out-of-repository source: " + relative)
    return item


def source_rows() -> list[dict]:
    historical, extra, furrva, votes = map(obj, (LEGACY, EXCEPTION, FURRVA, VOTES))
    assert historical["count"] == len(historical["entries"]) == 74
    assert len(extra["matches"]) == 8
    assert votes["count"] == len(votes["entries"]) == 166
    assert votes["keepCount"] == 154 and votes["cutCount"] == 12
    rows = []
    for x in historical["entries"]:
        assert x["effectiveDecision"] == "keep" and x["artworkIntegrationAllowed"] is False
        files = {}
        for original, slot in (("front", "front"), ("back", "back"),
                               ("shinyFront", "shiny_front"), ("shinyBack", "shiny_back")):
            v = x.get(original)
            if v:
                files[slot] = {"path": v["path"], "expected_blob": v["gitBlobSha"]}
        rows.append({"key": x["identity"], "reviewId": x["reviewId"], "name": x["name"],
                     "family": x["family"], "source": x["source"], "tier": "historically_approved_source",
                     "creativeVote": "KEEP (original specific artwork only)", "files": files})
    for x in extra["matches"]:
        assert x["romIntegrated"] is False and x["artChanged"] is False
        files = {slot: {"path": x[slot]["path"], "expected_blob": x[slot]["blobSHA"]}
                 for slot in ("front", "back")}
        rows.append({"key": "source_pair_" + x["id"].replace(":", "_"), "reviewId": x["id"],
                     "name": x["originalName"], "family": None, "source": x["source"],
                     "tier": x["classification"], "creativeVote": "NO NEW VOTE",
                     "files": files})
    assert furrva["species"] == "Furrva" and not furrva["game_integration_allowed"]
    files = {slot: {"path": furrva["assets"][slot]["png_path"],
                    "expected_sha256": furrva["assets"][slot]["png_sha256"]}
             for slot in ("front", "back")}
    rows.append({"key": "pokengine_mikitari_furrva_original", "reviewId": None,
                 "name": "Furrva", "family": "Furrva → Kocomb → Granebee / Beelitant",
                 "source": furrva["source"] + " (credit " + furrva["source_artist"] + ")",
                 "tier": "unapproved_external_original_source", "creativeVote": "NONE",
                 "files": files})
    if len(rows) != 83 or len({r["key"] for r in rows}) != len(rows):
        raise ValueError("source inventory changed; reject ambiguous overlap")
    return rows


def transposed_palette(rgb: Image.Image, alpha: Image.Image) -> Image.Image:
    # Quantize the visible pixels only; transparent background colors are ignored.
    # This is a 4bpp technical preview, never an automatically approved art replacement.
    mask = alpha.point(lambda a: 255 if a > 0 else 0)
    black = Image.new("RGB", rgb.size, (0, 0, 0))
    black.paste(rgb, mask=mask)
    indexed = black.quantize(colors=15, method=Image.Quantize.MEDIANCUT,
                             dither=Image.Dither.NONE).convert("RGB")
    out = Image.new("RGBA", rgb.size, (0, 0, 0, 0))
    out.paste(indexed, (0, 0), mask)
    return out


def build_one(source: Path, expected: dict, output: Path) -> dict:
    raw = source.read_bytes()
    if expected.get("expected_blob") and git_blob_sha(raw) != expected["expected_blob"]:
        raise ValueError("Source SHA-1 blob changed: " + source.as_posix())
    if expected.get("expected_sha256") and sha256(raw) != expected["expected_sha256"]:
        raise ValueError("Source SHA-256 changed: " + source.as_posix())
    try:
        with Image.open(source) as image:
            image.load()
            if image.format != "PNG" or getattr(image, "n_frames", 1) != 1:
                raise ValueError("Not a standalone original PNG")
            original_canvas = list(image.size)
            rgba = image.convert("RGBA")
    except (OSError, ValueError) as err:
        # A PNG magic header is not proof the actual pixel stream can be decoded.
        # Keep the original source, explicitly quarantine instead of forging art.
        return {"original": str(source.relative_to(ROOT)), "sha256": sha256(raw),
                "original_canvas": None, "bounds": None, "original_opaque_colors": None,
                "original_alpha_values": None, "output": None, "output_sha256": None,
                "status": "BLOCKED_UNDECODABLE_OR_UNSUPPORTED_PNG",
                "failure_type": type(err).__name__,
                "palette_changed": False, "pixel_art_scaled": False,
                "gameIntegrationAllowed": False}
    alphas = set(rgba.getchannel("A").getdata())
    bounds = rgba.getchannel("A").getbbox()
    opaque = {p[:3] for p in rgba.getdata() if p[3] == 255}
    detail = {"original": str(source.relative_to(ROOT)), "sha256": sha256(raw),
              "original_canvas": original_canvas, "bounds": list(bounds) if bounds else None,
              "original_opaque_colors": len(opaque), "original_alpha_values": len(alphas),
              "output": None, "output_sha256": None, "status": None, "palette_changed": False,
              "pixel_art_scaled": False, "gameIntegrationAllowed": False}
    if not bounds:
        detail["status"] = "BLOCKED_EMPTY_SOURCE"
        return detail
    if not alphas.issubset({0, 255}):
        detail["status"] = "BLOCKED_PARTIAL_ALPHA"
        return detail
    w, h = bounds[2]-bounds[0], bounds[3]-bounds[1]
    detail["visible_content_dimensions"] = [w, h]
    if w > 64 or h > 64:
        detail["status"] = "BLOCKED_OVERSIZE_NO_SCALING"
        return detail
    cropped = rgba.crop(bounds)
    canvas = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    # Existing Mercury GBA→DS conversion convention: horizontally center
    # and ground on the bottom pixel row. Cropping only transparent margins.
    x, y = (64 - w)//2, 64 - h
    canvas.alpha_composite(cropped, (x, y))
    after_colors = len({p[:3] for p in canvas.getdata() if p[3] == 255})
    if after_colors > 15:
        canvas = transposed_palette(canvas.convert("RGB"), canvas.getchannel("A"))
        detail["palette_changed"] = True
    resulting = len({p[:3] for p in canvas.getdata() if p[3] == 255})
    if resulting > 15 or canvas.getbbox() is None or canvas.size != (64, 64):
        raise AssertionError("Invalid 64x64/15-color technical output")
    # Output as transparent RGBA preview, not raw DS engine binary/tile graphics.
    # Separate ROM encoder/integration gate must validate exact target format.
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, format="PNG", optimize=False)
    detail.update({"output": str(output.relative_to(ROOT)),
                   "output_sha256": sha256(output.read_bytes()),
                   "status": ("PALETTE_QUANTIZED_NEEDS_ART_REVIEW" if detail["palette_changed"]
                              else "PIXEL_PRESERVED_DS64_CANDIDATE"),
                   "output_opaque_colors": resulting, "output_canvas": [64, 64],
                   "placement_offset": [x, y], "origin": "alpha-cropped, bottom-centered"})
    return detail


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify existing output without writing files")
    args = parser.parse_args()
    out_manifest = OUT / "technical_quality_manifest.json"
    rows = source_rows()
    result = []
    for design in rows:
        detail = {k: v for k, v in design.items() if k != "files"}
        detail["slots"] = {}
        for slot in SLOTS:
            slot_source = design["files"].get(slot)
            if not slot_source:
                detail["slots"][slot] = {"status": "MISSING_SOURCE", "output": None}
                continue
            f = safe_asset(slot_source["path"])
            destination = OUT / design["key"] / (slot + ".png")
            if args.check:
                # Recompute deterministically into temporary path? Avoid altering any
                # files during checks; check existence and manifest hashes below.
                detail["slots"][slot] = {"source": slot_source["path"],
                                          "output": str(destination.relative_to(ROOT))}
            else:
                detail["slots"][slot] = build_one(f, slot_source, destination)
        result.append(detail)
    if args.check:
        saved = obj(out_manifest)
        assert len(saved["designs"]) == len(result) == 83
        expected = {(d["key"], slot): meta
                    for d in saved["designs"] for slot, meta in d["slots"].items()}
        for design in rows:
            for slot, source_meta in design["files"].items():
                meta = expected[(design["key"], slot)]
                src = safe_asset(source_meta["path"])
                raw = src.read_bytes()
                assert sha256(raw) == meta["sha256"], source_meta["path"]
                if meta["output"]:
                    o = ROOT / meta["output"]
                    assert o.is_file() and sha256(o.read_bytes()) == meta["output_sha256"], meta["output"]
                    with Image.open(o) as i:
                        i.load()
                        assert i.size == (64, 64)
                        pix = i.convert("RGBA")
                        assert set(pix.getchannel("A").getdata()).issubset({0, 255})
                        assert len({p[:3] for p in pix.getdata() if p[3]}) <= 15
        print("PASS verified", len(rows), "original identities, technical previews and source checksums")
        return
    counts = Counter(meta["status"] for d in result for meta in d["slots"].values())
    summary = {"schema": "mercury-verified-source-ds64-technical-v1", "target": "64x64 RGBA PNG preview / ≤15 opaque colors / no resampling",
               "policy": {"notDSROMReady": True, "notNativeGameTileFormat": True,
                          "sourceFilesNeverReplaced": True, "neverAutomaticallyApproved": True,
                          "noNewEvolutionLinks": True, "noFabricatedArt": True},
               "sources": {"historicallyApprovedFamilies": 74, "repairedSourceComparisons": 8,
                           "originalFurrvaSource": 1, "originalHistoricalVotes": 166},
               "counts": dict(sorted(counts.items())), "designs": result}
    OUT.mkdir(parents=True, exist_ok=True)
    out_manifest.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", "utf-8")
    print(json.dumps({"designs": len(result), "counts": summary["counts"],
                      "outputs": sum(x["output"] is not None for d in result for x in d["slots"].values())},
                     indent=2))


if __name__ == "__main__":
    main()
