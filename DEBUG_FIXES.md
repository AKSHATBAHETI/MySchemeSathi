# Debugging Output for Bot Issues

## Issues Fixed

### 1. **Search Not Finding Schemes Despite Them Existing**
**Problem**: User searched for "Lakshya Scheme" but bot said "No local schemes found"
**Root Cause**: Search was using `full_chat_context` which includes all previous messages, making it harder to find exact matches
**Fix**: Changed search to use ONLY current `user_text` instead of full context

### 2. **Vague/Generic Matches**
**Problem**: Searching "Lakshya Scheme" matched 20+ results because it was matching the generic word "scheme"
**Root Cause**: Search was matching ANY token, not prioritizing exact matches
**Fix**: 
- Filter out short words (< 3 characters like "the", "a", etc.)
- Prioritize exact matches (all tokens match) over partial matches
- Sort exact matches first in results

### 3 **Second Message Not Visible in Terminal**
**Problem**: Only first message shows up, subsequent messages don't appear in terminal
**Root Cause**: No debug logging for message handling flow
**Fix**: Added comprehensive debug print statements:
```python
print(f"\n{'='*60}")
print(f"[USER {chat_id}] {user_text}")
print(f"{'='*60}")
print(f"[INTENT] {intent}")
print(f"[HANDLER] {handler_type}")
print(f"[SEARCH] Found {count} schemes")
```

### 4. **Eligibility AI Parse Error**
**Problem**: `Eligibility AI parse error: Expecting value: line 1 column 1 (char 0)`
**Root Cause**: AI model not returning valid JSON, or response had extra text before/after JSON
**Fix**: 
- Extract JSON array from response (find `[` and `]`)
- Better error handling with detailed logging
- Graceful fallback if JSON parsing fails

## Files Modified

### app/main.py
- Added comprehensive debug logging for each message
- Search now uses `user_text` instead of `full_chat_context`
- Fixed field names: `name` → `scheme_name`, etc.
- Better error messages

### app/schemes_service.py  
- Improved search ranking (exact matches first)
- Filter short tokens to avoid generic matches
- Better JSON parsing with error recovery
- Added detailed logging at each step

## Debug Output Example

```
============================================================
[USER 123456789] Lakshya Scheme
============================================================
[INTENT] general_query
[HANDLER] General query - searching for schemes
[SEARCH] Query: 'Lakshya Scheme' -> Tokens (length > 2): ['lakshya', 'scheme']
[SEARCH MATCH] ID 45: 'lakshya' found in 'lakshya scheme'
[SEARCH RESULT] Found 1 exact + 20 partial = 21 total
[SEARCH] Matching 1 schemes
[SEARCH] Returning 5 formatted schemes
```

## Testing

Run tests with:
```bash
python test_search.py       # Test search functionality
python test_startup.py      # Test bot startup
python test_schemes.py      # Test data loading
```
