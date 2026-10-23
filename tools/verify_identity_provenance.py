#!/usr/bin/env python3
"""Assert that Mercury sprite identity metadata never overwrites saved artwork decisions."""
import json
import re
import subprocess
import tempfile
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
snapshot = json.loads((BASE / "master-review-data.json").read_text("utf-8"))
votes = json.loads((BASE / "review/user-iphone-decisions-2026-10-23.json").read_text("utf-8"))
raw_export = json.loads((BASE / "review/recovered-user-export-decisions-2026-10-23.json").read_text("utf-8"))
html = (BASE / "master-review.html").read_text("utf-8")
identity = snapshot.get("identityAudit", {})
entries = snapshot["entries"]
holds = snapshot["technicalHolds"]
all_items = entries + holds
ids = {item["id"] for item in all_items}


def verify(assertion, description):
    if not assertion:
        raise AssertionError(description)
    print("PASS:", description)


verify(snapshot["schema"] == "mercury-master-review-v1", "canonical review schema")
verify(votes["schema"] == "mercury-user-iphone-decisions-v1", "user iPhone export schema")
verify(len(votes["entries"]) == 166, "all 166 originally submitted iPhone votes preserved")
verify(sum(x["decision"] == "keep" for x in votes["entries"]) == 154, "154 user KEEP choices preserved")
verify(sum(x["decision"] == "cut" for x in votes["entries"]) == 12, "12 user CUT choices preserved")
verify(len(entries) == 158, "154 originally reviewed cards, 2 Wailmer/Wailord and 2 newly recovered Rainther source comparisons")
verify(len(holds) == 14, "14 technical cards remain after recovering two Rainther front/back pairs")
verify(len(ids) == len(all_items), "each active card has a stable unique ID")
original_voted_ids = {x["id"] for x in votes["entries"]}
actionable_ids = {x["id"] for x in entries}
new_ids = actionable_ids - original_voted_ids
authorized_new = {"reconcile:wailmer-alternate-form-1", "reconcile:wailord-alternate-form-1",
                  "compare:rainther:1", "compare:rainther:2"}
verify(new_ids == authorized_new, "newly reviewable choices limited to Wailmer/Wailord and recovered Rainther")
pairs = json.loads((BASE / "review/verified-exception-source-pairs-2026-10-23.json").read_text("utf-8"))
pair_by_id = {x["id"]: x for x in pairs["matches"]}
verify({"compare:rainther:1", "compare:rainther:2"} <= set(pair_by_id),
       "both Rainther front/back pairs are documented in source integrity ledger")
for x in entries:
    if x["id"] in new_ids:
        if x["id"].startswith("reconcile:wail"):
            verify(x.get("previewOnly") is True and "Reborn_Plates_Legacy" in x["front"] and x["back"],
                   "Wailmer source pair is present and explicitly marked unconverted: " + x["id"])
        else:
            evidence = pair_by_id[x["id"]]
            verify(x.get("previewOnly") is True and x.get("dsReady") is False and
                   x.get("type1") == "Water" and x["front"] == evidence["front"]["path"] and
                   x["back"] == evidence["back"]["path"],
                   "Rainther exact source art is paired but not DS-certified: " + x["id"])
verify(identity["flagged"] == 25, "original 25 source-label/family/identity exceptions retained in historical audit")
verify(sum(bool(x.get("identityFlag")) for x in all_items) == 5,
       "exactly five direct evolution-link conflicts remain unresolved in current master reviewer")
verify(identity["flaggedReviewEntries"] == 17 and identity["flaggedTechnicalHolds"] == 8, "original artist-name exception counts retained for audit history")
verify(all(x.get("originalSourceName") and "creator" in x and "identityFlag" in x for x in all_items), "original labels and creator fields preserved")
verify(all(x.get("displayName") for x in all_items), "every card retains a safe visible name")
verify(all(x.get("sourceReference","")=="" or x["sourceReference"].startswith("https://") for x in all_items), "external source references use HTTPS")
verify(all(x["displayName"].strip().lower() not in ("mikitarian","luminian") for x in all_items if x.get("identityFlag")), "artist and regional source labels are not asserted as species identities")
verify("!x.identityFlag" in html, "batch operations skip unverified artwork")
verify('<option value="pending" selected>' in html, "review opens on undecided families")
verify('VISIBLE_IDS.has(x.id)' in html, "bulk KEEP is restricted to the rendered page")
verify('x.previewOnly' in html, "original GBA artwork is explicitly marked as preview only")
verify('<option value="identity">' in html, "identity-only review section available")
verify("identityVerified" in html and "identityConfirmedAt" in html, "identity confirmations are tracked separately from KEEP/CUT")
verify("original_source_name" in html and "artist_credit" in html, "exports preserve both original source name and credited creator")
verify("uploadedDecisionSource" in html and "current.concat(prior)" in html, "earlier iPhone votes not in current review are retained on export")
verify(len(raw_export["exports"]) == 3, "previous DS and polished review CSV backups preserved")
with tempfile.TemporaryDirectory() as directory:
    scripts = re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>", html, re.I | re.S)
    verify(len(scripts) == 1, "single canonical reviewer script")
    js = Path(directory) / "canonical.js"
    js.write_text(scripts[0], "utf-8")
    result = subprocess.run(["node", "--check", str(js)], capture_output=True, text=True)
    verify(result.returncode == 0, "canonical reviewer JavaScript passes syntax check: " + result.stderr)
print("ALL Mercury sprite attribution and user-decision safeguards passed.")
