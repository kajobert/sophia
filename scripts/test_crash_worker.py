#!/usr/bin/env python3
"""Test script that simulates worker crash for guardian testing."""
import sys
import time
import random

print("[TEST WORKER] Starting...")
print("[TEST WORKER] Working for a few seconds...")
time.sleep(3)

# Simulate crash
if random.random() > 0.5:
    print("[TEST WORKER] SIMULATED CRASH!")
    sys.exit(1)
else:
    print("[TEST WORKER] Normal exit")
    sys.exit(0)
