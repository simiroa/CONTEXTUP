import customtkinter as ctk
import tkinter.messagebox
import threading
import time
import os
import shutil
import webbrowser
from pathlib import Path
from typing import Optional, Dict

from manager.mgr_core.updater import UpdateChecker, UpdateInfo
from utils import external_tools

class ToolRow(ctk.CTkFrame):
    """A consistent row for tool path management and status."""
    def __init__(self, parent, tool_key, label_text, initial_value, on_browse, on_detect):
        super().__init__(parent, fg_color="transparent")
        self.tool_key = tool_key
        
        self.grid_columnconfigure(1, weight=1)
        
        # Label
        ctk.CTkLabel(self, text=label_text, width=80, anchor="w", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=(5, 10))
        
        # Entry
        self.entry = ctk.CTkEntry(self)
        self.entry.grid(row=0, column=1, sticky="ew", padx=5)
        self.entry.insert(0, initial_value)
        
        # Browse Button
        ctk.CTkButton(self, text="📂", width=30, command=lambda: on_browse(self.entry, tool_key)).grid(row=0, column=2, padx=2)
        
        # Auto-Detect Button
        self.btn_detect = ctk.CTkButton(self, text="🔍", width=30, fg_color="gray40", hover_color="gray30", 
                                        command=lambda: on_detect(self.entry, tool_key))
        self.btn_detect.grid(row=0, column=3, padx=2)
        
        # Status Label
        self.lbl_status = ctk.CTkLabel(self, text="---", width=60, font=ctk.CTkFont(size=11))
        self.lbl_status.grid(row=0, column=4, padx=(10, 5))

    def set_status(self, is_found: bool):
        if is_found:
            self.lbl_status.configure(text="Ready", text_color="#27AE60")
        else:
            self.lbl_status.configure(text="Missing", text_color="#E74C3C")

