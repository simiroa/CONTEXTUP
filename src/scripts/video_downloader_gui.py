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

# Add project root to path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.append(str(project_root))

try:
    import yt_dlp
except ImportError:
    messagebox.showerror("Error", "yt-dlp library not found. Please run setup.")
    sys.exit(1)

# Configuration Paths
CONFIG_DIR = project_root / "config"
HISTORY_FILE = CONFIG_DIR / "download_history.json"
SETTINGS_FILE = CONFIG_DIR / "settings.json"

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class VideoDownloaderGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("ContextUp Video Downloader")
        self.geometry("900x750")
        
        # Data
        self.current_video_info = None
        self.queue = []
        self.is_downloading = False
        self.stop_event = threading.Event()
        self.history = self.load_history()
        self.settings = self.load_settings()
        
        # Layout
        self.create_widgets()
        
        # Protocol
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def load_settings(self):
        defaults = {"download_path": str(Path.home() / "Downloads")}
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

    def load_history(self):
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return []

    def save_history(self):
        CONFIG_DIR.mkdir(exist_ok=True)
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=4)

    def create_widgets(self):
        # --- Top Bar: URL & Update ---
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        self.url_var = ctk.StringVar()
        self.entry_url = ctk.CTkEntry(top_frame, textvariable=self.url_var, placeholder_text="Paste YouTube URL here...", height=40, font=("Arial", 14))
        self.entry_url.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry_url.bind("<Return>", lambda e: self.start_analysis())
        
        self.btn_analyze = ctk.CTkButton(top_frame, text="Analyze", command=self.start_analysis, width=100, height=40)
        self.btn_analyze.pack(side="left", padx=(0, 10))
        
        self.btn_update = ctk.CTkButton(top_frame, text="Update Core", command=self.update_core, width=100, height=40, fg_color="#444444")
        self.btn_update.pack(side="left")

        # --- Main Content Area (Split) ---
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Left: Preview & Info
        self.info_frame = ctk.CTkFrame(content_frame, width=400)
        self.info_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        self.lbl_thumb = ctk.CTkLabel(self.info_frame, text="No Video Loaded", width=320, height=180, fg_color="#2b2b2b", corner_radius=10)
        self.lbl_thumb.pack(pady=20, padx=20)
        
        self.lbl_title = ctk.CTkLabel(self.info_frame, text="", font=("Arial", 16, "bold"), wraplength=350)
        self.lbl_title.pack(pady=(0, 5), padx=20)
        
        self.lbl_meta = ctk.CTkLabel(self.info_frame, text="", text_color="gray")
        self.lbl_meta.pack(pady=(0, 20), padx=20)

        # Right: Options
        self.opt_frame = ctk.CTkFrame(content_frame, width=300)
        self.opt_frame.pack(side="right", fill="both", padx=(10, 0))
        
        ctk.CTkLabel(self.opt_frame, text="Download Options", font=("Arial", 14, "bold")).pack(pady=15)
        
        # Quality
        self.var_quality = ctk.StringVar(value="Best Video+Audio")
        ctk.CTkOptionMenu(self.opt_frame, variable=self.var_quality, values=["Best Video+Audio", "4K (2160p)", "1080p", "720p", "Audio Only (MP3)", "Audio Only (M4A)"]).pack(pady=10, padx=20, fill="x")
        
        # Subtitles
        self.var_subs = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(self.opt_frame, text="Download Subtitles", variable=self.var_subs).pack(pady=10, padx=20, anchor="w")
        
        # Path
        path_frame = ctk.CTkFrame(self.opt_frame, fg_color="transparent")
        path_frame.pack(pady=10, padx=20, fill="x")
        
        self.lbl_path = ctk.CTkLabel(path_frame, text=f"Save to: {Path(self.settings['download_path']).name}", anchor="w")
        self.lbl_path.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(path_frame, text="...", width=30, command=self.browse_path).pack(side="right")
        
        # Add to Queue Button (Centered)
        self.btn_add = ctk.CTkButton(self.opt_frame, text="Add to Queue", command=self.add_to_queue, state="disabled", height=40, font=("Arial", 14, "bold"))
        self.btn_add.pack(side="bottom", pady=20, padx=20, fill="x")

        # --- Bottom: Queue & History Tabs ---
        self.tabview = ctk.CTkTabview(self, height=250)
        self.tabview.pack(fill="x", padx=20, pady=(0, 20))
        
        self.tab_queue = self.tabview.add("Queue")
        self.tab_history = self.tabview.add("History")
        
        # Queue List
        self.queue_frame = ctk.CTkScrollableFrame(self.tab_queue, fg_color="transparent")
        self.queue_frame.pack(fill="both", expand=True)
        
        # Queue Controls
        q_ctrl_frame = ctk.CTkFrame(self.tab_queue, fg_color="transparent", height=40)
        q_ctrl_frame.pack(fill="x", pady=5)
        
        self.btn_start = ctk.CTkButton(q_ctrl_frame, text="Start Queue", command=self.start_queue, fg_color="green")
        self.btn_start.pack(side="right", padx=5)
        
        self.btn_stop = ctk.CTkButton(q_ctrl_frame, text="Stop", command=self.stop_queue, fg_color="red", state="disabled")
        self.btn_stop.pack(side="right", padx=5)
        
        self.lbl_status = ctk.CTkLabel(q_ctrl_frame, text="Ready", anchor="w")
        self.lbl_status.pack(side="left", padx=5)

        # History List
        self.history_frame = ctk.CTkScrollableFrame(self.tab_history, fg_color="transparent")
        self.history_frame.pack(fill="both", expand=True)
        
        h_ctrl_frame = ctk.CTkFrame(self.tab_history, fg_color="transparent", height=40)
        h_ctrl_frame.pack(fill="x", pady=5)
        
        ctk.CTkButton(h_ctrl_frame, text="Clear History", command=self.clear_history, fg_color="#444444").pack(side="right", padx=5)
        
        self.refresh_history_ui()

    def browse_path(self):
        path = filedialog.askdirectory(initialdir=self.settings['download_path'])
        if path:
            self.settings['download_path'] = path
            self.lbl_path.configure(text=f"Save to: {Path(path).name}")
            self.save_settings()

    def update_core(self):
        if messagebox.askyesno("Update Core", "This will update the internal 'yt-dlp' library to the latest version.\nContinue?"):
            threading.Thread(target=self._run_update).start()

    def _run_update(self):
        self.btn_update.configure(state="disabled", text="Updating...")
        try:
            python_exe = sys.executable
            subprocess.check_call([python_exe, "-m", "pip", "install", "--upgrade", "yt-dlp"])
            self.after(0, lambda: messagebox.showinfo("Success", "Library updated successfully!"))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", f"Update failed: {e}"))
        finally:
            self.after(0, lambda: self.btn_update.configure(state="normal", text="Update Core"))

    def start_analysis(self):
        url = self.url_var.get().strip()
        if not url:
            return
        
        self.btn_analyze.configure(state="disabled", text="Analyzing...")
        self.lbl_status.configure(text="Analyzing URL...")
        threading.Thread(target=self._analyze_thread, args=(url,)).start()

    def _analyze_thread(self, url):
        try:
            ydl_opts = {'quiet': True, 'no_warnings': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
            
            self.after(0, lambda: self._update_ui_with_info(info))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", f"Could not analyze URL: {e}"))
            self.after(0, lambda: self.lbl_status.configure(text="Analysis failed"))
        finally:
            self.after(0, lambda: self.btn_analyze.configure(state="normal", text="Analyze"))

    def _update_ui_with_info(self, info):
        self.current_video_info = info
        title = info.get('title', 'Unknown Title')
        uploader = info.get('uploader', 'Unknown Uploader')
        duration = info.get('duration_string', '??:??')
        thumb_url = info.get('thumbnail')
        
        self.lbl_title.configure(text=title)
        self.lbl_meta.configure(text=f"{uploader} | {duration}")
        self.btn_add.configure(state="normal")
        self.lbl_status.configure(text="Analysis complete")
        
        # Load Thumbnail
        if thumb_url:
            threading.Thread(target=self._load_thumbnail, args=(thumb_url,)).start()

    def _load_thumbnail(self, url):
        try:
            with urllib.request.urlopen(url) as u:
                raw_data = u.read()
            
            image = Image.open(BytesIO(raw_data))
            # Resize to fit 320x180 (16:9)
            image.thumbnail((320, 180))
            ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=image.size)
            
            self.after(0, lambda: self.lbl_thumb.configure(image=ctk_image, text=""))
        except:
            pass

    def add_to_queue(self):
        if not self.current_video_info:
            return
            
        item = {
            "info": self.current_video_info,
            "options": {
                "quality": self.var_quality.get(),
                "subs": self.var_subs.get(),
                "path": self.settings['download_path']
            },
            "status": "Pending"
        }
        self.queue.append(item)
        self.refresh_queue_ui()
        self.lbl_status.configure(text=f"Added to queue. Total: {len(self.queue)}")
        
        # Reset Input
        self.url_var.set("")
        self.current_video_info = None
        self.btn_add.configure(state="disabled")
        self.lbl_title.configure(text="")
        self.lbl_meta.configure(text="")
        self.lbl_thumb.configure(image=None, text="No Video Loaded")

    def refresh_queue_ui(self):
        for widget in self.queue_frame.winfo_children():
            widget.destroy()
            
        for i, item in enumerate(self.queue):
            frame = ctk.CTkFrame(self.queue_frame)
            frame.pack(fill="x", pady=2, padx=5)
            
            title = item['info'].get('title', 'Unknown')
            status = item['status']
            
            ctk.CTkLabel(frame, text=f"{i+1}. {title}", anchor="w", width=300).pack(side="left", padx=10)
            ctk.CTkLabel(frame, text=item['options']['quality'], width=100).pack(side="left")
            
            status_color = "orange" if status == "Pending" else "green" if status == "Done" else "blue" if status == "Downloading" else "red"
            ctk.CTkLabel(frame, text=status, text_color=status_color, width=100).pack(side="left")
            
            if status == "Pending":
                ctk.CTkButton(frame, text="X", width=30, fg_color="red", command=lambda idx=i: self.remove_from_queue(idx)).pack(side="right", padx=5)

    def remove_from_queue(self, index):
        if 0 <= index < len(self.queue):
            del self.queue[index]
            self.refresh_queue_ui()

    def start_queue(self):
        if self.is_downloading:
            return
        
        pending = [i for i in self.queue if i['status'] == "Pending"]
        if not pending:
            messagebox.showinfo("Info", "No pending items in queue.")
            return
            
        self.is_downloading = True
        self.stop_event.clear()
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        
        threading.Thread(target=self._process_queue).start()

    def stop_queue(self):
        if self.is_downloading:
            self.stop_event.set()
            self.lbl_status.configure(text="Stopping after current download...")

    def _process_queue(self):
        for i, item in enumerate(self.queue):
            if self.stop_event.is_set():
                break
                
            if item['status'] == "Pending":
                item['status'] = "Downloading"
                self.after(0, self.refresh_queue_ui)
                
                success = self._download_item(item)
                
                item['status'] = "Done" if success else "Failed"
                self.after(0, self.refresh_queue_ui)
                
                if success:
                    self._add_to_history(item)

        self.is_downloading = False
        self.after(0, lambda: self.btn_start.configure(state="normal"))
        self.after(0, lambda: self.btn_stop.configure(state="disabled"))
        self.after(0, lambda: self.lbl_status.configure(text="Queue finished"))

    def _download_item(self, item):
        info = item['info']
        opts = item['options']
        url = info['webpage_url']
        path = opts['path']
        
        ydl_opts = {
            'outtmpl': f'{path}/%(title)s.%(ext)s',
            'progress_hooks': [lambda d: self._progress_hook(d)],
            'quiet': True,
        }
        
        # Quality Configuration
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
        else: # Best
            ydl_opts['format'] = 'bestvideo+bestaudio/best'
            
        if opts['subs']:
            ydl_opts['writesubtitles'] = True
            ydl_opts['subtitleslangs'] = ['en', 'ko', 'auto']

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            return True
        except Exception as e:
            print(f"Download Error: {e}")
            return False

    def _progress_hook(self, d):
        if d['status'] == 'downloading':
            p = d.get('_percent_str', '0%')
            self.after(0, lambda: self.lbl_status.configure(text=f"Downloading: {p}"))

    def _add_to_history(self, item):
        record = {
            "title": item['info'].get('title'),
            "url": item['info'].get('webpage_url'),
            "path": item['options']['path'],
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "quality": item['options']['quality']
        }
        self.history.insert(0, record) # Add to top
        self.save_history()
        self.after(0, self.refresh_history_ui)

    def refresh_history_ui(self):
        for widget in self.history_frame.winfo_children():
            widget.destroy()
            
        for record in self.history:
            frame = ctk.CTkFrame(self.history_frame)
            frame.pack(fill="x", pady=2, padx=5)
            
            ctk.CTkLabel(frame, text=record['date'], width=120, text_color="gray").pack(side="left")
            ctk.CTkLabel(frame, text=record['title'], anchor="w", width=300).pack(side="left", padx=10)
            ctk.CTkButton(frame, text="Open Folder", width=80, command=lambda p=record['path']: self.open_folder(p)).pack(side="right", padx=5)

    def open_folder(self, path):
        if os.path.exists(path):
            os.startfile(path)

    def clear_history(self):
        if messagebox.askyesno("Confirm", "Clear all download history?"):
            self.history = []
            self.save_history()
            self.refresh_history_ui()

    def on_close(self):
        self.stop_event.set()
        self.destroy()

if __name__ == "__main__":
    app = VideoDownloaderGUI()
    app.mainloop()
