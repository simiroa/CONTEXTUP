import os
import subprocess
from pathlib import Path
from tkinter import messagebox


from utils.external_tools import get_ffmpeg
from utils.files import get_safe_path

def extract_audio(target_path: str):
    from scripts import video_audio_gui
    video_audio_gui.run_gui(target_path)

def remove_audio(target_path: str):
    from scripts import video_audio_gui
    video_audio_gui.run_gui(target_path)

def convert_video(target_path: str):
    from scripts import video_convert_gui
    video_convert_gui.run_gui(target_path)

def create_proxy(target_path: str):
    # Proxy is just a preset in convert_video now
    from scripts import video_convert_gui
    video_convert_gui.run_gui(target_path)

def seq_to_video(target_path: str):
    from scripts import video_seq_gui
    video_seq_gui.run_gui(target_path)

def frame_interp_30fps(target_path: str):
    try:
        path = Path(target_path)
        ffmpeg = get_ffmpeg()
        
        output_path = get_safe_path(path.with_name(f"{path.stem}_30fps.mp4"))
        
        # Simple blend interpolation to 30fps
        cmd = [
            ffmpeg, "-i", str(path),
            "-filter:v", "minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1",
            "-c:v", "libx264", "-crf", "20",
            "-c:a", "copy",
            "-y", str(output_path)
        ]
        
        # This can be slow, maybe show progress?
        # For now, just run.
        subprocess.run(cmd, check=True, capture_output=True)
        messagebox.showinfo("Success", f"Created {output_path.name}")
        
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"FFmpeg failed: {e.stderr.decode('utf-8', errors='ignore')}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed: {e}")
