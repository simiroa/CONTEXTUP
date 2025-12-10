import sys
import os
import time
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

try:
    from scripts.ui_finder_v2 import scan_worker
except ImportError as e:
    print(f"Import Error: {e}")
    # If script is run from root, src.scripts might work
    # But files are in src/scripts/ui_finder_v2.py
    # We are in C:\Users\HG\Documents\HG_context_v2
    pass

def status_print(msg):
    print(f"[STATUS] {msg}")

def run_test(target_path):
    print(f"--- Starting Performance Test on: {target_path} ---")
    start_time = time.time()
    
    # Test Mode: exact
    print("\n[Test 1] Mode: Exact Duplicates (Hash+Name)")
    groups = scan_worker(Path(target_path), "exact", status_callback=status_print)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"--- Scan Complete ---")
    print(f"Time Taken: {duration:.2f} seconds")
    print(f"Groups Found: {len(groups)}")
    for name, files in list(groups.items())[:5]:
        print(f"  Group: {name} ({len(files)} files)")
    
    # Test Mode: smart
    print("\n[Test 2] Mode: Smart Grouping (Ver/Seq)")
    start_time = time.time()
    groups = scan_worker(Path(target_path), "smart", status_callback=status_print)
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"--- Scan Complete ---")
    print(f"Time Taken: {duration:.2f} seconds")
    print(f"Groups Found: {len(groups)}")

if __name__ == "__main__":
    target = r"C:\Users\HG\Desktop\unyo\rd"
    if not os.path.exists(target):
        print(f"Target path not found: {target}")
    else:
        run_test(target)
