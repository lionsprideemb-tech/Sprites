#!/usr/bin/env python3
"""Mercury Redux read-only Orpheus Thracean DS64 source conversion experiment.
NO artwork approval, source overwrite, user-vote edits, or ROM packaging.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import base64
import hashlib
import json
import math
import struct

ARCHIVE = Path("orpheus-original-resources.rar")
EXPECTED_ARCHIVE_SHA256 = "72539b83b55a427c4adcdf2f3e5397cc28371875a720f687ffcf4e2a6d803ef9"
SOURCE = Path("safepng")
OUT = Path("report/ds64_experiment")
OUT.mkdir(parents=True, exist_ok=True)
STAGES = [(328, "Trapinch", "Bug"), (329, "Vibrava", "Bug/Dragon"), (330, "Flygon", "Bug/Dragon")]
FONT = ImageFont.load_default()

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()

def hex5(c):
    return max(0, min(31, round(c * 31 / 255)))

def bgr555(rgb):
    r, g, b = rgb
    return hex5(r) | hex5(g) << 5 | hex5(b) << 10

def from_bgr555(v):
    return tuple(round(255 * ((v >> shift) & 31) / 31) for shift in (0, 5, 10))

def fit64(rgba):
    """Crop only transparency and preserve silhouettes; nearest-neighbor 64px stage."""
    bbox = rgba.getchannel("A").getbbox()
    if bbox is None:
        raise ValueError("empty alpha silhouette")
    crop = rgba.crop(bbox)
    w, h = crop.size
    factor = min(60 / w, 60 / h, 1.0)
    tw, th = max(1, round(w * factor)), max(1, round(h * factor))
    resized = crop.resize((tw, th), Image.Resampling.NEAREST)
    dst = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    dst.alpha_composite(resized, ((64 - tw) // 2, (64 - th) // 2))
    return dst, dict(sourceBBox=list(bbox), originalOpaqueCrop=[w, h], fitSize=[tw, th])

def rgb_palette_and_indices(img):
    """Select at most 15 opaque RGB colors and reserve index 0 for transparency."""
    pixels = list(img.getdata())
    assert len(pixels) == 4096
    if any(px[3] not in (0, 255) for px in pixels):
        raise ValueError("partial alpha not compatible with strict 1-bit mask")
    rgb = [px[:3] for px in pixels if px[3] != 0]
    if not rgb:
        raise ValueError("No opaque pixels")
    colors_before = len(set(rgb))
    if colors_before <= 15:
        rgb_out = rgb
        was_quantized = False
    else:
        strip = Image.new("RGB", (len(rgb), 1))
        strip.putdata(rgb)
        quant = strip.quantize(colors=15, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        rgb_out = [tuple(quant.getpalette()[3 * q:3 * q + 3]) for q in quant.getdata()]
        was_quantized = True
    # 5-bit BGR555 rounding can collapse RGB palette entries. Deduplicate after rounding.
    pal = [(0, 0, 0)]
    lut = {}
    indices = []
    opaque_ptr = 0
    changed_pixels = 0
    pixel_abs_err = 0
    for raw in pixels:
        if raw[3] == 0:
            indices.append(0)
            continue
        selected = rgb_out[opaque_ptr]
        opaque_ptr += 1
        native = bgr555(selected)
        ds_rgb = from_bgr555(native)
        if native not in lut:
            if len(pal) >= 16:
                raise ValueError("16 color palette exceeded")
            lut[native] = len(pal)
            pal.append(ds_rgb)
        indices.append(lut[native])
        if raw[:3] != ds_rgb:
            changed_pixels += 1
        pixel_abs_err += sum(abs(raw[i] - ds_rgb[i]) for i in range(3))
    out = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    out.putdata([(*pal[idx], 255) if idx else (0, 0, 0, 0) for idx in indices])
    count_opaque = len(rgb)
    return out, indices, pal, {
        "sourceColorsAt64ExcludingAlpha": colors_before,
        "paletteQuantizationNeeded": was_quantized,
        "DSColorsIncludingTransparency": len(pal),
        "changedOpaquePixelsVsUnrestricted64": changed_pixels,
        "opaquePixelCount": count_opaque,
        "changedOpaquePixelPercent": round(changed_pixels / count_opaque * 100, 2),
        "averageAbsoluteRGBChannelError": round(pixel_abs_err / (3 * count_opaque), 3),
    }

def tile4bpp(indices):
    if len(indices) != 64 * 64:
        raise ValueError("wrong tile canvas")
    out = bytearray()
    for by in range(0, 64, 8):
        for bx in range(0, 64, 8):
            for y in range(8):
                for x in range(0, 8, 2):
                    a, b = indices[(by + y) * 64 + bx + x:(by + y) * 64 + bx + x + 2]
                    if not 0 <= a <= 15 or not 0 <= b <= 15:
                        raise ValueError("palette index out of range")
                    out.append(a | (b << 4))
    if len(out) != 2048:
        raise ValueError("wrong tile byte count")
    # Decode to prove DS nibble arrangement round-trips every source index.
    decoded = [0] * (64 * 64)
    i = 0
    for by in range(0, 64, 8):
        for bx in range(0, 64, 8):
            for y in range(8):
                for x in range(0, 8, 2):
                    value = out[i]
                    i += 1
                    decoded[(by + y) * 64 + bx + x] = value & 15
                    decoded[(by + y) * 64 + bx + x + 1] = value >> 4
    if decoded != indices:
        raise AssertionError("tile pack/unpack failed")
    return bytes(out)

def render_panel(canvas, sprite, x, y, box_size, zoom=None):
    if zoom is None:
        zoom = box_size
    src = sprite.resize((zoom, zoom), Image.Resampling.NEAREST)
    board = Image.new("RGBA", (box_size, box_size), (239, 243, 246, 255))
    board.alpha_composite(src, ((box_size - zoom) // 2, (box_size - zoom) // 2))
    canvas.paste(board.convert("RGB"), (x, y))

if sha256(ARCHIVE) != EXPECTED_ARCHIVE_SHA256:
    raise RuntimeError("Orpheus RAR SHA256 mismatch; refusing to use unpinned asset archive")
W, margin, row_h = 1290, 24, 244
H = 116 + 6 * row_h + 28
sheet = Image.new("RGB", (W, H), "#f6f6f3")
d = ImageDraw.Draw(sheet)
d.text((margin, 15), "ORPHEUS THRACEAN FLYGON  -  EXPERIMENTAL DS64 QUALITY TEST", fill="#27303c", font=FONT)
d.text((margin, 36), "Original 160x160 source  /  cropped nearest-neighbor 64x64  /  DS 15 opaque colors + BGR555", fill="#586574", font=FONT)
d.text((margin, 57), "Unapproved and NOT ROM READY | No art modifications to archive | Preview only | Pixel art shown at 3x", fill="#934343", font=FONT)
d.text((margin, 86), "Source 160px", fill="#384553", font=FONT)
d.text((263, 86), "Unrestricted 64px (zoomed 3x)", fill="#384553", font=FONT)
d.text((559, 86), "DS 64px / 4bpp palette (zoomed 3x)", fill="#384553", font=FONT)
d.text((892, 86), "Quality changes and source coverage", fill="#384553", font=FONT)
records = []
for stage_i, (num, name, original_type) in enumerate(STAGES):
    for view_i, (role, suffix) in enumerate([("front", "_1"), ("back", "b_1")]):
        path = SOURCE / f"{num}{suffix}.png"
        if not path.exists():
            raise FileNotFoundError(path)
        im = Image.open(path).convert("RGBA")
        if im.size != (160, 160):
            raise RuntimeError(f"unexpected original size {path}: {im.size}")
        source_rgb = {px for px in im.getdata() if px[3] > 0}
        no_limit, source_dims = fit64(im)
        ds, indices, palette, quality = rgb_palette_and_indices(no_limit)
        payload = tile4bpp(indices)
        palette_words = [0] + [bgr555(px) for px in palette[1:]]
        if len(palette_words) > 16:
            raise AssertionError("palette too long")
        pal_file = bytes().join(struct.pack("<H", x) for x in (palette_words + [0] * (16 - len(palette_words))))
        if len(pal_file) != 32:
            raise AssertionError("wrong PAL bytes")
        basename = f"{name.lower()}_{role}"
        ds.save(OUT / f"{basename}_experimental_ds64.png")
        no_limit.save(OUT / f"{basename}_unlimited64.png")
        (OUT / f"{basename}_4bpp_tiles.bin").write_bytes(payload)
        (OUT / f"{basename}_bgr555_palette.bin").write_bytes(pal_file)
        record = {
            "species": name, "sourceForm": "Thracean", "originalType": original_type,
            "targetFinalTypeIfChosen": "Bug/Ground" if name == "Flygon" else "Bug included",
            "view": role, "sourceFile": str(path), "sourceSHA256": sha256(path),
            "sourceDimension": list(im.size), "sourceOpaqueRGBColors": len({p[:3] for p in source_rgb}),
            "sourceAlphaValues": sorted({p[3] for p in im.getdata()}),
            **source_dims, **quality,
            "ds64Canvas": [64,64], "tileBytes": len(payload), "paletteBytes": len(pal_file),
            "binaryTileSHA256": hashlib.sha256(payload).hexdigest(),
            "binaryPaletteSHA256": hashlib.sha256(pal_file).hexdigest(),
            "experimentalOnly": True, "approved": False, "romIntegrated": False,
        }
        records.append(record)
        y = 117 + (stage_i * 2 + view_i) * row_h
        d.rounded_rectangle((margin - 8, y - 8, W - margin, y + row_h - 10), radius=12, fill="#ffffff", outline="#d4d8df", width=1)
        # Original transparent PNG is displayed without resampling at 160px.
        render_panel(sheet, im, margin, y + 22, 160, 160)
        # Both 64px outputs enlarged 3x, nearest pixels only.
        render_panel(sheet, no_limit, 256, y + 3, 202, 192)
        render_panel(sheet, ds, 560, y + 3, 202, 192)
        d.text((margin + 10, y + 4), f"{name} / {role.upper()}", fill="#202a38", font=FONT)
        txt = [
            f"Original {original_type}",
            f"Source RGB colors: {record['sourceOpaqueRGBColors']}",
            f"Content bbox {source_dims['originalOpaqueCrop'][0]}x{source_dims['originalOpaqueCrop'][1]} to {source_dims['fitSize'][0]}x{source_dims['fitSize'][1]}",
            f"Color count after resize: {quality['sourceColorsAt64ExcludingAlpha']}",
            f"DS colors (inc transparent): {quality['DSColorsIncludingTransparency']}/16",
            f"Quantize: {'YES' if quality['paletteQuantizationNeeded'] else 'not required'}",
            f"Palette-changed pixels: {quality['changedOpaquePixelPercent']:.1f}%",
            f"Avg RGB channel error: {quality['averageAbsoluteRGBChannelError']:.2f}/255",
            "Exact DS 4bpp tile round-trip: PASS",
        ]
        for line_no, txt_line in enumerate(txt):
            d.text((892, y + 16 + line_no * 19), txt_line, fill="#394659", font=FONT)
        print("DS64_RESULT", json.dumps(record, sort_keys=True))
sheet_path = OUT / "orpheus_ds64_quality_sheet.png"
sheet.save(sheet_path, optimize=True)
summary = {
    "schema": "mercury-orpheus-ds64-experimental-v1",
    "sourceArchive": "Orpheus_Resources.rar",
    "sourceArchiveSHA256": EXPECTED_ARCHIVE_SHA256,
    "qaStatus": "EXPERIMENTAL_PREVIEW_NOT_APPROVED_NOT_ROM_INTEGRATED",
    "method": "source-transparent-bbox crop, 60px max sprite fit, Pillow NEAREST, max 15 opaque RGB palette colors, RGB555, 64x64 8x8 DS OBJ 4bpp tiled encoding and decoding",
    "limitations": [
        "Visible detail may disappear at 64px; no manual pixel redrawing performed",
        "Source view palettes above 15 opaque colors require irreversible color quantization",
        "Source regional shiny artwork was not verified; this experiment covers normal fronts and backs only",
        "Raw tiles and palettes are not game-engine NCGR/NCLR/NARC packages and are not validated by emulator",
        "Source asset artist-level reuse permissions not established",
        "Orpheus Flygon's original typing is Bug/Dragon; Mercury final requirement is Bug/Ground",
    ],
    "records": records,
}
(OUT / "quality_metrics.json").write_text(json.dumps(summary, indent=2) + "\n")
print("DS64_SUMMARY", json.dumps({
    "views": len(records),
    "stageNames": [row[1] for row in STAGES],
    "paletteQuantizedViews": sum(x["paletteQuantizationNeeded"] for x in records),
    "maxPalette": max(x["DSColorsIncludingTransparency"] for x in records),
    "tileRoundTripPasses": len(records),
    "approved": False,
    "romIntegrated": False,
}))
print("PREVIEW_SHEET", sheet_path, "bytes", sheet_path.stat().st_size, "sha256", sha256(sheet_path))
print("BASE64_START orpheus_ds64_quality_sheet.png")
print(base64.b64encode(sheet_path.read_bytes()).decode("ascii"))
print("BASE64_END orpheus_ds64_quality_sheet.png")
