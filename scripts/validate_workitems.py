import json
from collections import Counter

# load workitems
with open(".specsmith/workitems.json", encoding="utf-8") as f:
    work = json.load(f)
# load requirements to verify links
with open(".specsmith/requirements.json", encoding="utf-8") as f:
    reqs = json.load(f)
ids = [w["id"] for w in work]
miss = [f"WORK-{i:03d}" for i in range(1, 65) if f"WORK-{i:03d}" not in ids]
counts = Counter(ids)
dup = [k for k, v in counts.items() if v > 1]
# requirement mapping
req_ids = {r["id"] for r in reqs}
# verify each work item links to existing requirement
invalid_req = [w["requirement_id"] for w in work if w["requirement_id"] not in req_ids]
# verify each work item has at least one test_case_id
no_tests = [w["id"] for w in work if not w.get("test_case_ids")]
# check every requirement has a work item
req_no_work = [r for r in req_ids if r not in {w["requirement_id"] for w in work}]
print("work item count", len(work))
print("first ID", work[0]["id"])
print("last ID", work[-1]["id"])
print("missing IDs", miss)
print("duplicate IDs", dup)
print("invalid requirement links", invalid_req)
print("work items with no tests", no_tests)
print("requirements without work", req_no_work)
