#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, 'd:\\myscheme-telegram-bot')

from app.schemes_service import get_all_schemes

print("Testing bot startup logic...")

try:
    schemes = get_all_schemes()
    print(f"Loaded {len(schemes)} schemes")
    print("Bot startup would succeed!")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
