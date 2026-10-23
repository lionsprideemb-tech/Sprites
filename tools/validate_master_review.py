#!/usr/bin/env python3
"""Validate the non-destructive Mercury Redux sprite-review snapshot.

Standard library only; does not write to or alter the sprite library.
Run from repo root: python3 tools/validate_master_review.py
"""
from collections import Counter
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = json.loads((ROOT / "master-review-data.json").read_text(encoding="utf-8"))
HISTORY = json.loads((ROOT / "audit/2026-10-23/historical-decisions.json").read_text(encoding="utf-8"))
REPAIR = json.loads((ROOT / "audit/2026-10-23/repair-queue.json").read_text(encoding="utf-8"))
HTML = (ROOT / "master-review.html").read_text(encoding="utf-8")

def require(value, explanation):
    if not value:
        raise AssertionError(explanation)

def safe_file(relative):
    require(relative and not Path(relative).is_absolute(), "Missing or absolute sprite path: " + str(relative))
    path = (ROOT / relative).resolve()
    require(path.is_relative_to(ROOT), "Path escapes repository: " + relative)
    require(path.is_file(), "Sprite not tracked in checkout: " + relative)
    with path.open("rb") as handle:
        header = handle.read(24)
    require(header[:8] == b"\x89PNG\r\n\x1a\n" and header[12:16] == b"IHDR",
            "Invalid PNG header: " + relative)
    width, height = struct.unpack(">II", header[16:24])
    require(0 < width <= 4096 and 0 < height <= 4096, "Implausible PNG dimensions: " + relative)
    return (width, height)

require(SNAPSHOT["schema"] == "mercury-master-review-v1", "Unexpected snapshot schema")
require(HISTORY["schema"] == "mercury-historical-decision-ledger-v1", "Unexpected ledger schema")
require(REPAIR["schema"] == "mercury-sprite-repair-queue-v1", "Unexpected repair schema")
require(REPAIR["destructiveActionsTaken"] == 0, "Unexpected destructive-action marker")
entries = SNAPSHOT["entries"]
technical = SNAPSHOT["technicalHolds"]
history = HISTORY["entries"]
ids = [x["id"] for x in entries]
require(len(ids) == len(set(ids)), "Duplicate actionable review IDs")
require(len(history) == len({x["id"] for x in history}), "Duplicate historical identity IDs")
require(len(history) == SNAPSHOT["counts"]["historical"], "Historical count mismatch")
require(len(entries) == SNAPSHOT["counts"]["actionable"], "Actionable count mismatch")
require(len(technical) == SNAPSHOT["counts"]["blocked"], "Hold count mismatch")
require(len(HISTORY["changedHistory"]) == SNAPSHOT["counts"]["changedGbaDecisions"], "Changed-decision count mismatch")
require(len(REPAIR["historicalApprovedMissingMappedPaths"]) > 0, "Historical sprite repair queue unexpectedly empty")
require(SNAPSHOT["counts"]["falseNewImportsMatchedHistory"] == 246, "Rejection-recovery regression")
require(SNAPSHOT["counts"]["distinctCompetingIdentities"] == 15, "Lost competing-design identities")
require("master-review-data.json" in HTML and "mercury-sprite-decisions-v1" in HTML,
        "Reviewer missing dataset or export format")
require("Backup / GitHub JSON" in HTML and "Export CSV" in HTML and "Restore progress" in HTML,
        "Reviewer missing required export/import controls")
require("localStorage" in HTML, "Reviewer missing persistent progress")

historical_by_id = {x["id"]: x for x in history}
dims = Counter()
categories = Counter()
for entry in entries:
    require(entry["family"] and entry["name"] and entry["source"], "Unresolved display metadata: " + entry["id"])
    require(entry["type1"] and entry["typeAuthority"] != "Unverified", "Unverified type in review: " + entry["id"])
    require(entry["front"] != entry["back"], "Front and back alias: " + entry["id"])
    require(entry["id"] not in {x["id"] for x in technical}, "Review and repair queues overlap: " + entry["id"])
    older = historical_by_id.get(entry["identity"])
    require(older is None or entry["category"] == "decision-conflict",
            "Historical decision incorrectly requeued: " + entry["id"])
    for side in ("front", "back"):
        size = safe_file(entry[side])
        dims[(side, size)] += 1
    categories[entry["category"]] += 1

for entry in technical:
    require(entry["holdReason"], "Technical hold is missing explanation: " + entry["id"])

print("PASS: Mercury sprite review snapshot")
print("Protected historical decisions:", len(history))
print("Actionable designs:", len(entries))
print("Technical holds:", len(technical))
print("Verified front/back PNGs:", len(entries) * 2)
print("Category counts:", dict(categories))
print("PNG dimension samples:", dict(dims.most_common(8)))
print("No assets modified or deleted.")
