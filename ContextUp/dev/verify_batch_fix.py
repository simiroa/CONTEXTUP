import os
import sys
import threading
import time
from pathlib import Path

# Add src to path
current_script_path = Path(__file__).resolve()
src_dir = current_script_path.parent.parent / "src"
sys.path.append(str(src_dir))

from utils.batch_runner import collect_batch_context

def simulate_process(item_id, target_path, results):
    res = collect_batch_context(item_id, target_path)
    if res is not None:
        results.append((target_path, res))

def run_test(num_files=500):
    item_id = "test_batch"
    import tempfile
    test_dir = Path(tempfile.gettempdir()) / "ContextUp_BatchTest"
    test_dir.mkdir(exist_ok=True)
    
    # Clean old files
    for f in test_dir.glob("*.txt"):
        try: f.unlink()
        except: pass

    threads = []
    results = []
    
    print(f"--- Starting Simulation with {num_files} files ---")
    start_wall = time.time()
    
    # Windows menu grouping usually happens in batches of 15-16.
    # We simulate the number of PROCESSES that would be launched.
    num_processes = (num_files // 15) + (1 if num_files % 15 != 0 else 0)
    print(f"Simulating {num_processes} concurrent processes for {num_files} files...")

    for i in range(num_processes):
        # Each process has its own 'target'
        p = test_dir / f"test_proc_{i:03d}.txt"
        p.touch()
        t = threading.Thread(target=simulate_process, args=(item_id, str(p), results))
        threads.append(t)
    
    for t in threads:
        t.start()
        # Simulate delay between process launches (OS overhead)
        time.sleep(0.01) 
        
    for t in threads:
        t.join()
        
    end_wall = time.time()
    total_time = end_wall - start_wall
    
    print(f"\nResults:")
    print(f"Total 'Leader' processes: {len(results)}")
    print(f"Total time elapsed: {total_time:.2f}s")
    
    if len(results) == 1:
        leader_path, selection = results[0]
        print(f"SUCCESS: Only one leader found.")
        print(f"Batch size (processes): {len(selection)} (Expected: {num_processes})")
    else:
        print(f"FAILED: Found {len(results)} leaders.")

if __name__ == "__main__":
    import sys
    n = 500
    if len(sys.argv) > 1:
        try: n = int(sys.argv[1])
        except: pass
    run_test(n)
