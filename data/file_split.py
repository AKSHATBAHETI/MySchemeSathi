import json

INPUT_FILE = "final_sequential_ids.json"
MASTER_FILE = "scheme_master.json"
DETAILS_FILE = "scheme_details.json"

# Load original data
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    schemes = json.load(f)

master_table = []
details_table = []

for s in schemes:
    scheme_id = s["scheme_id"]

    # MASTER TABLE (ID + NAME ONLY)
    master_table.append({
        "scheme_id": scheme_id,
        "scheme_name": s.get("scheme_name")
    })

    # DETAILS TABLE (ALL OTHER DATA)
    details_table.append({
        "scheme_id": scheme_id,          # foreign key
        "state": s.get("state"),
        "objective": s.get("objective"),
        "tags": s.get("tags", []),
        "benefits": s.get("benefits", []),
        "eligibility": s.get("eligibility", []),
        "documents_required": s.get("documents_required", []),
        "source_url": s.get("source_url")
    })

# Write MASTER table
with open(MASTER_FILE, "w", encoding="utf-8") as f:
    json.dump(master_table, f, indent=2, ensure_ascii=False)

# Write DETAILS table
with open(DETAILS_FILE, "w", encoding="utf-8") as f:
    json.dump(details_table, f, indent=2, ensure_ascii=False)

print("✅ Split completed successfully")
print("📁 Created:", MASTER_FILE)
print("📁 Created:", DETAILS_FILE)
