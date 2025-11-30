"""
Texture Generation & PBR Tools using CV2 and Gemini.
"""
import sys
import argparse
import os
import cv2
import numpy as np
from pathlib import Path
import google.generativeai as genai
from PIL import Image

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent
sys.path.append(str(src_dir))

from core.settings import load_settings

def setup_gemini():
    settings = load_settings()
    api_key = settings.get('GEMINI_API_KEY')
    if not api_key:
        print("Error: GEMINI_API_KEY not found in settings or environment.")
        return False
    genai.configure(api_key=api_key)
    return True

def make_tileable(image_path, overlap=0.1):
    """
    Make image tileable using synthesis (simple blending).
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            return False
            
        h, w = img.shape[:2]
        # Simple approach: Crop and blend edges
        # For a robust solution, we'd use patch-based synthesis, but let's do a simple cross-fade
        
        # This is a placeholder for a complex algorithm. 
        # For now, let's just output the original with a suffix to show flow.
        # In a real tool, we would implement proper boundary synthesis.
        
        # Let's do a simple mirror for now to ensure seamlessness (cheap trick)
        # img_tile = cv2.copyMakeBorder(img, 0, 0, 0, 0, cv2.BORDER_WRAP) # No, that's not it
        
        # Real synthesis is hard in one function. Let's skip complex synthesis for this iteration
        # and focus on PBR.
        print("Tileable generation not fully implemented yet.")
        return False
    except Exception as e:
        print(f"Error making tileable: {e}")
        return False

def generate_normal_map(img, strength=1.0):
    """Generate normal map from image intensity."""
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Invert if needed (assuming dark is deep)
    # gray = 255 - gray
    
    # Sobel gradients
    x_grad = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    y_grad = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    
    # Normalize
    z = np.ones_like(x_grad) * (1.0 / strength)
    
    # Stack
    normal = np.dstack((-x_grad, -y_grad, z))
    
    # Normalize vector
    norm = np.linalg.norm(normal, axis=2)
    normal = normal / norm[:, :, np.newaxis]
    
    # Map to 0-255
    normal = ((normal + 1) * 0.5 * 255).astype(np.uint8)
    
    # RGB -> BGR for OpenCV
    return cv2.cvtColor(normal, cv2.COLOR_RGB2BGR)

def generate_roughness_map(img):
    """Generate roughness map (inverted intensity usually)."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # High contrast
    roughness = cv2.equalizeHist(gray)
    # Invert: Dark (smooth) -> Light (rough) or vice versa depending on material
    # Let's assume lighter = rougher
    return roughness

def generate_pbr(image_path):
    """Generate PBR maps (Normal, Roughness, Displacement)."""
    try:
        img = cv2.imread(image_path)
        if img is None:
            print(f"Error loading {image_path}")
            return False
            
        path = Path(image_path)
        stem = path.stem
        parent = path.parent
        
        print(f"Generating PBR maps for {path.name}...")
        
        # 1. Normal Map
        normal = generate_normal_map(img, strength=2.0)
        cv2.imwrite(str(parent / f"{stem}_Normal.png"), normal)
        print(f"- Created {stem}_Normal.png")
        
        # 2. Roughness Map
        roughness = generate_roughness_map(img)
        cv2.imwrite(str(parent / f"{stem}_Roughness.png"), roughness)
        print(f"- Created {stem}_Roughness.png")
        
        # 3. Displacement (Height) - Just grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        cv2.imwrite(str(parent / f"{stem}_Displacement.png"), gray)
        print(f"- Created {stem}_Displacement.png")
        
        return True
    except Exception as e:
        print(f"Error generating PBR: {e}")
        return False

def analyze_texture(image_path):
    """Analyze texture using Gemini Vision."""
    if not setup_gemini():
        return False
        
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        img = Image.open(image_path)
        
        prompt = "Analyze this texture. Describe its material (e.g., wood, metal, fabric), pattern, and physical properties (roughness, reflectivity). Suggest PBR settings."
        
        response = model.generate_content([prompt, img])
        print("\n--- Texture Analysis ---")
        print(response.text)
        print("------------------------\n")
        return True
    except Exception as e:
        print(f"Error analyzing texture: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Texture Tools')
    parser.add_argument('image_path', help='Input image path')
    parser.add_argument('--action', choices=['pbr', 'analyze', 'tile'], required=True, help='Action to perform')
    
    args = parser.parse_args()
    
    if args.action == 'pbr':
        success = generate_pbr(args.image_path)
    elif args.action == 'analyze':
        success = analyze_texture(args.image_path)
    elif args.action == 'tile':
        success = make_tileable(args.image_path)
    else:
        success = False
        
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
