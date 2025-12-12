import customtkinter as ctk
from tkinter import messagebox
import tkinter.filedialog
import logging
import os
from pathlib import Path

logger = logging.getLogger("manager.ui.settings")

class SettingsFrame(ctk.CTkFrame):
    def __init__(self, parent, settings_manager, package_manager):
        super().__init__(parent)
        self.settings_manager = settings_manager # Reference to core settings (dict/manager)
        self.package_manager = package_manager
        
        # We assume settings_manager is the dict "settings" for now, 
        # but ideally it should be a manager. 
        # For this refactor, let's assume it's the `self.settings` dict passed from App.
        self.settings = settings_manager 
        
        self.tool_vars = {}
        self.tool_entries = {}
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)
        
        self._setup_startup()
        self._setup_dashboard()
        self._setup_config()
        self._setup_api()
    
    def _setup_startup(self):
        """Setup startup and general options section."""
        import sys
        import winreg
        
        startup_frame = ctk.CTkFrame(self, corner_radius=10)
        startup_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
        
        header = ctk.CTkFrame(startup_frame, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 10))
        ctk.CTkLabel(header, text="General Settings", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        
        # Check current startup state
        def is_startup_enabled():
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                    r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
                try:
                    winreg.QueryValueEx(key, "ContextUpTray")
                    winreg.CloseKey(key)
                    return True
                except FileNotFoundError:
                    winreg.CloseKey(key)
                    return False
            except Exception:
                return False
        
        self.var_startup = ctk.BooleanVar(value=is_startup_enabled())
        
        def toggle_startup():
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                    r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
                
                if self.var_startup.get():
                    # Get tray agent path
                    src_dir = Path(__file__).parent.parent.parent.parent
                    tray_script = src_dir / "scripts" / "tray_agent.py"
                    python_exe = sys.executable
                    
                    tray_cmd = f'"{python_exe}" "{tray_script}"'
                    winreg.SetValueEx(key, "ContextUpTray", 0, winreg.REG_SZ, tray_cmd)
                    logger.info(f"Enabled Windows startup: {tray_cmd}")
                else:
                    try:
                        winreg.DeleteValue(key, "ContextUpTray")
                        logger.info("Disabled Windows startup")
                    except FileNotFoundError:
                        pass
                
                winreg.CloseKey(key)
            except Exception as e:
                logger.error(f"Failed to toggle startup: {e}")
                messagebox.showerror("Error", f"Failed to change startup setting: {e}")
        
        options_frame = ctk.CTkFrame(startup_frame, fg_color="transparent")
        options_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        # Startup checkbox
        ctk.CTkCheckBox(options_frame, text="Windows 시작시 트레이 자동 실행", 
                       variable=self.var_startup, command=toggle_startup).pack(anchor="w", pady=5)
        
        # Feedback button
        def open_feedback():
            import webbrowser
            webbrowser.open("https://github.com/simiroa/CONTEXTUP/issues/new")
        
        btn_row = ctk.CTkFrame(options_frame, fg_color="transparent")
        btn_row.pack(fill="x", pady=10)
        ctk.CTkButton(btn_row, text="📝 피드백 보내기", width=150, height=32,
                     fg_color="#6c757d", hover_color="#5a6268",
                     command=open_feedback).pack(side="left")
        
    def _setup_dashboard(self):
        # 1. Missing Components Dashboard
        dash_frame = ctk.CTkFrame(self, fg_color=("gray90", "gray20"), corner_radius=10)
        dash_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        
        # Header
        dash_header = ctk.CTkFrame(dash_frame, fg_color="transparent")
        dash_header.pack(fill="x", padx=15, pady=(15, 5))
        ctk.CTkLabel(dash_header, text="Missing Components", font=ctk.CTkFont(size=16, weight="bold"), text_color=("#C0392B", "#E74C3C")).pack(side="left")
        
        # Content
        self.missing_scroll = ctk.CTkScrollableFrame(dash_frame, height=120, fg_color="transparent")
        self.missing_scroll.pack(fill="x", padx=10, pady=(0, 15))
        
        # Populate (Initial load is empty, App should trigger refresh or we do it here)
        msg = ctk.CTkLabel(self.missing_scroll, text="Click 'Run Health Check' in sidebar to scan.")
        msg.pack(pady=10)

    def _setup_config(self):
        # 2. Configuration Management
        config_frame = ctk.CTkFrame(self, corner_radius=10)
        config_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=10)
        
        header_row = ctk.CTkFrame(config_frame, fg_color="transparent")
        header_row.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(header_row, text="Tool Configuration", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        ctk.CTkButton(header_row, text="Save Paths", width=100, height=28, command=self.save_paths).pack(side="right")
        
        tools_frame = ctk.CTkFrame(config_frame, fg_color="transparent")
        tools_frame.pack(fill="x", padx=10, pady=(0, 15))
        
        # Tools including Python
        tools = ["PYTHON_PATH", "FFMPEG_PATH", "BLENDER_PATH", "MAYO_PATH"]
        
        for tool in tools:
            tool_name = tool.replace("_PATH", "")
            row = ctk.CTkFrame(tools_frame, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=5)
            
            ctk.CTkLabel(row, text=tool_name, width=80, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left")
            
            current_val = self.settings.get(tool, "")
            is_custom = bool(current_val)
            
            chk_var = ctk.BooleanVar(value=is_custom)
            self.tool_vars[tool] = chk_var
            
            # Checkbox
            chk = ctk.CTkCheckBox(row, text="Custom", variable=chk_var, width=70, 
                                command=lambda t=tool: self.toggle_tool_entry(t))
            chk.pack(side="left", padx=10)
            
            # Entry
            entry = ctk.CTkEntry(row, height=28)
            entry.pack(side="left", fill="x", expand=True, padx=5)
            
            if is_custom:
                entry.insert(0, current_val)
            else:
                entry.configure(state="normal")
                entry.insert(0, "") 
                entry.configure(state="disabled", text_color="gray")
                
            ctk.CTkButton(row, text="Browse", width=70, height=28, command=lambda e=entry: self.browse_file(e)).pack(side="right", padx=(5,0))
            self.tool_entries[tool] = entry
            
            # Special: Test Button for Python
            if tool == "PYTHON_PATH":
                ctk.CTkButton(row, text="Test", width=50, height=28, fg_color="#F39C12", hover_color="#D68910",
                            command=lambda: self.test_python(entry)).pack(side="right", padx=5)

    def test_python(self, entry):
        path = entry.get().strip() or "python"
        
        # Check integrity
        res = self.package_manager.check_tray_dependencies(path)
        
        if res['valid']:
             messagebox.showinfo("Python Check", f"✅ Valid Environment!\nSaved libs found: {', '.join(['pystray', 'pillow', 'pywin32'])}")
        else:
             missing = ", ".join(res['missing'])
             if messagebox.askyesno("Missing Deps", f"❌ Missing libraries: {missing}\n\nAttempt to install them now?"):
                 # Trigger install
                 # We need a way to run pip install on THAT environment
                 self.run_install(path, res['missing'])

    def run_install(self, python_path, starting_deps):
        # We need to construct commands.
        # This is a bit complex for a quick fix, let's just use the `update_system_libs` logic from PackageManager 
        # but customized for specific libs and python path.
        # For now, let's just tell user to install.
        # Or better, use the package_manager if it supports custom python path?
        # PackageManager.install_packages uses sys.executable. We need to override.
        messagebox.showinfo("Manual Install Required", f"Please run:\n{python_path} -m pip install pystray pillow pywin32")

    def _setup_api(self):
        # 3. API Configuration
        api_frame = ctk.CTkFrame(self, corner_radius=10)
        api_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=10)
        
        api_header = ctk.CTkFrame(api_frame, fg_color="transparent")
        api_header.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(api_header, text="API Configuration", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        ctk.CTkButton(api_header, text="Save APIs", width=100, height=28, command=self.save_api_settings).pack(side="right")

        # Gemini
        row_gemini = ctk.CTkFrame(api_frame, fg_color="transparent")
        row_gemini.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(row_gemini, text="Gemini Key:", width=100, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left")
        self.entry_gemini = ctk.CTkEntry(row_gemini, show="*", height=28)
        self.entry_gemini.pack(side="left", fill="x", expand=True, padx=5)
        self.entry_gemini.insert(0, self.settings.get("GEMINI_API_KEY", ""))

        # Ollama
        row_ollama = ctk.CTkFrame(api_frame, fg_color="transparent")
        row_ollama.pack(fill="x", padx=20, pady=(5, 20))
        ctk.CTkLabel(row_ollama, text="Ollama URL:", width=100, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left")
        self.entry_ollama = ctk.CTkEntry(row_ollama, height=28)
        self.entry_ollama.pack(side="left", fill="x", expand=True, padx=5)
        self.entry_ollama.insert(0, self.settings.get("OLLAMA_URL", "http://localhost:11434"))

    def toggle_tool_entry(self, tool_key):
        is_custom = self.tool_vars[tool_key].get()
        entry = self.tool_entries[tool_key]
        if is_custom:
            entry.configure(state="normal", text_color=("black", "white"))
        else:
            entry.delete(0, "end")
            entry.configure(state="disabled", text_color="gray")
            # Clear from settings strictly
            self.settings[tool_key] = ""
            
    def browse_file(self, entry):
        path = tkinter.filedialog.askopenfilename()
        if path:
            current_state = entry.cget("state")
            entry.configure(state="normal")
            entry.delete(0, "end")
            entry.insert(0, path)
            if current_state == "disabled":
                entry.configure(state="disabled")

    def save_paths(self):
        # Update settings from UI
        for tool, var in self.tool_vars.items():
            if var.get():
                path = self.tool_entries[tool].get().strip()
                if path:
                    self.settings[tool] = path
            else:
                 self.settings[tool] = ""
        
        # Parent app handles saving to disk usually, but we can do it via a callback or event
        # For now, we assume App will save, or we call a helper.
        # ... 
        try:
            from manager.core.settings import save_settings
            save_settings(self.settings)
            tkinter.messagebox.showinfo("Success", "Settings saved.")
        except Exception as e:
            tkinter.messagebox.showerror("Error", str(e))

    def save_api_settings(self):
        self.settings["GEMINI_API_KEY"] = self.entry_gemini.get().strip()
        self.settings["OLLAMA_URL"] = self.entry_ollama.get().strip()
        if hasattr(self.master, "save_app_settings"):
            self.master.save_app_settings()
        messagebox.showinfo("Success", "API settings saved!")

    def update_dashboard(self, missing_items):
        for widget in self.missing_scroll.winfo_children():
            widget.destroy()
            
        if not missing_items:
            ctk.CTkLabel(self.missing_scroll, text="All systems go! No missing components.", 
                       text_color="green").pack(pady=10)
            return

        for item in missing_items:
            row = ctk.CTkFrame(self.missing_scroll, fg_color="transparent")
            row.pack(fill="x", padx=5, pady=2)
            ctk.CTkLabel(row, text=f"• {item}", anchor="w").pack(side="left")
