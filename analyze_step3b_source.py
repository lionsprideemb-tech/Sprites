#!/usr/bin/env python3
"""
Pokemon Mercury Redux — Step 3B exact Elite Redux source analyzer.

Usage:
  python analyze_step3b_source.py \
    <SpeciesList.textproto> \
    <ER243_IMPORT_QUEUE.csv> \
    <mercury_source_root> \
    <output_dir>

This script does NOT modify Mercury source.
It extracts the exact 243 approved species/form blocks and audits all
SPECIES_/ABILITY_/MOVE_/ITEM_/TYPE_ dependencies against Mercury.
"""
from pathlib import Path
import pandas as pd
import re, json, sys, collections

if len(sys.argv) != 5:
    raise SystemExit(__doc__)

species_file = Path(sys.argv[1])
queue_file = Path(sys.argv[2])
mercury = Path(sys.argv[3])
out = Path(sys.argv[4])
out.mkdir(parents=True, exist_ok=True)

text = species_file.read_text(encoding="utf-8", errors="replace")
queue = pd.read_csv(queue_file)

def extract_species_blocks(src):
    blocks = []
    i = 0
    needle = "species {"
    while True:
        start = src.find(needle, i)
        if start < 0:
            break
        brace = src.find("{", start)
        depth = 0
        j = brace
        in_string = False
        escaped = False
        while j < len(src):
            ch = src[j]
            if in_string:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == '"':
                    in_string = False
            else:
                if ch == '"':
                    in_string = True
                elif ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        blocks.append(src[start:j+1])
                        j += 1
                        break
            j += 1
        i = j
    return blocks

blocks = extract_species_blocks(text)
by_id = {}
for block in blocks:
    m = re.search(r'(?m)^\s*id:\s*(SPECIES_[A-Z0-9_]+)\s*$', block)
    if m:
        by_id[m.group(1)] = block

approved = queue["internal_id"].astype(str).tolist()
missing_blocks = [x for x in approved if x not in by_id]
selected = {x: by_id[x] for x in approved if x in by_id}

# Collect constants defined anywhere in Mercury's include/constants headers.
def constants_from(path):
    if not path.exists():
        return set()
    s = path.read_text(errors="ignore")
    return set(re.findall(r'\b(?:SPECIES|ABILITY|MOVE|ITEM|TYPE)_[A-Z0-9_]+\b', s))

mercury_defs = set()
for p in (mercury / "include" / "constants").glob("*.h"):
    mercury_defs |= constants_from(p)

ref_patterns = {
    "species": r'\bSPECIES_[A-Z0-9_]+\b',
    "ability": r'\bABILITY_[A-Z0-9_]+\b',
    "move": r'\bMOVE_[A-Z0-9_]+\b',
    "item": r'\bITEM_[A-Z0-9_]+\b',
    "type": r'\bTYPE_[A-Z0-9_]+\b',
}

rows = []
all_refs = {k:set() for k in ref_patterns}
for _, q in queue.iterrows():
    iid = str(q["internal_id"])
    block = selected.get(iid, "")
    refs = {k: sorted(set(re.findall(pat, block))) for k,pat in ref_patterns.items()}
    for k,v in refs.items():
        all_refs[k].update(v)
    missing = sorted({x for vals in refs.values() for x in vals if x not in mercury_defs and x != iid})
    rows.append({
        "internal_id": iid,
        "source_name": q["source_name"],
        "mercury_story_name": q["mercury_story_name"],
        "delta_story_form": q["delta_story_form"],
        "source_block_found": bool(block),
        "species_refs": " | ".join(refs["species"]),
        "ability_refs": " | ".join(refs["ability"]),
        "move_refs": " | ".join(refs["move"]),
        "item_refs": " | ".join(refs["item"]),
        "type_refs": " | ".join(refs["type"]),
        "missing_mercury_constants": " | ".join(missing),
        "missing_count": len(missing),
    })

audit = pd.DataFrame(rows)
audit.to_csv(out / "ER243_SOURCE_COMPATIBILITY_AUDIT.csv", index=False)

# Exact selected source blocks, unmodified.
with (out / "ER243_SELECTED_SOURCE_BLOCKS.textproto").open("w", encoding="utf-8") as f:
    for iid in approved:
        if iid in selected:
            f.write("# ------------------------------------------------------------------\n")
            f.write(f"# {iid}\n")
            f.write("# ------------------------------------------------------------------\n")
            f.write(selected[iid])
            f.write("\n\n")

# Global missing refs by category.
missing_by_cat = {}
for cat, refs in all_refs.items():
    missing_by_cat[cat] = sorted(x for x in refs if x not in mercury_defs and x not in approved)

summary = {
    "species_blocks_in_source": len(blocks),
    "approved_requested": len(approved),
    "approved_blocks_found": len(selected),
    "approved_blocks_missing": missing_blocks,
    "entries_with_missing_mercury_dependencies": int((audit["missing_count"] > 0).sum()),
    "missing_dependencies_by_category": missing_by_cat,
}
(out / "ER243_SOURCE_COMPATIBILITY_SUMMARY.json").write_text(
    json.dumps(summary, indent=2), encoding="utf-8"
)

# Small human-readable report.
lines = [
    "POKEMON MERCURY REDUX — STEP 3B SOURCE COMPATIBILITY",
    "",
    f"Approved records requested: {len(approved)}",
    f"Exact source records found: {len(selected)}",
    f"Missing source records: {len(missing_blocks)}",
    f"Entries with at least one Mercury dependency gap: {summary['entries_with_missing_mercury_dependencies']}",
    "",
]
for cat, vals in missing_by_cat.items():
    lines.append(f"Missing {cat.upper()} constants: {len(vals)}")
(out / "ER243_SOURCE_COMPATIBILITY_REPORT.txt").write_text(
    "\n".join(lines) + "\n", encoding="utf-8"
)

print(json.dumps(summary, indent=2))
