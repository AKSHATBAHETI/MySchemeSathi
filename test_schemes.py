#!/usr/bin/env python
import sys
sys.path.insert(0, 'd:\\myscheme-telegram-bot')

from app.schemes_service import get_all_schemes, load_scheme_master, load_scheme_details

print("Testing scheme loading...")

try:
    master = load_scheme_master()
    print(f"✓ Loaded scheme_master.json: {len(master)} schemes")
except Exception as e:
    print(f"✗ Error loading master: {e}")

try:
    details = load_scheme_details()
    print(f"✓ Loaded scheme_details.json: {len(details)} schemes")
except Exception as e:
    print(f"✗ Error loading details: {e}")

try:
    all_schemes = get_all_schemes()
    print(f"✓ get_all_schemes(): {len(all_schemes)} schemes")
    if all_schemes:
        print(f"  First scheme: {all_schemes[0].get('scheme_name')}")
        print(f"  Last scheme: {all_schemes[-1].get('scheme_name')}")
except Exception as e:
    print(f"✗ Error getting all schemes: {e}")
    import traceback
    traceback.print_exc()
