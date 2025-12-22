
import sys
import os
import time
from pathlib import Path

# Setup Path
project_root = Path(__file__).resolve().parents[2] 
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

from manager.helpers.comfyui_client import ComfyUIManager
from features.comfyui import workflow_utils

def verify_z_image():
    print("🧪 Starting Z Image Turbo Verification...")
    
    # 1. Setup Client
    client = ComfyUIManager()
    if not client.start():
        print("❌ Failed to start ComfyUI")
        sys.exit(1)
        
    # 2. Load Workflow
    wf_path = project_root / "assets" / "workflows" / "z_image" / "turbo.json"
    print(f"📂 Loading workflow: {wf_path}")
    workflow = workflow_utils.load_workflow(wf_path)
    if not workflow:
        print("❌ Failed to load workflow")
        sys.exit(1)
        
    
    # Check execution format and convert if necessary
    if "nodes" in workflow:
        print("🔄 Detected Saved Workflow format. Converting to API format...")
        workflow = convert_to_api_format(workflow)
        
    # 3. Inject Parameters
    print("💉 Injecting Parameters...")
    prompt = "A futuristic cyberpunk city with neon lights, detailed, 8k"
    width = 512
    height = 512
    batch_size = 1
    seed = 12345
    steps = 1
    guidance = 1.0
    
    # Update Nodes (Using IDs from image_z_image_turbo.json)
    # 45: CLIPTextEncode (Positive)
    # 41: EmptySD3LatentImage
    # 44: KSampler
    # 35: (Wait, 35 was MarkdownNote in file view? flux guidance?)
    # Let's check file view again. 
    # ID 35 is MarkdownNote?
    # ID 6 was CLIPTextEncode (Pos) in "zimage workflow_example.json" BUT `turbo.json` (image_z_image_turbo) has ID 45.
    # The file I viewed (Step 807/825) has ID 45 as CLIPTextEncode.
    # ID 41 as EmptySD3LatentImage.
    # ID 44 as KSampler.
    # ID 35 is MarkdownNote.
    # ID 47 is ModelSamplingAuraFlow (Guidance?)
    # ID 6 is NOT present in the file view of turbo.json (Step 825).
    # Ah, the user provided `zimage workflow_example.json` (ID 6, 27, 31) BUT I copied `image_z_image_turbo.json` (ID 39, 40 ... 45, 44).
    # I MUST use the IDs from the FILE I COPIED (`turbo.json` / `image_z_image_turbo.json`).
    
    try:
        # Prompt (Node 45)
        workflow["45"]["inputs"]["text"] = prompt
        
        # Latent (Node 41)
        workflow["41"]["inputs"]["width"] = width
        workflow["41"]["inputs"]["height"] = height
        workflow["41"]["inputs"]["batch_size"] = batch_size
        
        # KSampler (Node 44)
        workflow["44"]["inputs"]["seed"] = seed
        workflow["44"]["inputs"]["steps"] = steps
        workflow["44"]["inputs"]["cfg"] = guidance # Assuming generic KSampler uses cfg
        
        print("✅ Parameters Injected.")
    except Exception as e:
        print(f"❌ Failed to inject parameters: {e}")
        sys.exit(1)

def convert_to_api_format(data):
    api = {}
    
    # Link Map
    links = {}
    for l in data.get("links", []):
         # [id, origin_id, origin_slot, target_id, target_slot, type]
         links[l[0]] = (str(l[1]), l[2])
         
    for node in data.get("nodes", []):
        node_id = str(node["id"])
        
        inputs = {}
        # Links
        if "inputs" in node:
            for inp in node["inputs"]:
                if inp.get("link"):
                    link_id = inp["link"]
                    if link_id in links:
                        inputs[inp["name"]] = list(links[link_id])
                        
        # Widgets to Inputs Mapping
        vals = node.get("widgets_values", [])
        if vals:
            ct = node["type"]
            if ct == "CLIPTextEncode":
                inputs["text"] = vals[0]
            elif ct == "EmptySD3LatentImage":
                inputs["width"] = vals[0]
                inputs["height"] = vals[1]
                inputs["batch_size"] = vals[2]
            elif ct == "KSampler":
                inputs["seed"] = vals[0]
                inputs["control_after_generate"] = vals[1]
                inputs["steps"] = vals[2]
                inputs["cfg"] = vals[3]
                inputs["sampler_name"] = vals[4]
                inputs["scheduler"] = vals[5]
                inputs["denoise"] = vals[6]
            elif ct == "SaveImage":
                inputs["filename_prefix"] = vals[0]
            elif ct == "CLIPLoader":
                 inputs["clip_name"] = vals[0]
                 inputs["type"] = vals[1] # lumina2
            elif ct == "VAELoader":
                 inputs["vae_name"] = vals[0]
            elif ct == "UNETLoader":
                 inputs["unet_name"] = vals[0]
                 inputs["weight_dtype"] = vals[1]
            elif ct == "LoraLoaderModelOnly":
                 inputs["lora_name"] = vals[0]
                 inputs["strength_model"] = vals[1]
                 
        api[node_id] = {
            "class_type": node["type"],
            "inputs": inputs
        }
        
    return api

    # 4. Execute
    print("🚀 Queueing Workflow...")
    try:
        outputs = client.generate_image(workflow)
        if outputs:
             print("✅ Execution Complete! Images received.")
        else:
             print("❌ Execution Failed: No images returned.")
             sys.exit(1)
             
    except Exception as e:
        print(f"❌ Execution Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_z_image()
