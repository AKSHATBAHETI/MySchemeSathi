import json

# Load the original final.json
with open('final.json', 'r', encoding='utf-8') as f:
    schemes = json.load(f)

# Create scheme_master (lookup table)
scheme_master = []
# Create scheme_details (full details)
scheme_details = []

for idx, scheme in enumerate(schemes, start=1):
    # Master table: id and scheme_name
    master_entry = {
        "scheme_id": idx,
        "scheme_name": scheme.get("scheme_name", "")
    }
    scheme_master.append(master_entry)
    
    # Details table: id and all other information
    details_entry = {
        "scheme_id": idx,
        "state": scheme.get("state", ""),
        "objective": scheme.get("objective", ""),
        "tags": scheme.get("tags", []),
        "benefits": scheme.get("benefits", []),
        "eligibility": scheme.get("eligibility", []),
        "documents_required": scheme.get("documents_required", []),
        "source_url": scheme.get("source_url", "")
    }
    scheme_details.append(details_entry)

# Save scheme_master.json
with open('scheme_master.json', 'w', encoding='utf-8') as f:
    json.dump(scheme_master, f, ensure_ascii=False, indent=2)

# Save scheme_details.json
with open('scheme_details.json', 'w', encoding='utf-8') as f:
    json.dump(scheme_details, f, ensure_ascii=False, indent=2)

print(f"✓ Created scheme_master.json with {len(scheme_master)} schemes")
print(f"✓ Created scheme_details.json with {len(scheme_details)} schemes")