class UpdatesFrame(ctk.CTkFrame):
    def __init__(self, parent, settings_manager, package_manager, config_manager=None, root_dir=None, on_update_available=None):
        super().__init__(parent)
        self.settings = settings_manager
        self.package_manager = package_manager
        self.config_manager = config_manager
        self.root_dir = Path(root_dir) if root_dir else None
        self.on_update_available = on_update_available
        
        self.tool_rows: Dict[str, ToolRow] = {}
        self.api_entries = {}
        
        # Update checker
        self.update_checker: Optional[UpdateChecker] = None
        if self.root_dir:
            self.update_checker = UpdateChecker(str(self.root_dir))
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # Scrollable area
        
        # --- App Update Section (Row 0) ---
        self._create_app_update_section()
        
        # --- Navigation/Header for Middle Section (Row 1) ---
        self._create_section_headers()
        
        # --- Scrollable Content Area (Row 2) ---
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 10))
        self.scroll_frame.grid_columnconfigure(0, weight=1)
        
        self._create_connectivity_content()
        self._create_deps_content()
        
        # Flags
        self._deps_loaded = False
        self._update_checked = False

    def _create_app_update_section(self):
        self.update_frame = ctk.CTkFrame(self, fg_color=("gray90", "gray17"))
        self.update_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 10))
        self.update_frame.grid_columnconfigure(1, weight=1)
        
        title_frame = ctk.CTkFrame(self.update_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, columnspan=3, sticky="w", padx=15, pady=(15, 5))
        
        ctk.CTkLabel(title_frame, text="📦 App Update", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        
        self.version_frame = ctk.CTkFrame(self.update_frame, fg_color="transparent")
        self.version_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=15, pady=5)
        
        self.lbl_current = ctk.CTkLabel(self.version_frame, text="Current: ...", font=ctk.CTkFont(size=13))
        self.lbl_current.pack(side="left", padx=(0, 20))
        
        self.lbl_latest = ctk.CTkLabel(self.version_frame, text="Latest: ...", font=ctk.CTkFont(size=13), text_color="gray")
        self.lbl_latest.pack(side="left")
        
        self.lbl_status = ctk.CTkLabel(self.version_frame, text="", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_status.pack(side="left", padx=20)
        
        btn_frame = ctk.CTkFrame(self.update_frame, fg_color="transparent")
        btn_frame.grid(row=1, column=2, sticky="e", padx=15, pady=5)
        
        self.btn_check = ctk.CTkButton(btn_frame, text="Check", width=80, command=self._check_for_updates)
        self.btn_check.pack(side="left", padx=5)
        
        self.btn_update = ctk.CTkButton(btn_frame, text="Update Now", width=100, fg_color="#27AE60", hover_color="#2ECC71", command=self._perform_update)
        self.btn_update.pack(side="left", padx=5)
        self.btn_update.configure(state="disabled")

    def _create_section_headers(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(10, 5))
        
        ctk.CTkLabel(header_frame, text="🔗 External Tools & Connectivity", font=ctk.CTkFont(size=15, weight="bold")).pack(side="left")
        
        # Tools Control
        ctk.CTkButton(header_frame, text="Scan All", width=80, command=self.refresh_all).pack(side="right", padx=5)

    def _create_connectivity_content(self):
        self.conn_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.conn_frame.pack(fill="x", pady=(0, 20))
        self.conn_frame.grid_columnconfigure(0, weight=1)
        
        tools_map = [
            ("PYTHON_PATH", "Python"),
            ("FFMPEG_PATH", "FFmpeg"),
            ("BLENDER_PATH", "Blender"),
            ("COMFYUI_PATH", "ComfyUI"),
            ("MAYO_PATH", "Mayo")
        ]
        
        for i, (key, name) in enumerate(tools_map):
            initial_val = self.settings.get(key, "")
            row = ToolRow(self.conn_frame, key, name, initial_val, self._on_browse, self._on_detect)
            row.pack(fill="x", pady=2)
            self.tool_rows[key] = row
            
        # APIs Section inside connectivity
        sep = ctk.CTkFrame(self.conn_frame, height=1, fg_color="gray30")
        sep.pack(fill="x", pady=15)
        
        api_grid = ctk.CTkFrame(self.conn_frame, fg_color="transparent")
        api_grid.pack(fill="x")
        api_grid.grid_columnconfigure(1, weight=1)
        api_grid.grid_columnconfigure(3, weight=1)
        
        apis = [
            ("GEMINI_API_KEY", "Gemini API"),
            ("OLLAMA_URL", "Ollama URL")
        ]
        
        for i, (key, name) in enumerate(apis):
            ctk.CTkLabel(api_grid, text=name, font=ctk.CTkFont(weight="bold"), width=80, anchor="w").grid(row=i, column=0, padx=5, pady=2)
            entry = ctk.CTkEntry(api_grid, show="•" if "KEY" in key else None)
            entry.grid(row=i, column=1, columnspan=3, sticky="ew", padx=5, pady=2)
            default = "http://localhost:11434" if "OLLAMA" in key else ""
            entry.insert(0, self.settings.get(key, default))
            self.api_entries[key] = entry

    def _create_deps_content(self):
        # Header for Deps
        deps_header = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        deps_header.pack(fill="x", pady=(10, 5))
        ctk.CTkLabel(deps_header, text="📦 Python Dependencies", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        
        btn_box = ctk.CTkFrame(deps_header, fg_color="transparent")
        btn_box.pack(side="right")
        
        ctk.CTkButton(btn_box, text="Update Sys Libs", width=100, font=ctk.CTkFont(size=11), fg_color="#8E44AD", command=self.update_system_libs).pack(side="left", padx=2)
        ctk.CTkButton(btn_box, text="Install AI Engine", width=100, font=ctk.CTkFont(size=11), fg_color="#D35400", hover_color="#E74C3C", command=self.install_ai_heavy_batch).pack(side="left", padx=2)
        
        self.deps_list_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.deps_list_frame.pack(fill="x", pady=5)
        
        self._show_loading_placeholder()

    def _on_browse(self, entry, key):
        from tkinter import filedialog
        path = filedialog.askopenfilename()
        
        if path:
            entry.delete(0, "end")
            entry.insert(0, path)
            self.refresh_tool_status(key)

    def _on_detect(self, entry, key):
        """Auto-detect tool path using external_tools logic."""
        try:
            detected = None
            if key == "PYTHON_PATH":
                # Check tools/python/python.exe
                p = self.root_dir / "tools" / "python" / "python.exe" if self.root_dir else Path("tools/python/python.exe")
                if p.exists(): detected = str(p)
            elif key == "FFMPEG_PATH":
                detected = external_tools.get_ffmpeg()
            elif key == "BLENDER_PATH":
                detected = external_tools.get_blender()
            elif key == "COMFYUI_PATH":
                detected = external_tools.get_comfyui()
            elif key == "MAYO_PATH":
                try: detected = external_tools.get_mayo_viewer()
                except: pass
            
            if detected and detected != "ffmpeg": # Ignore generic 'ffmpeg' fallback if we want absolute path
                entry.delete(0, "end")
                entry.insert(0, detected)
                self.refresh_tool_status(key)
                # Toast or message?
            else:
                tkinter.messagebox.showinfo("Not Found", f"Could not auto-detect {key}. Please browse manually.")
        except Exception as e:
            tkinter.messagebox.showerror("Error", f"Detection failed: {e}")

    def refresh_all(self):
        """Refresh both tool paths and python dependencies."""
        self.refresh_tool_statuses()
        self.refresh_deps()

    def refresh_tool_statuses(self):
        for key in self.tool_rows:
            self.refresh_tool_status(key)

    def refresh_tool_status(self, key):
        row = self.tool_rows.get(key)
        if not row: return
        
        path = row.entry.get().strip()
        if not path:
            row.set_status(False)
            return
            
        is_valid = False
        try:
            is_valid = os.path.exists(path)
        except: pass
        
        row.set_status(is_valid)

    def save(self):
        """Save all settings to manager's settings."""
        for key, row in self.tool_rows.items():
            self.settings[key] = row.entry.get().strip()
        for key, entry in self.api_entries.items():
            self.settings[key] = entry.get().strip()

    def on_visible(self):
        if not self._deps_loaded:
            self._deps_loaded = True
            self.refresh_all()
        
        if not self._update_checked:
            self._update_checked = True
            self._check_for_updates()

    # --- Re-using and slightly adjusting existing logic for Deps and Updates ---

    def _show_loading_placeholder(self):
        for w in self.deps_list_frame.winfo_children(): w.destroy()
        ctk.CTkLabel(self.deps_list_frame, text="Scanning dependencies...", text_color="gray").pack(pady=10)

    def refresh_deps(self):
        threading.Thread(target=self._scan_deps, daemon=True).start()

    def _scan_deps(self):
        self.installed_packages = self.package_manager.get_installed_packages()
        
        self.pkg_ai_heavy = [
            ("torch", "PyTorch (AI Core)"),
            ("paddlepaddle-gpu", "PaddlePaddle (OCR)"),
            ("rembg", "Rembg (BG Removal)"),
            ("faster-whisper", "Faster Whisper"),
            ("transformers", "Transformers"),
        ]
        
        common_libs = [
            ("customtkinter", "CustomTkinter"),
            ("pystray", "Pystray"),
            ("Pillow", "Pillow"),
            ("google-generativeai", "Gemini API"),
            ("numpy", "NumPy"),
        ] + self.pkg_ai_heavy
        
        self.after(0, lambda: [w.destroy() for w in self.deps_list_frame.winfo_children()])
        for pkg, label in common_libs:
            ver = self.installed_packages.get(pkg.lower(), None)
            self.after(0, lambda p=pkg, l=label, v=ver: self._add_dep_row(p, l, v))

    def _add_dep_row(self, pkg, label, version):
        row = ctk.CTkFrame(self.deps_list_frame, fg_color="transparent")
        row.pack(fill="x", pady=1)
        
        ctk.CTkLabel(row, text=label, width=150, anchor="w").pack(side="left", padx=10)
        
        status_text = f"v{version}" if version else "Missing"
        status_color = "#27AE60" if version else "#C0392B"
        ctk.CTkLabel(row, text=status_text, text_color=status_color, width=100).pack(side="left")
        
        if not version:
            ctk.CTkButton(row, text="Install", width=60, height=22, font=ctk.CTkFont(size=10),
                          command=lambda: self.install_pkg(pkg)).pack(side="right", padx=10)

    def _check_for_updates(self):
        if not self.update_checker: return
        self.lbl_latest.configure(text="Latest: checking...")
        self.btn_check.configure(state="disabled")
        
        def on_result(info: Optional[UpdateInfo]):
            self.after(0, lambda: self._display_update_info(info))
            self.after(0, lambda: self.btn_check.configure(state="normal"))
        
        self.update_checker.check_for_updates(callback=on_result)

    def _display_update_info(self, info: Optional[UpdateInfo]):
        if info is None:
            self.lbl_latest.configure(text="Latest: check failed")
            self.lbl_status.configure(text="⚠️ Failed", text_color="#E67E22")
            return
        
        self.lbl_current.configure(text=f"v{info.current_version}")
        self.lbl_latest.configure(text=f"v{info.latest_version}", text_color="white")
        
        if info.is_newer:
            self.lbl_status.configure(text="Update Available!", text_color="#E74C3C")
            self.btn_update.configure(state="normal")
            if self.on_update_available: self.on_update_available(True)
        else:
            self.lbl_status.configure(text="Up to date", text_color="#27AE60")
            if self.on_update_available: self.on_update_available(False)

    def _perform_update(self):
        if not self.update_checker: return
        if not tkinter.messagebox.askyesno("Update", "Update ContextUp now?"): return
        
        self.btn_update.configure(state="disabled", text="Updating...")
        self.update_checker.perform_update(callback=lambda s, m: self.after(0, lambda: self._on_update_done(s, m)))

    def _on_update_done(self, success, message):
        self.btn_update.configure(text="Update Now")
        if success:
            tkinter.messagebox.showinfo("Success", message)
            self._check_for_updates()
        else:
            tkinter.messagebox.showerror("Error", message)
            self.btn_update.configure(state="normal")

    def install_ai_heavy_batch(self):
        if not tkinter.messagebox.askyesno("Install AI Engine", "Install heavy AI dependencies? (approx 4GB)"): return
        pkgs = [p[0] for p in self.pkg_ai_heavy] + ["torchvision", "torchaudio"]
        meta = {
            "torch": {'pip_name': "torch", 'install_args': ["--index-url", "https://download.pytorch.org/whl/cu121"]},
            "torchvision": {'pip_name': "torchvision", 'install_args': ["--index-url", "https://download.pytorch.org/whl/cu121"]},
            "torchaudio": {'pip_name': "torchaudio", 'install_args': ["--index-url", "https://download.pytorch.org/whl/cu121"]},
        }
        self.package_manager.install_packages(pkgs, meta, lambda c, f: None, lambda s: self.after(0, lambda: self.refresh_all()))

    def install_pkg(self, pkg):
        if not tkinter.messagebox.askyesno("Confirm", f"Install {pkg}?"): return
        meta = {pkg: {'pip_name': pkg, 'install_args': []}}
        self.package_manager.install_packages([pkg], meta, lambda c, f: None, lambda s: self.after(0, lambda: self.refresh_all()))

    def update_system_libs(self):
        if not tkinter.messagebox.askyesno("System Update", "Install all requirements?"): return
        self.package_manager.update_system_libs(lambda s, m: self.after(0, lambda: tkinter.messagebox.showinfo("Result", m)))
