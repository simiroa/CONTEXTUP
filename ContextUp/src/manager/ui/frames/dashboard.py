"""
Settings Dashboard - Central Hub for Status & Configuration
"""
import customtkinter as ctk
from tkinter import messagebox, filedialog
import logging
import sys
import json
import shutil
import time
import subprocess
import webbrowser
from pathlib import Path
from datetime import datetime

# Core
# Core
# from core.config import MenuConfig # Removed to avoid redundant reload

logger = logging.getLogger("manager.ui.dashboard")

class DashboardFrame(ctk.CTkFrame):
    def __init__(self, parent, settings_manager, package_manager, config_manager=None, translator=None, update_checker=None):
        super().__init__(parent)
        self.settings = settings_manager
        self.package_manager = package_manager
        self.config_manager = config_manager
        self.update_checker = update_checker # New dependency
        self.tr = translator if translator else lambda k: k 
        
        self.tool_entries = {}
        self.tool_vars = {}
        self.api_entries = {}
        
        self.src_dir = Path(__file__).parent.parent.parent.parent
        self.config_dir = self.src_dir.parent / "config"
        self.userdata_dir = self.src_dir.parent / "userdata"
        self.backup_dir = self.src_dir.parent / "backups"
        
        # Grid Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self._setup_ui()
    
    def on_visible(self):
        """Refresh status on show."""
        self._refresh_status()
    
    def _setup_ui(self):
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.scroll.grid_columnconfigure(0, weight=1)
        self.scroll.grid_columnconfigure(1, weight=1) # Two columns for lower section
        
        # 1. STATUS HEADER (Full Width)
        self._setup_status_section()
        
        # 2. APPEARANCE & BEHAVIOR (Left Col, Row 1)
        self._setup_appearance_behavior()
        
        # 3. HOTKEYS (Right Col)
        self._setup_hotkeys_section()
        
        # 4. DANGER ZONE (Bottom - Fixed in Main Frame)
        self._setup_danger_section()
        
        # Footer
        ctk.CTkLabel(self.scroll, text=self.tr("manager.dashboard.footer_tip"), 
                    text_color="gray", font=ctk.CTkFont(size=10)).grid(row=99, column=0, columnspan=2, pady=20)

    # ========================
    # 1. STATUS HEADER
    # ========================

    def _setup_status_section(self):
        self.status_frame = ctk.CTkFrame(self.scroll, corner_radius=10, fg_color=("gray85", "gray20"))
        self.status_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        self.status_frame.grid_columnconfigure(1, weight=1)
        
        # Icon / Title
        icon_lbl = ctk.CTkLabel(self.status_frame, text="📊", font=ctk.CTkFont(size=40))
        icon_lbl.grid(row=0, column=0, rowspan=2, padx=20, pady=20)
        
        # Status Text
        self.lbl_install_type = ctk.CTkLabel(self.status_frame, text="Checking...", 
                                           font=ctk.CTkFont(size=20, weight="bold"), anchor="w")
        self.lbl_install_type.grid(row=0, column=1, sticky="w", pady=(15, 0))
        
        self.lbl_features_active = ctk.CTkLabel(self.status_frame, text="...", 
                                              font=ctk.CTkFont(size=14), text_color="gray", anchor="w")
        self.lbl_features_active.grid(row=1, column=1, sticky="nw")
        
        # Quick Actions (Right side)
        self.action_frame = ctk.CTkFrame(self.status_frame, fg_color="transparent")
        self.action_frame.grid(row=0, column=2, rowspan=2, padx=20, pady=20)
        
        # "Check Updates" Button (Always there)
        ctk.CTkButton(self.action_frame, text=self.tr("manager.dashboard.status.check_updates"), 
                     width=140, height=32, 
                     fg_color="transparent", border_width=1, border_color="gray",
                     command=self._on_check_updates_click).pack(pady=2)

        # "Restart Explorer" Button (Fix for 'WEIRD MENU')
        ctk.CTkButton(self.action_frame, text="Restart Explorer", 
                     width=140, height=32, 
                     fg_color="#E67E22", hover_color="#D35400",
                     command=self._restart_explorer).pack(pady=2)

        # "Upgrade" Button (Hidden by default, shown if Minimal)
        self.btn_upgrade = ctk.CTkButton(self.action_frame, text=self.tr("manager.dashboard.status.upgrade_full"),
                                        width=140, height=32, fg_color="#2ECC71", hover_color="#27AE60",
                                        command=lambda: self.master.master.master.show_frame("dependencies"))
        # self.btn_upgrade.pack(pady=2) # Packed dynamically in refresh

    def _refresh_status(self):
        # 1. Feature Count
        try:
            if self.config_manager:
                items = self.config_manager.load_config(force_reload=False)
            else:
                from core.config import MenuConfig
                items = MenuConfig().items
                
            total = len(items)
            enabled = len([i for i in items if i.get('enabled', True)])
            
            # Count Issues (Simple check: Missing critical paths or API keys)
            issues = 0
            # Check Python (Critical)
            if not self.settings.get("PYTHON_PATH"): issues += 1
            # Check FFMPEG (Recommended)
            if not self.settings.get("FFMPEG_PATH"): issues += 1
            
            status_text = f"{enabled} / {total} {self.tr('manager.dashboard.status.features_active')}"
            if issues > 0:
                status_text += f" | ⚠️ {issues} {self.tr('manager.dashboard.status.issues_detect')}"
                self.lbl_features_active.configure(text_color="#E74C3C")
                status_text += f" | ✅ {self.tr('manager.dashboard.status.no_issues')}"
                self.lbl_features_active.configure(text_color="gray")
                
            self.lbl_features_active.configure(text=status_text)
            
            # Update Checker Mini-Visual
            if self.update_checker:
                info = self.update_checker.get_cached_update()
                if info and info.is_newer:
                    self.btn_upgrade.configure(text=f"Update Available (v{info.latest_version})", fg_color="#E74C3C", hover_color="#C0392B")
                    self.btn_upgrade.pack(pady=2)
                elif self.lbl_install_type.cget("text") == self.tr("manager.dashboard.status.install_minimal"):
                    # Show upgrade prompt if minimal and no update
                    self.btn_upgrade.configure(text=self.tr("manager.dashboard.status.upgrade_full"), fg_color="#2ECC71", hover_color="#27AE60")
                    self.btn_upgrade.pack(pady=2)
                else:
                    self.btn_upgrade.pack_forget()
            
        except:
            self.lbl_features_active.configure(text="Unknown Status")
            
        # 2. Install Type (Heuristic)
        tools_dir = self.src_dir.parent / "tools"
        has_blender = (tools_dir / "blender").exists()
        has_ffmpeg = (tools_dir / "ffmpeg").exists()
        
        if has_blender and has_ffmpeg:
            self.lbl_install_type.configure(text=self.tr("manager.dashboard.status.install_full"), text_color=("#2ECC71", "#27AE60"))
            self.btn_upgrade.pack_forget()
        else:
            self.lbl_install_type.configure(text=self.tr("manager.dashboard.status.install_minimal"), text_color=("#3498DB", "#2980B9"))
            self.btn_upgrade.pack(pady=2)

        # Last Sync Time
        last_sync = self.settings.get("LAST_REGISTRY_SYNC", "Never")
        if last_sync != "Never":
            try:
                dt = datetime.fromisoformat(last_sync)
                display_time = dt.strftime("%Y-%m-%d %H:%M")
            except: display_time = last_sync
        else:
            display_time = self.tr("manager.dashboard.status.never_synced")
            
        self.lbl_features_active.configure(text=f"{self.lbl_features_active.cget('text')} | 🕒 {display_time}")

    def _restart_explorer(self):
        if messagebox.askyesno(self.tr("manager.dashboard.restart_explorer_title"), self.tr("manager.dashboard.restart_explorer_msg")):
            try:
                subprocess.run(["taskkill", "/f", "/im", "explorer.exe"], check=False)
                subprocess.Popen(["explorer.exe"])
                self.config_manager.load_config(force_reload=True) # Refresh internal state too
                self._refresh_status()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to restart Explorer: {e}")

    def _force_re_register(self):
        try:
            self.master.master.master.save_all_and_apply()
            # Update timestamp
            self.settings.set("LAST_REGISTRY_SYNC", datetime.now().isoformat())
            self.settings.save()
            self._refresh_status()
            # Ask to restart explorer
            # self._restart_explorer() # Optional, maybe too aggressive to auto-chain? Let user decide.
        except Exception as e:
             messagebox.showerror("Error", str(e))

    def _on_check_updates_click(self):
        if not self.update_checker: return
        self.lbl_install_type.configure(text="Checking...")
        
        def on_result(info):
            self.after(0, lambda: self._refresh_status())
            if info and info.is_newer:
                self.after(0, lambda: messagebox.showinfo("Update Available", f"New version {info.latest_version} available!"))
            else:
                self.after(0, lambda: messagebox.showinfo("Up to Date", "You are using the latest version."))
        
        self.update_checker.check_for_updates(callback=on_result)

    # ========================
    # 2. APPEARANCE & BEHAVIOR
    # ========================
    def _setup_appearance_behavior(self):
        card = ctk.CTkFrame(self.scroll, corner_radius=8)
        card.grid(row=1, column=0, sticky="nsew", padx=(0, 5), pady=5)
        card.grid_columnconfigure(1, weight=1)
        
        self._add_header(card, self.tr("manager.dashboard.appearance.title"))
        
        row = 1
        # Theme
        self._add_row_label(card, row, self.tr("manager.dashboard.appearance.theme"))
        self.theme_var = ctk.StringVar(value=self.settings.get("THEME", "Dark"))
        ctk.CTkOptionMenu(card, variable=self.theme_var, values=["Dark", "Light", "System"], width=120,
                         command=self._on_theme_preview).grid(row=row, column=1, sticky="e", padx=15, pady=5)
        row += 1
        
        # Language
        self._add_row_label(card, row, self.tr("manager.dashboard.appearance.language"))
        current_lang = self.settings.get("LANGUAGE", "en")
        self.lang_var = ctk.StringVar(value=f"{current_lang}")
        ctk.CTkOptionMenu(card, variable=self.lang_var, values=["en", "ko"], width=120).grid(row=row, column=1, sticky="e", padx=15, pady=5)
        row += 1
        
        # Separator
        ctk.CTkFrame(card, height=2, fg_color=("gray90", "gray30")).grid(row=row, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        row += 1
        
        # Menu Position (Top)
        self._add_row_label(card, row, self.tr("manager.dashboard.appearance.show_menu_top"))
        self.var_menu_top = ctk.BooleanVar(value=self.settings.get("MENU_POSITION_TOP", True))
        ctk.CTkCheckBox(card, text="", variable=self.var_menu_top, width=24).grid(row=row, column=1, sticky="e", padx=15, pady=5)
        row += 1
        
        # Auto-start Tray
        import winreg
        def is_startup():
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
                winreg.QueryValueEx(key, "ContextUpTray")
                winreg.CloseKey(key)
                return True
            except: return False
            
        self._add_row_label(card, row, self.tr("manager.dashboard.appearance.start_tray_login"))
        self.var_startup = ctk.BooleanVar(value=is_startup())
        ctk.CTkCheckBox(card, text="", variable=self.var_startup, width=24).grid(row=row, column=1, sticky="e", padx=15, pady=5)
        row += 1

    def _on_theme_preview(self, value):
        ctk.set_appearance_mode(value)



    # ========================
    # 3. HOTKEYS (Right Col)
    # ========================
    def _setup_hotkeys_section(self):
        card = ctk.CTkFrame(self.scroll, corner_radius=8)
        # Just row 1
        card.grid(row=1, column=1, sticky="nsew", padx=(5, 0), pady=5)
        card.grid_columnconfigure(0, weight=1)
        
        # Header with slightly different text maybe?
        self._add_header(card, self.tr("manager.dashboard.info.main_hotkeys"))
        
        hk_container = ctk.CTkFrame(card, fg_color="transparent") # Transparent inside card
        hk_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        # 1. Quick Menu
        self._add_hotkey_row(hk_container, "Ctrl+Shift+C", self.tr("manager.dashboard.info.quick_menu"))
        
        # 2. Configured Hotkeys
        try:
            items = []
            if self.config_manager:
                items = self.config_manager.load_config(force_reload=False)
            else:
                from core.config import MenuConfig
                items = MenuConfig().items
            
            for item in items:
                hk = item.get("hotkey")
                if hk:
                    name = item.get("name", "Unknown")
                    self._add_hotkey_row(hk_container, hk.upper(), name)
                    
        except Exception as e:
            logger.error(f"Failed to load hotkeys: {e}")

    # ========================
    # 4. CONNECTIVITY (Paths & APIs)
    # ========================
    def _setup_connectivity_section(self):
        card = ctk.CTkFrame(self.scroll, corner_radius=8)
        card.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)
        card.grid_columnconfigure(1, weight=1)
        
        self._add_header(card, self.tr("manager.dashboard.connectivity.title"))
        
        # --- Tools ---
        r = 1
        tools_map = [
            ("PYTHON_PATH", self.tr("manager.dashboard.connectivity.python")),
            ("FFMPEG_PATH", self.tr("manager.dashboard.connectivity.ffmpeg")),
            ("BLENDER_PATH", self.tr("manager.dashboard.connectivity.blender")),
            ("MAYO_PATH", self.tr("manager.dashboard.connectivity.mayo"))
        ]
        
        for key, name in tools_map:
            
            ctk.CTkLabel(card, text=name, width=80, anchor="w", font=ctk.CTkFont(weight="bold")).grid(row=r, column=0, padx=15, pady=5)
            
            frame = ctk.CTkFrame(card, fg_color="transparent")
            frame.grid(row=r, column=1, sticky="ew", padx=15, pady=5)
            
            val = self.settings.get(key, "")
            chk_var = ctk.BooleanVar(value=bool(val))
            self.tool_vars[key] = chk_var
            
            entry = ctk.CTkEntry(frame)
            entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
            entry.insert(0, val)
            
            if not val:
                 entry.configure(state="disabled", text_color="gray")
            
            self.tool_entries[key] = entry
            
            # Logic to enable/disable
            def on_chk(k=key, e=entry, v=chk_var):
                if v.get():
                    e.configure(state="normal", text_color=("black", "white"))
                else:
                    e.configure(state="disabled", text_color="gray")
                    
            chk = ctk.CTkCheckBox(frame, text="", variable=chk_var, width=20, command=on_chk)
            chk.pack(side="left", padx=5)
            
            btn = ctk.CTkButton(frame, text="📂", width=30, command=lambda e=entry: self._browse(e))
            btn.pack(side="right")
            
            r += 1
            
        # --- APIs ---
        ctk.CTkFrame(card, height=2, fg_color=("gray90", "gray30")).grid(row=r, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        r += 1
        
        api_map = [
            ("GEMINI_API_KEY", self.tr("manager.dashboard.connectivity.gemini_api")), 
            ("OLLAMA_URL", self.tr("manager.dashboard.connectivity.ollama_url"))
        ]
        
        for key, name in api_map:
            ctk.CTkLabel(card, text=name, width=80, anchor="w", font=ctk.CTkFont(weight="bold")).grid(row=r, column=0, padx=15, pady=5)
            
            entry = ctk.CTkEntry(card, show="•" if "KEY" in key else None)
            entry.grid(row=r, column=1, sticky="ew", padx=15, pady=5)
            default = "http://localhost:11434" if "OLLAMA" in key else ""
            entry.insert(0, self.settings.get(key, default))
            self.api_entries[key] = entry
            
            r += 1

    # ========================
    # 5. DANGER ZONE
    # ========================
    def _setup_danger_section(self):
        # Move to Main Frame (Bottom) instead of Scroll
        card = ctk.CTkFrame(self, corner_radius=8, fg_color=("gray95", "#2c1c1c")) 
        card.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        card.grid_columnconfigure(0, weight=1)
        
        # Header
        header = ctk.CTkLabel(card, text=self.tr("manager.dashboard.danger.title"), text_color="#E74C3C", font=ctk.CTkFont(weight="bold", size=14))
        header.pack(anchor="w", padx=15, pady=(10, 5))
        
        # Content Container
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="x", padx=15, pady=(0, 15))
        
        # Row 1: Data Management
        row1 = ctk.CTkFrame(content, fg_color="transparent")
        row1.pack(fill="x", pady=2)
        
        ctk.CTkLabel(row1, text=self.tr("manager.dashboard.danger.data_management"), width=120, anchor="w", text_color="gray").pack(side="left")
        
        ctk.CTkButton(row1, text=self.tr("manager.dashboard.danger.export_userdata"), width=120, height=28, fg_color="#34495E", command=self._export_userdata).pack(side="left", padx=5)
        ctk.CTkButton(row1, text=self.tr("manager.dashboard.danger.import_userdata"), width=120, height=28, fg_color="#34495E", command=self._import_userdata).pack(side="left", padx=5)
        ctk.CTkButton(row1, text=self.tr("manager.dashboard.danger.backup_settings"), width=120, height=28, fg_color="gray", command=self._backup).pack(side="left", padx=5)

        # Row 2: Reset / Destructive
        row2 = ctk.CTkFrame(content, fg_color="transparent")
        row2.pack(fill="x", pady=(10, 2))
        
        ctk.CTkLabel(row2, text=self.tr("common.reset"), width=120, anchor="w", text_color="#E74C3C").pack(side="left")
        
        ctk.CTkButton(row2, text=self.tr("manager.dashboard.danger.reset_userdata"), width=120, height=28, fg_color="#C0392B", hover_color="#A93226", command=self._reset_userdata).pack(side="left", padx=5)
        ctk.CTkButton(row2, text=self.tr("manager.dashboard.danger.factory_reset"), width=120, height=28, fg_color="#922B21", hover_color="#641E16", command=self._reset).pack(side="left", padx=5)


    # ========================
    # HELPERS
    # ========================
    def _add_header(self, parent, text):
        f = ctk.CTkFrame(parent, height=40, fg_color="transparent")
        f.grid(row=0, column=0, columnspan=2, sticky="ew")
        ctk.CTkLabel(f, text=text, font=ctk.CTkFont(size=15, weight="bold")).pack(side="left", padx=15, pady=10)
        
    def _add_row_label(self, parent, row, text):
        ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(weight="bold"), anchor="w").grid(row=row, column=0, sticky="w", padx=15, pady=5)

    def _add_hotkey_row(self, parent, key, desc):
        row_frame = ctk.CTkFrame(parent, fg_color="transparent")
        row_frame.pack(fill="x", padx=5, pady=2)
        
        ctk.CTkLabel(row_frame, text=key, font=ctk.CTkFont(family="Consolas", weight="bold"), width=100, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(row_frame, text=desc, anchor="w").pack(side="left", padx=5)

    def _browse(self, entry):
        path = filedialog.askopenfilename()
        if path:
            entry.configure(state="normal")
            entry.delete(0, "end")
            entry.insert(0, path)

    # ========================
    # LOGIC: SAVE & PERSIST
    # ========================
    def save(self):
        """Called by Global Apply. Gather all data and update self.settings."""
        logger.info("Saving Dashboard...")
        
        # 1. Appearance
        self.settings["THEME"] = self.theme_var.get()
        self.settings["LANGUAGE"] = self.lang_var.get()
        self.settings["MENU_POSITION_TOP"] = self.var_menu_top.get()
        
        # 2. Behavior (Registry handling)
        self._update_startup_registry()
        
        # 3. Paths & APIs now managed by UpdatesFrame (Dependencies)
            
        logger.info("Settings dictionary updated.")

    def _update_startup_registry(self):
        import winreg
        is_enabled = self.var_startup.get()
        
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
            if is_enabled:
                cmd = f'"{sys.executable}" "{self.src_dir / "tray" / "agent.py"}"'
                winreg.SetValueEx(key, "ContextUpTray", 0, winreg.REG_SZ, cmd)
            else:
                try: winreg.DeleteValue(key, "ContextUpTray")
                except: pass
            winreg.CloseKey(key)
        except Exception as e:
            logger.error(f"Failed to update startup registry: {e}")

    # ========================
    # LOGIC: BACKUP & RESET
    # ========================
    def _backup(self):
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            dest = self.backup_dir / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            dest.mkdir(parents=True)
            if self.config_dir.exists(): shutil.copytree(self.config_dir, dest / "config")
            if self.userdata_dir.exists(): shutil.copytree(self.userdata_dir, dest / "userdata")
            messagebox.showinfo("Backup", f"Backed up to:\n{dest.name}")
        except Exception as e:
            messagebox.showerror(self.tr("common.error"), f"{self.tr('manager.dashboard.danger.backup_failed')}: {e}")

    def _export_userdata(self):
        try:
            if not self.userdata_dir.exists():
                messagebox.showinfo(self.tr("common.info"), "No userdata to export.")
                return
                
            path = filedialog.asksaveasfilename(defaultextension=".zip", filetypes=[("Zip files", "*.zip")], initialfile="contextup_userdata.zip")
            if not path: return
            
            shutil.make_archive(path.replace('.zip', ''), 'zip', self.userdata_dir)
            messagebox.showinfo(self.tr("common.success"), self.tr("manager.dashboard.danger.export_success").format(path=path))
        except Exception as e:
            messagebox.showerror(self.tr("common.error"), str(e))

    def _import_userdata(self):
        if not messagebox.askyesno(self.tr("dialogs.confirm"), self.tr("manager.dashboard.danger.confirm_import")): return
        
        path = filedialog.askopenfilename(filetypes=[("Zip files", "*.zip")])
        if not path: return
        
        try:
            # Clear existing userdata? Or merge? "Import" usually implies restore/overwrite.
            # Safe to clear to avoid ghosts.
            if self.userdata_dir.exists():
                shutil.rmtree(self.userdata_dir)
            self.userdata_dir.mkdir(parents=True, exist_ok=True)
            
            shutil.unpack_archive(path, self.userdata_dir)
            
            # Force refresh
            self.config_manager.load_config(force_reload=True)
            self._refresh_status()
            messagebox.showinfo(self.tr("common.success"), self.tr("manager.dashboard.danger.import_success"))
        except Exception as e:
            messagebox.showerror(self.tr("common.error"), str(e))

    def _reset_userdata(self):
        if not messagebox.askyesno(self.tr("dialogs.confirm"), self.tr("manager.dashboard.danger.confirm_reset_userdata")): return
        try:
            if self.userdata_dir.exists():
                shutil.rmtree(self.userdata_dir)
                self.userdata_dir.mkdir()
                
            messagebox.showinfo(self.tr("common.success"), self.tr("manager.dashboard.danger.reset_complete"))
        except Exception as e:
            messagebox.showerror(self.tr("common.error"), str(e))

    def _reset(self):
        if not messagebox.askyesno(self.tr("dialogs.confirm"), self.tr("manager.dashboard.danger.confirm_reset")): return
        try:
            self._backup()
            for f in self.userdata_dir.glob("*.json"): f.unlink(missing_ok=True)
            ov_file = self.config_dir / "user_overrides.json"
            if ov_file.exists(): ov_file.unlink()
            messagebox.showinfo(self.tr("common.success"), self.tr("manager.dashboard.danger.reset_complete"))
        except Exception as e:
            messagebox.showerror(self.tr("common.error"), f"{self.tr('manager.dashboard.danger.reset_failed')}: {e}")
