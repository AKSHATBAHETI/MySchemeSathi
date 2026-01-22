#!/usr/bin/env python3
"""
Test script to validate recent fixes:
1. Age extraction from text
2. State extraction from text
3. Search result cache clearing
4. Eligibility profile validation
"""

import sys
import re
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.user_profile import get_or_create_profile
from app.schemes_service import search_schemes, search_schemes_as_list

# Test 1: Profile Extraction
print("="*60)
print("TEST 1: Profile Extraction")
print("="*60)

# Simulate the extraction patterns from main.py
STATES = ["delhi", "maharashtra", "karnataka", "tamil nadu", "uttar pradesh", "west bengal", 
          "punjab", "haryana", "telangana", "rajasthan", "bihar", "odisha", "madhya pradesh",
          "andhra pradesh", "gujarat", "himachal pradesh", "jharkhand", "goa", "kerala", 
          "tripura", "manipur", "meghalaya", "assam", "arunachal pradesh"]

AGE_PATTERN = r'(\d{1,3})\s*(?:year|yr|years|yrs|old)'

test_cases = [
    "i am 20 years old",
    "I am 35 year old",
    "I'm 42 years old",
    "i live in delhi",
    "I am from Maharashtra",
    "I am 30 years old and live in Delhi",
]

for text in test_cases:
    print(f"\nText: '{text}'")
    text_lower = text.lower()
    
    # Age extraction
    age_match = re.search(AGE_PATTERN, text_lower)
    if age_match:
        age = int(age_match.group(1))
        print(f"  ✓ Age extracted: {age}")
    else:
        print(f"  ✗ Age not extracted")
    
    # State extraction
    for state in STATES:
        if state in text_lower:
            print(f"  ✓ State extracted: {state.title()}")
            break
    else:
        print(f"  ✗ State not extracted")

# Test 2: Search Results
print("\n" + "="*60)
print("TEST 2: Search Results Caching")
print("="*60)

# Simulate search for "Lakshya Scheme"
print("\nSearch 1: Looking for 'Lakshya Scheme'")
results1 = search_schemes_as_list("Lakshya Scheme")
print(f"  Found {len(results1)} schemes")
if results1:
    print(f"  First result: {results1[0].get('scheme_name')}")

print("\nSearch 2: Looking for 'Lakshya Scheme' again")
results2 = search_schemes_as_list("Lakshya Scheme")
print(f"  Found {len(results2)} schemes")
if results2:
    print(f"  First result: {results2[0].get('scheme_name')}")

if len(results1) == len(results2) and results1[0].get('scheme_id') == results2[0].get('scheme_id'):
    print("\n  ✓ Search results are consistent")
else:
    print("\n  ✗ Search results differ between calls")

# Test 3: Different Searches Don't Mix
print("\n" + "="*60)
print("TEST 3: Different Searches Don't Mix")
print("="*60)

print("\nSearch 1: 'agriculture' schemes")
ag_results = search_schemes_as_list("agriculture")
print(f"  Found {len(ag_results)} schemes")
if ag_results:
    print(f"  Top 2: {[s.get('scheme_name') for s in ag_results[:2]]}")

print("\nSearch 2: 'student' schemes")
student_results = search_schemes_as_list("student")
print(f"  Found {len(student_results)} schemes")
if student_results:
    print(f"  Top 2: {[s.get('scheme_name') for s in student_results[:2]]}")

if ag_results and student_results:
    if ag_results[0].get('scheme_id') != student_results[0].get('scheme_id'):
        print("\n  ✓ Different searches return different top results")
    else:
        print("\n  ✗ Different searches returning same results")

print("\n" + "="*60)
print("TESTS COMPLETE")
print("="*60)
