#!/usr/bin/env python3
"""Find *exactly reversible* larger integer-pixel duplication in oversized source PNGs.

Never interpolate, trim colored pixels, quantize a palette, alter originals,
infer approvals, or integrate sprites. Candidate PNGs are visual QA only.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
TECH = ROOT / "DS_CUSTOM_LIBRARY/converted/Verified_Source_DS64_Technical_2026_10_23/technical_quality_manifest.json"
FACTORS = (2, 3, 4, 5, 6, 8)


def safe_read(path: str) -> bytes:
    if not path or "\\" in path:
        raise ValueError("Invalid source path")
    source = (ROOT / path).resolve()
    if not source.is_relative_to(ROOT) or not source.is_file():
        raise ValueError("Missing or escaped original source: " + path)
    return source.read_bytes()


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def report(out: Path, verify: bool) -> dict:
    master = json.loads(TECH.read_text("utf-8"))
    assert master["schema"] == "mercury-verified-source-ds64-technical-v1"
    assert master["counts"]["BLOCKED_OVERSIZE_NO_SCALING"] == 179
    rows = []
    factors = Counter()
    palette_ready = 0
    checked = 0
    for design in master["designs"]:
        for slot, original in design["slots"].items():
            if original.get("status") != "BLOCKED_OVERSIZE_NO_SCALING":
                continue
            checked += 1
            raw = safe_read(original["original"])
            if digest(raw) != original["sha256"]:
                raise ValueError("Source PNG has changed: " + original["original"])
            with Image.open(io.BytesIO(raw)) as image:
                image.load()
                if image.format != "PNG" or getattr(image, "n_frames", 1) != 1:
                    raise ValueError("Source is not original standalone PNG")
                rgba = image.convert("RGBA")
            if not set(rgba.getchannel("A").getdata()).issubset({0, 255}):
                raise ValueError("Partial alpha silently entered oversized group")
            source_bytes = rgba.tobytes()
            selected = None
            for n in FACTORS:
                if rgba.width % n or rgba.height % n:
                    continue
                shrink = rgba.resize((rgba.width // n, rgba.height // n), Image.Resampling.NEAREST)
                if shrink.resize(rgba.size, Image.Resampling.NEAREST).tobytes() != source_bytes:
                    continue
                bbox = shrink.getchannel("A").getbbox()
                if not bbox:
                    continue
                width, height = bbox[2] - bbox[0], bbox[3] - bbox[1]
                if width > 64 or height > 64:
                    continue
                selected = (n, shrink, bbox, width, height)
                break
            if selected is None:
                continue
            n, shrink, bbox, width, height = selected
            canvas = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
            crop = shrink.crop(bbox)
            canvas.alpha_composite(crop, ((64 - width)//2, 64 - height))
            opaque_colors = len({rgba[:3] for rgba in canvas.getdata() if rgba[3] == 255})
            palette_safe = opaque_colors <= 15
            png_buffer = io.BytesIO()
            canvas.save(png_buffer, format="PNG")
            png = png_buffer.getvalue()
            rel = "candidate_previews/" + design["key"] + "/" + slot + ".png"
            dest = out / rel
            if verify:
                if not dest.is_file() or dest.read_bytes() != png:
                    raise ValueError("Lossless duplicate-pixel candidate changed: " + rel)
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(png)
            factors[n] += 1
            palette_ready += int(palette_safe)
            rows.append({
                "identity": design["key"], "name": design["name"], "reviewId": design["reviewId"],
                "tier": design["tier"], "family": design.get("family"), "slot": slot,
                "originalPath": original["original"], "originalSha256": original["sha256"],
                "sourceDimensions": list(rgba.size), "exactDuplicateFactor": n,
                "visibleContentDimensions": [width, height], "opaqueColors": opaque_colors,
                "palettePreservedMax15": palette_safe,
                "qaPng": rel, "qaPngSha256": digest(png),
                "sourcePixelsExactlyReconstructible": True,
                "creativeApprovalNotInferred": True, "romIntegrationAllowed": False
            })
    assert checked == 179
    summary = {
        "schema": "mercury-oversized-exact-integer-duplication-probe-v1",
        "target": "original 179 oversize blocked images only",
        "checked": checked, "losslessGeometryRecovered": len(rows),
        "withoutNewPaletteQuantization": palette_ready,
        "stillOversizedOrNonDuplicated": checked - len(rows),
        "factorCounts": dict(sorted(factors.items())),
        "policy": {"sourceFilesUnchanged": True, "noInterpolation": True,
                   "noPaletteChanges": True, "creativeVoteUnchanged": True,
                   "QAOnlyNotDSCertified": True, "noROMIntegration": True},
        "candidates": rows
    }
    payload = (json.dumps(summary, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    manifest_file = out / "lossless-probe-manifest.json"
    if verify:
        if not manifest_file.is_file() or manifest_file.read_bytes() != payload:
            raise ValueError("Lossless probe report mismatch")
    else:
        out.mkdir(parents=True, exist_ok=True)
        manifest_file.write_bytes(payload)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="build/lossless-oversize-probe")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    result = report(Path(args.out).resolve(), args.verify)
    print(json.dumps({k: result[k] for k in ("checked", "losslessGeometryRecovered",
        "withoutNewPaletteQuantization", "stillOversizedOrNonDuplicated", "factorCounts")},
        sort_keys=True))
