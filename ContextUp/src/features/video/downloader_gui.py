import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import sys
import os
import threading
import json
import subprocess
import urllib.request
from PIL import Image, ImageTk
from io import BytesIO
from pathlib import Path
import time
from datetime import datetime

# Add project root and src to path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.append(str(project_root))
sys.path.append(str(current_dir.parent)) # Add src to path for core imports

try:
    import yt_dlp
except ImportError:
    messagebox.showerror("Error", "yt-dlp library not found. Please run setup.")
    sys.exit(1)

# Configuration Paths
CONFIG_DIR = project_root / "config"
USERDATA_DIR = project_root / "userdata"
HISTORY_FILE = USERDATA_DIR / "download_history.json"
SETTINGS_FILE = CONFIG_DIR / "settings.json"

# Appearance mode is now inherited from settings.json

from core.config import MenuConfig
from utils.gui_lib import setup_theme

class VideoDownloaderGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        setup_theme()  # Apply theme from settings.json

        # Sync Name
        self.tool_name = "ContextUp Video Downloader"
        try:
             config = MenuConfig()
             item = config.get_item_by_id("youtube_downloader")
             if item: self.tool_name = item.get("name", self.tool_name)
        except: pass

        self.title(self.tool_name)
        self.geometry("450x650")
        
        # Data
        self.current_video_info = None
        self.settings = self.load_settings()
        self.active_downloads = {} # id -> widget_dict
        self.download_counter = 0
        
        # Layout
        self.create_widgets()
        
        # Protocol
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def load_settings(self):
        # Default to current execution directory
        defaults = {"download_path": os.getcwd()}
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    defaults.update(data)
                    return defaults
            except:
                pass
        return defaults

    def save_settings(self):
        CONFIG_DIR.mkdir(exist_ok=True)
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, indent=4)

    def create_widgets(self):
        # 1. Header & URL
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=15, pady=(15, 10))
        
        ctk.CTkLabel(top_frame, text="Video Downloader", font=("Arial", 18, "bold")).pack(anchor="w", pady=(0, 10))
        
        url_row = ctk.CTkFrame(top_frame, fg_color="transparent")
        url_row.pack(fill="x")
        
        self.url_var = ctk.StringVar()
        self.entry_url = ctk.CTkEntry(url_row, textvariable=self.url_var, placeholder_text="Paste YouTube URL...", height=35)
        self.entry_url.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.entry_url.bind("<Return>", lambda e: self.start_analysis())
        
        self.btn_analyze = ctk.CTkButton(url_row, text="Search", width=60, height=35, command=self.start_analysis)
        self.btn_analyze.pack(side="right")

        # 2. Preview Area (Vertical Stack)
        self.preview_frame = ctk.CTkFrame(self)
        self.preview_frame.pack(fill="x", padx=15, pady=(5, 0)) # Reduced bottom padding
        
        self.lbl_thumb = ctk.CTkLabel(self.preview_frame, text="No Video Loaded", width=400, height=225, text_color="gray")
        self.lbl_thumb.pack(pady=5) # Reduced padding
        
        # Info
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(fill="x", padx=20, pady=(2, 0)) # Reduced padding
        
        self.lbl_title = ctk.CTkLabel(info_frame, text="", font=("Arial", 14, "bold"), wraplength=400, anchor="w", justify="left")
        self.lbl_title.pack(fill="x")
        
        self.lbl_meta = ctk.CTkLabel(info_frame, text="", text_color="gray", font=("Arial", 11), anchor="w", justify="left")
        self.lbl_meta.pack(fill="x")

        # 3. Options
        opt_frame = ctk.CTkFrame(self, fg_color="transparent")
        opt_frame.pack(fill="x", padx=20, pady=(5, 10)) # Reduced top padding
        
        # Quality
        q_row = ctk.CTkFrame(opt_frame, fg_color="transparent")
        q_row.pack(fill="x", pady=2)
        ctk.CTkLabel(q_row, text="Quality:", width=60, anchor="w").pack(side="left")
        self.var_quality = ctk.StringVar(value="Best Video+Audio")
        ctk.CTkOptionMenu(q_row, variable=self.var_quality, values=["Best Video+Audio", "4K (2160p)", "1080p", "720p", "Audio Only (MP3)", "Audio Only (M4A)"]).pack(side="left", fill="x", expand=True)

        # Path
        p_row = ctk.CTkFrame(opt_frame, fg_color="transparent")
        p_row.pack(fill="x", pady=5)
        ctk.CTkLabel(p_row, text="Save to:", width=60, anchor="w").pack(side="left")
        self.lbl_path = ctk.CTkButton(p_row, text=Path(self.settings['download_path']).name, anchor="w", command=self.browse_path)
        self.lbl_path.pack(side="left", fill="x", expand=True)

        # Subs
        self.var_subs = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(opt_frame, text="Download Subtitles", variable=self.var_subs).pack(pady=5, anchor="w")

        # 4. Action Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(5, 10))
        
        self.btn_download = ctk.CTkButton(btn_frame, text="Download", command=self.start_download, state="disabled", height=40, font=("Arial", 14, "bold"), fg_color="green", hover_color="darkgreen")
        self.btn_download.pack(fill="x")

        # 5. Active Downloads
        ctk.CTkLabel(self, text="Active Downloads", font=("Arial", 12, "bold")).pack(anchor="w", padx=20, pady=(10, 0))
        
        self.downloads_frame = ctk.CTkScrollableFrame(self, height=200)
        self.downloads_frame.pack(fill="both", expand=True, padx=15, pady=(5, 15))

    def browse_path(self):
        path = filedialog.askdirectory(initialdir=self.settings['download_path'])
        if path:
            self.settings['download_path'] = path
            self.lbl_path.configure(text=f"Save to: {Path(path).name}")
            self.save_settings()

    def start_analysis(self):
        url = self.url_var.get().strip()
        if not url:
            return
        
        self.btn_analyze.configure(state="disabled", text="...")
        threading.Thread(target=self._analyze_thread, args=(url,)).start()

    def _analyze_thread(self, url):
        try:
            ydl_opts = {'quiet': True, 'no_warnings': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
            self.after(0, lambda: self._update_ui_with_info(info))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", f"Could not analyze URL: {e}"))
        finally:
            self.after(0, lambda: self.btn_analyze.configure(state="normal", text="Search"))

    def _update_ui_with_info(self, info):
        self.current_video_info = info
        title = info.get('title', 'Unknown Title')
        uploader = info.get('uploader', 'Unknown Uploader')
        duration = info.get('duration_string', '??:??')
        thumb_url = info.get('thumbnail')
        
        self.lbl_title.configure(text=title)
        self.lbl_meta.configure(text=f"{uploader} | {duration}")
        self.btn_download.configure(state="normal")
        
        # Load Thumbnail
        if thumb_url:
            threading.Thread(target=self._load_thumbnail, args=(thumb_url,)).start()

    def _load_thumbnail(self, url):
        try:
            with urllib.request.urlopen(url) as u:
                raw_data = u.read()
            image = Image.open(BytesIO(raw_data))
            image.thumbnail((320, 180))
            ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=image.size)
            self.after(0, lambda: self.lbl_thumb.configure(image=ctk_image, text=""))
        except: pass

    def start_download(self):
        if not self.current_video_info:
            return
            
        # Capture current state for this download
        download_id = self.download_counter
        self.download_counter += 1
        
        info = self.current_video_info
        options = {
            "quality": self.var_quality.get(),
            "subs": self.var_subs.get(),
            "path": self.settings['download_path']
        }
        
        # Create UI Row
        self._create_download_row(download_id, info['title'])
        
        # Start Thread
        threading.Thread(target=self._download_thread, args=(download_id, info, options)).start()
        
        # Optional: Clear active selection to allow next search easily? 
        # User might want to download same video with different settings, so keep it for now.
        # But maybe clear the "Ready" state visual slightly? No, keep it simple.

    def _create_download_row(self, dl_id, title):
        frame = ctk.CTkFrame(self.downloads_frame)
        frame.pack(fill="x", pady=2)
        
        lbl_title = ctk.CTkLabel(frame, text=title, anchor="w", width=200)
        lbl_title.pack(side="left", padx=5)
        
        lbl_status = ctk.CTkLabel(frame, text="Starting...", width=100)
        lbl_status.pack(side="right", padx=5)
        
        progress = ctk.CTkProgressBar(frame)
        progress.pack(side="right", fill="x", expand=True, padx=5)
        progress.set(0)
        
        self.active_downloads[dl_id] = {
            "frame": frame,
            "status": lbl_status,
            "progress": progress
        }

    def _download_thread(self, dl_id, info, opts):
        url = info['webpage_url']
        path = opts['path']
        
        ydl_opts = {
            'outtmpl': f'{path}/%(title)s.%(ext)s',
            'progress_hooks': [lambda d: self._progress_hook(d, dl_id)],
            'quiet': True,
        }
        
        # Quality Logic
        quality = opts['quality']
        if "Audio Only" in quality:
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3' if 'MP3' in quality else 'm4a',
            }]
        elif "4K" in quality:
            ydl_opts['format'] = 'bestvideo[height<=2160]+bestaudio/best[height<=2160]'
        elif "1080p" in quality:
            ydl_opts['format'] = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]'
        elif "720p" in quality:
            ydl_opts['format'] = 'bestvideo[height<=720]+bestaudio/best[height<=720]'
        else: 
            ydl_opts['format'] = 'bestvideo+bestaudio/best'
            
        if opts['subs']:
            ydl_opts['writesubtitles'] = True
            ydl_opts['subtitleslangs'] = ['en', 'ko', 'auto']

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.after(0, lambda: self._update_status(dl_id, "Complete", 1.0, "green"))
        except Exception as e:
            print(e)
            self.after(0, lambda: self._update_status(dl_id, "Failed", 0.0, "red"))

    def _progress_hook(self, d, dl_id):
        if d['status'] == 'downloading':
            try:
                p = d.get('_percent_str', '0%').replace('%','')
                val = float(p) / 100
                self.after(0, lambda: self._update_status(dl_id, f"{d.get('_percent_str')}", val))
            except: pass

    def _update_status(self, dl_id, text, progress_val, color=None):
        widgets = self.active_downloads.get(dl_id)
        if widgets:
            widgets['status'].configure(text=text)
            widgets['progress'].set(progress_val)
            if color:
                widgets['status'].configure(text_color=color)

    def on_close(self):
        # We should wait for threads or just kill app? 
        # Standard behavior for simple tools: just exit.
        self.destroy()
        sys.exit(0)

if __name__ == "__main__":
    app = VideoDownloaderGUI()
    app.mainloop()
