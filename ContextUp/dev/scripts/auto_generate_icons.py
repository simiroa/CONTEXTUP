
import sys
import json
import io
import time
import os
import random
from pathlib import Path
from PIL import Image

# Add src to path
current_dir = Path(__file__).resolve().parent
src_dir = current_dir.parent.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.append(str(src_dir))

from manager.helpers.comfyui_client import ComfyUIManager
from utils import paths

# Set U2NET_HOME to use our local resources
os.environ["U2NET_HOME"] = str(paths.REMBG_DIR)

try:
    from rembg import remove
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False
    print("Warning: rembg not installed. Background removal will be skipped.")

def create_workflow_json(prompt, seed):
    return {
        "3": { "class_type": "KSampler", "inputs": { "seed": seed, "steps": 4, "cfg": 1.0, "sampler_name": "euler_ancestral", "scheduler": "simple", "denoise": 1, "model": ["10", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0] } },
        "5": { "class_type": "EmptyLatentImage", "inputs": {"width": 512, "height": 512, "batch_size": 1} },
        "6": { "class_type": "CLIPTextEncode", "inputs": { "text": f"{prompt}", "clip": ["12", 0] } },
        "7": { "class_type": "CLIPTextEncode", "inputs": { "text": "text, watermark, low quality, cropped, photo, realistic, complex, busy", "clip": ["12", 0] } },
        "8": { "class_type": "VAEDecode", "inputs": { "samples": ["3", 0], "vae": ["11", 0] } },
        "9": { "class_type": "SaveImage", "inputs": { "filename_prefix": "icon_gen_auto", "images": ["8", 0] } },
        "10": { "class_type": "UNETLoader", "inputs": { "unet_name": "z-image-turbo-fp8-e5m2.safetensors", "weight_dtype": "default" } },
        "11": { "class_type": "VAELoader", "inputs": { "vae_name": "ae.safetensors" } },
        "12": { "class_type": "CLIPLoader", "inputs": { "clip_name": "qwen_3_4b.safetensors", "type": "stable_diffusion" } }
    }

def main():
    print("Initializing ComfyUI Client...")
    client = ComfyUIManager()
    
    if not client.is_running():
        print("ComfyUI is not running. Attempting to start...")
        if not client.start():
            print("Failed to start ComfyUI.")
            return

    # Load Prompts
    prompts_file = current_dir.parent / "resources" / "icon_generation_prompts.json"
    if not prompts_file.exists():
        print(f"Error: Prompts file not found at {prompts_file}")
        return
        
    with open(prompts_file, "r", encoding="utf-8") as f:
        tasks = json.load(f)

    assets_dir = current_dir.parent.parent / "assets" / "icons"
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating {len(tasks)} icons...")
    
    for task in tasks:
        fname = task['filename']
        prompt = task['prompt']
        # Use simple hash of prompt for consistent seed, or random if you prefer variation
        seed = random.randint(1, 999999999) 
        
        print(f"\nProcessing {fname}...")
        print(f"  Prompt: {prompt}")
        print(f"  Seed: {seed}")
        
        try:
            workflow = create_workflow_json(prompt, seed)
            outputs = client.generate_image(workflow, output_node_id=9)
            
            if not outputs:
                print(f"  FAILED to generate image.")
                continue
                
            img_data = outputs[0]
            img = Image.open(io.BytesIO(img_data))
            
            # Post-Process: Remove BG -> Pad -> Save
            if REMBG_AVAILABLE:
                try:
                    print("  Removing background...")
                    img = remove(img)
                    bbox = img.getbbox()
                    if bbox: 
                        img = img.crop(bbox)
                except Exception as e:
                    print(f"  RemBG error: {e}")
            
            # Pad to square 256x256
            final_size = (256, 256)
            new_img = Image.new("RGBA", final_size, (0, 0, 0, 0))
            
            # Scale down to fit with padding (max 220px to leave margin)
            img.thumbnail((220, 220), Image.Resampling.LANCZOS)
            
            x = (final_size[0] - img.width) // 2
            y = (final_size[1] - img.height) // 2
            new_img.paste(img, (x, y), img)
            
            # Save ICO
            save_path = assets_dir / fname
            new_img.save(save_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
            print(f"  Saved ICO: {save_path}")
            
            # Save PNG fallback
            png_name = fname.replace(".ico", ".png")
            new_img.save(assets_dir / png_name)
            print(f"  Saved PNG: {assets_dir / png_name}")
            
        except Exception as e:
            print(f"  Error processing {fname}: {e}")
            
    print("\nAll tasks completed.")

if __name__ == "__main__":
    main()
