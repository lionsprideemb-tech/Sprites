#!/usr/bin/env python3
"""Stage *non-integrated* Nintendo DS OBJ 4bpp QA data from approved DS64 PNGs.

Outputs 64x64 tiled 4bpp OBJ pixels (2048 bytes/view), one 16-color BGR555
palette (32 bytes/view), and a round-trip decoded preview. This is NOT a
Platinum NARC, compressed NCGR/NCLR archive, ROM patch, visual approval, or
permission to insert any artwork in-game. Source files are never modified.

Only previously KEEP'd, exact-source-matched, non-quantized, binary-alpha
technical previews enter this isolated QA output. 8-bit RGB must be rounded
to DS 5-bit/channel color; the report measures that unavoidable hardware loss.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
TECH = "DS_CUSTOM_LIBRARY/converted/Verified_Source_DS64_Technical_2026_10_23/technical_quality_manifest.json"
USER = "review/user-iphone-decisions-2026-10-23.json"
OVERLAY = "review/final-artwork-approval-overlay-2026-10-24.json"
SAFE = {"PIXEL_PRESERVED_DS64_CANDIDATE", "PIXEL_PRESERVED_EXACT_2X_COLLAPSE_DS64_CANDIDATE"}
SLOTS = ("front", "back", "shiny_front", "shiny_back")


def file_in_repo(relative: str) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise ValueError("Invalid source path")
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError("Source outside repo or missing: " + relative)
    return path


def load_json(relative: str) -> dict:
    return json.loads(file_in_repo(relative).read_text(encoding="utf-8"))


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def bgr555(rgb: tuple[int, int, int]) -> int:
    r, g, b = rgb
    return round(r * 31 / 255) | (round(g * 31 / 255) << 5) | (round(b * 31 / 255) << 10)


def rgb888(value: int) -> tuple[int, int, int]:
    return tuple(round(((value >> offset) & 31) * 255 / 31) for offset in (0, 5, 10))


def encode_obj(pixels: Image.Image) -> tuple[bytes, bytes, Image.Image, int]:
    if pixels.size != (64, 64):
        raise ValueError("DS OBJ QA requires a 64x64 canvas")
    rgba = pixels.convert("RGBA")
    indexed = []
    lookup: dict[tuple[int, int, int], int] = {}
    palette: list[int] = [0]
    original_pixels = []
    for r, g, b, a in rgba.getdata():
        if a not in (0, 255):
            raise ValueError("Partial alpha cannot be encoded silently")
        if not a:
            indexed.append(0)
            original_pixels.append((0, 0, 0, 0))
            continue
        rgb = (r, g, b)
        if rgb not in lookup:
            if len(lookup) >= 15:
                raise ValueError("Too many source colors for 4bpp (15 opaque maximum)")
            lookup[rgb] = len(lookup) + 1
            palette.append(bgr555(rgb))
        indexed.append(lookup[rgb])
        original_pixels.append((r, g, b, 255))
    if not lookup:
        raise ValueError("Empty sprite")

    # Nintendo DS OBJ tiles, 1D 8x8 tile order, low nibble = left pixel.
    packed = bytearray()
    for ty in range(0, 64, 8):
        for tx in range(0, 64, 8):
            for y in range(ty, ty + 8):
                for x in range(tx, tx + 8, 2):
                    i = y * 64 + x
                    packed.append(indexed[i] | (indexed[i + 1] << 4))
    if len(packed) != 2048:
        raise AssertionError("64x64 4bpp OBJ must occupy 2048 bytes")
    pal_bytes = b"".join(v.to_bytes(2, "little") for v in (palette + [0] * (16 - len(palette))))
    if len(pal_bytes) != 32:
        raise AssertionError("One DS 16-color palette must occupy 32 bytes")
    decoded = decode_obj(bytes(packed), pal_bytes)
    max_channel_delta = 0
    for original, back in zip(original_pixels, decoded.getdata()):
        if original[3] != back[3]:
            raise AssertionError("Transparency changed in 4bpp round-trip")
        if original[3]:
            max_channel_delta = max(max_channel_delta, *(abs(original[c] - back[c]) for c in range(3)))
    if max_channel_delta > 5:
        raise AssertionError("Unexpected change beyond Nintendo DS RGB555 channel rounding")
    return bytes(packed), pal_bytes, decoded, max_channel_delta


def decode_obj(packed: bytes, palette_bytes: bytes) -> Image.Image:
    if len(packed) != 2048 or len(palette_bytes) != 32:
        raise ValueError("Wrong DS raw OBJ tile or palette length")
    palette = [int.from_bytes(palette_bytes[i:i + 2], "little") for i in range(0, 32, 2)]
    out = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    px = out.load()
    pos = 0
    for ty in range(0, 64, 8):
        for tx in range(0, 64, 8):
            for y in range(ty, ty + 8):
                for x in range(tx, tx + 8, 2):
                    value = packed[pos]
                    pos += 1
                    for dx, index in enumerate((value & 15, value >> 4)):
                        if index:
                            px[x + dx, y] = (*rgb888(palette[index]), 255)
    return out


def exact_vote(design: dict, vote: dict) -> bool:
    slots = design["slots"]
    front = slots.get("front") or {}
    back = slots.get("back") or {}
    return (vote.get("id") == design.get("reviewId")
            and bool(vote.get("front_path")) and bool(vote.get("back_path"))
            and vote["front_path"] == front.get("original")
            and vote["back_path"] == back.get("original"))


def allowed_by_artwork_choice(design: dict, user_votes: dict, final_votes: dict) -> tuple[bool, str]:
    # Source-verified historical approvals only; the history is not a blanket
    # approval for visually similar artist/source variants.
    historical = (design["tier"] == "historically_approved_source"
                  and design.get("creativeVote") == "KEEP (original specific artwork only)")
    matched = [x for x in user_votes.get(design.get("reviewId"), []) if exact_vote(design, x)]
    matched += [x for x in final_votes.get(design.get("reviewId"), []) if exact_vote(design, x)]
    if matched:
        # The later explicit final overlay takes priority over the older iPhone backup.
        last = matched[-1]
        return (last["decision"] == "keep", "exact_source_saved_vote")
    if historical:
        return True, "verified_historical_source_keep"
    return False, "no_exact_source_KEEP_vote"


def self_test() -> None:
    im = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    px = im.load()
    for k in range(1, 16):
        px[(k * 7) % 64, (k * 13) % 64] = (k * 16, k * 9, 255 - k * 15, 255)
    px[7, 7] = (255, 0, 0, 255)
    px[8, 8] = (0, 255, 0, 255)
    raw, pal, restored, error = encode_obj(im)
    assert len(raw) == 2048 and len(pal) == 32 and error <= 5
    assert restored.getpixel((0, 0))[3] == 0
    assert restored.getpixel((7, 7))[3] == 255
    assert restored.getpixel((8, 8))[3] == 255
    try:
        bad = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        bad.putpixel((0, 0), (8, 9, 10, 128))
        encode_obj(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("Partial alpha must fail")
    print("Nintendo DS 4bpp tile/palette round-trip synthetic self-test: PASS")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="build/native-ds4bpp-qa", help="QA artifact output directory; never a ROM")
    parser.add_argument("--verify", action="store_true", help="Byte-compare all previously produced QA artifacts")
    parser.add_argument("--self-test", action="store_true", help="Test nibble order and tile/palette round-trip")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    out = Path(args.out).resolve()
    if out == ROOT or out == ROOT / "DS_CUSTOM_LIBRARY" or out == ROOT / "platinum-overlay":
        raise ValueError("Refusing to write QA outputs into a source or game asset directory")

    technical = load_json(TECH)
    if technical["schema"] != "mercury-verified-source-ds64-technical-v1":
        raise ValueError("Unexpected technical source schema")
    if technical["policy"]["notNativeGameTileFormat"] is not True:
        raise ValueError("Expected source report to identify PNG-only staging")
    counts = technical["counts"]
    if counts["PIXEL_PRESERVED_DS64_CANDIDATE"] != 13 or counts["PIXEL_PRESERVED_EXACT_2X_COLLAPSE_DS64_CANDIDATE"] != 55:
        raise ValueError("Source-preserving inventory changed; audit before proceeding")
    old_votes, final_overlay = load_json(USER), load_json(OVERLAY)
    if (old_votes["count"], old_votes["keepCount"], old_votes["cutCount"]) != (166, 154, 12):
        raise ValueError("Original user approvals changed")
    if (final_overlay["summary"]["totalActionableResolved"] != 158
            or final_overlay["summary"]["pendingActionable"] != 0):
        raise ValueError("Final review approval coverage changed")
    user_by_id: dict[str, list[dict]] = {}
    final_by_id: dict[str, list[dict]] = {}
    for entry in old_votes["entries"]:
        user_by_id.setdefault(entry["id"], []).append(entry)
    for entry in final_overlay["decisions"]:
        final_by_id.setdefault(entry["id"], []).append(entry)

    candidates = []
    exclusions = Counter()
    by_design = {}
    for design in technical["designs"]:
        allowed, approval_basis = allowed_by_artwork_choice(design, user_by_id, final_by_id)
        for slot in SLOTS:
            part = design["slots"].get(slot, {})
            status = part.get("status", "MISSING_SOURCE")
            if status not in SAFE:
                exclusions[status] += 1
                continue
            if not allowed:
                exclusions["NOT_EXACT_SOURCE_APPROVED"] += 1
                continue
            if part.get("palette_changed") is not False or part.get("gameIntegrationAllowed") is not False:
                raise ValueError("Unsafe technical candidate state")
            png_path = file_in_repo(part["output"])
            data = png_path.read_bytes()
            if sha256(data) != part["output_sha256"]:
                raise ValueError("Technical PNG hash mismatch: " + part["output"])
            with Image.open(png_path) as image:
                image.load()
                raw, pal, decoded, delta = encode_obj(image)
            key = design["key"]
            if "/" in key or "\\" in key or key in (".", ".."):
                raise ValueError("Unexpected design output path")
            relative = Path("views") / key / slot
            items = {
                str(relative) + ".4bpp": raw,
                str(relative) + ".pal": pal,
            }
            # Deterministic PNG preview, for visually inspecting hardware color rounding.
            import io
            buffer = io.BytesIO()
            decoded.save(buffer, format="PNG")
            items[str(relative) + ".decoded.png"] = buffer.getvalue()
            for name, payload in items.items():
                target = out / name
                if args.verify:
                    if not target.is_file() or target.read_bytes() != payload:
                        raise ValueError("Staged artifact mismatches reconstruction: " + name)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(payload)
            candidates.append({
                "identity": key,
                "name": design["name"],
                "reviewId": design.get("reviewId"),
                "family": design.get("family"),
                "slot": slot,
                "technicalStatus": status,
                "approvalBasis": approval_basis,
                "sourcePng": part["output"],
                "sourcePngSha256": part["output_sha256"],
                "raw4bpp": str(relative) + ".4bpp",
                "raw4bppSha256": sha256(raw),
                "palette": str(relative) + ".pal",
                "paletteSha256": sha256(pal),
                "decodedPreview": str(relative) + ".decoded.png",
                "decodedPreviewSha256": sha256(items[str(relative) + ".decoded.png"]),
                "maxRgb888ToBgr555ChannelDelta": delta,
                "romIntegrationAllowed": False
            })
            by_design.setdefault(key, set()).add(slot)

    full_pairs = [key for key, slots in by_design.items() if {"front", "back"} <= slots]
    full_quartets = [key for key, slots in by_design.items() if set(SLOTS) <= slots]
    report = {
        "schema": "mercury-native-ds-obj4bpp-isolated-qa-v1",
        "sourceManifest": TECH,
        "sourceManifestOriginalColorCandidates": 68,
        "approvedEncodedViews": len(candidates),
        "completeApprovedNormalPairs": len(full_pairs),
        "completeApprovedNormalShinyQuartets": len(full_quartets),
        "excludedSlotsByReason": dict(sorted(exclusions.items())),
        "format": {"width": 64, "height": 64, "tile": [8, 8], "layout": "OBJ 1D row-major 8x8 tiles",
                   "bytesPerView": 2048, "bitsPerPixel": 4,
                   "paletteFormat": "16 entries x LE RGB555/BGR555 (red low five bits), index 0 transparent",
                   "paletteBytes": 32, "rgbConversion": "round(channel * 31 / 255)"},
        "policy": {"qualityAssuranceOnly": True, "noROMIntegration": True,
                   "notNCGRorNCLR": True, "noSourceModification": True,
                   "notHumanVisualApproved": True, "notCompleteUntilAllRequiredViewsCertified": True},
        "completePairs": sorted(full_pairs),
        "completeQuartets": sorted(full_quartets),
        "views": candidates
    }
    report_bytes = (json.dumps(report, indent=2, ensure_ascii=False) + "\n").encode()
    summary = out / "qa-manifest.json"
    if args.verify:
        if not summary.is_file() or summary.read_bytes() != report_bytes:
            raise ValueError("QA manifest changed or missing")
    else:
        out.mkdir(parents=True, exist_ok=True)
        summary.write_bytes(report_bytes)
    print(json.dumps({"mode": "verify" if args.verify else "stage",
                      "DS4bppViews": len(candidates),
                      "completeNormalPairs": len(full_pairs),
                      "completeQuartets": len(full_quartets),
                      "excluded": dict(exclusions)}, sort_keys=True))


if __name__ == "__main__":
    main()
