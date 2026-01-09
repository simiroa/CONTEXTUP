import os
import sys
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw

# Add src to path just in case
sys.path.append(str(Path("c:/Users/HG/Documents/HG_context_v2/ContextUp/src")))
from utils.external_tools import get_ffmpeg

BASE_DIR = Path("c:/Users/HG/Documents/HG_context_v2/ContextUp/dev/test_data")
IMG_DIR = BASE_DIR / "image"
VID_DIR = BASE_DIR / "video"
AUD_DIR = BASE_DIR / "audio"
DOC_DIR = BASE_DIR / "doc"

for d in [IMG_DIR, VID_DIR, AUD_DIR, DOC_DIR]:
    d.mkdir(parents=True, exist_ok=True)

ffmpeg = get_ffmpeg()

def create_images(count=5):
    print(f"Generating {count} test images...")
    for i in range(count):
        img = Image.new('RGB', (1920, 1080), color=(i*40, 100, 200))
        d = ImageDraw.Draw(img)
        d.text((10,10), f"Test Image {i}", fill=(255,255,255))
        img.save(IMG_DIR / f"test_img_{i}.jpg")

def create_videos(count=3):
    print(f"Generating {count} test videos...")
    if not ffmpeg:
        print("FFmpeg not found, skipping video gen")
        return
        
    for i in range(count):
        out = VID_DIR / f"test_vid_{i}.mp4"
        # Generate 1 second video
        cmd = [
            ffmpeg, "-f", "lavfi", "-i", "testsrc=duration=1:size=640x360:rate=30",
            "-f", "lavfi", "-i", "sine=frequency=1000:duration=1",
            "-c:v", "libx264", "-c:a", "aac", "-y", str(out)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def create_audio(count=3):
    print(f"Generating {count} test audio files...")
    if not ffmpeg: return
    for i in range(count):
        out = AUD_DIR / f"test_audio_{i}.wav"
        cmd = [
            ffmpeg, "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
            "-y", str(out)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if __name__ == "__main__":
    create_images()
    create_videos()
    create_audio()
    print("Test data generation complete.")
