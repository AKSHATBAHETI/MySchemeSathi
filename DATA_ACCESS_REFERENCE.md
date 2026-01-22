# Quick Reference - Data Access Layer

## File Structure

```
data/
├── scheme_master.json      (Lookup: scheme_id → scheme_name)
└── scheme_details.json     (Details: scheme_id → full info)
```

## Function Overview

### Load Data
```python
from app.schemes_service import load_scheme_master, load_scheme_details

master = load_scheme_master()  # All scheme IDs and names
details = load_scheme_details()  # All scheme details by ID
```

### Search by Name
```python
from app.schemes_service import search_scheme_master_by_name, get_scheme_details_by_id

# Find scheme IDs matching a name
ids = search_scheme_master_by_name("Financial Assistance Marriage")
# Returns: [1]

# Get full details for that scheme
full_scheme = get_scheme_details_by_id(1)
```

### Search with Results Formatted
```python
from app.schemes_service import search_schemes

# Returns formatted string with matching schemes
result = search_schemes("Widow assistance")
```

### Get Eligible Schemes (AI-powered)
```python
from app.schemes_service import get_eligible_schemes_using_ai

user_info = "I am a widow from Delhi with income less than 1 lakh"
eligible = get_eligible_schemes_using_ai(user_info)
# Returns list of schemes user is eligible for
```

### Get All Schemes (Full Join)
```python
from app.schemes_service import get_all_schemes

all_schemes = get_all_schemes()
# Returns all 45 schemes with combined master + details data
```

## Data Schema

### scheme_master.json
```json
[
  {
    "scheme_id": 1,
    "scheme_name": "Financial Assistance For The Marriage Of Daughters Of Poor Widows And Orphan Girls"
  },
  ...
]
```

### scheme_details.json
```json
[
  {
    "scheme_id": 1,
    "state": "Delhi",
    "objective": "The scheme provides...",
    "tags": ["Financial Assistance", "Girl Child", ...],
    "benefits": ["One‑time ₹30,000 per daughter..."],
    "eligibility": ["Financial assistance can be granted...", ...],
    "documents_required": ["Recommendation letter...", ...],
    "source_url": "https://edistrict.delhigovt.nic.in/"
  },
  ...
]
```

## Key Points

✅ **Foreign Key**: scheme_id connects master and details tables  
✅ **Caching**: Both files are loaded once and cached in memory  
✅ **Complete Parsing**: All 45 schemes checked (no hard limits)  
✅ **Normalization**: No data duplication between files  
✅ **Field Mapping**:
   - scheme_name: Full scheme name
   - objective: Scheme description/purpose
   - source_url: Official scheme URL
   - eligibility: Array of eligibility criteria
   - tags: Array of category tags
   - benefits: Array of benefits
   - documents_required: Array of required documents

## Common Operations

### 1. User searches for a specific scheme
```
search_schemes("scheme name") → master lookup → foreign key join → return details
```

### 2. User asks about eligibility
```
get_eligible_schemes_using_ai("user profile") → eligibility match → get IDs → join names → return results
```

### 3. User wants PDF of eligible schemes
```
eligible_schemes = get_eligible_schemes_using_ai(...)
generate_schemes_pdf(eligible_schemes, ...)
```

### 4. Display matching schemes in chat
```
matched = search_schemes_as_list("query")
# Each item has: scheme_id, scheme_name, objective, source_url, tags, eligibility, ...
```
