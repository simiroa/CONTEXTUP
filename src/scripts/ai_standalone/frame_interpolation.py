"""
Frame interpolation using FFmpeg minterpolate filter.
Fast and reliable alternative to RIFE.
"""
import sys
import argparse
from pathlib import Path
import subprocess

# Add src to path to import utils
sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.external_tools import get_ffmpeg

def get_video_info(input_path):
    """Get video information using FFprobe."""
    ffmpeg = get_ffmpeg()
    ffprobe = ffmpeg.replace("ffmpeg.exe", "ffprobe.exe")
    
    if not Path(ffprobe).exists():
        # Fallback to system ffprobe if not found next to ffmpeg
        ffprobe = "ffprobe"
    
    cmd = [
        ffprobe,
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=r_frame_rate,width,height",
        "-of", "default=noprint_wrappers=1",
        str(input_path)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')
        
        info = {}
        for line in lines:
            if '=' in line:
                key, value = line.split('=')
                info[key] = value
        
        # Parse FPS
        if 'r_frame_rate' in info:
            num, den = info['r_frame_rate'].split('/')
            if float(den) > 0:
                fps = float(num) / float(den)
                info['fps'] = fps
            else:
                info['fps'] = 30.0
        
        return info
    except Exception as e:
        print(f"Warning: Failed to get video info: {e}")
        return {'fps': 30.0, 'width': 0, 'height': 0}

def interpolate_video_ffmpeg(input_path, output_path, target_fps=60, method="mci"):
    """
    Interpolate video frames using FFmpeg.
    """
    ffmpeg = get_ffmpeg()
    
    print(f"Using FFmpeg: {ffmpeg}")
    
    # Get input video info
    info = get_video_info(input_path)
    input_fps = info.get('fps', 30)
    width = info.get('width', 'unknown')
    height = info.get('height', 'unknown')
    
    print(f"Input: {input_fps:.2f} FPS, {width}x{height}")
    print(f"Target: {target_fps} FPS")
    print(f"Method: {method.upper()}")
    
    # Build FFmpeg command
    if method == "mci":
        # Motion Compensated Interpolation (best quality)
        # scd=none: disable scene change detection to prevent stutter on some clips
        filter_complex = f"minterpolate=fps={target_fps}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1:scd=none"
    else:
        # Simple blend interpolation (faster)
        filter_complex = f"minterpolate=fps={target_fps}:mi_mode=blend"
    
    # Build FFmpeg command
    # Removed -hwaccel cuda because minterpolate is CPU-only and mixing them can cause stability issues
    # or "moov atom not found" if the pipeline breaks.
    # We stick to software decoding for stability with this complex filter.
    cmd = [
        ffmpeg,
        "-i", str(input_path),
        "-vf", filter_complex,
        "-c:v", "libx264",            # Use CPU encoding for maximum compatibility
        "-preset", "medium",
        "-crf", "20",                 # High quality
        "-c:a", "copy",
        "-y",
        str(output_path)
    ]
    
    print(f"\nProcessing (this may take a while)...")
    
    # Run FFmpeg
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        
        print(f"✓ Success: {output_path}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"✗ FFmpeg error:")
        print(e.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(description='Video Frame Interpolation (FFmpeg)')
    parser.add_argument('input_path', help='Input video path')
    parser.add_argument('--output', help='Output path (optional)')
    parser.add_argument('--fps', type=int, default=None, help='Target FPS (optional, overrides multiplier)')
    parser.add_argument('--multiplier', type=int, default=2, choices=[2, 3, 4],
                       help='FPS multiplier: 2x, 3x, or 4x (default: 2)')
    parser.add_argument('--method', choices=['mci', 'blend'], default='mci',
                       help='Interpolation method: mci (best) or blend (fast)')
    
    args = parser.parse_args()
    
    input_path = Path(args.input_path)
    if not input_path.exists():
        print(f"Error: Video not found: {input_path}")
        return 1
        
    # Check file size
    if input_path.stat().st_size == 0:
        print(f"Error: Input file is empty: {input_path}")
        return 1
    
    # Calculate target FPS
    if args.fps:
        target_fps = args.fps
    else:
        # Auto-detect input FPS and multiply
        info = get_video_info(str(input_path))
        input_fps = info.get('fps', 30)
        target_fps = int(input_fps * args.multiplier)
    
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.with_name(f"{input_path.stem}_{args.multiplier}x.mp4")
    
    try:
        success = interpolate_video_ffmpeg(
            str(input_path),
            str(output_path),
            target_fps=target_fps,
            method=args.method
        )
        return 0 if success else 1
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
