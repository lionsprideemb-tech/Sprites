#!/usr/bin/env python3
"""Non-destructive, attributed original-source Furrva recovery. NOT DS conversion."""
from __future__ import annotations
from io import BytesIO
from pathlib import Path
import hashlib
import json
import urllib.request

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "DS_CUSTOM_LIBRARY/recovered/Pokengine_Mikitari_Furrva_Source"
BASE = "https://pokengine.b-cdn.net/play/images/mons/"
SOURCE = "https://pokengine.org/mons/00uc0o89/Furrva"
MON_ID = "00uc0o89"


def preserve_exact(path: Path, data: bytes) -> None:
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError(f"Existing source file differs; refusing overwrite: {path}")
        return
    path.write_bytes(data)


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    files = {}
    for direction, remote_dir in (("front", "fronts"), ("back", "backs")):
        url = f"{BASE}{remote_dir}/{MON_ID}.webp?t=56"
        request = urllib.request.Request(url, headers={
            "User-Agent": "MercuryReduxResearch/1.0 (source attribution: Pokengine; personal project)",
            "Accept": "image/webp,image/*;q=0.8",
        })
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read(1024 * 1024 + 1)
            mime = response.headers.get("Content-Type", "")
        if not raw or len(raw) > 1024 * 1024:
            raise ValueError(f"Invalid or oversized original source image: {direction}")
        with Image.open(BytesIO(raw)) as image:
            image.load()
            if image.format != "WEBP" or image.size != (64, 64) or getattr(image, "n_frames", 1) != 1:
                raise ValueError(f"Unexpected original Furrva artwork: {direction}, {image.format} {image.size}")
            rgba = image.convert("RGBA")
            if not rgba.getbbox():
                raise ValueError(f"Blank Furrva artwork: {direction}")
            out = BytesIO()
            rgba.save(out, format="PNG", optimize=False)
            png = out.getvalue()
        preserve_exact(DEST / f"{direction}_original.webp", raw)
        preserve_exact(DEST / f"{direction}_source.png", png)
        files[direction] = {
            "source_url": url,
            "raw_path": (DEST / f"{direction}_original.webp").relative_to(ROOT).as_posix(),
            "png_path": (DEST / f"{direction}_source.png").relative_to(ROOT).as_posix(),
            "raw_sha256": hashlib.sha256(raw).hexdigest(),
            "png_sha256": hashlib.sha256(png).hexdigest(),
            "size": [64, 64],
            "content_type": mime,
            "conversion": "lossless rendering to RGBA PNG; original WebP retained",
            "ds_certified": False,
        }
    manifest = {
        "schema": "mercury-original-source-furrva-v1",
        "species": "Furrva",
        "identity": MON_ID,
        "type": "Bug",
        "source": SOURCE,
        "source_artist": "Mikitari",
        "source_permission": "Free to use with credit",
        "usage": "Source-only technical recovery. Not a DS-ready sprite, not an approval vote, not implemented in ROM.",
        "assets": files,
        "artwork_fabricated": False,
        "game_integration_allowed": False,
    }
    payload = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode()
    preserve_exact(DEST / "source_manifest.json", payload)
    preserve_exact(DEST / "README.md", (
        "# Furrva — original source recovery (not DS-certified)\n"
        "Original designer **Mikitari**, hosted on [Pokéngine]("+SOURCE+"). "
        "Source permission explicitly states **Free to use with credit**.\n\n"
        "The two .webp files are preserved original source bytes. The .png files are "
        "lossless decoded RGBA previews for technical inspection, **not** polished or newly drawn sprites.\n\n"
        "No new Pokémon IDs, approvals, evolutions, DS-format claims or ROM changes are made.\n"
    ).encode("utf-8"))
    print("PASS: original Furrva fronts/backs preserved with attribution; source-only, no ROM integration")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
