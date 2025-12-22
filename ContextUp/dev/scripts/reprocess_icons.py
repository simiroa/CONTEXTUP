import os
import sys
from pathlib import Path
from PIL import Image
try:
    from rembg import remove
except ImportError:
    print("Error: rembg not installed. pip install rembg")
    sys.exit(1)

def process_image(img_path):
    print(f"Processing: {img_path.name}")
    try:
        # Load original image
        img = Image.open(img_path).convert("RGBA")
        
        # 1. Ensure Background is Removed (Run rembg again to be sure)
        img = remove(img)
        
        # 2. Get Bounding Box (Crop Tight)
        bbox = img.getbbox()
        if bbox:
            # Crop to the content
            img_cropped = img.crop(bbox)
            
            # 3. Create new canvas
            # We want the icon to be as large as possible within 256x256 but with some padding
            # Let's say we want 240x240 max size for the content to leave 8px padding
            target_size = (256, 256)
            max_content_size = (248, 248) # Slight padding
            
            # Resize cropped content to fit within max_content_size while maintaining aspect ratio
            img_cropped.thumbnail(max_content_size, Image.Resampling.LANCZOS)
            
            # Create centered final image
            final_img = Image.new("RGBA", target_size, (0, 0, 0, 0))
            
            # Calculate center position
            x = (target_size[0] - img_cropped.width) // 2
            y = (target_size[1] - img_cropped.height) // 2
            
            final_img.paste(img_cropped, (x, y), img_cropped)
            
            # Save PNG
            final_img.save(img_path)
            
            # Save ICO
            ico_path = img_path.with_suffix('.ico')
            final_img.save(ico_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
            
            print(f"  -> Fixed margins for {img_path.name}")
            
    except Exception as e:
        print(f"  Error processing {img_path.name}: {e}")

def main():
    base_dir = Path(__file__).parent.parent
    icon_dir = base_dir / "assets" / "icons"
    
    if not icon_dir.exists():
        print("Icon directory not found.")
        return

    # Find all PNGs that correspond to our prompts (or just all PNGs in the folder)
    # We'll just process all PNGs in the folder to be safe/comprehensive
    png_files = list(icon_dir.glob("*.png"))
    
    print(f"Found {len(png_files)} icons to re-process.")
    
    for png in png_files:
        process_image(png)
        
    print("\n✅ Reprocessing Complete.")

if __name__ == "__main__":
    main()
