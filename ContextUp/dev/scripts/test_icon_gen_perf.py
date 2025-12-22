
import os
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from google import genai

# Add the current directory to sys.path so we can import generate_icons_ai
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.append(str(current_dir))

import generate_icons_ai

# User provided key
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("Error: GEMINI_API_KEY environment variable not set.")
    print("Please set it or provide it in the script temporarily (not recommended).")
    # For testing without env var, you will need to set it manually here, but do not commit it.
    sys.exit(1)

def test_performance(num_icons=1, workers=1):
    print(f"Starting performance test with {num_icons} icons and {workers} workers...")
    
    # 1. Setup
    client = genai.Client(api_key=API_KEY)
    
    # 2. Get Prompts (use a subset of real prompts)
    base_dir = Path(__file__).resolve().parents[2]
    md_path = base_dir / "assets" / "icons" / "PROMPTS.md"
    prompts = generate_icons_ai.parse_icons_md(md_path)
    
    # Slice first N prompts
    test_prompts = dict(list(prompts.items())[:num_icons])
    
    icon_dir = base_dir / "assets" / "icons" / "perf_test"
    icon_dir.mkdir(parents=True, exist_ok=True)
    
    # 3. Define Tasks
    tasks = []
    for icon_id, icon_data in test_prompts.items():
        out_path = icon_dir / icon_id
        tasks.append((icon_id, icon_data, out_path))
        
    start_time = time.time()
    
    # 4. Run Parallel Generation
    success_count = 0
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(generate_icons_ai.generate_single_icon, client, icon_id, icon_data, out_path): icon_id
            for icon_id, icon_data, out_path in tasks
        }
        
        for future in as_completed(futures):
            res = future.result()
            if res[0]: # Success
                success_count += 1
            else:
                print(f"Failed: {res[1]} - {res[2]}")

    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"\nTest Completed.")
    print(f"Total Time: {total_time:.2f} seconds")
    print(f"Total Icons: {success_count}/{num_icons}")
    if success_count > 0:
        avg_time_per_image_load = total_time / success_count
        throughput = success_count / total_time
        print(f"Average Time per Image (Load): {avg_time_per_image_load:.2f}s")
        print(f"Throughput: {throughput:.2f} images/sec")
        
        target_throughput = 0.5 # 1 image per 2 seconds
        if throughput >= target_throughput:
            print("✅ PASS: Throughput meets the target (>= 0.5 images/sec)")
        else:
            print(f"❌ FAIL: Throughput is too low ({throughput:.2f} < 0.5)")
    else:
        print("❌ FAIL: No images generated.")

if __name__ == "__main__":
    test_performance()
