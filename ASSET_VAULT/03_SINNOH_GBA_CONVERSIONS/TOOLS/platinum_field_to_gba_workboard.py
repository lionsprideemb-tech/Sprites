#!/usr/bin/env python3
"""Build Mercury Redux GBA conversion workboards from official Platinum field sprites.

This tool does NOT produce an approved final sprite. It creates repeatable reference
and nearest-neighbor preview sheets from a local `pret/pokeplatinum` checkout so an
artist can perform the final pixel cleanup without copying the original Platinum
PNG files into this public asset vault.

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


def make_reference_strip(frames: list[Image.Image]) -> Image.Image:
    # 9 selected official frames in target animation order, still at Platinum size.
    out = Image.new("RGBA", (32 * 9, 32), (0, 0, 0, 0))
    for dst_idx, src_idx in enumerate(FRAME_MAP):
        out.alpha_composite(frames[src_idx].convert("RGBA"), (dst_idx * 32, 0))
    return out


def make_auto_preview(frames: list[Image.Image]) -> Image.Image:
    # Mechanical width reduction only. This is deliberately NOT a final master.
    out = Image.new("RGBA", GBA_SHEET_SIZE, (0, 0, 0, 0))
    for dst_idx, src_idx in enumerate(FRAME_MAP):
        src = frames[src_idx].convert("RGBA")
        preview = src.resize(GBA_FRAME_SIZE, Image.Resampling.NEAREST)
        out.alpha_composite(preview, (dst_idx * 16, 0))
    return out


def make_workboard(reference: Image.Image, preview: Image.Image) -> Image.Image:
    # Top: official selected frames at native 32x32.
    # Middle: nearest-neighbor 16x32 mechanical preview enlarged 2x for inspection.
    # Bottom: blank 16x32 target cells enlarged 2x for redraw planning.
    width = 32 * 9
    height = 32 * 3
    board = Image.new("RGBA", (width, height), (255, 255, 255, 255))
    board.alpha_composite(reference, (0, 0))

    preview_2x = preview.resize((288, 64), Image.Resampling.NEAREST)
    board.alpha_composite(preview_2x.crop((0, 0, 288, 32)), (0, 32))

    # Draw simple 32x32 target-cell outlines without introducing antialiasing.
    pixels = board.load()
    y0 = 64
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
    preview = make_auto_preview(frames)
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
