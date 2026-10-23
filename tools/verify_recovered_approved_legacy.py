#!/usr/bin/env python3
"""Non-destructive checks for recovered, historically approved GBA-source sprite pairs."""
import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "review/recovered-approved-legacy-pairs-2026-10-23.json").read_text(encoding="utf-8"))
HISTORY = json.loads((ROOT / "audit/2026-10-23/historical-decisions.json").read_text(encoding="utf-8"))
REPAIR = json.loads((ROOT / "audit/2026-10-23/repair-queue.json").read_text(encoding="utf-8"))
GALLERY = (ROOT / "approved-legacy-recovery.html").read_text(encoding="utf-8")
CANONICAL = (ROOT / "master-review.html").read_text(encoding="utf-8")

assert DATA["schema"] == "mercury-recovered-approved-source-pairs-v1"
assert len(DATA["entries"]) == DATA["count"] == DATA["frontBackPairs"] == 74
assert DATA["policy"]["preserveExistingVotes"] and DATA["policy"]["noROMIntegration"]
assert DATA["policy"]["readOnly"] and DATA["policy"]["notAnApprovalPage"]
assert len({x["identity"] for x in DATA["entries"]}) == 74
originals = {x["id"]: x for x in HISTORY["entries"] if x["effective"] == "keep"}
legacy_holds = {x["identity"] for x in REPAIR["historicalApprovedMissingMappedPaths"]
                if x["resolution"] == "legacy-embedded"}
assert {x["identity"] for x in DATA["entries"]} == legacy_holds
missing_shinies = set()
file_count = 0
for entry in DATA["entries"]:
    original = originals[entry["identity"]]
    assert original["reviewId"] == entry["reviewId"]
    assert original["family"] == entry["family"]
    assert original["type1"] == entry["type1"] and original["type2"] == entry["type2"]
    assert entry["effectiveDecision"] == "keep" and entry["reviewRequired"] is False
    assert entry["artworkIntegrationAllowed"] is False
    assert entry["previewFormat"] == "original-GBA-artwork-not-DS-certified"
    for key in ("front", "back", "shinyFront", "shinyBack"):
        info = entry.get(key)
        if info is None:
            assert key in ("shinyFront", "shinyBack"), "Missing mandatory front/back"
            continue
        path = ROOT / info["path"]
        assert path.is_relative_to(ROOT)
        assert path.is_file(), str(path)
        assert path.stat().st_size == info["bytes"] and info["bytes"] >= 24, str(path)
        assert path.open("rb").read(8) == b"\\x89PNG\\r\\n\\x1a\\n", str(path)
        file_count += 1
    assert bool(entry["shinyFront"]) == bool(entry["shinyBack"])
    assert entry["missingShiny"] == (entry["shinyFront"] is None)
    if entry["missingShiny"]:
        missing_shinies.add(entry["identity"])
assert len(missing_shinies) == DATA["shinyIncomplete"] == 5
assert DATA["completeShinyQuartets"] == 69
assert DATA["linkedPNGFiles"] == file_count == 286
assert {"breloom-alternate-form-3", "combee-alternate-form-1", "vespiquen-alternate-form-1",
        "dwebble-alternate-form-1", "crustle-alternate-form-1"} == missing_shinies
assert "recovered-approved-legacy-pairs-2026-10-23.json" in GALLERY
assert "approved-legacy-recovery.html" in CANONICAL
assert "KEEP/CUT" in GALLERY and "not DS-certified" in GALLERY
print("PASS: 74 previously approved front/back source pairs; 69 complete shiny quartets")
print("PASS: 286 linked PNG files and five missing shiny sets recorded accurately")
print("PASS: Historical KEEP provenance and read-only/no-ROM-integration safety preserved")
