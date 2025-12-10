import customtkinter as ctk
import os
from pathlib import Path
import threading
import time

class LogsFrame(ctk.CTkFrame):
    def __init__(self, parent, root_dir):
        super().__init__(parent)
        self.root_dir = root_dir
        self.log_dir = root_dir / "logs"
        self.running = False
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Controls
        ctrl = ctk.CTkFrame(self, height=40, fg_color="transparent")
        ctrl.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        
        ctk.CTkLabel(ctrl, text="Log Viewer", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=10)
        
        self.btn_refresh = ctk.CTkButton(ctrl, text="Refresh", width=80, command=self.load_logs)
        self.btn_refresh.pack(side="right", padx=10)
        
        self.chk_auto = ctk.CTkCheckBox(ctrl, text="Auto Refresh (3s)", command=self.toggle_auto)
        self.chk_auto.pack(side="right", padx=10)
        
        # Tabs
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        # Create tabs
        self.log_files = {
            "App": "app_*.log", # Wildcard logic needed
            "Tray": "debug_*.log",
            "Recent": "recent_folders.log"
        }
        
        self.text_widgets = {}
        
        for name, _ in self.log_files.items():
            self.tabview.add(name)
            txt = ctk.CTkTextbox(self.tabview.tab(name), font=("Consolas", 12))
            txt.pack(fill="both", expand=True)
            txt.configure(state="disabled")
            self.text_widgets[name] = txt
            
        # Initial Load
        self.load_logs()

    def toggle_auto(self):
        if self.chk_auto.get():
            self.running = True
            self._auto_loop()
        else:
            self.running = False

    def _auto_loop(self):
        if self.running:
            self.load_logs()
            self.after(3000, self._auto_loop)

    def load_logs(self):
        for name, pattern in self.log_files.items():
            content = self._read_latest_log(pattern)
            self._update_text(name, content)

    def _read_latest_log(self, pattern):
        try:
            # Find latest matching file
            files = list(self.log_dir.glob(pattern))
            if not files:
                return f"No log files found for pattern: {pattern}"
            
            # Sort by modification time
            latest = max(files, key=lambda f: f.stat().st_mtime)
            
            # Read last 200 lines
            text = latest.read_text(encoding="utf-8", errors="ignore")
            lines = text.splitlines()
            if len(lines) > 200:
                lines = lines[-200:]
            return "\n".join(lines)
            
        except Exception as e:
            return f"Error reading log: {e}"

    def _update_text(self, name, content):
        widget = self.text_widgets[name]
        current_y = widget.yview()[1] # Check if scrolled to bottom
        
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", content)
        widget.configure(state="disabled")
        
        # If was largely at bottom, autoscroll
        if current_y > 0.9:
            widget.yview_moveto(1.0)
