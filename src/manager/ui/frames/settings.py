"""
Settings Frame - Reorganized with better UX
Tray features consolidated, sections ordered by usage frequency.
"""
import customtkinter as ctk
from tkinter import messagebox, filedialog
import logging
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("manager.ui.settings")

class SettingsFrame(ctk.CTkFrame):
    def __init__(self, parent, settings_manager, package_manager):
        super().__init__(parent)
        self.settings = settings_manager
        self.package_manager = package_manager
        
        self.tool_vars = {}
        self.tool_entries = {}
        
        self.src_dir = Path(__file__).parent.parent.parent.parent
        self.config_dir = self.src_dir.parent / "config"
        self.backup_dir = self.src_dir.parent / "backups"
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self._setup_ui()
    
    def _setup_ui(self):
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.scroll.grid_columnconfigure(0, weight=1)
        
        # Order by usage frequency
        self._setup_tray_section()      # 1. Most used - includes status
        self._setup_tools_section()     # 2. Core paths
        self._setup_api_section()       # 3. AI features
        self._setup_hotkeys_section()   # 4. Reference info
        self._setup_backup_section()    # 5. Rarely used - bottom
    def on_visible(self):
        self._refresh_hotkeys()
        self._refresh_quick_menu()
    
    # ========================
    # 1. TRAY AGENT (Consolidated)
    # ========================
    def _setup_tray_section(self):
        import winreg
        
        card = ctk.CTkFrame(self.scroll, corner_radius=8)
        card.grid(row=0, column=0, sticky="ew", pady=6)
        card.grid_columnconfigure(0, weight=1)
        
        # Header with status indicator
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=15, pady=(12, 8))
        
        ctk.CTkLabel(header, text="🖥️ Tray Agent", 
                    font=ctk.CTkFont(size=15, weight="bold")).pack(side="left")
        
        # Status in header
        self.lbl_tray_status = ctk.CTkLabel(header, text="● Checking...", text_color="gray")
        self.lbl_tray_status.pack(side="left", padx=15)
        
        # Control button in header
        self.btn_tray_toggle = ctk.CTkButton(header, text="Start", width=70, height=26,
                                            command=self._toggle_tray)
        self.btn_tray_toggle.pack(side="right", padx=5)
        
        # Description
        desc = "백그라운드에서 실행되며 Ctrl+Shift+C로 Quick Menu에 접근합니다."
        ctk.CTkLabel(card, text=desc, text_color="gray", wraplength=550,
                    anchor="w", justify="left").grid(row=1, column=0, sticky="w", padx=15, pady=2)
        
        # Auto-start option
        def is_startup_enabled():
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                    r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
                try:
                    winreg.QueryValueEx(key, "ContextUpTray")
                    winreg.CloseKey(key)
                    return True
                except: 
                    winreg.CloseKey(key)
                    return False
            except: return False
        
        self.var_startup = ctk.BooleanVar(value=is_startup_enabled())
        
        def toggle_startup():
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                    r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
                if self.var_startup.get():
                    cmd = f'"{sys.executable}" "{self.src_dir / "scripts" / "tray_agent.py"}"'
                    winreg.SetValueEx(key, "ContextUpTray", 0, winreg.REG_SZ, cmd)
                else:
                    try: winreg.DeleteValue(key, "ContextUpTray")
                    except: pass
                winreg.CloseKey(key)
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        opts = ctk.CTkFrame(card, fg_color="transparent")
        opts.grid(row=2, column=0, sticky="ew", padx=15, pady=(5, 8))
        
        ctk.CTkCheckBox(opts, text="Windows 시작시 자동 실행", 
                       variable=self.var_startup, command=toggle_startup).pack(side="left")
        
        # Quick Menu Preview (inline, styled like hotkeys)
        ctk.CTkLabel(card, text="Quick Menu", text_color="gray", 
                    font=ctk.CTkFont(size=11)).grid(row=3, column=0, sticky="w", padx=15, pady=(8, 4))
        
        self.quick_menu_frame = ctk.CTkFrame(card, fg_color="transparent")
        self.quick_menu_frame.grid(row=4, column=0, sticky="ew", padx=15, pady=(0, 12))
        
        # Initial status check
        self.after(500, self._update_tray_status)
        self.after(600, self._refresh_quick_menu)
    
    def _refresh_quick_menu(self):
        """Refresh quick menu display."""
        for w in self.quick_menu_frame.winfo_children(): w.destroy()
        
        # Load Copy My Info items
        info_path = self.config_dir / "copy_my_info.json"
        info_items = []
        if info_path.exists():
            try:
                with open(info_path, 'r', encoding='utf-8') as f:
                    info_items = json.load(f).get('items', [])
            except: pass
        
        # Quick menu items
        menu_items = [
            ("📂", "Reopen Last Closed Folder"),
            ("📋", f"Copy My Info ({len(info_items)} items)"),
            ("📁", "Open from Clipboard"),
            ("🌐", "Translator"),
            ("⚙️", "Manager"),
        ]
        
        for icon, label in menu_items:
            row = ctk.CTkFrame(self.quick_menu_frame, fg_color=("gray85", "gray25"), corner_radius=4, height=26)
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)
            ctk.CTkLabel(row, text=icon, width=28).pack(side="left", padx=6, pady=2)
            ctk.CTkLabel(row, text=label, text_color=("gray30", "gray60"), 
                        font=ctk.CTkFont(size=11)).pack(side="left", padx=4)
    
    def _get_process_manager(self):
        """Get or create TrayProcessManager (shared logic with sidebar)."""
        try:
            from manager.core.process import TrayProcessManager
            return TrayProcessManager(self.src_dir.parent, self.settings)
        except:
            return None
    
    def _update_tray_status(self):
        """Check if tray is running using same method as sidebar."""
        pm = self._get_process_manager()
        running = pm.is_running() if pm else False
        
        if running:
            self.lbl_tray_status.configure(text="● Running", text_color="#2ECC71")
            self.btn_tray_toggle.configure(text="Stop", fg_color="#E74C3C", hover_color="#C0392B")
        else:
            self.lbl_tray_status.configure(text="● Stopped", text_color="#E74C3C")
            self.btn_tray_toggle.configure(text="Start", fg_color="#27AE60", hover_color="#2ECC71")
    
    def _toggle_tray(self):
        """Start/Stop tray agent."""
        pm = self._get_process_manager()
        if not pm:
            messagebox.showerror("Error", "TrayProcessManager not available")
            return
        
        try:
            if pm.is_running():
                pm.stop()
            else:
                pm.start()
            self.after(1000, self._update_tray_status)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    
    # ========================
    # 2. TOOL PATHS
    # ========================
    def _setup_tools_section(self):
        card = ctk.CTkFrame(self.scroll, corner_radius=8)
        card.grid(row=1, column=0, sticky="ew", pady=6)
        card.grid_columnconfigure(0, weight=1)
        
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=15, pady=(12, 8))
        ctk.CTkLabel(header, text="🔧 Tool Paths", 
                    font=ctk.CTkFont(size=15, weight="bold")).pack(side="left")
        ctk.CTkButton(header, text="Save", width=60, height=26, 
                     command=self._save_paths).pack(side="right")
        
        frame = ctk.CTkFrame(card, fg_color="transparent")
        frame.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 12))
        
        for key, label in [("PYTHON_PATH", "Python"), ("FFMPEG_PATH", "FFmpeg"), 
                           ("BLENDER_PATH", "Blender"), ("MAYO_PATH", "Mayo")]:
            row = ctk.CTkFrame(frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            
            ctk.CTkLabel(row, text=label, width=65, anchor="w",
                        font=ctk.CTkFont(weight="bold")).pack(side="left")
            
            current = self.settings.get(key, "")
            var = ctk.BooleanVar(value=bool(current))
            self.tool_vars[key] = var
            
            ctk.CTkCheckBox(row, text="", variable=var, width=20,
                           command=lambda k=key: self._toggle_entry(k)).pack(side="left", padx=2)
            
            entry = ctk.CTkEntry(row, height=26)
            entry.pack(side="left", fill="x", expand=True, padx=2)
            if current: entry.insert(0, current)
            else: entry.configure(state="disabled", text_color="gray")
            self.tool_entries[key] = entry
            
            ctk.CTkButton(row, text="...", width=28, height=26,
                         command=lambda e=entry: self._browse(e)).pack(side="right")
    
    def _toggle_entry(self, key):
        e = self.tool_entries[key]
        if self.tool_vars[key].get():
            e.configure(state="normal", text_color=("black", "white"))
        else:
            e.delete(0, "end")
            e.configure(state="disabled", text_color="gray")
    
    def _browse(self, entry):
        path = filedialog.askopenfilename()
        if path:
            entry.configure(state="normal")
            entry.delete(0, "end")
            entry.insert(0, path)
    
    def _save_paths(self):
        for k in self.tool_vars:
            self.settings[k] = self.tool_entries[k].get().strip() if self.tool_vars[k].get() else ""
        try:
            from core.settings import save_settings
            save_settings(self.settings)
            messagebox.showinfo("Success", "Saved!")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    # ========================
    # 3. API KEYS
    # ========================
    def _setup_api_section(self):
        card = ctk.CTkFrame(self.scroll, corner_radius=8)
        card.grid(row=2, column=0, sticky="ew", pady=6)
        card.grid_columnconfigure(0, weight=1)
        
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=15, pady=(12, 8))
        ctk.CTkLabel(header, text="🔑 API Keys", 
                    font=ctk.CTkFont(size=15, weight="bold")).pack(side="left")
        ctk.CTkButton(header, text="Save", width=60, height=26,
                     command=self._save_api).pack(side="right")
        
        frame = ctk.CTkFrame(card, fg_color="transparent")
        frame.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 12))
        
        for label, key, show in [("Gemini", "GEMINI_API_KEY", "•"), ("Ollama", "OLLAMA_URL", "")]:
            row = ctk.CTkFrame(frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=label, width=65, anchor="w",
                        font=ctk.CTkFont(weight="bold")).pack(side="left")
            entry = ctk.CTkEntry(row, height=26, show=show if show else None)
            entry.pack(side="left", fill="x", expand=True, padx=2)
            default = "http://localhost:11434" if key == "OLLAMA_URL" else ""
            entry.insert(0, self.settings.get(key, default))
            setattr(self, f"entry_{key.lower()}", entry)
    
    def _save_api(self):
        self.settings["GEMINI_API_KEY"] = self.entry_gemini_api_key.get().strip()
        self.settings["OLLAMA_URL"] = self.entry_ollama_url.get().strip()
        try:
            from core.settings import save_settings
            save_settings(self.settings)
            messagebox.showinfo("Success", "Saved!")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    # ========================
    # 4. HOTKEYS (Reference)
    # ========================
    def _setup_hotkeys_section(self):
        card = ctk.CTkFrame(self.scroll, corner_radius=8)
        card.grid(row=3, column=0, sticky="ew", pady=6)
        card.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(card, text="⌨️ Registered Hotkeys", 
                    font=ctk.CTkFont(size=15, weight="bold")).grid(row=0, column=0, sticky="w", padx=15, pady=(12, 8))
        
        self.hotkeys_frame = ctk.CTkFrame(card, fg_color="transparent")
        self.hotkeys_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 12))
        self._refresh_hotkeys()
    
    def _refresh_hotkeys(self):
        for w in self.hotkeys_frame.winfo_children(): w.destroy()
        
        hotkeys = [("Ctrl+Shift+C", "Quick Menu Popup")]
        try:
            from core.config import MenuConfig
            for item in MenuConfig().items:
                hk = item.get('hotkey')
                if hk: hotkeys.append((hk, item.get('name', '')))
        except: pass
        
        for key, desc in hotkeys[:6]:
            row = ctk.CTkFrame(self.hotkeys_frame, fg_color=("gray85", "gray25"), corner_radius=4, height=28)
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)
            ctk.CTkLabel(row, text=key, width=130, fg_color=("gray75", "gray35"), corner_radius=3,
                        font=ctk.CTkFont(family="Consolas", size=10, weight="bold")).pack(side="left", padx=6, pady=3)
            ctk.CTkLabel(row, text=desc, text_color=("gray40", "gray60"), 
                        font=ctk.CTkFont(size=11)).pack(side="left", padx=8)
    
    # ========================
    # 5. BACKUP/RESET (Bottom)
    # ========================
    def _setup_backup_section(self):
        card = ctk.CTkFrame(self.scroll, corner_radius=8)
        card.grid(row=4, column=0, sticky="ew", pady=6)
        card.grid_columnconfigure(0, weight=1)
        
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=15, pady=(12, 8))
        ctk.CTkLabel(header, text="💾 Backup & Reset", 
                    font=ctk.CTkFont(size=15, weight="bold")).pack(side="left")
        
        btns = ctk.CTkFrame(card, fg_color="transparent")
        btns.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 12))
        
        ctk.CTkButton(btns, text="📥 Backup", width=85, height=28,
                     fg_color="#3498DB", command=self._backup).pack(side="left", padx=3)
        ctk.CTkButton(btns, text="📤 Restore", width=85, height=28,
                     fg_color="#27AE60", command=self._restore).pack(side="left", padx=3)
        ctk.CTkButton(btns, text="🔄 Factory Reset", width=110, height=28,
                     fg_color="#E74C3C", command=self._reset).pack(side="right", padx=3)
        
        # Feedback at very bottom
        ctk.CTkButton(self.scroll, text="📝 Send Feedback", width=130, height=28,
                     fg_color=("gray70", "gray30"),
                     command=lambda: __import__('webbrowser').open("https://github.com/simiroa/CONTEXTUP/issues/new")
                     ).grid(row=5, column=0, pady=15)
    
    def _backup(self):
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            dest = self.backup_dir / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copytree(self.config_dir, dest)
            messagebox.showinfo("Backup", f"Saved: {dest.name}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def _restore(self):
        folder = filedialog.askdirectory(initialdir=str(self.backup_dir), title="Select Backup")
        if not folder: return
        src = Path(folder)
        if not (src / "menu_categories").exists():
            messagebox.showerror("Error", "Invalid backup folder.")
            return
        if not messagebox.askyesno("Confirm", "Overwrite current settings?"): return
        try:
            for item in src.iterdir():
                dest = self.config_dir / item.name
                if item.is_dir():
                    if dest.exists(): shutil.rmtree(dest)
                    shutil.copytree(item, dest)
                else: shutil.copy(item, dest)
            messagebox.showinfo("Done", "Restored. Please restart.")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def _reset(self):
        if not messagebox.askyesno("⚠️ Reset", "All settings will be cleared.\nCurrent config will be backed up."): return
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            shutil.copytree(self.config_dir, self.backup_dir / f"pre_reset_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            for f in (self.config_dir / "menu_categories").glob("*.json"):
                with open(f, 'w') as file: json.dump([], file)
            info = self.config_dir / "copy_my_info.json"
            if info.exists():
                with open(info, 'w') as f: json.dump({"items": []}, f)
            messagebox.showinfo("Done", "Reset complete. Please restart.")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def update_dashboard(self, _): pass  # Legacy
