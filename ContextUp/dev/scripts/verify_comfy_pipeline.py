
import sys
import time
from pathlib import Path

# Add src to path
project_root = Path(__file__).resolve().parents[3]
src_path = project_root / "ContextUp" / "src"
sys.path.append(str(src_path))

from manager.helpers.comfyui_client import ComfyUIManager
from features.comfyui import workflow_utils

def main():
    print("Testing ComfyUI Pipeline with Dummy Workflow...")
    
    # 1. Setup Client
    client = ComfyUIManager()
    if not client.start():
        print("❌ ComfyUI failed to start.")
        return

    # 2. Load Workflow
    wf_path = project_root / "ContextUp" / "assets" / "workflows" / "dummy_test.json"
    workflow = workflow_utils.load_workflow(wf_path)
    if not workflow:
        return

    # 3. Modify Workflow (Use a known image)
    # Finding "LoadImage" node
    load_node = workflow_utils.find_node_by_class(workflow, "LoadImage")
    if load_node:
        # We need a valid image in ComfyUI input folder? 
        # Or ComfyUI can read absolute paths if configured? 
        # Standard LoadImage usually expects name in Input folder.
        # Let's try uploading or copying 'example.png' to ComfyUI/input?
        # For this dummy test, let's assume 'example.png' exists or use a generated one.
        pass
    
    # Just checking connection by queuing
    # It might fail "LoadImage" but if we get that error, it proves pipeline active.
    
    try:
        # We expect this to fail on execution (Missing Image) but succeed in queuing
        print("Queuing workflow...")
        response = client.queue_prompt(workflow)
        print(f"Queue Response: {response}")
        
        # Wait a bit
        time.sleep(2)
        
    except Exception as e:
        print(f"Pipeline Error: {e}")
    finally:
        # DO NOT STOP for this test if we want to keep it running for user, 
        # but user asked validation.
        # client.stop() 
        pass

if __name__ == "__main__":
    main()
