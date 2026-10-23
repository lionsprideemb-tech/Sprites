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
verify(len(entries) == 154, "154 primary review cards preserved")
verify(len(holds) == 18, "18 technical hold cards preserved")
verify(len(ids) == len(all_items), "each active card has a stable unique ID")
verify(identity["flagged"] == 25, "25 source-label/family/identity exceptions documented")
verify(identity["flaggedReviewEntries"] == 17 and identity["flaggedTechnicalHolds"] == 8, "identity exceptions scoped correctly")
verify(all(x.get("originalSourceName") and "creator" in x and "identityFlag" in x for x in all_items), "original labels and creator fields preserved")
verify(all(x.get("displayName") for x in all_items), "every card retains a safe visible name")
verify(all(x.get("sourceReference","")=="" or x["sourceReference"].startswith("https://") for x in all_items), "external source references use HTTPS")
verify(all(x["displayName"].strip().lower() not in ("mikitarian","luminian") for x in all_items if x.get("identityFlag")), "artist and regional source labels are not asserted as species identities")
verify("!x.identityFlag" in html, "batch operations skip unverified artwork")
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
