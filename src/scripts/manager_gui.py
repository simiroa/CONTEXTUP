"""
Management GUI for Creator Tools.
"""
import sys
import os
import json
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog, simpledialog
from pathlib import Path
import subprocess
import threading

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.append(str(src_dir))

from core.config import MenuConfig
from core.settings import load_settings, save_settings

class ManagerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Creator Tools Manager")
        self.geometry("600x800")
        
        self.config_path = src_dir.parent / "config" / "menu_config.json"
        self.settings = load_settings()
        
        # Icons
        self.icon_ok = "✅"
        self.icon_warn = "⚠️"
        self.icon_err = "❌"
        
        self.create_widgets()
        self.load_config()
        
        # Auto-run health check on startup to update status icons
        self.after(1000, self.run_health_check_silent)
        
    def create_widgets(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tab 1: Features (Registry)
        self.tab_features = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_features, text="Features & Registry")
        self.setup_features_tab()
        
        # Tab 2: System Health
        self.tab_health = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_health, text="System Health")
        self.setup_health_tab()
        
        # Tab 3: Settings
        self.tab_settings = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_settings, text="Settings")
        self.setup_settings_tab()
        
    def setup_features_tab(self):
        # Top Actions
        top_frame = ttk.Frame(self.tab_features, padding="5")
        top_frame.pack(fill=tk.X)
        
        # Global Select/Deselect
        ttk.Button(top_frame, text="Select All", command=self.select_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(top_frame, text="Deselect All", command=self.deselect_all).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(top_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        ttk.Button(top_frame, text="Export Preset", command=self.export_preset).pack(side=tk.LEFT, padx=2)
        ttk.Button(top_frame, text="Import Preset", command=self.import_preset).pack(side=tk.LEFT, padx=2)
        
        # Main Action Buttons
        btn_frame = ttk.Frame(self.tab_features, padding="5")
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        ttk.Button(btn_frame, text="Apply Changes (Update Registry)", command=self.apply_registry).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Reload Config", command=self.load_config).pack(side=tk.RIGHT, padx=5)
        
        # Scrollable Area for Features
        self.canvas = tk.Canvas(self.tab_features)
        self.scrollbar = ttk.Scrollbar(self.tab_features, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = ttk.Frame(self.canvas)
        
        self.scroll_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def setup_health_tab(self):
        frame = ttk.Frame(self.tab_health, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        top_frame = ttk.Frame(frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(top_frame, text="Run Diagnostics", command=self.run_health_check).pack(side=tk.LEFT)
        self.lbl_health_status = ttk.Label(top_frame, text="Ready", foreground="gray")
        self.lbl_health_status.pack(side=tk.LEFT, padx=10)
        
        self.health_text = scrolledtext.ScrolledText(frame, height=20, width=80, font=("Consolas", 10))
        self.health_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure tags
        self.health_text.tag_config("OK", foreground="green")
        self.health_text.tag_config("WARNING", foreground="#FF8C00") # Dark Orange
        self.health_text.tag_config("ERROR", foreground="red")
        self.health_text.tag_config("HEADER", font=("Consolas", 10, "bold"))

    def setup_settings_tab(self):
        frame = ttk.Frame(self.tab_settings, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # --- API Keys ---
        lbl_frame = ttk.LabelFrame(frame, text="API Configuration", padding="10")
        lbl_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Gemini API Key
        ttk.Label(lbl_frame, text="Gemini API Key:").pack(anchor=tk.W, pady=(0, 5))
        self.entry_gemini = ttk.Entry(lbl_frame, width=60)
        self.entry_gemini.pack(anchor=tk.W, pady=(0, 15))
        if self.settings.get("GEMINI_API_KEY"):
            self.entry_gemini.insert(0, self.settings["GEMINI_API_KEY"])
            
        # Ollama URL
        ttk.Label(lbl_frame, text="Ollama URL (default: http://localhost:11434):").pack(anchor=tk.W, pady=(0, 5))
        self.entry_ollama = ttk.Entry(lbl_frame, width=60)
        self.entry_ollama.pack(anchor=tk.W, pady=(0, 15))
        if self.settings.get("OLLAMA_URL"):
            self.entry_ollama.insert(0, self.settings["OLLAMA_URL"])

        # --- External Tools Paths ---
        path_frame = ttk.LabelFrame(frame, text="External Tools Paths (Optional - Leave empty to auto-detect)", padding="10")
        path_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.path_entries = {}
        tools = [
            ("FFmpeg Path (ffmpeg.exe)", "FFMPEG_PATH"),
            ("Blender Path (blender.exe)", "BLENDER_PATH"),
            ("Mayo Path (mayo-conv.exe)", "MAYO_PATH")
        ]
        
        for label_text, key in tools:
            sub_frame = ttk.Frame(path_frame)
            sub_frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(sub_frame, text=label_text, width=25).pack(side=tk.LEFT)
            entry = ttk.Entry(sub_frame)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            
            if self.settings.get(key):
                entry.insert(0, self.settings[key])
                
            self.path_entries[key] = entry
            
            btn = ttk.Button(sub_frame, text="Browse", width=8, command=lambda k=key, e=entry: self.browse_file(k, e))
            btn.pack(side=tk.LEFT)

        # Save Button
        ttk.Button(frame, text="Save Settings", command=self.save_app_settings).pack(anchor=tk.W, pady=10)

    def browse_file(self, key, entry):
        file_path = filedialog.askopenfilename(title=f"Select {key}")
        if file_path:
            entry.delete(0, tk.END)
            entry.insert(0, file_path)

    def load_config(self):
        # Clear existing
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
            
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config_data = json.load(f)
                
            # Group by category
            categories = {}
            for item in self.config_data:
                cat = item.get('category', 'Uncategorized')
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(item)
                
            # Create widgets
            self.check_vars = {}
            self.status_labels = {} 
            self.icon_images = {} # Keep references to prevent GC
            self.category_vars = {} # Store category items for batch selection
            self.name_labels = {} # Store name labels to update them
            
            for cat, items in categories.items():
                # Category Header Frame
                cat_frame = ttk.LabelFrame(self.scroll_frame, text=cat, padding="5")
                cat_frame.pack(fill=tk.X, padx=10, pady=5)
                
                # Category Actions (Select All / Deselect All for this category)
                cat_action_frame = ttk.Frame(cat_frame)
                cat_action_frame.pack(fill=tk.X, pady=(0, 5))
                
                # Store item IDs for this category
                cat_item_ids = [item['id'] for item in items]
                self.category_vars[cat] = cat_item_ids
                
                ttk.Button(cat_action_frame, text="All", width=5, 
                           command=lambda c=cat: self.select_category(c, True)).pack(side=tk.RIGHT, padx=2)
                ttk.Button(cat_action_frame, text="None", width=5, 
                           command=lambda c=cat: self.select_category(c, False)).pack(side=tk.RIGHT, padx=2)
                
                for item in items:
                    row_frame = ttk.Frame(cat_frame)
                    row_frame.pack(fill=tk.X, pady=1)
                    
                    # Status Icon (Colored Dot)
                    lbl_status = ttk.Label(row_frame, text="●", width=2, foreground="gray")
                    lbl_status.pack(side=tk.LEFT)
                    self.status_labels[item['id']] = lbl_status
                    
                    # Feature Icon
                    icon_path_str = item.get('icon', '')
                    if icon_path_str:
                        # Resolve path relative to project root
                        icon_abs_path = src_dir.parent / icon_path_str
                        if icon_abs_path.exists():
                            try:
                                from PIL import Image, ImageTk
                                pil_img = Image.open(icon_abs_path)
                                pil_img = pil_img.resize((16, 16), Image.LANCZOS)
                                tk_icon = ImageTk.PhotoImage(pil_img)
                                self.icon_images[item['id']] = tk_icon # Keep ref
                                lbl_icon = ttk.Label(row_frame, image=tk_icon)
                                lbl_icon.pack(side=tk.LEFT, padx=(0, 5))
                            except Exception:
                                pass # Icon load failed, skip
                    
                    # Checkbox
                    var = tk.BooleanVar(value=item.get('enabled', True))
                    self.check_vars[item['id']] = var
                    
                    cb = ttk.Checkbutton(row_frame, variable=var)
                    cb.pack(side=tk.LEFT)
                    
                    # Name Label (Clickable or separate Rename button)
                    # Using a separate small button for clarity
                    lbl_name = ttk.Label(row_frame, text=item['name'])
                    lbl_name.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
                    self.name_labels[item['id']] = lbl_name
                    
                    btn_rename = ttk.Button(row_frame, text="✎", width=3, 
                                          command=lambda i=item['id']: self.rename_item(i))
                    btn_rename.pack(side=tk.RIGHT)
                    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load config: {e}")

    def rename_item(self, item_id):
        # Find item
        item = next((i for i in self.config_data if i['id'] == item_id), None)
        if not item:
            return
            
        new_name = simpledialog.askstring("Rename Feature", "Enter new name:", initialvalue=item['name'])
        if new_name:
            item['name'] = new_name
            # Update UI
            if item_id in self.name_labels:
                self.name_labels[item_id].config(text=new_name)
            # Note: Changes are in self.config_data, will be saved on "Apply"

    def select_category(self, category, state):
        if category in self.category_vars:
            for item_id in self.category_vars[category]:
                if item_id in self.check_vars:
                    self.check_vars[item_id].set(state)

    def select_all(self):
        for var in self.check_vars.values():
            var.set(True)
            
    def deselect_all(self):
        for var in self.check_vars.values():
            var.set(False)

    def export_preset(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")],
            title="Export Preset"
        )
        if not file_path:
            return
            
        preset = {}
        for item_id, var in self.check_vars.items():
            preset[item_id] = var.get()
            
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(preset, f, indent=4)
            messagebox.showinfo("Success", "Preset exported successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export preset: {e}")

    def import_preset(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON Files", "*.json")],
            title="Import Preset"
        )
        if not file_path:
            return
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                preset = json.load(f)
                
            for item_id, enabled in preset.items():
                if item_id in self.check_vars:
                    self.check_vars[item_id].set(enabled)
            
            messagebox.showinfo("Success", "Preset imported successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import preset: {e}")

    def apply_registry(self):
        # Update config data
        for item in self.config_data:
            item_id = item['id']
            if item_id in self.check_vars:
                item['enabled'] = self.check_vars[item_id].get()
                
        # Save config
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config: {e}")
            return

        # Run register
        try:
            python_exe = sys.executable
            manage_script = src_dir.parent / "manage.py"
            
            subprocess.run([python_exe, str(manage_script), "register"], check=True)
            messagebox.showinfo("Success", "Registry updated successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to register: {e}")

    def save_app_settings(self):
        new_settings = {
            "GEMINI_API_KEY": self.entry_gemini.get().strip(),
            "OLLAMA_URL": self.entry_ollama.get().strip()
        }
        
        # Add paths
        for key, entry in self.path_entries.items():
            val = entry.get().strip()
            if val:
                new_settings[key] = val
            else:
                new_settings[key] = "" # Clear if empty
                
        if save_settings(new_settings):
            messagebox.showinfo("Success", "Settings saved.")
            os.environ["GEMINI_API_KEY"] = new_settings["GEMINI_API_KEY"]
        else:
            messagebox.showerror("Error", "Failed to save settings.")

    def run_health_check(self):
        self.health_text.delete(1.0, tk.END)
        self.health_text.insert(tk.END, "Running diagnostics...\n\n")
        self.lbl_health_status.config(text="Running...", foreground="blue")
        threading.Thread(target=self._run_health_thread, daemon=True).start()
        
    def run_health_check_silent(self):
        """Runs health check in background just to update status icons."""
        threading.Thread(target=self._run_health_thread, args=(True,), daemon=True).start()

    def _run_health_thread(self, silent=False):
        try:
            from core.health import HealthCheck
            checker = HealthCheck()
            results = checker.run_all()
            
            # Update UI in main thread
            self.after(0, lambda: self._update_health_ui(results, silent))
            
        except Exception as e:
            if not silent:
                self.after(0, lambda: self.health_text.insert(tk.END, f"\nError running checks: {e}", "ERROR"))

    def _update_health_ui(self, results, silent):
        if not silent:
            self.health_text.delete(1.0, tk.END)
            for category, status, message in results:
                self.health_text.insert(tk.END, f"[{category}] ", "HEADER")
                self.health_text.insert(tk.END, f"[{status}] ", status)
                self.health_text.insert(tk.END, f"{message}\n")
            self.health_text.insert(tk.END, "\nDiagnostic Complete.")
            self.lbl_health_status.config(text="Complete", foreground="green")

        # Update Feature Icons based on health
        # Logic:
        # - If AI Env missing -> Warning on AI tools
        # - If FFmpeg missing -> Error on Video/Audio tools
        
        ai_ok = any(r[0] == "AI Env" and r[1] == "OK" for r in results)
        ffmpeg_ok = any(r[0] == "FFmpeg" and r[1] == "OK" for r in results)
        
        for item_id, lbl in self.status_labels.items():
            color = "green" # OK
            
            # AI Tools
            if "ai" in item_id or "remove_bg" in item_id or "upscale" in item_id:
                if not ai_ok:
                    color = "#FF8C00" # Warning (Dark Orange)
            
            # Video/Audio Tools
            if "video" in item_id or "audio" in item_id or "convert" in item_id:
                if not ffmpeg_ok:
                    color = "red" # Error
                    
            lbl.config(foreground=color)

if __name__ == "__main__":
    app = ManagerGUI()
    app.mainloop()
