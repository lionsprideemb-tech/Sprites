#!/usr/bin/env python3
"""Recover only valid original PNG pixel streams from broken ancillary containers.

Targets source-verified Munna/Musharna alternate normal front/back. Leaves ALL
historical approved source bytes untouched; retained IDAT chunks stay exact.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import struct
import zlib
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"review/recovered-approved-legacy-pairs-2026-10-23.json"
DEST=ROOT/"DS_CUSTOM_LIBRARY/recovered/Reborn_Plates_Legacy_PNG_Container_Repairs"
EXPECTED={
    "munna-alternate-form-1": ("front","back"),
    "musharna-alternate-form-1": ("front","back"),
}
SIGNATURE=b"\x89PNG\r\n\x1a\n"
# PNG critical chunks + image transparency, retained without recompression.
# All image-critical chunk bytes are reproduced exactly (including CRCs).
KEEP={b"IHDR",b"PLTE",b"tRNS",b"IDAT",b"IEND"}

def hashhex(data:bytes): return hashlib.sha256(data).hexdigest()

def chunks(data:bytes):
    if not data.startswith(SIGNATURE): raise ValueError("PNG signature absent")
    pos=8
    blocks=[]
    while pos<len(data):
        if pos+12>len(data): raise ValueError("Truncated PNG chunk header")
        length=struct.unpack(">I",data[pos:pos+4])[0]
        name=data[pos+4:pos+8]
        if length>len(data) or pos+12+length>len(data):
            raise ValueError("Broken PNG chunk length")
        chunk=data[pos:pos+12+length]
        actual=struct.unpack(">I",chunk[-4:])[0]
        expected=zlib.crc32(name+chunk[8:-4])&0xffffffff
        blocks.append({"type":name,"blob":chunk,"crc_ok":actual==expected,"size":length})
        pos+=len(chunk)
        if name==b"IEND": break
    if pos!=len(data): raise ValueError("Bytes after PNG IEND; manual recovery required")
    if not blocks or blocks[0]["type"]!=b"IHDR" or blocks[-1]["type"]!=b"IEND":
        raise ValueError("Invalid critical PNG chunk order")
    return blocks

def main():
    data=json.loads(SOURCE.read_text("utf-8"))
    lookup={x["identity"]:x for x in data["entries"]}
    DEST.mkdir(parents=True,exist_ok=True)
    result=[]
    for identity,views in EXPECTED.items():
        entry=lookup[identity]
        for slot in views:
            original=entry[slot]
            old=(ROOT/original["path"]).resolve()
            if not old.is_relative_to(ROOT) or not old.is_file():
                raise ValueError("Unresolved approved original source "+str(old))
            raw=old.read_bytes()
            git_sha=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
            if git_sha!=original["gitBlobSha"]:
                raise ValueError("Original approved Git blob changed "+original["path"])
            item={"identity":identity,"slot":slot,"source":original["path"],
                  "source_sha256":hashhex(raw),"original_git_blob_sha":git_sha,
                  "source_never_overwritten":True,"status":None}
            try:
                p=chunks(raw)
                critical=[x for x in p if x["type"] in KEEP]
                for ch in critical:
                    if not ch["crc_ok"]:
                        raise ValueError("Critical image chunk CRC invalid "+ch["type"].decode("ascii"))
                if not any(x["type"]==b"IDAT" for x in critical):
                    raise ValueError("Missing compressed pixel data")
                if any(x["type"][0]&32==0 and x["type"] not in KEEP for x in p):
                    raise ValueError("Unrecognized critical PNG data")
                if any(x["type"]==b"tRNS" for x in critical) and any(x["type"]==b"PLTE" for x in critical):
                    pass
                repaired=SIGNATURE+b"".join(x["blob"] for x in critical)
                staged=DEST/identity/(slot+".png")
                staged.parent.mkdir(parents=True,exist_ok=True)
                if staged.exists() and staged.read_bytes()!=repaired:
                    raise ValueError("Refusing to overwrite changed previously repaired container")
                if not staged.exists(): staged.write_bytes(repaired)
                with Image.open(staged) as im:
                    im.load()
                    if im.format!="PNG" or getattr(im,"n_frames",1)!=1 or not im.getbbox():
                        raise ValueError("Repaired PNG could not decode actual artwork")
                    size=list(im.size)
                    rgba=im.convert("RGBA")
                    px_sha=hashhex(rgba.tobytes())
                item.update(status="RECOVERED_ORIGINAL_PIXEL_STREAM",
                            repaired_source=str(staged.relative_to(ROOT)),
                            repaired_sha256=hashhex(repaired),
                            png_pixel_rgba_sha256=px_sha,
                            original_canvas=size,
                            retained_chunks=[{"type":x["type"].decode("ascii"),"bytes":len(x["blob"])} for x in critical],
                            stripped_ancillary=[{"type":x["type"].decode("ascii",errors="replace"),
                                                 "bytes":len(x["blob"]), "crc_ok":x["crc_ok"]}
                                                for x in p if x["type"] not in KEEP],
                            unchanged_compressed_IDAT=True,
                            warning="Unmodified pixel stream. Ancillary profile/metadata stripped: visually inspect source colors.",
                            gameIntegrationAllowed=False)
            except (ValueError,OSError,struct.error,zlib.error) as exc:
                item.update(status="BLOCKED_ORIGINAL_PIXEL_STREAM_UNRECOVERABLE",
                            error=str(exc),gameIntegrationAllowed=False)
            result.append(item)
    manifest={"schema":"mercury-original-png-container-triage-v1","sourceLedger":str(SOURCE.relative_to(ROOT)),
              "originalApprovedFilesNeverModified":True,
              "artRedrawn":False,"ROMIntegrationAllowed":False,
              "records":result,
              "counts":{"recovered":sum(x["status"].startswith("RECOVERED") for x in result),
                        "unresolved":sum(x["status"].startswith("BLOCKED") for x in result)}}
    name=DEST/"recovery_manifest.json"
    name.write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf8")
    print(json.dumps(manifest["counts"]))
    for row in result:print(row["identity"],row["slot"],row["status"],row.get("error",""))
if __name__=="__main__":main()
