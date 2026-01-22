# Bot Improvements - Summary of Fixes

## Issues Fixed

### 1. **Old Search Results Persisting Between Queries** ✅
**Problem:** When user searched for "Lakshya Scheme" and then searched for something else, old results would still show.

**Root Cause:** The `last_shown_schemes[chat_id]` cache was never cleared, so old results persisted.

**Fix:** Added cache clearing at the start of general query handler:
```python
# Clear old search results for this user
if chat_id in last_shown_schemes:
    del last_shown_schemes[chat_id]
    print(f"[SEARCH] Cleared old results for user {chat_id}")
```

**Result:** ✓ Each new search now starts fresh with no old results

---

### 2. **Incorrect Field Names in Number Selection Handler** ✅
**Problem:** When user selected a scheme by number, bot referenced wrong field names:
- Used `name` instead of `scheme_name`
- Used `raw_text` instead of `objective`
- Used `url` instead of `source_url`

**Fix:** Updated field names to match current JSON schema:
```python
# OLD:
f"{s['name']}\n\n{s.get('raw_text','')}\n\nURL: {s.get('url','')}"

# NEW:
f"{s['scheme_name']}\n\n{s.get('objective','')}\n\nURL: {s.get('source_url','')}"
```

**Result:** ✓ Scheme details now display correctly when user selects by number

---

### 3. **Profile Extraction Order** ✅
**Problem:** Profile extraction happened after intent detection, so some intents checked profile before it was populated.

**Fix:** Moved profile extraction to immediately after chat memory (before intent detection):
```python
# Extract info from CURRENT message FIRST
await extract_user_info_from_text(user_text, user_profile)

# Then detect intent
intent = await detect_intent(user_text)
```

**Result:** ✓ Profile is always populated before eligibility checks

---

## Profile Extraction Capabilities

The bot now extracts user information using regex patterns:

### Age Extraction
```python
Pattern: r'(\d{1,3})\s*(?:year|yr|years|yrs|old)'

Examples that work:
✓ "i am 20 years old" → age: 20
✓ "I am 35 year old" → age: 35
✓ "I'm 42 years old" → age: 42
✓ "I am 30 years old and live in Delhi" → age: 30
```

### State/Region Extraction
```python
STATES = ["delhi", "maharashtra", "karnataka", "tamil nadu", ...]

Examples that work:
✓ "i live in delhi" → state: Delhi
✓ "I am from Maharashtra" → state: Maharashtra
✓ "I am 30 years old and live in Delhi" → state: Delhi
```

### Gender Extraction
```python
Male keywords: "male", "man", "boy", "mr.", "he"
Female keywords: "female", "woman", "girl", "mrs.", "ms.", "she"

Examples:
✓ "I am a male student" → gender: Male
✓ "I am a girl from Delhi" → gender: Female
```

### Occupation Extraction
```python
Supported: "student", "farmer", "businessman", "employee", "doctor", 
           "engineer", "teacher", "nurse", "laborer", "self-employed", 
           "unemployed", "retired"

Examples:
✓ "I am a student" → occupation: Student
✓ "I am a farmer from Maharashtra" → occupation: Farmer
```

### Disability & Income Extraction
```python
Disability keywords: "disabled", "disability", "pwd", "physically challenged"
Income keywords: "poor", "low income", "below poverty", "bpl", 
                 "middle class", "medium income", "stable income"
```

---

## Eligibility Query Flow

### Before Requesting Schemes

1. **Extract user info** from their message using regex patterns
2. **Check if we have essential info**: age + state
3. **If missing info**: Ask user to provide it
4. **If we have info**: Call AI eligibility matcher with full profile

### Example Conversation

```
User: "i am 20 years old"
Bot: [Extracts age: 20]
Bot: "To find eligible schemes, I need your: state/region, occupation."

User: "I am a student from Delhi"
Bot: [Extracts state: Delhi, occupation: Student]
Bot: "Based on your profile (age 20, Delhi, student), here are eligible schemes:
     1. Scheme A
     2. Scheme B
     ..."
```

---

## Testing Results

### Test 1: Profile Extraction ✅
All regex patterns working correctly:
- Age extraction: 100% (all test cases passed)
- State extraction: 100% (all test cases passed)
- Gender extraction: Works
- Occupation extraction: Works

### Test 2: Search Consistency ✅
- Search 1: "Lakshya Scheme" → Found 10 schemes, top result: Lakshya Scheme
- Search 2: "Lakshya Scheme" again → Found 10 schemes, top result: Lakshya Scheme
- ✓ Results are consistent between calls

### Test 3: Different Searches Don't Mix ✅
- Search 1: "agriculture" → Found web results (no local matches)
- Search 2: "student" → Found 3 local schemes
- ✓ Different searches return completely different results
- ✓ No bleeding of old results

---

## Code Changes Summary

### File: `app/main.py`

**Changes:**
1. Moved `extract_user_info_from_text()` call right after chat memory (line ~208)
2. Added cache clearing in general query handler (line ~340-342)
3. Fixed field names in number selection handler (line ~237)

**Lines modified:**
- Line 208: Profile extraction moved up
- Line 237: Field names updated (`name` → `scheme_name`, etc.)
- Line 340-342: Cache clearing added

---

## Immediate Benefits

✅ **Consistency**: Users get same results when searching same query multiple times
✅ **Clarity**: Scheme details display with correct fields
✅ **Privacy**: Each user has their own isolated search cache
✅ **Intelligence**: Bot extracts age, state, occupation automatically from messages
✅ **Validation**: Bot asks for missing info before running AI eligibility checks

---

## Next Steps (Optional Enhancements)

1. **Enhanced Income Extraction**: Parse rupee amounts (e.g., "Rs 50,000" → income: 50000)
2. **Caste Detection**: Extract caste/category information if provided
3. **Disability Type**: Categorize types of disabilities
4. **Employment Status**: Extract employment type (employed, self-employed, etc.)
5. **Family Size**: Extract number of family members if mentioned
