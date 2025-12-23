import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import sys
import os
import threading
import json
import shutil
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
LEGACY_HISTORY_FILES = [
    project_root / "config" / "runtime" / "download_history.json",
    project_root / "config" / "download_history.json",
]

# Appearance mode is now inherited from settings.json

from core.config import MenuConfig
from utils.gui_lib import setup_theme

class VideoDownloaderGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        setup_theme()  # Apply theme from settings.json

        # Hide Default Title Bar
        self.overrideredirect(True)
        self._offsetx = 0
        self._offsety = 0

        # Sync Name
        self.tool_name = "ContextUp Video Downloader"
        try:
             config = MenuConfig()
             item = config.get_item_by_id("youtube_downloader")
             if item: self.tool_name = item.get("name", self.tool_name)
        except: pass

        self.title(self.tool_name)
        # Larger initial height for the new layout
        self.geometry("480x720")
        
        # Data
        self.current_video_info = None
        self.settings = self.load_settings()
        self.active_downloads = {} # id -> widget_dict
        self.download_counter = 0
        self._history_lock = threading.Lock()
        self._migrate_download_history()
        
        # Colors & Constants (Adaptive: Light, Dark)
        self.BG_COLOR = ("#F5F5F5", "#050505")
        self.HEADER_BG = ("#FFFFFF", "#111111")
        self.ACCENT_COLOR = ("#3498db", "#3498db")  # Consistent Blue
        self.NEUTRAL_BORDER = ("#E0E0E0", "#1A1A1A")
        self.CARD_BG = ("#FCFCFC", "#0A0A0A")
        self.INNER_CARD = ("#F0F0F0", "#181818")
        self.TEXT_MAIN = ("#222222", "#E0E0E0")
        self.TEXT_DIM = ("#666666", "#888888")
        self.BORDER_DEEP = ("#D0D0D0", "#333333")
        
        # Layout
        self.setup_modern_ui()
        
        # Protocol
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_modern_ui(self):
        """Unified premium look with custom title bar and rounded containers"""
        # Outer Frame with Rounded Corners
        TRANS_KEY = "#000001"
        self.configure(fg_color=TRANS_KEY)
        self.wm_attributes("-transparentcolor", TRANS_KEY)
        
        self.outer_frame = ctk.CTkFrame(self, fg_color=self.BG_COLOR, corner_radius=16, border_width=1, border_color="#333333")
        self.outer_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # 1. Custom Title Bar
        self.title_bar = ctk.CTkFrame(self.outer_frame, fg_color="transparent", height=40)
        self.title_bar.pack(fill="x", padx=10, pady=(5, 0))
        
        title_lbl = ctk.CTkLabel(self.title_bar, text=" ✨ VIDEO", font=("Segoe UI", 13, "bold"), text_color="#E0E0E0")
        title_lbl.pack(side="left", padx=(5, 0))
        ctk.CTkLabel(self.title_bar, text=" | Downloader", font=("Segoe UI", 13), text_color="#666").pack(side="left")
        
        btn_close = ctk.CTkButton(self.title_bar, text="✕", width=32, height=28, fg_color="transparent", hover_color="#922B21", 
                                  command=self.on_close, font=("Arial", 11), corner_radius=6)
        btn_close.pack(side="right", padx=5)
        
        # Drag support
        self.title_bar.bind("<Button-1>", self.start_move)
        self.title_bar.bind("<B1-Motion>", self.do_move)
        title_lbl.bind("<Button-1>", self.start_move)
        title_lbl.bind("<B1-Motion>", self.do_move)

        # 2. Main content container
        self.container = ctk.CTkScrollableFrame(self.outer_frame, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.create_widgets()

    def start_move(self, event):
        self._offsetx = event.x
        self._offsety = event.y

    def do_move(self, event):
        x = self.winfo_x() + event.x - self._offsetx
        y = self.winfo_y() + event.y - self._offsety
        self.geometry(f"+{x}+{y}")

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

    def _migrate_download_history(self):
        if HISTORY_FILE.exists():
            return
        for legacy_path in LEGACY_HISTORY_FILES:
            if legacy_path.exists():
                try:
                    USERDATA_DIR.mkdir(exist_ok=True)
                    shutil.move(str(legacy_path), str(HISTORY_FILE))
                except Exception:
                    pass
                return

    def _load_download_history(self):
        if not HISTORY_FILE.exists():
            return []
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
        except Exception:
            pass
        return []

    def _save_download_history(self, history):
        try:
            USERDATA_DIR.mkdir(exist_ok=True)
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=4, ensure_ascii=False)
        except Exception:
            pass

    def _record_download_history(self, info, opts):
        try:
            entry = {
                "title": info.get("title") or "Unknown Title",
                "url": info.get("webpage_url") or info.get("original_url") or "",
                "path": opts.get("path") or "",
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "quality": opts.get("quality") or "",
            }
            with self._history_lock:
                history = self._load_download_history()
                history.insert(0, entry)
                history = history[:100]
                self._save_download_history(history)
        except Exception:
            pass

    def create_widgets(self):
        # --- 1. Main Info & Settings Card (URL + Preview + Quality) ---
        main_card = ctk.CTkFrame(self.container, fg_color=self.HEADER_BG, corner_radius=12, border_width=1, border_color=self.NEUTRAL_BORDER)
        main_card.pack(fill="x", padx=10, pady=(10, 5))
        
        # URL Row
        ctk.CTkLabel(main_card, text="VIDEO SOURCE & SETTINGS", font=("Segoe UI", 11, "bold"), text_color=self.TEXT_MAIN, anchor="w").pack(fill="x", padx=15, pady=(12, 5))
        
        url_row = ctk.CTkFrame(main_card, fg_color="transparent")
        url_row.pack(fill="x", padx=10, pady=(0, 10))
        
        self.url_var = ctk.StringVar()
        self.entry_url = ctk.CTkEntry(url_row, textvariable=self.url_var, placeholder_text="Paste video URL here...", height=40, 
                                      fg_color=self.CARD_BG, border_color=self.BORDER_DEEP, corner_radius=8, text_color=self.TEXT_MAIN)
        self.entry_url.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.entry_url.bind("<Return>", lambda e: self.start_analysis())
        
        self.btn_analyze = ctk.CTkButton(url_row, text="SEARCH", width=80, height=40, command=self.start_analysis, 
                                        fg_color=self.ACCENT_COLOR, hover_color="#2980b9", font=("Segoe UI", 12, "bold"), corner_radius=8)
        self.btn_analyze.pack(side="right")

        # Preview Area (Nested within main_card)
        self.preview_inner = ctk.CTkFrame(main_card, fg_color=self.CARD_BG, corner_radius=10, border_width=1, border_color=self.BORDER_DEEP)
        self.preview_inner.pack(fill="x", padx=10, pady=5)
        
        self.preview_inner.grid_columnconfigure(1, weight=1)
        self.lbl_thumb = ctk.CTkLabel(self.preview_inner, text="No Media", width=120, height=68, fg_color=self.INNER_CARD, corner_radius=6)
        self.lbl_thumb.grid(row=0, column=0, rowspan=2, padx=10, pady=10)
        
        self.lbl_title = ctk.CTkLabel(self.preview_inner, text="Video title will appear here", font=("Segoe UI", 12, "bold"), 
                                      wraplength=250, anchor="nw", justify="left", text_color=self.TEXT_MAIN)
        self.lbl_title.grid(row=0, column=1, padx=(0, 10), pady=(12, 2), sticky="nsew")
        
        self.lbl_meta = ctk.CTkLabel(self.preview_inner, text="Uploader | 00:00", text_color=self.TEXT_DIM, font=("Segoe UI", 11), 
                                     anchor="nw", justify="left")
        self.lbl_meta.grid(row=1, column=1, padx=(0, 10), pady=(0, 12), sticky="nsew")

        # Quality Row (Nested within main_card)
        q_row = ctk.CTkFrame(main_card, fg_color="transparent")
        q_row.pack(fill="x", padx=12, pady=(5, 12))
        
        self.var_quality = ctk.StringVar(value="Best Video+Audio")
        self.quality_menu = ctk.CTkOptionMenu(q_row, variable=self.var_quality, height=32,
                          values=["Best Video+Audio", "4K (2160p)", "1080p", "720p", "Audio Only (MP3)", "Audio Only (M4A)"],
                          fg_color=self.CARD_BG, button_color=self.INNER_CARD, button_hover_color=self.BORDER_DEEP, 
                          text_color=self.TEXT_MAIN, corner_radius=6, dropdown_fg_color=self.HEADER_BG, dropdown_hover_color=self.INNER_CARD, dropdown_text_color=self.TEXT_MAIN)
        self.quality_menu.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.var_subs = ctk.BooleanVar(value=False)
        self.check_subs = ctk.CTkCheckBox(q_row, text="Subs", variable=self.var_subs, font=("Segoe UI", 11), text_color=self.TEXT_DIM, 
                                          checkbox_width=18, checkbox_height=18, corner_radius=6, hover_color=self.INNER_CARD)
        self.check_subs.pack(side="left")

        # --- 2. Save Path Card ---
        p_card = ctk.CTkFrame(self.container, fg_color=self.HEADER_BG, corner_radius=12, border_width=1, border_color=self.NEUTRAL_BORDER)
        p_card.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(p_card, text="SAVE PATH", font=("Segoe UI", 10, "bold"), text_color=self.TEXT_DIM, anchor="w").pack(fill="x", padx=15, pady=(8, 2))
        
        p_input = ctk.CTkFrame(p_card, fg_color="transparent")
        p_input.pack(fill="x", padx=10, pady=(0, 10))
        
        self.entry_path = ctk.CTkEntry(p_input, height=32, fg_color=self.CARD_BG, border_width=1, border_color=self.BORDER_DEEP, corner_radius=6, text_color=self.TEXT_MAIN)
        self.entry_path.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.entry_path.insert(0, self.settings['download_path'])
        
        self.btn_browse = ctk.CTkButton(p_input, text="📂", width=36, height=32, command=self.browse_path, 
                                        fg_color=self.INNER_CARD, hover_color=self.BORDER_DEEP, text_color=self.TEXT_MAIN, corner_radius=6)
        self.btn_browse.pack(side="left", padx=2)
        
        self.btn_open_folder = ctk.CTkButton(p_input, text="↗", width=36, height=32, command=self.open_current_folder, 
                                        fg_color=self.INNER_CARD, hover_color=self.BORDER_DEEP, text_color=self.TEXT_MAIN, corner_radius=6)
        self.btn_open_folder.pack(side="left")

        # --- 3. Action Buttons ---
        btn_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        self.btn_queue = ctk.CTkButton(btn_frame, text="ADD TO QUEUE", command=self.add_to_queue, state="disabled", height=45, 
                                      fg_color=self.INNER_CARD, hover_color=self.BORDER_DEEP, text_color=self.TEXT_MAIN,
                                      font=("Segoe UI", 12, "bold"), corner_radius=10, border_width=1, border_color=self.BORDER_DEEP)
        self.btn_queue.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.btn_download = ctk.CTkButton(btn_frame, text="DOWNLOAD NOW", command=self.start_download, state="disabled", height=45, 
                                         font=("Segoe UI", 13, "bold"), fg_color=self.ACCENT_COLOR, hover_color="#2980b9", corner_radius=10)
        self.btn_download.pack(side="left", fill="x", expand=True)

        # --- 4. Progress Section ---
        ctk.CTkLabel(self.container, text="DOWNLOAD PROGRESS", font=("Segoe UI", 11, "bold"), text_color=self.TEXT_DIM).pack(anchor="w", padx=20, pady=(5, 0))
        
        self.downloads_frame = ctk.CTkFrame(self.container, fg_color=self.CARD_BG, corner_radius=12, border_width=1, border_color=self.NEUTRAL_BORDER)
        self.downloads_frame.pack(fill="both", expand=True, padx=10, pady=(5, 20))
        
        # Internal scrollable frame for items
        self.scroll_list = ctk.CTkScrollableFrame(self.downloads_frame, fg_color="transparent", height=180)
        self.scroll_list.pack(fill="both", expand=True, padx=2, pady=2)

        # Queue Logic
        self.queue = []
        self.is_downloading_queue = False

    def set_quick_path(self, target):
        if target == "desktop":
            path = str(Path.home() / "Desktop")
        else:
            path = str(Path.home() / "Downloads")
        
        self.entry_path.delete(0, "end")
        self.entry_path.insert(0, path)
        self.settings['download_path'] = path
        self.save_settings()

    def open_current_folder(self):
        path = self.entry_path.get()
        if os.path.exists(path):
            os.startfile(path)
        else:
            print(f"Path not found: {path}")

    def browse_path(self):
        current = self.entry_path.get() or self.settings['download_path']
        path = filedialog.askdirectory(initialdir=current)
        if path:
            self.entry_path.delete(0, "end")
            self.entry_path.insert(0, path)
            self.settings['download_path'] = path
            self.save_settings()

    def add_to_queue(self):
        if not self.current_video_info:
            return
        
        info = self.current_video_info.copy()
        options = {
            "quality": self.var_quality.get(),
            "subs": self.var_subs.get(),
            "path": self.entry_path.get()
        }
        
        download_id = self.download_counter
        self.download_counter += 1
        
        # Create row in "Pending" state
        self._create_download_row(download_id, info['title'], status="Queued")
        
        self.queue.append((download_id, info, options))
        
        if not self.is_downloading_queue:
            threading.Thread(target=self._process_queue_thread).start()

    def _process_queue_thread(self):
        self.is_downloading_queue = True
        while self.queue:
            dl_id, info, opts = self.queue.pop(0)
            self.after(0, lambda: self._update_status(dl_id, "Starting...", 0))
            self._download_thread(dl_id, info, opts) # Sync call inside thread
            time.sleep(1) # Small gap
        self.is_downloading_queue = False

    def start_download(self):
        if not self.current_video_info:
            return
            
        download_id = self.download_counter
        self.download_counter += 1
        
        info = self.current_video_info.copy()
        options = {
            "quality": self.var_quality.get(),
            "subs": self.var_subs.get(),
            "path": self.entry_path.get()
        }
        
        self._create_download_row(download_id, info['title'])
        threading.Thread(target=self._download_thread, args=(download_id, info, options)).start()

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
        self.btn_queue.configure(state="normal")
        
        # Load Thumbnail
        if thumb_url:
            threading.Thread(target=self._load_thumbnail, args=(thumb_url,)).start()

    def _load_thumbnail(self, url):
        try:
            with urllib.request.urlopen(url) as u:
                raw_data = u.read()
            image = Image.open(BytesIO(raw_data))
            # Resize for specific smaller preview (160x90)
            image.thumbnail((160, 90))
            ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=image.size)
            self.after(0, lambda: self.lbl_thumb.configure(image=ctk_image, text=""))
        except: pass

    def _create_download_row(self, dl_id, title, status="Enqueued"):
        # Use scroll_list instead of downloads_frame
        frame = ctk.CTkFrame(self.scroll_list, fg_color=self.INNER_CARD, corner_radius=8)
        frame.pack(fill="x", pady=2, padx=5)
        
        lbl_title = ctk.CTkLabel(frame, text=title, anchor="w", width=180, font=("Segoe UI", 11, "bold"), text_color=self.TEXT_MAIN)
        lbl_title.pack(side="left", padx=12, pady=8)
        
        lbl_status = ctk.CTkLabel(frame, text=status, width=80, font=("Segoe UI", 10), text_color=self.ACCENT_COLOR)
        lbl_status.pack(side="right", padx=12)
        
        progress = ctk.CTkProgressBar(frame, height=6, progress_color=self.ACCENT_COLOR, fg_color=self.CARD_BG, corner_radius=3)
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
            self._record_download_history(info, opts)
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
