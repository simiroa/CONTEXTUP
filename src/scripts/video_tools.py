import os
import subprocess
from pathlib import Path
from tkinter import simpledialog, messagebox
import tkinter as tk

from utils.external_tools import get_ffmpeg

def _get_root():
    root = tk.Tk()
    root.withdraw()
    return root

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

class SequenceDialog(simpledialog.Dialog):
    def __init__(self, parent, title, initial_pattern, presets):
        self.initial_pattern = initial_pattern
        self.presets = presets
        self.result = None
        super().__init__(parent, title)

    def body(self, master):
        tk.Label(master, text="Input Pattern (e.g. seq.%04d.jpg):").grid(row=0, sticky=tk.W)
        self.e_pattern = tk.Entry(master, width=40)
        self.e_pattern.insert(0, self.initial_pattern)
        self.e_pattern.grid(row=1, padx=5, pady=5)

        tk.Label(master, text="Framerate:").grid(row=2, sticky=tk.W)
        self.e_fps = tk.Entry(master)
        self.e_fps.insert(0, "30")
        self.e_fps.grid(row=3, padx=5, pady=5)

        tk.Label(master, text="Preset:").grid(row=4, sticky=tk.W)
        self.var_preset = tk.StringVar(master)
        self.var_preset.set(self.presets[0])
        self.opt_preset = tk.OptionMenu(master, self.var_preset, *self.presets)
        self.opt_preset.grid(row=5, padx=5, pady=5)
        
        self.var_skip = tk.BooleanVar(value=False)
        self.chk_skip = tk.Checkbutton(master, text="Skip First Frame (Unreal)", variable=self.var_skip)
        self.chk_skip.grid(row=6, padx=5, pady=5, sticky=tk.W)
        
        return self.e_pattern

    def apply(self):
        pattern = self.e_pattern.get()
        try:
            fps = int(self.e_fps.get())
        except ValueError:
            fps = 30
        preset = self.var_preset.get()
        skip = self.var_skip.get()
        self.result = (pattern, fps, preset, skip)

def seq_to_video(target_path: str):
    try:
        target = Path(target_path)
        if target.is_dir():
            folder = target
        else:
            folder = target.parent
            
        files = sorted([f.name for f in folder.iterdir() if f.is_file()])
        img_files = [f for f in files if f.lower().endswith(('.jpg', '.png', '.exr', '.tga', '.tif'))]
        
        guess_pattern = ""
        start_num = 0
        
        if img_files:
            import re
            ref_file = target.name if target.is_file() and target.name in img_files else img_files[0]
            match = re.search(r"(\d+)", ref_file)
            if match:
                padding = len(match.group(1))
                prefix = ref_file[:match.start()]
                suffix = ref_file[match.end():]
                guess_pattern = f"{prefix}%0{padding}d{suffix}"
                start_num = int(match.group(1))

        root = _get_root()
        presets = [
            "MP4 High (H.264, CRF 18)",
            "MP4 Low/Proxy (H.264, CRF 28)",
            "ProRes 422 (MOV)",
            "ProRes 4444 + Alpha (MOV)"
        ]
        
        dlg = SequenceDialog(root, "Sequence to Video", guess_pattern, presets)
        if not dlg.result: return
        
        pattern, framerate, preset, skip = dlg.result
        if not pattern: return
        
        if skip:
            start_num += 1
            
        output_name = folder.name
        ffmpeg_args = []
        
        if "MP4 High" in preset:
            output_name += "_high.mp4"
            ffmpeg_args = ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18"]
        elif "MP4 Low" in preset:
            output_name += "_proxy.mp4"
            ffmpeg_args = ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "28", "-preset", "fast"]
        elif "ProRes 422" in preset:
            output_name += "_422.mov"
            ffmpeg_args = ["-c:v", "prores_ks", "-profile:v", "2", "-pix_fmt", "yuv422p10le"]
        elif "ProRes 4444" in preset:
            output_name += "_4444.mov"
            ffmpeg_args = ["-c:v", "prores_ks", "-profile:v", "4", "-pix_fmt", "yuva444p10le"]
            
        output_path = folder / output_name
        
        ffmpeg = get_ffmpeg()
        cmd = [
            ffmpeg,
            "-framerate", str(framerate),
            "-start_number", str(start_num),
            "-i", str(folder / pattern)
        ] 
        
        cmd.extend(ffmpeg_args)
        cmd.extend(["-y", str(output_path)])
        
        subprocess.run(cmd, check=True, capture_output=True)
        messagebox.showinfo("Success", f"Created {output_name}")
        
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"FFmpeg failed: {e.stderr.decode('utf-8', errors='ignore')}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed: {e}")

def frame_interp_30fps(target_path: str):
    try:
        path = Path(target_path)
        ffmpeg = get_ffmpeg()
        
        output_path = path.with_name(f"{path.stem}_30fps.mp4")
        
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
