"""
Modern Management GUI for ContextUp using CustomTkinter.
"""
import sys
import os
import json
import threading
import uuid
import shutil
from pathlib import Path
import subprocess
import tkinter.colorchooser
import tkinter.colorchooser
from tkinter import messagebox
import importlib.metadata
import webbrowser
import time

import customtkinter as ctk
from PIL import Image

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.append(str(src_dir))

from core.config import MenuConfig
from core.settings import load_settings, save_settings
from core.logger import setup_logger, logger
from utils.config_builder import build_config

# Set default theme
# ctk.set_appearance_mode("Dark") # Removed hardcoded default
ctk.set_default_color_theme("blue")

class ItemEditorDialog(ctk.CTkToplevel):
    def __init__(self, parent, item_data=None):
        super().__init__(parent)
        self.title("Edit Menu Item" if item_data else "Add New Item")
        self.geometry("500x750")
        self.item_data = item_data
        self.result = None
        self.delete_requested = False
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.frame = ctk.CTkFrame(self)
        self.frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.frame.grid_columnconfigure(1, weight=1)
        
        # Name
        ctk.CTkLabel(self.frame, text="Name:").grid(row=0, column=0, sticky="w", pady=10, padx=10)
        self.entry_name = ctk.CTkEntry(self.frame)
        self.entry_name.grid(row=0, column=1, sticky="ew", pady=10, padx=10)
        
        # Category
        ctk.CTkLabel(self.frame, text="Category:").grid(row=1, column=0, sticky="w", pady=10, padx=10)
        categories = list(parent.settings.get("CATEGORY_COLORS", {}).keys())
        if "Custom" not in categories: categories.append("Custom")
        self.combo_category = ctk.CTkComboBox(self.frame, values=categories)
        self.combo_category.grid(row=1, column=1, sticky="ew", pady=10, padx=10)
        self.combo_category.set("Custom")
        
        # Command
        ctk.CTkLabel(self.frame, text="Command:").grid(row=2, column=0, sticky="w", pady=10, padx=10)
        self.entry_command = ctk.CTkEntry(self.frame, placeholder_text="e.g. notepad.exe \"%1\"")
        self.entry_command.grid(row=2, column=1, sticky="ew", pady=10, padx=10)
        
        # Icon
        ctk.CTkLabel(self.frame, text="Icon Path:").grid(row=3, column=0, sticky="w", pady=10, padx=10)
        self.entry_icon = ctk.CTkEntry(self.frame)
        self.entry_icon.grid(row=3, column=1, sticky="ew", pady=10, padx=10)
        ctk.CTkButton(self.frame, text="Browse", width=60, command=self.browse_icon).grid(row=3, column=2, padx=5)
        
        # Types
        ctk.CTkLabel(self.frame, text="File Types:").grid(row=4, column=0, sticky="w", pady=10, padx=10)
        self.entry_types = ctk.CTkEntry(self.frame, placeholder_text="e.g. .jpg;.png or *")
        self.entry_types.grid(row=4, column=1, sticky="ew", pady=10, padx=10)
        
        # Scope
        ctk.CTkLabel(self.frame, text="Scope:").grid(row=5, column=0, sticky="w", pady=10, padx=10)
        self.combo_scope = ctk.CTkComboBox(self.frame, values=["file", "folder", "both"])
        self.combo_scope.grid(row=5, column=1, sticky="ew", pady=10, padx=10)
        self.combo_scope.set("file")

        # Submenu
        ctk.CTkLabel(self.frame, text="Submenu:").grid(row=6, column=0, sticky="w", pady=10, padx=10)
        self.combo_submenu = ctk.CTkComboBox(self.frame, values=["ContextUp", "(Top Level)", "Custom..."])
        self.combo_submenu.grid(row=6, column=1, sticky="ew", pady=10, padx=10)
        self.combo_submenu.set("ContextUp")
        
        help_text = "• 'ContextUp': Default menu.\n• '(Top Level)': Directly in right-click.\n• Type ANY name to create a NEW Root Menu."
        ctk.CTkLabel(self.frame, text=help_text, text_color="gray", font=("", 10), justify="left").grid(row=7, column=1, sticky="w", padx=10)
        
        # Buttons
        btn_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        btn_frame.grid(row=8, column=0, columnspan=3, pady=20, sticky="ew")
        
        ctk.CTkButton(btn_frame, text="Save", command=self.save).pack(side="right", padx=10)
        ctk.CTkButton(btn_frame, text="Cancel", fg_color="transparent", border_width=1, command=self.destroy).pack(side="right", padx=10)
        
        if item_data:
            ctk.CTkButton(btn_frame, text="Delete Item", fg_color="#C0392B", hover_color="#E74C3C", 
                        command=self.delete).pack(side="left", padx=10)
            self.load_data(item_data)
            
    def load_data(self, data):
        self.entry_name.insert(0, data.get('name', ''))
        self.combo_category.set(data.get('category', 'Custom'))
        self.entry_command.insert(0, data.get('command', ''))
        self.entry_icon.insert(0, data.get('icon', ''))
        self.entry_types.insert(0, data.get('types', '*'))
        self.combo_scope.set(data.get('scope', 'file'))
        self.combo_submenu.set(data.get('submenu', 'ContextUp'))
        
    def browse_icon(self):
        path = ctk.filedialog.askopenfilename(filetypes=[("Icon Files", "*.ico"), ("All Files", "*.*")])
        if path:
            self.entry_icon.delete(0, "end")
            self.entry_icon.insert(0, path)
            
    def save(self):
        if not self.entry_name.get(): return
        self.result = {
            "name": self.entry_name.get(),
            "category": self.combo_category.get(),
            "command": self.entry_command.get(),
            "icon": self.entry_icon.get(),
            "types": self.entry_types.get(),
            "scope": self.combo_scope.get(),
            "submenu": self.combo_submenu.get(),
            "enabled": True,
            "status": "COMPLETE"
        }
        if self.item_data: self.result['id'] = self.item_data['id']
        else:
            safe_name = "".join(c for c in self.result['name'] if c.isalnum()).lower()
            self.result['id'] = f"custom_{safe_name}_{uuid.uuid4().hex[:4]}"
        self.destroy()

    def delete(self):
        if ctk.CTkInputDialog(text="Type 'delete' to confirm:", title="Delete Item").get_input() == 'delete':
            self.delete_requested = True
            self.destroy()

class ManagerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ContextUp Manager v3.0")
        self.geometry("1100x800")
        
        self.config_path = src_dir.parent / "config" / "menu_config.json"
        self.settings = load_settings()
        
        # Init Logger
        log_level = self.settings.get("LOG_LEVEL", "Debug (All)")
        setup_logger(log_level)
        logger.info("Manager GUI started")
        
        # Apply saved theme
        saved_theme = self.settings.get("THEME", "System")
        ctk.set_appearance_mode(saved_theme)
        
        self.config_data = []
        self.tool_entries = {}
        self.tool_entries = {}
        self.tool_vars = {}
        
        # Load Dependency Metadata
        self.dep_metadata = {}
        self.load_dep_metadata()
        
        # Cache installed packages
        self.installed_packages = self.get_installed_packages()
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.create_sidebar()
        self.create_main_area()
        self.load_config()
        self.show_frame("editor")
        self.after(1000, self.run_health_check_silent)

    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(8, weight=1)
        
        # Title & Version
        title_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        title_frame.grid(row=0, column=0, padx=20, pady=(20, 10))
        ctk.CTkLabel(title_frame, text="ContextUp", font=ctk.CTkFont(size=20, weight="bold")).pack()
        ctk.CTkLabel(title_frame, text="v3.2", text_color="gray", font=ctk.CTkFont(size=12)).pack()
        
        # Navigation Group
        ctk.CTkLabel(self.sidebar, text="Navigation", text_color="gray", font=("", 12)).grid(row=1, column=0, padx=20, pady=(10, 5), sticky="w")
        ctk.CTkButton(self.sidebar, text="Menu Editor", command=lambda: self.show_frame("editor")).grid(row=2, column=0, padx=20, pady=5)
        ctk.CTkButton(self.sidebar, text="Settings", command=lambda: self.show_frame("settings")).grid(row=3, column=0, padx=20, pady=5)
        ctk.CTkButton(self.sidebar, text="Updates & Health", command=lambda: self.show_frame("updates")).grid(row=4, column=0, padx=20, pady=5)
        ctk.CTkButton(self.sidebar, text="Backups & Logs", command=lambda: self.show_frame("logs")).grid(row=5, column=0, padx=20, pady=5)
        
        # Configuration Group
        ctk.CTkLabel(self.sidebar, text="Configuration", text_color="gray", font=("", 12)).grid(row=5, column=0, padx=20, pady=(20, 5), sticky="w")
        
        btn_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        btn_frame.grid(row=6, column=0, padx=10, pady=5)
        ctk.CTkButton(btn_frame, text="Import", width=80, command=self.import_config).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="Export", width=80, command=self.export_config).pack(side="left", padx=2)
        
        ctk.CTkButton(self.sidebar, text="Reset to Default", fg_color="#C0392B", hover_color="#E74C3C", 
                     command=self.reset_to_default).grid(row=7, column=0, padx=20, pady=10)
        
        # Apply Button at bottom
        ctk.CTkButton(self.sidebar, text="Apply Changes", fg_color="green", hover_color="darkgreen", 
                     command=self.apply_registry).grid(row=9, column=0, padx=20, pady=20)

    def create_main_area(self):
        self.frame_editor = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.setup_editor_frame()
        self.frame_settings = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.setup_settings_frame()
        self.frame_updates = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.setup_updates_frame()
        self.frame_logs = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.setup_log_frame()

    def setup_editor_frame(self):
        self.frame_editor.grid_columnconfigure(0, weight=1)
        self.frame_editor.grid_rowconfigure(3, weight=1) 
        
        # Toolbar
        toolbar = ctk.CTkFrame(self.frame_editor, height=40)
        toolbar.grid(row=0, column=0, sticky="ew", padx=20, pady=(10,0))
        ctk.CTkLabel(toolbar, text="Menu Items", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=15, pady=5)
        # Buttons removed from here

        # Filter Bar
        filter_frame = ctk.CTkFrame(self.frame_editor, height=40, fg_color="transparent")
        filter_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(5,0))
        
        ctk.CTkLabel(filter_frame, text="Filter:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(5, 10))
        self.filter_cat_var = ctk.StringVar(value="All Categories")
        cat_values = ["All Categories"] + list(self.settings.get("CATEGORY_COLORS", {}).keys()) + ["Custom"]
        cat_values = sorted(list(set(cat_values)), key=lambda x: (x != "All Categories", x))
        self.filter_cat = ctk.CTkComboBox(filter_frame, values=cat_values, width=130, variable=self.filter_cat_var, command=self.refresh_list)
        self.filter_cat.pack(side="left", padx=5)

        self.filter_sub_var = ctk.StringVar(value="All Locations")
        self.filter_sub = ctk.CTkComboBox(filter_frame, values=["All Locations", "ContextUp", "(Top Level)", "Custom"], width=130, variable=self.filter_sub_var, command=self.refresh_list)
        self.filter_sub.pack(side="left", padx=5)

        self.filter_stat_var = ctk.StringVar(value="All Status")
        self.filter_stat = ctk.CTkComboBox(filter_frame, values=["All Status", "Enabled", "Disabled"], width=110, variable=self.filter_stat_var, command=self.refresh_list)
        self.filter_stat.pack(side="left", padx=5)
        ctk.CTkButton(filter_frame, text="Reset", width=60, fg_color="gray", command=self.reset_filters).pack(side="left", padx=10)
        
        # Tools in Filter Bar
        ctk.CTkLabel(filter_frame, text="|", text_color="gray").pack(side="left", padx=10)
        ctk.CTkButton(filter_frame, text="Group by Category", width=120, fg_color="#2980b9", command=self.preset_group_by_category).pack(side="left", padx=5)
        ctk.CTkButton(filter_frame, text="Reset to Flat", width=100, fg_color="gray", command=self.preset_flat).pack(side="left", padx=5)
        
        # Header
        header_frame = ctk.CTkFrame(self.frame_editor, height=30, fg_color="transparent")
        header_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(5,0))
        
        # List
        self.scroll_frame = ctk.CTkScrollableFrame(self.frame_editor, label_text="")
        self.scroll_frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=5)
        self.scroll_frame.grid_columnconfigure(0, weight=1)
        self.item_widgets = {} 

    def setup_settings_frame(self):
        self.frame_settings.grid_columnconfigure(0, weight=1)
        self.frame_settings.grid_rowconfigure(4, weight=1) 
        
        # 1. Configuration Management
        config_frame = ctk.CTkFrame(self.frame_settings)
        config_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
        
        # Header with Theme Selection
        header_row = ctk.CTkFrame(config_frame, fg_color="transparent")
        header_row.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(header_row, text="Configuration", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        
        # Theme Selector
        ctk.CTkLabel(header_row, text="Theme:", width=60).pack(side="left", padx=(20, 5))
        self.option_theme = ctk.CTkOptionMenu(header_row, values=["System", "Light", "Dark"],
                                            command=self.change_appearance_mode_event, width=100)
        self.option_theme.pack(side="left")
        self.option_theme.pack(side="left")
        self.option_theme.set(self.settings.get("THEME", "System"))
        
        # Log Level
        ctk.CTkLabel(header_row, text="Log Level:", width=70).pack(side="left", padx=(20, 5))
        self.option_log = ctk.CTkOptionMenu(header_row, values=["Debug (All)", "Minimal (Errors Only)", "Disabled"],
                                            command=self.change_log_level, width=150)
        self.option_log.pack(side="left")
        self.option_log.set(self.settings.get("LOG_LEVEL", "Debug (All)"))

        # Determine internal tools path
        internal_tools_path = src_dir.parent / "Tools"
        
        tools_frame = ctk.CTkFrame(config_frame, fg_color="transparent")
        tools_frame.pack(fill="x", padx=5, pady=5)
        
        for tool in ["FFMPEG_PATH", "BLENDER_PATH", "MAYO_PATH"]:
            tool_name = tool.replace("_PATH", "")
            row = ctk.CTkFrame(tools_frame, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=2)
            
            # Label
            ctk.CTkLabel(row, text=tool_name + ":", width=80, anchor="w").pack(side="left")
            
            # Default Path Logic
            default_path = internal_tools_path / tool_name.lower() / (tool_name.lower() + ".exe")
            current_val = self.settings.get(tool, "")
            is_custom = bool(current_val)
            
            # Checkbox
            chk_var = ctk.BooleanVar(value=is_custom)
            self.tool_vars[tool] = chk_var
            chk = ctk.CTkCheckBox(row, text="Custom", variable=chk_var, width=80, 
                                command=lambda t=tool: self.toggle_tool_entry(t))
            chk.pack(side="left", padx=5)
            
            # Entry
            entry = ctk.CTkEntry(row)
            entry.pack(side="left", fill="x", expand=True, padx=5)
            if is_custom:
                entry.insert(0, current_val)
            else:
                entry.insert(0, str(default_path))
                entry.configure(state="disabled", text_color="gray")
                
            ctk.CTkButton(row, text="Browse", width=60, command=lambda e=entry: self.browse_file(e)).pack(side="right")
            self.tool_entries[tool] = entry
            
        ctk.CTkButton(tools_frame, text="Save Tool Paths", command=self.save_app_settings).pack(anchor="w", padx=20, pady=10)

        # 2. API Configuration
        api_frame = ctk.CTkFrame(self.frame_settings)
        api_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        ctk.CTkLabel(api_frame, text="API Configuration", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=5)

        # Gemini
        row_gemini = ctk.CTkFrame(api_frame, fg_color="transparent")
        row_gemini.pack(fill="x", padx=20, pady=2)
        ctk.CTkLabel(row_gemini, text="Gemini API Key:", width=100, anchor="w").pack(side="left")
        self.entry_gemini = ctk.CTkEntry(row_gemini, show="*")
        self.entry_gemini.pack(side="left", fill="x", expand=True, padx=5)
        self.entry_gemini.insert(0, self.settings.get("GEMINI_API_KEY", ""))

        # Ollama
        row_ollama = ctk.CTkFrame(api_frame, fg_color="transparent")
        row_ollama.pack(fill="x", padx=20, pady=2)
        ctk.CTkLabel(row_ollama, text="Ollama URL:", width=100, anchor="w").pack(side="left")
        self.entry_ollama = ctk.CTkEntry(row_ollama)
        self.entry_ollama.pack(side="left", fill="x", expand=True, padx=5)
        self.entry_ollama.insert(0, self.settings.get("OLLAMA_URL", "http://localhost:11434"))

        ctk.CTkButton(api_frame, text="Save API Settings", command=self.save_api_settings).pack(anchor="w", padx=20, pady=10)

        # 3. Management Section (Split into Categories and Groups)
        mgmt_frame = ctk.CTkFrame(self.frame_settings, fg_color="transparent")
        mgmt_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        mgmt_frame.grid_columnconfigure(0, weight=1)
        mgmt_frame.grid_columnconfigure(1, weight=1)

        # --- Left: Category Management ---
        cat_frame = ctk.CTkFrame(mgmt_frame)
        cat_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)
        
        cat_header = ctk.CTkFrame(cat_frame, fg_color="transparent")
        cat_header.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(cat_header, text="Category Management", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        
        # Add Category (Inline)
        ctk.CTkButton(cat_header, text="+", width=30, command=self.add_category).pack(side="right")
        self.new_cat_name = ctk.CTkEntry(cat_header, placeholder_text="New Cat", width=80)
        self.new_cat_name.pack(side="right", padx=5)

        # Vertical Scroll for Categories
        self.cat_grid = ctk.CTkScrollableFrame(cat_frame, height=150)
        self.cat_grid.pack(fill="both", expand=True, padx=10, pady=5)
        ctk.CTkLabel(cat_frame, text="* Click chip to edit color", text_color="gray", font=("", 10)).pack(anchor="w", padx=15)
        self.refresh_category_grid()

        # --- Right: Group Management ---
        group_frame = ctk.CTkFrame(mgmt_frame)
        group_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=5)
        
        group_header = ctk.CTkFrame(group_frame, fg_color="transparent")
        group_header.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(group_header, text="Group Management", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        
        # Group Actions
        ctk.CTkButton(group_header, text="Group by Category", width=120, fg_color="#2980b9", command=self.preset_group_by_category).pack(side="right", padx=2)
        
        # Group List (Vertical Scroll)
        self.group_scroll = ctk.CTkScrollableFrame(group_frame, height=150)
        self.group_scroll.pack(fill="both", expand=True, padx=10, pady=5)
        self.refresh_group_list()

    def setup_updates_frame(self):
        self.frame_updates.grid_columnconfigure(0, weight=1)
        self.frame_updates.grid_rowconfigure(2, weight=1)
        
        # 1. Dependency Manager
        dep_frame = ctk.CTkFrame(self.frame_updates)
        dep_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
        
        ctk.CTkLabel(dep_frame, text="Dependency Manager", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=10)
        
        btn_row = ctk.CTkFrame(dep_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkButton(btn_row, text="Update All Libraries", command=self.update_all_libs).pack(side="left", padx=5)
        ctk.CTkButton(btn_row, text="Reinstall Dependencies", fg_color="#C0392B", hover_color="#E74C3C", 
                     command=self.reinstall_libs).pack(side="left", padx=5)
        
        ctk.CTkLabel(dep_frame, text="* 'Update All' runs pip install -U -r requirements.txt", text_color="gray", font=("", 10)).pack(anchor="w", padx=25, pady=5)

        # 2. Tool Links
        link_frame = ctk.CTkFrame(self.frame_updates)
        link_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        
        ctk.CTkLabel(link_frame, text="External Tool Links", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=10)
        
        links = {
            "FFmpeg": "https://ffmpeg.org/download.html",
            "Blender": "https://www.blender.org/download/",
            "MeshLab": "https://www.meshlab.net/#download",
            "Ollama": "https://ollama.com/download"
        }
        
        link_row = ctk.CTkFrame(link_frame, fg_color="transparent")
        link_row.pack(fill="x", padx=20, pady=5)
        
        for name, url in links.items():
            ctk.CTkButton(link_row, text=name, width=100, command=lambda u=url: webbrowser.open(u)).pack(side="left", padx=5)

        # 3. Installed Libraries (Cleaner)
        cleaner_frame = ctk.CTkFrame(self.frame_updates)
        cleaner_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        
        ctk.CTkLabel(cleaner_frame, text="Installed Libraries", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=10)
        
        self.lib_scroll = ctk.CTkScrollableFrame(cleaner_frame, height=150)
        self.lib_scroll.pack(fill="both", expand=True, padx=20, pady=5)
        
        ctk.CTkButton(cleaner_frame, text="Refresh List", command=self.refresh_lib_list, width=100).pack(pady=5)

        # 4. System Health (Moved from Settings)
        health_frame = ctk.CTkFrame(self.frame_updates)
        health_frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=10)
        
        header = ctk.CTkFrame(health_frame, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(header, text="System Health", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        ctk.CTkButton(header, text="Run Diagnostics", width=100, command=self.run_health_check).pack(side="right")
        self.health_textbox = ctk.CTkTextbox(health_frame)
        self.health_textbox.pack(fill="both", expand=True, padx=20, pady=5)

    def update_all_libs(self):
        if not messagebox.askyesno("Confirm", "Update all libraries defined in requirements.txt?"): return
        req_path = src_dir.parent / "requirements.txt"
        if not req_path.exists():
            messagebox.showerror("Error", "requirements.txt not found.")
            return
        
        # Reuse install_dependencies logic but for requirements file
        # We'll create a custom thread for this
        top = ctk.CTkToplevel(self)
        top.title("Updating Libraries")
        top.geometry("400x100")
        lbl = ctk.CTkLabel(top, text="Updating...", font=("", 14))
        lbl.pack(pady=30)
        
        def run():
            python_exe = sys.executable
            try:
                subprocess.check_call([python_exe, "-m", "pip", "install", "-U", "-r", str(req_path)])
                self.after(0, lambda: messagebox.showinfo("Success", "Libraries updated!"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", f"Update failed: {e}"))
            self.after(0, top.destroy)
            
        threading.Thread(target=run, daemon=True).start()

    def reinstall_libs(self):
        if not messagebox.askyesno("Confirm Reinstall", "This will DELETE all libraries and reinstall them from requirements.txt.\nAre you sure?"): return
        # Call the reset_libs script logic or similar
        # Since reset_libs.py is external, we can run it or implement logic here.
        # Let's run the external script in a new console for safety/visibility?
        # Or just implement logic here.
        # Implementing here is better for UX (progress bar).
        # But deleting site-packages while running might be risky if we delete customtkinter.
        # Actually, we CANNOT delete customtkinter while running the GUI that depends on it.
        # So we must launch an external script and close the GUI.
        
        reset_script = src_dir.parent / "tools" / "reset_libs.py"
        if not reset_script.exists():
            messagebox.showerror("Error", "reset_libs.py not found.")
            return
            
        subprocess.Popen([sys.executable, str(reset_script)], creationflags=subprocess.CREATE_NEW_CONSOLE)
        self.destroy() # Close Manager

    def refresh_lib_list(self):
        for widget in self.lib_scroll.winfo_children(): widget.destroy()
        
        installed = sorted(list(self.get_installed_packages()))
        
        for lib in installed:
            row = ctk.CTkFrame(self.lib_scroll, fg_color="transparent")
            row.pack(fill="x", pady=2)
            
            # Check if critical
            meta = self.dep_metadata.get(lib, {})
            is_critical = meta.get('is_critical', False)
            
            # Also check hardcoded criticals just in case
            if lib in ['customtkinter', 'pillow', 'requests', 'pip', 'setuptools', 'wheel']: is_critical = True
            
            ctk.CTkLabel(row, text=lib, anchor="w").pack(side="left", padx=5, fill="x", expand=True)
            
            if is_critical:
                ctk.CTkLabel(row, text="System", text_color="gray", width=60).pack(side="right", padx=5)
            else:
                ctk.CTkButton(row, text="Uninstall", width=60, fg_color="#C0392B", hover_color="#E74C3C",
                            command=lambda l=lib: self.uninstall_lib(l)).pack(side="right", padx=5)

    def uninstall_lib(self, lib_name):
        if not messagebox.askyesno("Confirm Uninstall", f"Uninstall '{lib_name}'?"): return
        
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "-y", lib_name])
            messagebox.showinfo("Success", f"Uninstalled {lib_name}")
            self.installed_packages = self.get_installed_packages()
            self.refresh_lib_list()
            self.refresh_list() # Update tool status
        except Exception as e:
            messagebox.showerror("Error", f"Failed to uninstall: {e}")

    def toggle_tool_entry(self, tool):
        is_custom = self.tool_vars[tool].get()
        entry = self.tool_entries[tool]
        
        if is_custom:
            entry.configure(state="normal", text_color=("black", "white"))
            entry.delete(0, "end")
            # Restore saved value if any, else empty
            saved = self.settings.get(tool, "")
            entry.insert(0, saved)
        else:
            # Show default
            tool_name = tool.replace("_PATH", "")
            internal_tools_path = src_dir.parent / "Tools"
            default_path = internal_tools_path / tool_name.lower() / (tool_name.lower() + ".exe")
            
            entry.delete(0, "end")
            entry.insert(0, str(default_path))
            entry.configure(state="disabled", text_color="gray")

    def refresh_category_grid(self):
        for widget in self.cat_grid.winfo_children(): widget.destroy()
        
        cats = self.settings.get("CATEGORY_COLORS", {})
        
        for name, color in cats.items():
            chip = ctk.CTkFrame(self.cat_grid, fg_color=color, corner_radius=10)
            chip.pack(fill="x", padx=5, pady=2)
            
            # Contrasting text color logic (simple)
            try:
                text_color = "black" if int(color[1:], 16) > 0x888888 else "white"
            except: text_color = "white"
            
            lbl = ctk.CTkLabel(chip, text=name, text_color=text_color)
            lbl.pack(side="left", padx=10, pady=2)
            
            # Delete button (x)
            del_btn = ctk.CTkButton(chip, text="×", width=20, height=20, fg_color="transparent", 
                                  text_color=text_color, hover_color="gray",
                                  command=lambda n=name: self.delete_category(n))
            del_btn.pack(side="right", padx=2)
            
            # Edit color on click - Bind to Frame and Label
            chip.bind("<Button-1>", lambda e, n=name, c=color: self.pick_color(n, c))
            lbl.bind("<Button-1>", lambda e, n=name, c=color: self.pick_color(n, c))

    def refresh_group_list(self):
        for widget in self.group_scroll.winfo_children(): widget.destroy()
        
        # Find unique submenus
        submenus = set()
        for item in self.config_data:
            sub = item.get('submenu', 'ContextUp')
            if sub not in ["ContextUp", "(Top Level)"]:
                submenus.add(sub)
        
        sorted_subs = sorted(list(submenus))
        
        if not sorted_subs:
            ctk.CTkLabel(self.group_scroll, text="No custom groups found.", text_color="gray").pack(pady=10)
            return

        for sub in sorted_subs:
            row = ctk.CTkFrame(self.group_scroll, fg_color="transparent")
            row.pack(fill="x", pady=2)
            
            ctk.CTkLabel(row, text=sub, font=("", 12, "bold")).pack(side="left", padx=5)
            
            # Rename
            ctk.CTkButton(row, text="Rename", width=60, height=24, 
                        command=lambda s=sub: self.rename_group(s)).pack(side="right", padx=2)
            
            # Ungroup (Move to ContextUp)
            ctk.CTkButton(row, text="Ungroup", width=60, height=24, fg_color="gray",
                        command=lambda s=sub: self.ungroup_items(s)).pack(side="right", padx=2)

    def rename_group(self, old_name):
        new_name = ctk.CTkInputDialog(text=f"Rename group '{old_name}' to:", title="Rename Group").get_input()
        if new_name and new_name != old_name:
            count = 0
            for item in self.config_data:
                if item.get('submenu') == old_name:
                    item['submenu'] = new_name
                    count += 1
            if count > 0:
                self.save_config()
                self.refresh_group_list()
                self.refresh_list() # Update main list too if visible
                messagebox.showinfo("Success", f"Renamed {count} items to '{new_name}'.")

    def ungroup_items(self, group_name):
        if not messagebox.askyesno("Confirm", f"Move all items in '{group_name}' to 'ContextUp'?"): return
        count = 0
        for item in self.config_data:
            if item.get('submenu') == group_name:
                item['submenu'] = "ContextUp"
                count += 1
        if count > 0:
            self.save_config()
            self.refresh_group_list()
            self.refresh_list()
            messagebox.showinfo("Success", f"Moved {count} items to ContextUp.")

    def browse_file(self, entry):
        path = ctk.filedialog.askopenfilename()
        if path:
            entry.delete(0, "end")
            entry.insert(0, path)

    def import_config(self):
        path = ctk.filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    new_data = json.load(f)
                self.config_data = new_data
                self.save_config()
                self.refresh_list()
                self.refresh_group_list()
                messagebox.showinfo("Success", "Configuration imported successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import: {e}")

    def export_config(self):
        path = ctk.filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if path:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(self.config_data, f, indent=4)
                messagebox.showinfo("Success", "Configuration exported successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export: {e}")

    def add_category(self):
        name = self.new_cat_name.get().strip()
        if not name: return
        if name in self.settings.get("CATEGORY_COLORS", {}): return
        
        color = tkinter.colorchooser.askcolor(title="Choose Color")[1]
        if color:
            if "CATEGORY_COLORS" not in self.settings: self.settings["CATEGORY_COLORS"] = {}
            self.settings["CATEGORY_COLORS"][name] = color
            save_settings(self.settings)
            self.refresh_category_grid()
            self.new_cat_name.delete(0, "end")

    def delete_category(self, name):
        if name in self.settings.get("CATEGORY_COLORS", {}):
            del self.settings["CATEGORY_COLORS"][name]
            save_settings(self.settings)
            self.refresh_category_grid()

    def pick_color(self, name, current_color):
        color = tkinter.colorchooser.askcolor(color=current_color, title=f"Color for {name}")[1]
        if color:
            self.settings["CATEGORY_COLORS"][name] = color
            save_settings(self.settings)
            self.refresh_category_grid()

    def show_frame(self, name):
        self.frame_editor.grid_forget()
        self.frame_settings.grid_forget()
        self.frame_updates.grid_forget()
        self.frame_logs.grid_forget()
        
        if name == "editor": self.frame_editor.grid(row=0, column=1, sticky="nsew")
        elif name == "settings": 
            self.frame_settings.grid(row=0, column=1, sticky="nsew")
            self.refresh_group_list()
        elif name == "updates":
            self.frame_updates.grid(row=0, column=1, sticky="nsew")
        elif name == "logs":
            self.frame_logs.grid(row=0, column=1, sticky="nsew")
            self.refresh_logs()
            self.refresh_backups()

    def change_log_level(self, new_level: str):
        self.settings["LOG_LEVEL"] = new_level
        save_settings(self.settings)
        setup_logger(new_level)
        logger.info(f"Log level changed to: {new_level}")

    def sync_tool_config(self, item):
        """Updates the individual tool config file in config/tools/"""
        tool_id = item.get('id')
        if not tool_id: return
        
        tool_path = src_dir.parent / "config" / "tools" / f"{tool_id}.json"
        if tool_path.exists():
            try:
                # We only want to update fields that are managed by the GUI
                # But to be safe, we should load the existing file, update it, and save.
                with open(tool_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Update fields
                data['name'] = item['name']
                data['category'] = item['category']
                data['command'] = item['command']
                data['icon'] = item['icon']
                data['types'] = item['types']
                data['scope'] = item['scope']
                data['submenu'] = item['submenu']
                data['enabled'] = item['enabled']
                
                with open(tool_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4)
                logger.info(f"Synced config for {tool_id}")
            except Exception as e:
                logger.error(f"Failed to sync config for {tool_id}: {e}")

    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)
        self.settings["THEME"] = new_appearance_mode
        save_settings(self.settings)

    def reset_filters(self):
        self.filter_cat_var.set("All Categories")
        self.filter_sub_var.set("All Locations")
        self.filter_stat_var.set("All Status")
        self.refresh_list()

    def load_config(self):
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config_data = json.load(f)
            self.refresh_list()
        except Exception as e:
            print(f"Error loading config: {e}")

    def refresh_list(self, _=None):
        for widget in self.scroll_frame.winfo_children(): widget.destroy()
        self.item_widgets = {}
        
        f_cat = self.filter_cat_var.get()
        f_sub = self.filter_sub_var.get()
        f_stat = self.filter_stat_var.get()
        
        # Sort data: Category first, then Name
        sorted_data = sorted(self.config_data, key=lambda x: (x.get('category', 'Custom'), x['name']))
        
        for i, item in enumerate(sorted_data):
            if f_cat != "All Categories" and item.get('category', 'Custom') != f_cat: continue
            
            item_sub = item.get('submenu', 'ContextUp')
            if f_sub != "All Locations":
                if f_sub == "Custom" and item_sub not in ["ContextUp", "(Top Level)"]: pass
                elif item_sub != f_sub: continue

            if f_stat != "All Status":
                is_enabled = item.get('enabled', True)
                if f_stat == "Enabled" and not is_enabled: continue
                if f_stat == "Disabled" and is_enabled: continue

            # We need to find the original index for editing
            original_index = self.config_data.index(item)
            self.create_item_card(item, original_index, i) # Pass display index for grid
            
        btn_add = ctk.CTkButton(self.scroll_frame, text="+ Add New Function", fg_color="transparent", 
                              border_width=1, border_color="gray", height=40, command=self.add_item)
        btn_add.grid(row=len(self.config_data) + 1, column=0, sticky="ew", padx=10, pady=10)

    def load_icon(self, icon_path, size=(24, 24)):
        try:
            if not icon_path: return None
            if not os.path.isabs(icon_path):
                full_path = src_dir.parent / icon_path
                if not full_path.exists(): return None
            else: full_path = Path(icon_path)
            if not full_path.exists(): return None
            return ctk.CTkImage(light_image=Image.open(full_path), dark_image=Image.open(full_path), size=size)
        except Exception: return None

    def create_item_card(self, item, real_index, display_index):
        card = ctk.CTkFrame(self.scroll_frame, fg_color=("gray85", "gray20"))
        card.grid(row=display_index, column=0, sticky="ew", padx=2, pady=2)
        card.grid_columnconfigure(1, weight=1)
        
        icon_img = self.load_icon(item.get('icon'))
        icon_label = ctk.CTkLabel(card, text="", image=icon_img, width=40) if icon_img else ctk.CTkLabel(card, text="📄", font=("Arial", 16), width=40)
        icon_label.grid(row=0, column=0, padx=5, pady=5)
        icon_label.bind("<Double-Button-1>", lambda e, i=real_index: self.edit_item(i))
        
        name_label = ctk.CTkLabel(card, text=item['name'], font=ctk.CTkFont(size=13, weight="bold"), anchor="w")
        name_label.grid(row=0, column=1, sticky="ew", padx=5)
        name_label.bind("<Double-Button-1>", lambda e, i=real_index: self.edit_item(i))
        
        # Check Dependencies
        is_ready, missing_deps = self.check_dependencies(item)
        
        # Status/Category Label
        if is_ready:
            cat_name = item.get('category', 'Custom')
            cat_color = self.settings.get("CATEGORY_COLORS", {}).get(cat_name, "#7f8c8d")
            cat_text = cat_name
        else:
            cat_color = "#F39C12" # Orange for warning
            cat_text = "Setup Required"
            
        cat_label = ctk.CTkLabel(card, text=cat_text, text_color=cat_color, width=100, font=ctk.CTkFont(size=12, weight="bold"))
        cat_label.grid(row=0, column=2, padx=5)
        
        # Bind clicks
        if is_ready:
            icon_label.bind("<Double-Button-1>", lambda e, i=real_index: self.edit_item(i))
            name_label.bind("<Double-Button-1>", lambda e, i=real_index: self.edit_item(i))
            cat_label.bind("<Double-Button-1>", lambda e, i=real_index: self.edit_item(i))
        else:
            # Bind to Install Dialog
            for widget in [icon_label, name_label, cat_label, card]:
                widget.bind("<Button-1>", lambda e, it=item, m=missing_deps: self.show_install_dialog(it, m))
        
        submenu_var = ctk.StringVar(value=item.get('submenu', 'ContextUp'))
        submenu_combo = ctk.CTkComboBox(card, values=["ContextUp", "(Top Level)", "Custom..."], 
                                      variable=submenu_var, width=120, height=24,
                                      command=lambda v, i=real_index: self.update_submenu(i, v))
        submenu_combo.grid(row=0, column=3, padx=5)
        
        switch_var = ctk.BooleanVar(value=item.get('enabled', True))
        switch = ctk.CTkSwitch(card, text="", width=40, height=20, variable=switch_var, 
                             command=lambda i=real_index, v=switch_var: self.toggle_item(i, v))
        switch.grid(row=0, column=4, padx=10)
        
        if not is_ready:
            switch.configure(state="disabled")
            submenu_combo.configure(state="disabled")
            
        self.item_widgets[real_index] = card

    def update_submenu(self, index, value): self.config_data[index]['submenu'] = value
    def toggle_item(self, index, var): self.config_data[index]['enabled'] = var.get()
    def add_item(self):
        dialog = ItemEditorDialog(self)
        self.wait_window(dialog)
        if dialog.result:
            self.config_data.append(dialog.result)
            self.refresh_list()
            self.refresh_group_list() # Update groups
    def edit_item(self, index):
        item = self.config_data[index]
        dialog = ItemEditorDialog(self, item)
        self.wait_window(dialog)
        if dialog.delete_requested: self.delete_item(index)
        elif dialog.result:
            self.config_data[index] = dialog.result
            self.refresh_list()
            self.refresh_group_list() # Update groups
    def delete_item(self, index):
        del self.config_data[index]
        self.refresh_list()
        self.refresh_group_list() # Update groups
    def save_config(self):
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f: json.dump(self.config_data, f, indent=4)
            
            # Sync to individual files
            for item in self.config_data:
                self.sync_tool_config(item)
                
            print("Config saved and synced.")
            logger.info("Config saved and synced to tools.")
        except Exception as e: 
            print(f"Error saving: {e}")
            logger.error(f"Error saving config: {e}")
    def apply_registry(self):
        self.save_config()
        try:
            python_exe = sys.executable
            manage_script = src_dir.parent / "manage.py"
            subprocess.run([python_exe, str(manage_script), "register"], check=True)
            messagebox.showinfo("Success", "Registry updated successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to register: {e}")
    def save_app_settings(self):
        # Save tools
        for tool, entry in self.tool_entries.items():
            if self.tool_vars[tool].get():
                self.settings[tool] = entry.get().strip()
            else:
                self.settings[tool] = "" # Clear custom path to use default
        save_settings(self.settings)
        messagebox.showinfo("Success", "Settings saved!")

    def save_api_settings(self):
        self.settings["GEMINI_API_KEY"] = self.entry_gemini.get().strip()
        self.settings["OLLAMA_URL"] = self.entry_ollama.get().strip()
        save_settings(self.settings)
        # Also update env vars immediately for this session
        os.environ["GEMINI_API_KEY"] = self.settings["GEMINI_API_KEY"]
        os.environ["OLLAMA_HOST"] = self.settings["OLLAMA_URL"]
        messagebox.showinfo("Success", "API Settings saved!")
        
    def preset_flat(self):
        if not messagebox.askyesno("Confirm Reset", "This will move ALL items to the 'ContextUp' submenu.\nAre you sure?"): return
        for item in self.config_data:
            item['submenu'] = "ContextUp"
        self.save_config()
        self.refresh_list()
        self.refresh_group_list()
        messagebox.showinfo("Done", "All items have been moved to 'ContextUp'.")

    def preset_group_by_category(self):
        if not messagebox.askyesno("Confirm Grouping", "This will move items to submenus matching their Category.\nAre you sure?"): return
        for item in self.config_data:
            cat = item.get('category', 'Custom')
            item['submenu'] = cat
        self.save_config()
        self.refresh_list()
        self.refresh_group_list()
        messagebox.showinfo("Done", "Items have been grouped by Category.")

    def run_health_check(self):
        self.health_textbox.delete("0.0", "end")
        self.health_textbox.insert("0.0", "Running diagnostics...\n")
        threading.Thread(target=self._run_health_thread, daemon=True).start()
    def run_health_check_silent(self): pass
    def _run_health_thread(self):
        try:
            from core.health import HealthCheck
            checker = HealthCheck()
            results = checker.run_all()
            self.after(0, lambda: self._update_health_ui(results))
        except Exception as e: self.after(0, lambda: self.health_textbox.insert("end", f"Error: {e}"))
    def _update_health_ui(self, results):
        self.health_textbox.delete("0.0", "end")
        for category, status, message in results: self.health_textbox.insert("end", f"[{category}] {status}: {message}\n")

    def load_dep_metadata(self):
        try:
            path = src_dir.parent / "config" / "dependency_metadata.json"
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    self.dep_metadata = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load dependency metadata: {e}")

    def get_installed_packages(self):
        try:
            # Check packages in the CURRENT environment (embedded python)
            return {dist.metadata['Name'].lower() for dist in importlib.metadata.distributions()}
        except Exception as e:
            logger.error(f"Failed to list packages: {e}")
            return set()

    def check_dependencies(self, item):
        deps = item.get('dependencies', [])
        if not deps: return True, []
        
        missing = []
        for dep in deps:
            # Map to pip name if possible, else use dep name
            meta = self.dep_metadata.get(dep, {})
            pip_name = meta.get('pip_name', dep).lower()
            
            if pip_name not in self.installed_packages:
                missing.append(dep)
                
        return len(missing) == 0, missing

    def setup_log_frame(self):
        self.frame_logs.grid_columnconfigure(0, weight=1)
        self.frame_logs.grid_rowconfigure(1, weight=1)
        
        # Tabview
        self.log_tabs = ctk.CTkTabview(self.frame_logs)
        self.log_tabs.grid(row=0, column=0, sticky="nsew", padx=20, pady=10)
        self.log_tabs.grid_rowconfigure(0, weight=1)
        self.log_tabs.grid_columnconfigure(0, weight=1)
        
        self.tab_logs = self.log_tabs.add("Logs")
        self.tab_backups = self.log_tabs.add("Backups")
        
        # --- Logs Tab ---
        self.tab_logs.grid_columnconfigure(0, weight=1)
        self.tab_logs.grid_rowconfigure(1, weight=1)
        
        log_ctrl = ctk.CTkFrame(self.tab_logs, fg_color="transparent")
        log_ctrl.grid(row=0, column=0, sticky="ew", pady=5)
        ctk.CTkButton(log_ctrl, text="Refresh Logs", command=self.refresh_logs, width=100).pack(side="left")
        ctk.CTkButton(log_ctrl, text="Clear Logs", command=self.clear_logs, width=100, fg_color="gray").pack(side="left", padx=10)
        
        self.log_text = ctk.CTkTextbox(self.tab_logs, font=("Consolas", 12))
        self.log_text.grid(row=1, column=0, sticky="nsew", pady=5)
        
        # --- Backups Tab ---
        self.tab_backups.grid_columnconfigure(0, weight=1)
        self.tab_backups.grid_rowconfigure(1, weight=1)
        
        backup_ctrl = ctk.CTkFrame(self.tab_backups, fg_color="transparent")
        backup_ctrl.grid(row=0, column=0, sticky="ew", pady=5)
        ctk.CTkButton(backup_ctrl, text="Refresh List", command=self.refresh_backups, width=100).pack(side="left")
        
        self.backup_scroll = ctk.CTkScrollableFrame(self.tab_backups)
        self.backup_scroll.grid(row=1, column=0, sticky="nsew", pady=5)

    def refresh_logs(self):
        self.log_text.delete("0.0", "end")
        log_path = src_dir.parent / "debug.log"
        if log_path.exists():
            try:
                with open(log_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.log_text.insert("0.0", content)
                    self.log_text.see("end")
            except Exception as e:
                self.log_text.insert("0.0", f"Error reading log: {e}")
        else:
            self.log_text.insert("0.0", "No log file found.")

    def clear_logs(self):
        log_path = src_dir.parent / "debug.log"
        if log_path.exists():
            try:
                with open(log_path, 'w', encoding='utf-8') as f: f.write("")
                self.refresh_logs()
                logger.info("Logs cleared by user.")
            except Exception as e: messagebox.showerror("Error", f"Failed to clear logs: {e}")

    def refresh_backups(self):
        for widget in self.backup_scroll.winfo_children(): widget.destroy()
        
        backup_dir = src_dir.parent / "backups"
        if not backup_dir.exists():
            ctk.CTkLabel(self.backup_scroll, text="No backups directory found.").pack(pady=10)
            return
            
        files = sorted(list(backup_dir.glob("*.json")), key=os.path.getmtime, reverse=True)
        if not files:
            ctk.CTkLabel(self.backup_scroll, text="No backup files found.").pack(pady=10)
            return
            
        for f in files:
            row = ctk.CTkFrame(self.backup_scroll, fg_color="transparent")
            row.pack(fill="x", pady=2)
            
            name = f.name
            date_str = datetime.fromtimestamp(f.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            
            ctk.CTkLabel(row, text=f"{date_str} - {name}", anchor="w").pack(side="left", padx=5, fill="x", expand=True)
            ctk.CTkButton(row, text="Restore", width=60, height=24, 
                        command=lambda p=f: self.restore_backup(p)).pack(side="right", padx=5)

    def restore_backup(self, path):
        if not messagebox.askyesno("Confirm Restore", f"Restore configuration from {path.name}?\nCurrent settings will be overwritten."): return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                new_data = json.load(f)
            self.config_data = new_data
            self.save_config()
            self.refresh_list()
            self.refresh_group_list()
            messagebox.showinfo("Success", "Backup restored successfully!")
            logger.info(f"Restored backup from {path.name}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to restore: {e}")
            logger.error(f"Failed to restore backup: {e}")

    def reset_to_default(self):
        if not messagebox.askyesno("Confirm Reset", "This will rebuild the menu configuration from the individual tool files in 'config/tools/'.\nAny unsaved changes in the Manager will be lost.\n\nAre you sure?"): return
        
        try:
            build_config() # Run the builder
            self.load_config() # Reload
            messagebox.showinfo("Success", "Configuration reset to default (rebuilt from tools).")
            logger.info("Configuration reset to default.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reset: {e}")
            logger.error(f"Failed to reset config: {e}")

    def show_install_dialog(self, item, missing_deps):
        msg = f"Feature '{item['name']}' requires additional libraries:\n\n"
        total_size = 0
        
        for dep in missing_deps:
            meta = self.dep_metadata.get(dep, {})
            desc = meta.get('description', 'No description available.')
            size = meta.get('approx_size', 'Unknown')
            msg += f"• {dep}: {desc} (~{size})\n"
            
        msg += "\nDo you want to install them now?"
        
        if messagebox.askyesno("Feature Activation", msg):
            self.install_dependencies(missing_deps)

    def install_dependencies(self, deps):
        # Create progress window
        top = ctk.CTkToplevel(self)
        top.title("Installing Dependencies")
        top.geometry("400x150")
        
        lbl = ctk.CTkLabel(top, text="Installing...", font=("", 14))
        lbl.pack(pady=20)
        
        prog = ctk.CTkProgressBar(top)
        prog.pack(pady=10, padx=20, fill="x")
        prog.set(0)
        
        def run_install():
            python_exe = sys.executable
            total = len(deps)
            success = True
            
            for i, dep in enumerate(deps):
                meta = self.dep_metadata.get(dep, {})
                pip_name = meta.get('pip_name', dep)
                
                self.after(0, lambda d=dep: lbl.configure(text=f"Installing {d}..."))
                
                try:
                    subprocess.check_call([python_exe, "-m", "pip", "install", pip_name])
                except Exception as e:
                    logger.error(f"Failed to install {dep}: {e}")
                    success = False
                    break
                    
                self.after(0, lambda v=(i+1)/total: prog.set(v))
                
            self.after(0, top.destroy)
            if success:
                self.after(0, lambda: messagebox.showinfo("Success", "Installation complete!"))
                # Refresh installed packages cache
                self.installed_packages = self.get_installed_packages()
                self.after(0, self.refresh_list)
            else:
                self.after(0, lambda: messagebox.showerror("Error", "Installation failed. Check logs."))

        threading.Thread(target=run_install, daemon=True).start()

if __name__ == "__main__":
    app = ManagerGUI()
    app.mainloop()
