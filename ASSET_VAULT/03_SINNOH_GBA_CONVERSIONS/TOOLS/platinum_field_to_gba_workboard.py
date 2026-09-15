#!/usr/bin/env python3
"""Build Mercury Redux GBA conversion workboards from official Platinum field sprites.

This tool does NOT produce an approved final sprite. It creates repeatable reference
and proportion-preserving nearest-neighbor preview sheets from a local
`pret/pokeplatinum` checkout so an artist can perform the final pixel cleanup
without copying the original Platinum PNG files into this public asset vault.

Expected Platinum NPC source format:
- indexed PNG
- 32x512
- 16 stacked 32x32 frames
- palette index 0 transparent

Emerald target format:
- 9 frames
- 16x32 each
- 144x32 sheet
- frame order: face south, face north, face west, south A, south B,
  north A, north B, west A, west B
- east is mirrored in-engine from west
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

from PIL import Image

PLATINUM_FRAME_SIZE = (32, 32)
PLATINUM_SHEET_SIZE = (32, 512)
GBA_FRAME_SIZE = (16, 32)
GBA_SHEET_SIZE = (144, 32)

# Verified against Platinum's 16-frame field sheet structure and Emerald's
# standard 9-frame object-event animation layout.
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

    frames = []
    for idx in range(16):
        top = idx * PLATINUM_FRAME_SIZE[1]
        frame = sheet.crop((0, top, 32, top + 32))
        frames.append(frame)
    return frames


def palette_color_count(image: Image.Image) -> int:
    if image.mode == "P":
        return len(image.getcolors(maxcolors=256) or [])
    converted = image.convert("RGBA")
    return len(converted.getcolors(maxcolors=4096) or [])


def alpha_bbox(image: Image.Image) -> tuple[int, int, int, int] | None:
    rgba = image.convert("RGBA")
    return rgba.getchannel("A").getbbox()


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


def make_reference_strip(frames: list[Image.Image]) -> Image.Image:
    # 9 selected official frames in target animation order, still at Platinum size.
    out = Image.new("RGBA", (32 * 9, 32), (0, 0, 0, 0))
    for dst_idx, src_idx in enumerate(FRAME_MAP):
        out.alpha_composite(frames[src_idx].convert("RGBA"), (dst_idx * 32, 0))
    return out


def build_preview_geometry(selected: list[Image.Image]) -> dict:
    """Return one shared crop/scale for every pose to avoid animation pumping.

    We crop the *union* of all selected poses, not each pose independently. That
    preserves relative body position from frame to frame. We never upscale. If
    the character already fits in 16x32, the source pixels are retained 1:1.
    """
    bbox = union_bbox(selected)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    if width <= 0 or height <= 0:
        width, height = 32, 32
        bbox = (0, 0, 32, 32)

    scale = min(1.0, GBA_FRAME_SIZE[0] / width, GBA_FRAME_SIZE[1] / height)
    scaled_w = max(1, round(width * scale))
    scaled_h = max(1, round(height * scale))

    # Center horizontally and bottom-align every pose to one fixed baseline.
    x = (GBA_FRAME_SIZE[0] - scaled_w) // 2
    y = GBA_FRAME_SIZE[1] - scaled_h

    return {
        "bbox": bbox,
        "source_union_size": [width, height],
        "scale": scale,
        "scaled_size": [scaled_w, scaled_h],
        "placement": [x, y],
    }


def make_auto_preview(frames: list[Image.Image]) -> tuple[Image.Image, dict]:
    # Mechanical crop + proportional nearest-neighbor reduction only.
    # This is deliberately NOT a final master.
    selected = [frames[src_idx].convert("RGBA") for src_idx in FRAME_MAP]
    geometry = build_preview_geometry(selected)
    left, top, right, bottom = geometry["bbox"]
    scaled_w, scaled_h = geometry["scaled_size"]
    place_x, place_y = geometry["placement"]

    out = Image.new("RGBA", GBA_SHEET_SIZE, (0, 0, 0, 0))
    for dst_idx, src in enumerate(selected):
        cropped = src.crop((left, top, right, bottom))
        if cropped.size != (scaled_w, scaled_h):
            cropped = cropped.resize((scaled_w, scaled_h), Image.Resampling.NEAREST)
        out.alpha_composite(cropped, (dst_idx * 16 + place_x, place_y))
    return out, geometry


def make_workboard(reference: Image.Image, preview: Image.Image) -> Image.Image:
    # Top 32 px: official selected frames at native 32x32.
    # Middle 64 px: mechanical 16x32 preview enlarged 2x for inspection.
    # Bottom 32 px: blank 32x32 cells representing the nine 16x32 targets at 2x.
    width = 32 * 9
    height = 32 + 64 + 32
    board = Image.new("RGBA", (width, height), (255, 255, 255, 255))
    board.alpha_composite(reference, (0, 0))

    preview_2x = preview.resize((288, 64), Image.Resampling.NEAREST)
    board.alpha_composite(preview_2x, (0, 32))

    # Draw simple 32x32 target-cell outlines without introducing antialiasing.
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

    reference = make_reference_strip(frames)
    preview, geometry = make_auto_preview(frames)
    workboard = make_workboard(reference, preview)

    reference_path = char_out / f"{name}_platinum_9frame_reference.png"
    preview_path = char_out / f"{name}_gba_auto_preview_NOT_MASTER.png"
    workboard_path = char_out / f"{name}_workboard.png"

    reference.save(reference_path)
    preview.save(preview_path)
    workboard.save(workboard_path)

    metadata = {
        "character": name,
        "source": str(src),
        "source_size": list(sheet.size),
        "source_mode": source_mode,
        "source_color_count": source_colors,
        "source_frame_count": 16,
        "source_frame_size": [32, 32],
        "gba_target_frame_count": 9,
        "gba_target_frame_size": [16, 32],
        "gba_target_sheet_size": [144, 32],
        "frame_map": dict(zip(FRAME_LABELS, FRAME_MAP)),
        "preview_geometry": geometry,
        "status": "AUTO_PREVIEW_ONLY_REQUIRES_MANUAL_PIXEL_REDRAW_AND_QA",
        "approval_warning": "Do not promote the auto preview to MERCURY_APPROVED.",
    }
    with (char_out / "conversion_metadata.json").open("w", encoding="utf-8") as fh:
        json.dump(metadata, fh, indent=2)
        fh.write("\n")

    return metadata


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "pokeplatinum_root",
        type=Path,
        help="Path to a local pret/pokeplatinum checkout",
    )
    parser.add_argument(
        "output_dir",
        type=Path,
        help="Directory for generated conversion workboards",
    )
    parser.add_argument(
        "--characters",
        nargs="+",
        default=DEFAULT_CHARACTERS,
        help="NPC basenames under res/graphics/field_sprites/npc",
    )
    args = parser.parse_args(argv)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for name in args.characters:
        results.append(process_character(args.pokeplatinum_root, args.output_dir, name))

    with (args.output_dir / "conversion_batch.json").open("w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)
        fh.write("\n")

    print(f"Generated workboards for {len(results)} character(s) in {args.output_dir}")
    print("All auto previews are NON-MASTER reference outputs and require manual pixel cleanup.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
