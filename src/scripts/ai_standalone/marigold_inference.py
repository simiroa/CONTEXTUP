import torch
import numpy as np
import argparse
from PIL import Image
from diffusers import MarigoldDepthPipeline, MarigoldNormalsPipeline, MarigoldIntrinsicsPipeline
import sys
import os
from pathlib import Path

# Suppress HF warnings
import warnings
warnings.filterwarnings("ignore")

# Allow large images (disable decompression bomb check)
Image.MAX_IMAGE_PIXELS = None

def main():
    parser = argparse.ArgumentParser(description="Marigold PBR Inference")
    parser.add_argument("input_image", help="Path to input image")
    parser.add_argument("--depth", action="store_true", help="Generate Depth Map")
    parser.add_argument("--normal", action="store_true", help="Generate Normal Map")
    parser.add_argument("--albedo", action="store_true", help="Generate Albedo Map")
    parser.add_argument("--roughness", action="store_true", help="Generate Roughness Map")
    parser.add_argument("--metallicity", action="store_true", help="Generate Metallicity Map")
    parser.add_argument("--orm", action="store_true", help="Generate Packed ORM Map (R=Occlusion, G=Roughness, B=Metallicity)")
    parser.add_argument("--res", type=int, default=768, help="Processing resolution (0 for native)")
    parser.add_argument("--ensemble", type=int, default=1, help="Ensemble size")
    parser.add_argument("--flip_y", action="store_true", help="Flip Normal Y Channel (DirectX)")
    parser.add_argument("--invert_roughness", action="store_true", help="Invert Roughness to Smoothness")
    parser.add_argument("--steps", type=int, default=10, help="Inference steps")
    parser.add_argument("--model_version", type=str, default="v1-1", help="Model version (v1-0 or v1-1)")
    parser.add_argument("--fp16", action="store_true", help="Use Half Precision")
    
    args = parser.parse_args()
    
    input_path = Path(args.input_image)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)
        
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if args.fp16 and device == "cuda" else torch.float32
    
    print(f"Device: {device}, Dtype: {dtype}")
    print(f"Settings: Version={args.model_version}, Steps={args.steps}, Ensemble={args.ensemble}, Res={args.res if args.res > 0 else 'Native'}")
    
    # Load Input
    img = Image.open(input_path)
    
    # Check Resolution Logic
    # Marigold default is 768. If 0 is passed, we use None to enable native resolution processing (no resizing)
    proc_res = args.res if args.res > 0 else None
    
    generated_files = []

    # Helper to save output
    def save_output(data, path, mode="depth", flip_y=False):
        if not isinstance(data, np.ndarray):
            try:
                data = data.cpu().numpy()
            except:
                pass
                
        img_data = data
        
        # Normalize and Convert to uint8
        if mode == "depth":
            # Simple Min-Max normalization
            depth_min = img_data.min()
            depth_max = img_data.max()
            if depth_max - depth_min > 1e-6:
                img_data = (img_data - depth_min) / (depth_max - depth_min)
            
            img_data = (img_data * 255.0).astype(np.uint8)
            img_data = np.squeeze(img_data)
            
            if img_data.ndim > 2:
                 while img_data.ndim > 2: img_data = img_data[0]
            
            Image.fromarray(img_data, mode="L").save(path)
            
        elif mode == "normal" or mode == "albedo" or mode == "roughness" or mode == "metallicity" or mode == "orm":
            # RGB or Grayscale maps
            
            # Range check: If [-1, 1], map to [0, 1]
            if img_data.min() < 0:
                 img_data = (img_data + 1.0) / 2.0
            
            # Clip [0, 1] -> [0, 255]
            img_data = (img_data * 255.0).clip(0, 255).astype(np.uint8)
            
            # Squeeze
            img_data = np.squeeze(img_data)
            
            # Handle Channel First (3, H, W) -> (H, W, 3)
            if img_data.ndim == 3:
                if img_data.shape[0] == 3 and img_data.shape[2] != 3:
                    img_data = img_data.transpose(1, 2, 0)
            
            # Check for Grayscale 1-channel logic
            mode_pil = "RGB"
            if mode in ["roughness", "metallicity"]:
                if img_data.ndim == 2:
                    mode_pil = "L"
                elif img_data.ndim == 3 and img_data.shape[2] == 1:
                    img_data = img_data.squeeze(2)
                    mode_pil = "L"
            
            # Flip Y for Normal Map
            if mode == "normal" and flip_y:
                if img_data.ndim == 3 and img_data.shape[2] == 3:
                    img_data[:, :, 1] = 255 - img_data[:, :, 1]
                    print("Applied Flip Y to Normal Map")

            Image.fromarray(img_data, mode=mode_pil).save(path)

    try:
        # 1. Depth
        if args.depth:
            ckpt = "prs-eth/marigold-depth-v1-1" if args.model_version == "v1-1" else "prs-eth/marigold-depth-v1-0"
            print(f"Loading Depth Model ({ckpt})...")
            
            pipe = MarigoldDepthPipeline.from_pretrained(
                ckpt,
                torch_dtype=dtype,
                variant="fp16" if args.fp16 else None
            ).to(device)
            print("Running Depth Inference...")
            out = pipe(img, processing_resolution=proc_res, ensemble_size=args.ensemble, num_inference_steps=args.steps)
            out_path = input_path.with_name(f"{input_path.stem}_depth.png")
            save_output(out.prediction, out_path, "depth")
            print(f"Saved: {out_path}")
            del pipe; torch.cuda.empty_cache()

        # 2. Normal
        if args.normal:
            ckpt = "prs-eth/marigold-normals-v1-1" if args.model_version == "v1-1" else "prs-eth/marigold-normals-v0-1"
            print(f"Loading Normal Model ({ckpt})...")
            
            pipe = MarigoldNormalsPipeline.from_pretrained(
                ckpt,
                torch_dtype=dtype,
                variant="fp16" if args.fp16 else None
            ).to(device)
            print("Running Normal Inference...")
            out = pipe(img, processing_resolution=proc_res, ensemble_size=args.ensemble, num_inference_steps=args.steps)
            out_path = input_path.with_name(f"{input_path.stem}_normal.png")
            save_output(out.prediction, out_path, "normal", flip_y=args.flip_y)
            print(f"Saved: {out_path}")
            del pipe; torch.cuda.empty_cache()

        # 3. IID (Appearance: Albedo, Roughness, Metallicity, ORM)
        if args.albedo or args.roughness or args.metallicity or args.orm:
            ckpt = "prs-eth/marigold-iid-appearance-v1-1"
            print(f"Loading IID Appearance Model ({ckpt})...")
            pipe = MarigoldIntrinsicsPipeline.from_pretrained(
                ckpt,
                torch_dtype=dtype,
                variant="fp16" if args.fp16 else None
            ).to(device)
            
            print("Running IID Inference...")
            out = pipe(img, processing_resolution=proc_res, ensemble_size=args.ensemble, num_inference_steps=args.steps)
            
            # Process Output
            try:
                pred = out['prediction']
                if not isinstance(pred, np.ndarray): pred_np = pred.cpu().numpy()
                else: pred_np = pred
                
                if pred_np.ndim == 4 and pred_np.shape[0] == 1:
                    pred_np = pred_np.squeeze(0)
                
                if pred_np.shape[0] == 2 and pred_np.ndim == 4:
                    comp0 = pred_np[0] # Albedo
                    comp1 = pred_np[1] # Material
                    
                    if args.albedo:
                        save_output(comp0, input_path.with_name(f"{input_path.stem}_albedo.png"), "albedo")
                        print(f"Saved: {input_path.stem}_albedo.png")

                    if args.roughness:
                        r_data = comp1[:, :, 0]
                        if args.invert_roughness:
                            # Invert: Roughness -> Smoothness
                            if r_data.min() < 0:
                                r_data = (r_data + 1.0) / 2.0
                            r_data = 1.0 - r_data
                            out_name = f"{input_path.stem}_smoothness.png"
                        else:
                            out_name = f"{input_path.stem}_roughness.png"
                        save_output(r_data, input_path.with_name(out_name), "roughness")
                        print(f"Saved: {out_name}")

                    if args.metallicity:
                        save_output(comp1[:, :, 1], input_path.with_name(f"{input_path.stem}_metallicity.png"), "metallicity")
                        print(f"Saved: {input_path.stem}_metallicity.png")
                        
                    if args.orm:
                        out_path = input_path.with_name(f"{input_path.stem}_orm.png")
                        r_raw = comp1[:, :, 0]
                        m_raw = comp1[:, :, 1]
                        
                        if r_raw.min() < 0: r_raw = (r_raw + 1.0) / 2.0
                        if m_raw.min() < 0: m_raw = (m_raw + 1.0) / 2.0
                        
                        r_uint8 = (r_raw * 255.0).clip(0, 255).astype(np.uint8)
                        m_uint8 = (m_raw * 255.0).clip(0, 255).astype(np.uint8)
                        o_uint8 = np.full(r_uint8.shape, 255, dtype=np.uint8)
                        
                        orm_stack = np.stack([o_uint8, r_uint8, m_uint8], axis=2)
                        Image.fromarray(orm_stack, mode="RGB").save(out_path)
                        print(f"Saved: {out_path}")
                        
            except Exception as e:
                print(f"Inference Error (IID Parsing): {e}")
            
            del pipe; torch.cuda.empty_cache()

    except Exception as e:
        print(f"Inference Error: {e}")
        sys.exit(1)

    print("Done.")

if __name__ == "__main__":
    main()
