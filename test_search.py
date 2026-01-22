#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test scheme search functionality"""
import sys
sys.path.insert(0, 'd:\\myscheme-telegram-bot')

from app.schemes_service import (
    search_scheme_master_by_name,
    get_scheme_details_by_id,
    search_schemes,
    search_schemes_as_list
)

print("="*60)
print("TESTING SCHEME SEARCH")
print("="*60)

# Test 1: Search for "Lakshya Scheme"
print("\n[TEST 1] Searching for 'Lakshya Scheme'")
matching_ids = search_scheme_master_by_name("Lakshya Scheme")
print(f"Result: Found IDs {matching_ids}")

if matching_ids:
    for scheme_id in matching_ids:
        details = get_scheme_details_by_id(scheme_id)
        if details:
            print(f"  Scheme {scheme_id}: {details.get('scheme_name', 'Unknown')}")

# Test 2: Search and get formatted results
print("\n[TEST 2] Search formatted results")
results = search_schemes("Lakshya Scheme")
print(f"Formatted results:\n{results}")

# Test 3: Search as list
print("\n[TEST 3] Search as list")
list_results = search_schemes_as_list("Lakshya Scheme")
print(f"Found {len(list_results)} schemes")
for s in list_results[:2]:
    print(f"  - {s.get('scheme_name')}")

# Test 4: Test with partial match
print("\n[TEST 4] Partial match: 'Lakshya'")
matching_ids = search_scheme_master_by_name("Lakshya")
print(f"Result: Found IDs {matching_ids}")

# Test 5: Test with another scheme
print("\n[TEST 5] Search for 'Udyogini'")
matching_ids = search_scheme_master_by_name("Udyogini")
print(f"Result: Found IDs {matching_ids}")

print("\n" + "="*60)
print("TESTS COMPLETE")
print("="*60)
