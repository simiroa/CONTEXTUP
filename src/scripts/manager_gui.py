"""
Modern Management GUI for ContextUp using CustomTkinter.
"""
import sys
import os
import json
import threading
import uuid
from pathlib import Path
import subprocess
import tkinter.colorchooser

from tkinter import messagebox
import webbrowser
from datetime import datetime

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
        self.tool_vars = {}
        
        # Load Dependency Metadata
        self.dep_metadata = {}
        try:
            dep_path = src_dir.parent / "config" / "dependency_metadata.json"
            if dep_path.exists():
                with open(dep_path, 'r', encoding='utf-8') as f:
                    self.dep_metadata = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load dependency metadata: {e}")
        
        # Cache installed packages
        # Cache installed packages
        self.installed_packages = {}
        try:
            # Use pip list --format=json for reliable detection in the embedded environment
            python_exe = sys.executable
            result = subprocess.check_output([python_exe, "-m", "pip", "list", "--format=json"], text=True)
            packages = json.loads(result)
            self.installed_packages = {pkg['name'].lower(): pkg['version'] for pkg in packages}
        except Exception as e:
            logger.error(f"Failed to list packages: {e}")
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.create_sidebar()
        self.create_main_area()
        self.load_config()
        self.show_frame("editor")
        self.after(1000, self.run_health_check_silent)

    def get_installed_packages(self):
        try:
            # Use pip list --format=json for reliable detection in the embedded environment
            python_exe = sys.executable
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            result = subprocess.check_output([python_exe, "-m", "pip", "list", "--format=json"], text=True, startupinfo=startupinfo)
            packages = json.loads(result)
            # Return dict: {name: version}
            return {pkg['name'].lower(): pkg['version'] for pkg in packages}
        except Exception as e:
            logger.error(f"Failed to list packages: {e}")
            return {}

    def check_dependencies(self, item):
        deps = item.get('dependencies', [])
        if not deps: return True, []
        
        # self.installed_packages is now a dict, but 'in' operator checks keys, so this still works
        missing = [d for d in deps if d.lower() not in self.installed_packages]
        return len(missing) == 0, missing



    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=("gray95", "gray15"))
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(10, weight=1)
        # Title & Version
        title_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        title_frame.grid(row=0, column=0, padx=20, pady=(30, 20), sticky="ew")
        ctk.CTkLabel(title_frame, text="ContextUp", font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"), text_color=("gray10", "white")).pack(anchor="w")
        ctk.CTkLabel(title_frame, text="v0.3.2 Manager", font=ctk.CTkFont(size=12), text_color=("gray40", "gray60")).pack(anchor="w")
        
        # Navigation Group
        ctk.CTkLabel(self.sidebar, text="NAVIGATION", text_color=("gray50", "gray60"), font=("", 11, "bold")).grid(row=1, column=0, padx=20, pady=(10, 5), sticky="w")
        
        self.btn_editor = self.create_nav_button("Menu Editor", "editor", 2, icon="📝")
        self.btn_management = self.create_nav_button("Management", "management", 3, icon="🔧")
        self.btn_settings = self.create_nav_button("Configuration", "settings", 4, icon="⚙️")
        self.btn_updates = self.create_nav_button("Updates & Health", "updates", 5, icon="🏥")
        self.btn_logs = self.create_nav_button("Backups & Logs", "logs", 6, icon="📜")
        
        # Spacer to push everything else to bottom
        self.sidebar.grid_rowconfigure(7, weight=1)
        
        # Bottom Action Area
        bottom_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_frame.grid(row=8, column=0, sticky="ew", pady=10)
        
        # Theme Selector
        theme_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        theme_frame.pack(fill="x", padx=20, pady=2)
        ctk.CTkLabel(theme_frame, text="Theme Mode", text_color=("gray10", "gray90"), font=("", 12)).pack(side="left")
        self.option_theme = ctk.CTkOptionMenu(theme_frame, values=["System", "Light", "Dark"],
                                            command=self.change_appearance_mode_event, width=90, height=24,
                                            fg_color=("gray80", "gray30"), button_color=("gray70", "gray40"),
                                            text_color=("black", "white"))
        self.option_theme.pack(side="right")
        self.option_theme.set(self.settings.get("THEME", "System"))

        # Import/Export
        btn_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=5)
        ctk.CTkButton(btn_frame, text="Import", width=80, fg_color=("gray85", "gray25"), text_color=("black", "white"), hover_color=("gray75", "gray35"), command=self.import_config).pack(side="left", padx=2, expand=True, fill="x")
        ctk.CTkButton(btn_frame, text="Export", width=80, fg_color=("gray85", "gray25"), text_color=("black", "white"), hover_color=("gray75", "gray35"), command=self.export_config).pack(side="left", padx=2, expand=True, fill="x")
        
        # Reset
        ctk.CTkButton(bottom_frame, text="Reset to Default", fg_color="transparent", border_width=1, border_color=("#C0392B", "#E74C3C"), text_color=("#C0392B", "#E74C3C"), hover_color=("#FADBD8", "#581818"), 
                      command=self.reset_to_default).pack(fill="x", padx=20, pady=5)
        
        # Apply Button
        ctk.CTkButton(bottom_frame, text="Apply Changes", fg_color=("#27AE60", "#2ECC71"), hover_color=("#2ECC71", "#27AE60"), text_color="white", height=40, font=("", 14, "bold"),
                     command=self.apply_registry).pack(fill="x", padx=20, pady=(10, 20))

    def create_nav_button(self, text, name, row, icon=""):
        # Using a frame to hold icon + text could be nicer, but simple button with text is easier for now.
        # Let's just use text.
        btn = ctk.CTkButton(self.sidebar, text=f"  {text}", fg_color="transparent", 
                            text_color=("gray20", "gray80"), 
                            hover_color=("gray85", "gray25"), 
                            anchor="w", height=36, 
                            font=ctk.CTkFont(size=13),
                            command=lambda: self.show_frame(name))
        btn.grid(row=row, column=0, sticky="ew", padx=10, pady=2)
        return btn

    def create_main_area(self):
        self.frame_editor = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.setup_editor_frame()
        self.frame_management = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.setup_management_frame()
        self.frame_settings = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.setup_settings_frame()
        self.frame_updates = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.setup_updates_frame()
        self.frame_logs = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.setup_log_frame()

    def setup_management_frame(self):
        self.frame_management.grid_columnconfigure(0, weight=1)
        self.frame_management.grid_columnconfigure(1, weight=1)
        self.frame_management.grid_rowconfigure(0, weight=1)

        # --- Left: Category Management ---
        cat_frame = ctk.CTkFrame(self.frame_management)
        cat_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        cat_header = ctk.CTkFrame(cat_frame, fg_color="transparent")
        cat_header.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(cat_header, text="Category Management", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        
        # Add Category (Inline)
        ctk.CTkButton(cat_header, text="+", width=30, command=self.add_category).pack(side="right")
        self.new_cat_name = ctk.CTkEntry(cat_header, placeholder_text="New Cat", width=100)
        self.new_cat_name.pack(side="right", padx=5)

        # Vertical Scroll for Categories
        self.cat_grid = ctk.CTkScrollableFrame(cat_frame)
        self.cat_grid.pack(fill="both", expand=True, padx=10, pady=5)
        ctk.CTkLabel(cat_frame, text="* Click chip to edit color", text_color="gray", font=("", 10)).pack(anchor="w", padx=15, pady=5)
        self.refresh_category_grid()

        # --- Right: Group Management ---
        group_frame = ctk.CTkFrame(self.frame_management)
        group_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        group_header = ctk.CTkFrame(group_frame, fg_color="transparent")
        group_header.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(group_header, text="Group Management", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        
        # Group Actions
        ctk.CTkButton(group_header, text="Group by Category", width=120, fg_color="#2980b9", command=self.preset_group_by_category).pack(side="right", padx=2)
        
        # Group List (Vertical Scroll)
        self.group_scroll = ctk.CTkScrollableFrame(group_frame)
        self.group_scroll.pack(fill="both", expand=True, padx=10, pady=5)
        self.refresh_group_list()

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
        
        # 1. Missing Components Dashboard (Moved from Updates)
        # Card Frame
        dash_frame = ctk.CTkFrame(self.frame_settings, fg_color=("gray90", "gray20"), corner_radius=10)
        dash_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
        
        # Header Row (Title + Refresh Button)
        dash_header = ctk.CTkFrame(dash_frame, fg_color="transparent")
        dash_header.pack(fill="x", padx=15, pady=(15, 5))
        
        ctk.CTkLabel(dash_header, text="Missing Components", font=ctk.CTkFont(size=16, weight="bold"), text_color=("#C0392B", "#E74C3C")).pack(side="left")
        ctk.CTkButton(dash_header, text="↻ Refresh", width=80, height=24, font=ctk.CTkFont(size=12), 
                      fg_color="transparent", border_width=1, border_color="gray", text_color=("gray10", "gray90"),
                      command=self.refresh_missing_dashboard).pack(side="right")
        
        # Content
        self.missing_scroll = ctk.CTkScrollableFrame(dash_frame, height=120, fg_color="transparent")
        self.missing_scroll.pack(fill="x", padx=10, pady=(0, 15))

        # 2. Configuration Management
        config_frame = ctk.CTkFrame(self.frame_settings, corner_radius=10)
        config_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        
        # Header
        header_row = ctk.CTkFrame(config_frame, fg_color="transparent")
        header_row.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(header_row, text="Tool Configuration", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        ctk.CTkButton(header_row, text="Save Paths", width=100, height=28, command=self.save_app_settings).pack(side="right")
        
        # Determine internal tools path
        internal_tools_path = src_dir.parent / "Tools"
        
        tools_frame = ctk.CTkFrame(config_frame, fg_color="transparent")
        tools_frame.pack(fill="x", padx=10, pady=(0, 15))
        
        for tool in ["FFMPEG_PATH", "BLENDER_PATH", "MAYO_PATH"]:
            tool_name = tool.replace("_PATH", "")
            row = ctk.CTkFrame(tools_frame, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=5)
            
            # Label
            ctk.CTkLabel(row, text=tool_name, width=80, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left")
            
            # Default Path Logic
            default_path = internal_tools_path / tool_name.lower() / (tool_name.lower() + ".exe")
            current_val = self.settings.get(tool, "")
            is_custom = bool(current_val)
            
            # Checkbox
            chk_var = ctk.BooleanVar(value=is_custom)
            self.tool_vars[tool] = chk_var
            chk = ctk.CTkCheckBox(row, text="Custom", variable=chk_var, width=70, 
                                command=lambda t=tool: self.toggle_tool_entry(t))
            chk.pack(side="left", padx=10)
            
            # Entry
            entry = ctk.CTkEntry(row, height=28)
            entry.pack(side="left", fill="x", expand=True, padx=5)
            if is_custom:
                entry.insert(0, current_val)
            else:
                try:
                    # Try to show relative path for default if possible
                    rel_default = os.path.relpath(default_path, start=src_dir.parent)
                    entry.insert(0, str(rel_default))
                except:
                    entry.insert(0, str(default_path))
                entry.configure(state="disabled", text_color="gray")
                
            ctk.CTkButton(row, text="Browse", width=70, height=28, command=lambda e=entry: self.browse_file(e)).pack(side="right", padx=(5,0))
            self.tool_entries[tool] = entry

        # 3. API Configuration
        api_frame = ctk.CTkFrame(self.frame_settings, corner_radius=10)
        api_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=10)
        
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
        
        # Initial Dashboard Refresh
        self.after(1000, self.refresh_missing_dashboard)

    def save_api_settings(self):
        self.settings["GEMINI_API_KEY"] = self.entry_gemini.get().strip()
        self.settings["OLLAMA_URL"] = self.entry_ollama.get().strip()
        save_settings(self.settings)
        messagebox.showinfo("Success", "API settings saved!")
        logger.info("API settings saved.")

    def setup_updates_frame(self):
        self.frame_updates.grid_columnconfigure(0, weight=1)
        self.frame_updates.grid_rowconfigure(3, weight=1)
        
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

        # 2. Installed Libraries
        cleaner_frame = ctk.CTkFrame(self.frame_updates)
        cleaner_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        
        lib_head = ctk.CTkFrame(cleaner_frame, fg_color="transparent")
        lib_head.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(lib_head, text="Installed Libraries", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        
        self.show_all_libs_var = ctk.BooleanVar(value=False)
        ctk.CTkSwitch(lib_head, text="Show All (Advanced)", variable=self.show_all_libs_var, command=self.refresh_lib_list).pack(side="right")
        
        self.lib_scroll = ctk.CTkScrollableFrame(cleaner_frame, height=150, fg_color=("gray95", "gray15"))
        self.lib_scroll.pack(fill="both", expand=True, padx=20, pady=5)
        
        ctk.CTkButton(cleaner_frame, text="Refresh List", command=self.refresh_lib_list, width=100, fg_color="transparent", border_width=1, border_color="gray", text_color=("gray10", "gray90")).pack(pady=5)
        
        # Initial Dashboard Refresh
        self.after(1000, self.refresh_missing_dashboard)

    def check_external_tools(self):
        tools_status = {}
        tools_info = [
            {"name": "FFmpeg", "url": "https://ffmpeg.org/download.html", "desc": "Video/Audio"},
            {"name": "Blender", "url": "https://www.blender.org/download/", "desc": "3D Processing"},
            {"name": "MeshLab", "url": "https://www.meshlab.net/#download", "desc": "Mesh Ops"},
            {"name": "Ollama", "url": "https://ollama.com/download", "desc": "Local AI"},
            {"name": "Mayo", "url": "https://github.com/fougue/mayo?tab=readme-ov-file", "desc": "CAD Viewer"}
        ]
        
        for tool in tools_info:
            is_installed = False
            # 1. Check Configured Path (Settings)
            config_key = f"{tool['name'].upper()}_PATH"
            if self.settings.get(config_key):
                if os.path.exists(self.settings[config_key]):
                    is_installed = True

            # 2. Check Local Tools Directory
            if not is_installed:
                local_tool_path = src_dir.parent / "Tools" / tool['name'].lower() / f"{tool['name'].lower()}.exe"
                if local_tool_path.exists():
                    is_installed = True

            # 3. Check PATH
            if not is_installed:
                try:
                    startupinfo = None
                    if os.name == 'nt':
                        startupinfo = subprocess.STARTUPINFO()
                        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    subprocess.check_call(["where", tool['name']], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, startupinfo=startupinfo)
                    is_installed = True
                except: pass
            
            # 4. Check Default Paths (Windows)
            if not is_installed:
                common_paths = [
                    f"C:\\Program Files\\Blender Foundation\\Blender 4.2\\{tool['name']}.exe",
                    f"C:\\Program Files\\Blender Foundation\\Blender 4.1\\{tool['name']}.exe",
                    f"C:\\Program Files\\VCG\\MeshLab\\{tool['name']}.exe",
                    f"C:\\Users\\{os.environ.get('USERNAME')}\\AppData\\Local\\Programs\\Ollama\\{tool['name']}.exe"
                ]
                for p in common_paths:
                    if os.path.exists(p):
                        is_installed = True
                        break
            
            tools_status[tool['name']] = {"installed": is_installed, "url": tool['url'], "desc": tool['desc']}
            
        return tools_status

    def refresh_missing_dashboard(self):
        for widget in self.missing_scroll.winfo_children(): widget.destroy()
        
        # Check Tools
        tools_status = self.check_external_tools()
        missing_count = 0
        
        for name, info in tools_status.items():
            if not info['installed']:
                missing_count += 1
                row = ctk.CTkFrame(self.missing_scroll, fg_color="transparent")
                row.pack(fill="x", pady=2)
                ctk.CTkLabel(row, text=f"Missing: {name}", text_color=("#C0392B", "#E74C3C"), font=("", 12, "bold")).pack(side="left", padx=5)
                ctk.CTkLabel(row, text=f"({info['desc']})", text_color="gray").pack(side="left", padx=5)
                ctk.CTkButton(row, text="Download", width=80, height=24, command=lambda u=info['url']: webbrowser.open(u)).pack(side="right", padx=5)
        
        if missing_count == 0:
            ctk.CTkLabel(self.missing_scroll, text="All external tools installed!", text_color="green").pack(pady=10)

    def run_health_check(self):
        self.health_textbox.delete("0.0", "end")
        self.health_textbox.insert("end", "Running diagnostics...\n\n")
        
        def run():
            try:
                # Python Version
                ver = sys.version
                self.after(0, lambda: self.health_textbox.insert("end", f"Python: {ver}\n"))
                
                # Pip Check
                python_exe = sys.executable
                try:
                    startupinfo = None
                    if os.name == 'nt':
                        startupinfo = subprocess.STARTUPINFO()
                        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    subprocess.check_call([python_exe, "-m", "pip", "--version"], startupinfo=startupinfo, stdout=subprocess.DEVNULL)
                    self.after(0, lambda: self.health_textbox.insert("end", "Pip: OK\n"))
                except:
                    self.after(0, lambda: self.health_textbox.insert("end", "Pip: ERROR\n"))
                
                # Check critical libs
                criticals = ['customtkinter', 'pillow', 'requests']
                for lib in criticals:
                    if lib in self.installed_packages:
                        self.after(0, lambda l=lib: self.health_textbox.insert("end", f"{l}: OK\n"))
                    else:
                        self.after(0, lambda l=lib: self.health_textbox.insert("end", f"{l}: MISSING\n"))
                        
                self.after(0, lambda: self.health_textbox.insert("end", "\nDiagnostics complete."))
            except Exception as e:
                self.after(0, lambda: self.health_textbox.insert("end", f"\nError: {e}"))
                
        threading.Thread(target=run, daemon=True).start()

    def run_health_check_silent(self):
        # Just a quick check on startup
        try:
            python_exe = sys.executable
            subprocess.check_call([python_exe, "-m", "pip", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logger.info("Health check passed (silent)")
        except Exception as e:
            logger.error(f"Health check failed: {e}")

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
        
        # Header
        header = ctk.CTkFrame(self.lib_scroll, fg_color="transparent")
        header.pack(fill="x", pady=(0, 5))
        ctk.CTkLabel(header, text="Library", font=("", 12, "bold"), width=150, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(header, text="Version", font=("", 12, "bold"), width=80, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(header, text="Used By", font=("", 12, "bold"), width=150, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(header, text="Actions", font=("", 12, "bold"), width=100, anchor="e").pack(side="right", padx=5)
        
        installed = sorted(self.installed_packages.keys())
        
        for lib in installed:
            # Filter logic
            used_by = self.find_usage(lib)
            meta = self.dep_metadata.get(lib, {})
            is_critical = meta.get('is_critical', False)
            if lib in ['customtkinter', 'pillow', 'requests', 'pip', 'setuptools', 'wheel']: is_critical = True
            
            # If not showing all, skip if not critical, not in metadata, and not used by any tool
            if not self.show_all_libs_var.get():
                if not is_critical and not meta and not used_by:
                    continue

            version = self.installed_packages[lib]
            row = ctk.CTkFrame(self.lib_scroll, fg_color=("gray95", "gray20"))
            row.pack(fill="x", pady=2)
            
            usage_text = ", ".join(used_by) if used_by else "-"
            
            ctk.CTkLabel(row, text=lib, font=("", 12, "bold"), width=150, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(row, text=version, width=80, anchor="w", text_color="gray").pack(side="left", padx=5)
            ctk.CTkLabel(row, text=usage_text, width=150, anchor="w", text_color="gray").pack(side="left", padx=5)
            
            if is_critical:
                ctk.CTkLabel(row, text="System", text_color="gray", width=60).pack(side="right", padx=5)
            else:
                ctk.CTkButton(row, text="Uninstall", width=60, height=24, fg_color="#C0392B", hover_color="#E74C3C",
                            command=lambda l=lib: self.uninstall_lib(l)).pack(side="right", padx=5)

    def find_usage(self, lib_name):
        used_by = []
        for item in self.config_data:
            deps = item.get('dependencies', [])
            if any(d.lower() == lib_name.lower() for d in deps):
                used_by.append(item['name'])
        return used_by

    def uninstall_lib(self, lib_name):
        if not messagebox.askyesno("Confirm Uninstall", f"Uninstall '{lib_name}'?\n\nWarning: This may break features that depend on it."): return
        
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
        
        # Always include default groups
        default_groups = ["ContextUp", "(Top Level)"]
        for grp in default_groups:
            submenus.add(grp)
            
        sorted_subs = sorted(list(submenus), key=lambda x: (x not in default_groups, x))
        
        if not sorted_subs:
            # Should not happen now
            ctk.CTkLabel(self.group_scroll, text="No groups found.", text_color="gray").pack(pady=10)
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
            # Try to make relative
            try:
                rel_path = os.path.relpath(path, start=src_dir.parent)
                # If relative path starts with '..', it might be outside the project, but that's okay.
                # User prefers relative paths.
                path = rel_path
            except ValueError:
                pass # Keep absolute if on different drive
                
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
        self.frame_management.grid_forget()
        self.frame_settings.grid_forget()
        self.frame_updates.grid_forget()
        self.frame_logs.grid_forget()
        
        # Update sidebar buttons
        for btn, btn_name in [(self.btn_editor, "editor"), (self.btn_management, "management"), (self.btn_settings, "settings"), (self.btn_updates, "updates"), (self.btn_logs, "logs")]:
            if name == btn_name:
                btn.configure(fg_color=("gray80", "gray30"), text_color=("black", "white"))
            else:
                btn.configure(fg_color="transparent", text_color=("gray20", "gray80"))

        if name == "editor": self.frame_editor.grid(row=0, column=1, sticky="nsew")
        elif name == "management":
            self.frame_management.grid(row=0, column=1, sticky="nsew")
            self.refresh_category_grid()
            self.refresh_group_list()
        elif name == "settings": 
            self.frame_settings.grid(row=0, column=1, sticky="nsew")
        elif name == "updates":
            self.frame_updates.grid(row=0, column=1, sticky="nsew")
            self.refresh_lib_list()
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

    def preset_group_by_category(self):
        self.reset_filters()
        # Future: Implement specific grouping view if needed

    def preset_flat(self):
        self.reset_filters()
        # Future: Implement flat view if needed

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
        # Status/Category Label (Chip Style)
        if is_ready:
            cat_name = item.get('category', 'Custom')
            cat_color = self.settings.get("CATEGORY_COLORS", {}).get(cat_name, "#7f8c8d")
            cat_text = cat_name
        else:
            cat_color = "#F39C12" # Orange for warning
            cat_text = "Setup Required"
            
        # Determine contrasting text color
        try:
            # Simple brightness check
            h = cat_color.lstrip('#')
            rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
            brightness = (rgb[0] * 299 + rgb[1] * 587 + rgb[2] * 114) / 1000
            text_color = "black" if brightness > 128 else "white"
        except: text_color = "white"

        # Use CTkButton as a chip (static look)
        cat_chip = ctk.CTkButton(card, text=cat_text, fg_color=cat_color, text_color=text_color,
                               height=24, width=100, corner_radius=6, hover=False,
                               font=ctk.CTkFont(size=12, weight="bold"))
        cat_chip.grid(row=0, column=2, padx=5)
        
        # Bind clicks
        if is_ready:
            icon_label.bind("<Double-Button-1>", lambda e, i=real_index: self.edit_item(i))
            name_label.bind("<Double-Button-1>", lambda e, i=real_index: self.edit_item(i))
            cat_chip.bind("<Double-Button-1>", lambda e, i=real_index: self.edit_item(i))
        else:
            # Bind to Install Dialog
            for widget in [icon_label, name_label, cat_chip, card]:
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
        
        save_settings(self.settings)
        messagebox.showinfo("Success", "Tool paths saved!")
        logger.info("Tool paths saved.")

    def setup_log_frame(self):
        self.frame_logs.grid_columnconfigure(0, weight=1)
        self.frame_logs.grid_rowconfigure(0, weight=1)
        
        # Tabview
        self.log_tabs = ctk.CTkTabview(self.frame_logs, fg_color="transparent")
        self.log_tabs.grid(row=0, column=0, sticky="nsew", padx=20, pady=10)
        
        self.tab_logs = self.log_tabs.add("Logs")
        self.tab_backups = self.log_tabs.add("Backups")
        
        # --- Logs Tab ---
        self.tab_logs.grid_columnconfigure(0, weight=1)
        self.tab_logs.grid_rowconfigure(1, weight=1)
        
        # Toolbar
        log_ctrl = ctk.CTkFrame(self.tab_logs, fg_color="transparent")
        log_ctrl.grid(row=0, column=0, sticky="ew", pady=(5, 10))
        
        ctk.CTkButton(log_ctrl, text="Refresh Logs", command=self.refresh_logs, width=100, fg_color=("gray80", "gray30"), text_color=("black", "white")).pack(side="left")
        ctk.CTkButton(log_ctrl, text="Clear Logs", command=self.clear_logs, width=100, fg_color="transparent", border_width=1, border_color="gray", text_color=("gray20", "gray80")).pack(side="left", padx=10)
        
        # Log Level Selector
        ctk.CTkLabel(log_ctrl, text="Level:", font=("", 12, "bold"), text_color=("gray20", "gray80")).pack(side="right", padx=(10, 5))
        self.option_log = ctk.CTkOptionMenu(log_ctrl, values=["Debug (All)", "Info (Standard)", "Errors Only", "Disabled"],
                                            command=self.change_log_level, width=120)
        self.option_log.pack(side="right")
        self.option_log.set(self.settings.get("LOG_LEVEL", "Debug (All)"))
        
        # Log Text Area
        self.log_text = ctk.CTkTextbox(self.tab_logs, font=("Consolas", 12), fg_color=("white", "gray10"), text_color=("black", "white"))
        self.log_text.grid(row=1, column=0, sticky="nsew", pady=5)
        
        # Policy Label
        ctk.CTkLabel(self.tab_logs, text="* Logs are stored locally in 'logs/' for debugging purposes only.", 
                    text_color="gray", font=("", 10)).grid(row=2, column=0, sticky="w", padx=5, pady=2)
        
        # --- Backups Tab ---
        self.tab_backups.grid_columnconfigure(0, weight=1)
        self.tab_backups.grid_rowconfigure(1, weight=1)
        
        backup_ctrl = ctk.CTkFrame(self.tab_backups, fg_color="transparent")
        backup_ctrl.grid(row=0, column=0, sticky="ew", pady=5)
        ctk.CTkButton(backup_ctrl, text="Refresh List", command=self.refresh_backups, width=100).pack(side="left")
        
        self.backup_scroll = ctk.CTkScrollableFrame(self.tab_backups, fg_color=("gray95", "gray15"))
        self.backup_scroll.grid(row=1, column=0, sticky="nsew", pady=5)

    def refresh_logs(self):
        self.log_text.delete("0.0", "end")
        
        # Find the latest log file
        log_dir = src_dir.parent / "logs"
        if not log_dir.exists():
            self.log_text.insert("0.0", "No logs directory found.")
            return

        log_files = sorted(list(log_dir.glob("debug_*.log")), reverse=True)
        if not log_files:
            self.log_text.insert("0.0", "No log files found.")
            return
            
        latest_log = log_files[0]
        self.log_text.insert("0.0", f"--- Showing latest log: {latest_log.name} ---\n\n")
        
        try:
            with open(latest_log, 'r', encoding='utf-8') as f:
                content = f.read()
                self.log_text.insert("end", content)
                self.log_text.see("end")
        except Exception as e:
            self.log_text.insert("0.0", f"Error reading log: {e}")

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
                install_args = meta.get('install_args', [])
                
                self.after(0, lambda d=dep: lbl.configure(text=f"Installing {d}..."))
                
                try:
                    cmd = [python_exe, "-m", "pip", "install", pip_name] + install_args
                    subprocess.check_call(cmd)
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
