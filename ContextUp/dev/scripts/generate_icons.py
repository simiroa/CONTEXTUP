"""
Generate Dummy Icons for ContextUp Tools.
"""
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Define Tools and Colors
TOOLS = {
    "manager": {"color": "#2C3E50", "text": "M"},
    "gemini": {"color": "#8E44AD", "text": "AI"},
    "subtitle": {"color": "#E67E22", "text": "CC"},
    "texture": {"color": "#27AE60", "text": "TX"},
    "flatten": {"color": "#C0392B", "text": "FL"},
    "archive": {"color": "#F1C40F", "text": "AR"},
    "tray": {"color": "#3498DB", "text": "TR"},
    "youtube": {"color": "#E74C3C", "text": "YT"},
    "translator": {"color": "#1ABC9C", "text": "TL"},
    "mayo": {"color": "#95A5A6", "text": "MY"},
    "image_metadata": {"color": "#3498DB", "text": "EXIF"},
    "vectorizer": {"color": "#9B59B6", "text": "VEC"}
}

def generate_icons():
    # Output dir
    icon_dir = Path(__file__).parent.parent.parent / "assets" / "icons"
    icon_dir.mkdir(parents=True, exist_ok=True)
    
    size = (256, 256)
    
    for name, data in TOOLS.items():
        img = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Circle Background
        draw.ellipse((10, 10, 246, 246), fill=data['color'])
        
        # Text
        # Try to load a font, fallback to default
        try:
            font = ImageFont.truetype("arial.ttf", 120)
        except:
            font = ImageFont.load_default()
            
        text = data['text']
        
        # Center text (approximate)
        # PIL's textsize is deprecated/removed in newer versions, use textbbox
        try:
            left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
            w = right - left
            h = bottom - top
        except:
            w, h = 100, 100 # Fallback
            
        x = (size[0] - w) / 2
        y = (size[1] - h) / 2 - 20 # Adjust up slightly
        
        draw.text((x, y), text, font=font, fill="white")
        
        # Save as ICO and PNG
        icon_path = icon_dir / f"{name}.ico"
        png_path = icon_dir / f"{name}.png"
        
        img.save(png_path)
        img.save(icon_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
        
        print(f"Generated {name}.ico")

if __name__ == "__main__":
    generate_icons()
