
"""
Local Icon Generator using ComfyUI (Z-Image Turbo) + Rembg.
Replaces the old Cloud-based Gemini generator.

Features:
- Local High-Speed Generation (2-4s/image on GPU)
- Auto-Background Removal (rembg)
- .ICO and .PNG output
- Auto Start/Stop of ComfyUI Engine
"""
import argparse
import random
import time
import io
import re
import sys
from pathlib import Path
from PIL import Image

# Add src to path for module imports
project_root = Path(__file__).resolve().parents[3] # HG_context_v2
src_path = project_root / "ContextUp" / "src"
if src_path.exists():
    sys.path.append(str(src_path))

from manager.helpers.comfyui_client import ComfyUIManager

try:
    from rembg import remove
    REMBG_AVAILABLE = True
    print("✅ rembg imported")
except ImportError:
    REMBG_AVAILABLE = False
    print("⚠️ rembg not found. Background removal disabled.")

def parse_icons_md(md_path):
    """Parses ICONS.md table format to extract (id, prompt, category)."""
    prompts = {}
    if not md_path.exists():
        print(f"Error: {md_path} not found.")
        return prompts
        
    with open(md_path, 'r', encoding='utf-8') as f:
        for line in f:
            match = re.search(r"\|\s*`([^`]+\.ico)`\s*\|\s*([^|]+)\|\s*([^|]+)\|", line)
            if match:
                icon_id = match.group(1).strip()
                prompt = match.group(2).strip()
                category = match.group(3).strip()
                if icon_id not in prompts:
                    prompts[icon_id] = {
                        "prompt": prompt,
                        "category": category
                    }
    return prompts

def process_image(img):
    """Applies background removal and resizing."""
    if REMBG_AVAILABLE:
        img = remove(img)
        bbox = img.getbbox()
        if bbox:
            img = img.crop(bbox)

    # Resize to 256x256 (Center)
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    new_img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    img.thumbnail((256, 256), Image.Resampling.LANCZOS)
    x = (256 - img.width) // 2
    y = (256 - img.height) // 2
    new_img.paste(img, (x, y), img)
    return new_img

def create_workflow(prompt, seed, model_name="z_image_turbo.safetensors"):
    # Workflow optimized for Z-Image Turbo / SDXL Turbo
    # Validated Nodes: CheckpointLoaderSimple (if file exists) OR Split Loader
    
    # We use the Split Loader workflow since that matches the symlinked setup's files
    workflow = {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "seed": seed,
                "steps": 4, 
                "cfg": 1.0, 
                "sampler_name": "euler_ancestral",
                "scheduler": "simple",
                "denoise": 1,
                "model": ["10", 0], # From UNET
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0]
            }
        },
        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": 512,
                "height": 512,
                "batch_size": 1
            }
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": f"icon of {prompt}, 3d render, soft glassmorphism, neon glow, black background, minimal, 8k, best quality",
                "clip": ["12", 0] 
            }
        },
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "text, watermark, low quality, cropped, photo",
                "clip": ["12", 0]
            }
        },
        "8": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["3", 0],
                "vae": ["11", 0]
            }
        },
        "9": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": "icon_gen",
                "images": ["8", 0]
            }
        },
        "10": {
            "class_type": "UNETLoader",
            "inputs": {
                "unet_name": "z-image-turbo-fp8-e5m2.safetensors",
                "weight_dtype": "default"
            }
        },
        "11": {
            "class_type": "VAELoader",
            "inputs": {
                "vae_name": "ae.safetensors"
            }
        },
        "12": {
            "class_type": "CLIPLoader", 
            "inputs": {
                "clip_name": "qwen_3_4b.safetensors",
                "type": "stable_diffusion" 
            }
        }
    }
    return workflow

def main():
    parser = argparse.ArgumentParser(description="Generate Icons using local ComfyUI")
    parser.add_argument("--model", type=str, default="z_image_turbo.safetensors", help="Main model name (not used in split workflow, but kept for compat)")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of icons")
    parser.add_argument("--target", type=str, help="Generate only specific icon")
    args = parser.parse_args()

    # 1. Setup Client
    client = ComfyUIManager()
    if not client.start():
        print("❌ Could not start ComfyUI.")
        return

    # 2. Load Prompts
    base_dir = Path(__file__).resolve().parents[2] # ContextUp root
    md_path = base_dir / "assets" / "icons" / "PROMPTS.md"
    prompts = parse_icons_md(md_path)
    
    icon_dir = base_dir / "assets" / "icons"
    icon_dir.mkdir(parents=True, exist_ok=True)

    print(f"🚀 Generating Icons (Local Engine)...")

    count = 0
    start_time = time.time()
    
    try:
        for icon_id, icon_data in prompts.items():
            if args.target and args.target.lower() not in icon_id.lower():
                continue
                
            if args.limit and count >= args.limit:
                break
            
            # Check existing? (Optional: skip if exists)
            # if (icon_dir / icon_id).exists(): continue

            print(f"[{count+1}] Generating {icon_id}...")
            
            try:
                workflow = create_workflow(icon_data["prompt"], random.randint(1, 1000000000))
                images = client.generate_image(workflow, output_node_id=9)
                
                if images:
                    img_data = images[0]
                    
                    # Process (Rembg + Resize + Save)
                    try:
                        img = Image.open(io.BytesIO(img_data))
                        processed_img = process_image(img)
                        
                        # Save PNG
                        out_path = icon_dir / icon_id.replace(".ico", ".png")
                        processed_img.save(out_path)
                        
                        # Save ICO
                        ico_path = icon_dir / icon_id
                        processed_img.save(ico_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
                        
                        print(f"  ✓ Saved {icon_id}")
                    except Exception as e:
                        print(f"  ⚠️ Processing Error: {e}")
                        # Fallback save
                        with open(icon_dir / icon_id.replace(".ico", ".png"), "wb") as f:
                            f.write(img_data)
                        
                    count += 1
                else:
                    print(f"  ❌ Generation failed (No output)")
                    
            except Exception as e:
                print(f"  ❌ Error: {e}")
                # Critical errors stop the loop
                if "HTTP Error" in str(e):
                    break
                    
    finally:
        client.stop()

    total_time = time.time() - start_time
    print(f"\nDone. Generated {count} icons in {total_time:.2f}s.")

if __name__ == "__main__":
    main()
