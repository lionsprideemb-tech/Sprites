#!/usr/bin/env python3
"""Build Mercury Redux GBA conversion candidates/workboards from Platinum field sprites.

This tool generates two comparison lanes from a local pinned `pret/pokeplatinum`
checkout:

1. Fidelity-first native 32x32 candidate
   - exact Platinum pixel indices and palette
   - nine frames reordered for Emerald's standard object-event animation
   - 288x32 indexed PNG
   - intended for in-engine QA before any redraw is attempted

2. Narrow 16x32 automatic preview
   - crop/scale comparison only
   - NEVER a final master

Raw 32x512 Platinum source sheets are not copied into the public asset vault.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

from PIL import Image

PLATINUM_FRAME_SIZE = (32, 32)
PLATINUM_SHEET_SIZE = (32, 512)
NATIVE_GBA_FRAME_SIZE = (32, 32)
NATIVE_GBA_SHEET_SIZE = (288, 32)
NARROW_GBA_FRAME_SIZE = (16, 32)
NARROW_GBA_SHEET_SIZE = (144, 32)

# Verified against Platinum's generic field-walk layout and Emerald's standard
# 9-frame object-event animation table.
FRAME_MAP = [4, 0, 8, 5, 7, 1, 3, 9, 11]
FRAME_LABELS = [
    "south_idle",
    "north_idle",
    "west_idle",
    "south_walk_a",
    "south_walk_b",
    "north_walk_a",
    "north_walk_b",
    "west_walk_a",
    "west_walk_b",
]

DEFAULT_CHARACTERS = ["roark", "gardenia", "candice", "flint"]


def split_platinum_frames(sheet: Image.Image) -> list[Image.Image]:
    if sheet.size != PLATINUM_SHEET_SIZE:
        raise ValueError(
            f"Expected Platinum sheet size {PLATINUM_SHEET_SIZE}, got {sheet.size}"
        )
    return [sheet.crop((0, idx * 32, 32, idx * 32 + 32)) for idx in range(16)]


def palette_color_count(image: Image.Image) -> int:
    if image.mode == "P":
        return len(image.getcolors(maxcolors=256) or [])
    return len(image.convert("RGBA").getcolors(maxcolors=4096) or [])


def alpha_bbox(image: Image.Image) -> tuple[int, int, int, int] | None:
    return image.convert("RGBA").getchannel("A").getbbox()


def union_bbox(frames: list[Image.Image]) -> tuple[int, int, int, int]:
    boxes = [alpha_bbox(frame) for frame in frames]
    boxes = [box for box in boxes if box is not None]
    if not boxes:
        return (0, 0, 32, 32)
    return (
        min(box[0] for box in boxes),
        min(box[1] for box in boxes),
        max(box[2] for box in boxes),
        max(box[3] for box in boxes),
    )


def make_native32_candidate(sheet: Image.Image, frames: list[Image.Image]) -> Image.Image:
    """Reorder Platinum frames without changing their indexed pixels or palette."""
    if sheet.mode != "P":
        raise ValueError(f"Expected indexed Platinum PNG (mode P), got {sheet.mode}")

    out = Image.new("P", NATIVE_GBA_SHEET_SIZE, color=0)
    palette = sheet.getpalette()
    if palette is not None:
        out.putpalette(palette)

    for dst_idx, src_idx in enumerate(FRAME_MAP):
        out.paste(frames[src_idx], (dst_idx * 32, 0))

    transparency = sheet.info.get("transparency", 0)
    out.info["transparency"] = transparency
    return out


def make_reference_strip(frames: list[Image.Image]) -> Image.Image:
    # Human-readable RGBA copy of the selected native frames for workboard viewing.
    out = Image.new("RGBA", NATIVE_GBA_SHEET_SIZE, (0, 0, 0, 0))
    for dst_idx, src_idx in enumerate(FRAME_MAP):
        out.alpha_composite(frames[src_idx].convert("RGBA"), (dst_idx * 32, 0))
    return out


def build_narrow_preview_geometry(selected: list[Image.Image]) -> dict:
    """Use one shared crop/scale for every pose to avoid animation pumping."""
    bbox = union_bbox(selected)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    if width <= 0 or height <= 0:
        width, height = 32, 32
        bbox = (0, 0, 32, 32)

    scale = min(1.0, NARROW_GBA_FRAME_SIZE[0] / width, NARROW_GBA_FRAME_SIZE[1] / height)
    scaled_w = max(1, round(width * scale))
    scaled_h = max(1, round(height * scale))
    x = (NARROW_GBA_FRAME_SIZE[0] - scaled_w) // 2
    y = NARROW_GBA_FRAME_SIZE[1] - scaled_h

    return {
        "bbox": bbox,
        "source_union_size": [width, height],
        "scale": scale,
        "scaled_size": [scaled_w, scaled_h],
        "placement": [x, y],
    }


def make_narrow_auto_preview(frames: list[Image.Image]) -> tuple[Image.Image, dict]:
    selected = [frames[src_idx].convert("RGBA") for src_idx in FRAME_MAP]
    geometry = build_narrow_preview_geometry(selected)
    left, top, right, bottom = geometry["bbox"]
    scaled_w, scaled_h = geometry["scaled_size"]
    place_x, place_y = geometry["placement"]

    out = Image.new("RGBA", NARROW_GBA_SHEET_SIZE, (0, 0, 0, 0))
    for dst_idx, src in enumerate(selected):
        cropped = src.crop((left, top, right, bottom))
        if cropped.size != (scaled_w, scaled_h):
            cropped = cropped.resize((scaled_w, scaled_h), Image.Resampling.NEAREST)
        out.alpha_composite(cropped, (dst_idx * 16 + place_x, place_y))
    return out, geometry


def make_workboard(reference: Image.Image, narrow_preview: Image.Image) -> Image.Image:
    # Row 1: exact 32x32 selected Platinum poses.
    # Rows 2-3: 16x32 fallback preview enlarged 2x for inspection.
    # Row 4: blank redraw cells for fallback/manual comparison.
    width = 32 * 9
    height = 32 + 64 + 32
    board = Image.new("RGBA", (width, height), (255, 255, 255, 255))
    board.alpha_composite(reference, (0, 0))
    board.alpha_composite(
        narrow_preview.resize((288, 64), Image.Resampling.NEAREST),
        (0, 32),
    )

    pixels = board.load()
    y0 = 96
    for cell in range(9):
        x0 = cell * 32
        for x in range(x0, x0 + 32):
            pixels[x, y0] = (160, 160, 160, 255)
            pixels[x, y0 + 31] = (160, 160, 160, 255)
        for y in range(y0, y0 + 32):
            pixels[x0, y] = (160, 160, 160, 255)
            pixels[x0 + 31, y] = (160, 160, 160, 255)
    return board


def process_character(source_root: Path, output_root: Path, name: str) -> dict:
    src = source_root / "res" / "graphics" / "field_sprites" / "npc" / f"{name}.png"
    if not src.exists():
        raise FileNotFoundError(src)

    sheet = Image.open(src)
    source_mode = sheet.mode
    source_colors = palette_color_count(sheet)
    frames = split_platinum_frames(sheet)

    char_out = output_root / name
    char_out.mkdir(parents=True, exist_ok=True)

    native32 = make_native32_candidate(sheet, frames)
    reference = make_reference_strip(frames)
    narrow_preview, narrow_geometry = make_narrow_auto_preview(frames)
    workboard = make_workboard(reference, narrow_preview)

    native32_path = char_out / f"{name}_gba_native32_CANDIDATE.png"
    reference_path = char_out / f"{name}_platinum_9frame_reference.png"
    narrow_path = char_out / f"{name}_gba_narrow16_auto_preview_NOT_MASTER.png"
    workboard_path = char_out / f"{name}_workboard.png"

    native32.save(native32_path, transparency=sheet.info.get("transparency", 0))
    reference.save(reference_path)
    narrow_preview.save(narrow_path)
    workboard.save(workboard_path)

    metadata = {
        "character": name,
        "source": str(src),
        "source_size": list(sheet.size),
        "source_mode": source_mode,
        "source_color_count": source_colors,
        "source_frame_count": 16,
        "source_frame_size": [32, 32],
        "frame_map": dict(zip(FRAME_LABELS, FRAME_MAP)),
        "native32_candidate": {
            "frame_size": [32, 32],
            "frame_count": 9,
            "sheet_size": [288, 32],
            "mode": native32.mode,
            "color_count": palette_color_count(native32),
            "pixel_policy": "EXACT_SOURCE_PIXELS_REORDERED_ONLY",
            "emerald_geometry_tiles": [4, 4],
            "status": "FORMAT_CONVERSION_CANDIDATE_REQUIRES_IN_ENGINE_QA",
        },
        "narrow16_preview": {
            "frame_size": [16, 32],
            "frame_count": 9,
            "sheet_size": [144, 32],
            "preview_geometry": narrow_geometry,
            "status": "AUTO_PREVIEW_ONLY_NOT_MASTER",
        },
        "approval_warning": "Neither output is MERCURY_APPROVED until in-engine visual and technical QA passes.",
    }
    with (char_out / "conversion_metadata.json").open("w", encoding="utf-8") as fh:
        json.dump(metadata, fh, indent=2)
        fh.write("\n")

    return metadata


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pokeplatinum_root", type=Path, help="Path to local pret/pokeplatinum checkout")
    parser.add_argument("output_dir", type=Path, help="Directory for generated conversion artifacts")
    parser.add_argument(
        "--characters",
        nargs="+",
        default=DEFAULT_CHARACTERS,
        help="NPC basenames under res/graphics/field_sprites/npc",
    )
    args = parser.parse_args(argv)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    results = [process_character(args.pokeplatinum_root, args.output_dir, name) for name in args.characters]

    with (args.output_dir / "conversion_batch.json").open("w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)
        fh.write("\n")

    print(f"Generated conversion candidates/workboards for {len(results)} character(s) in {args.output_dir}")
    print("Native 32x32 sheets preserve source pixels but still require Mercury in-engine QA.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
