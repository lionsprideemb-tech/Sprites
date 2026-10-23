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
ORIGINAL_USER_EXPORTS = json.loads((ROOT / "review/recovered-user-export-decisions-2026-10-23.json").read_text(encoding="utf-8"))
USER_IPHONE_DECISIONS = json.loads((ROOT / "review/user-iphone-decisions-2026-10-23.json").read_text(encoding="utf-8"))
FAMILY_AUDIT = json.loads((ROOT / "review/family-regroup-audit-2026-10-23.json").read_text(encoding="utf-8"))
SOURCE_FAMILY_METADATA = json.loads((ROOT / "DS_CUSTOM_LIBRARY/DS_READY_MASTER/fakemon_enriched_metadata.json").read_text(encoding="utf-8"))

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
    require(0 < width <= 65535 and 0 < height <= 65535, "Invalid PNG dimensions: " + relative)
    require(max(width, height) <= 512 and max(width, height) / min(width, height) <= 5, "Unextracted animation strip in actionable review: " + relative)
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
require(len(history) == len({(x["reviewId"], x["id"]) for x in history}), "Duplicate historical review ID pairs")
require(len(HISTORY["identityCollisions"]) == SNAPSHOT["counts"]["historicalIdentityCollisions"], "Untracked historical ID collisions")
require(sum(1 for x in HISTORY["identityCollisions"] if x["conflictingDecision"]) == SNAPSHOT["counts"]["contradictoryIdentityCollisions"], "Untracked contradictory decisions")
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
require(ORIGINAL_USER_EXPORTS["schema"] == "mercury.sprite.review.user-exports.v1", "Unexpected recovered export format")
require(len(ORIGINAL_USER_EXPORTS["exports"]) == 3, "Missing recovered review export source")
require(SNAPSHOT["reconciledUserExport"]["designSelectionsRecovered"] == 10, "Recovered design decisions lost")
require(SNAPSHOT["reconciledUserExport"]["polishedKeepsRestored"] == 8, "Polished KEEP restoration lost")
require(len(REPAIR["resolvedByRecoveredUserExports"]["technicallyBlockedButAlreadyRejected"]) == 17, "Excluded previously rejected technical hold count changed")
require(len(HISTORY["userExportReconciliation"]["designReviewAlreadyDecided"]) == 10, "Design decision evidence lost")
recovered_review_ids = {x["reviewId"] for x in HISTORY["userExportReconciliation"]["designReviewAlreadyDecided"]}
require(not recovered_review_ids.intersection({x["id"] for x in entries}), "Old approved/rejected art appeared as an undecided choice")
for restored in HISTORY["userExportReconciliation"]["supersededHistoricalRejections"]:
    require(any(x["reviewId"] == restored["reviewId"] and x["effective"] == "keep" for x in history),
            "Restored polished approval not retained: " + restored["id"])


require(USER_IPHONE_DECISIONS["schema"] == "mercury-user-iphone-decisions-v1", "User decision export schema mismatch")
require(USER_IPHONE_DECISIONS["count"] == 166, "Original 166 user choices lost")
require(USER_IPHONE_DECISIONS["keepCount"] == 154 and USER_IPHONE_DECISIONS["cutCount"] == 12, "Vote tally mismatch")
require(USER_IPHONE_DECISIONS["sourceSHA256"] == "a0a00a257359449b034ac012b73676c8a24c13b05f190d96fb963bb26619718b", "User upload evidence changed")
require(len({x["id"] for x in USER_IPHONE_DECISIONS["entries"]}) == 166, "Duplicate ID in user submitted votes")
require(len(USER_IPHONE_DECISIONS["historicalVoteDisagreements"]) == 4, "Later Mega art changes not preserved")
require(FAMILY_AUDIT["schema"] == "mercury-family-regroup-v1", "Family audit schema mismatch")
require(len(FAMILY_AUDIT["corrections"]) == 15, "Unexpected source-family correction count")
require(SNAPSHOT["familyGrouping"]["schema"] == "mercury-evolution-family-grouping-v2", "Wrong family grouping version")
require(SNAPSHOT["familyGrouping"]["sourceBlob"] == FAMILY_AUDIT["sourceBlob"], "Family grouping source mismatch")
by_front_back = {(x["front_path"], x["back_path"]): x for x in SOURCE_FAMILY_METADATA["entries"].values()
                 if x.get("ready_for_approval") and x.get("front_path") and x.get("back_path")}
for entry in entries:
    if entry["category"] == "fakemon":
        authoritative = by_front_back.get((entry["front"], entry["back"]))
        require(authoritative is not None, "Source-evidence missing for Fakemon: " + entry["id"])
        require(entry["name"] == authoritative["name"], "Name drift in " + entry["id"])
        require(entry["family"] == authoritative["family"], "Family split in " + entry["id"])
    require(isinstance(entry.get("evolutionStageOrder"), int), "Stage order missing: " + entry["id"])
uploaded_by_id = {x["id"]: x for x in USER_IPHONE_DECISIONS["entries"]}
require({x["id"] for x in entries}.issubset(uploaded_by_id), "New reviewed sprite ID omitted from user votes")
for entry in entries:
    original = uploaded_by_id[entry["id"]]
    require(original["front_path"] == entry["front"] and original["back_path"] == entry["back"],
            "Stable sprite identity no longer matches its recorded user vote: " + entry["id"])
require("user-iphone-decisions-2026-10-23.json" in HTML and "familyMatches" in HTML and "evolutionStageOrder" in HTML,
        "Family-aware review and saved votes not wired into mobile page")

historical_by_id = {x["id"]: x for x in history}
dims = Counter()
large = []
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
        if max(size) > 512 or max(size) / min(size) > 5:
            large.append((entry["id"], side, entry[side], size))
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
print("Oversized/spritesheet candidate files:")
for item in large:
    print("OVERSIZE_CANDIDATE:", item)
print("No assets modified or deleted.")
