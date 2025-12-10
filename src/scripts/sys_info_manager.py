"""
ContextUp Info Manager
Modern, dark-themed GUI for managing personal information snippets.
Features: Scalable List, Search, Add/Edit/Delete, Auto-save.
"""
import sys
import json
from pathlib import Path
import customtkinter as ctk
from tkinter import messagebox
import tkinter as tk
import pyperclip

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.append(str(src_dir))

try:
    from utils.gui_lib import BaseWindow
except ImportError:
    class BaseWindow(ctk.CTk):
        def __init__(self, title="App", width=600, height=700):
            super().__init__()
            self.title(title)
            self.geometry(f"{width}x{height}")
            self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
            self.main_frame.pack(fill="both", expand=True)

# Import Core for Auto-Refresh
from core.registry import RegistryManager
from core.config import MenuConfig

class InfoManagerApp(BaseWindow):
    def __init__(self):
        super().__init__(title="ContextUp Info Manager", width=650, height=700)
        
        self.config_path = src_dir.parent / "config" / "copy_my_info.json"
        self.menu_config = MenuConfig()
        
        # Colors
        self.c_bg = "#1A1A1A"
        self.c_panel = "#252525" 
        self.c_accent = "#3498DB"
        self.c_accent_hover = "#2980B9"
        self.c_danger = "#E74C3C"
        
        ctk.set_appearance_mode("Dark")
        
        self.items = [] # List of dicts
        self.rows = []  # List of (frame, label_entry, content_entry) tuples
        
        self.load_config()
        self.setup_ui()
        self.render_rows()

    def load_config(self):
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.items = data.get('items', [])
            except: pass
        if not self.items:
            self.items = [{"label": "Email", "content": ""}]

    def setup_ui(self):
        # 1. Header (Clean, just title)
        header = ctk.CTkFrame(self.main_frame, fg_color="transparent", height=60)
        header.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(header, text="My Info", font=("Segoe UI", 24, "bold")).pack(side="left")
        ctk.CTkLabel(header, text="  (Changes applied on Save)", text_color="#888").pack(side="left", pady=(10,0))
        
        # 2. Scrollable List Area
        # Headers for columns
        col_header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        col_header.pack(fill="x", padx=30, pady=(0, 5))
        ctk.CTkLabel(col_header, text="Label (Name)", width=150, anchor="w", font=("Arial", 12, "bold")).pack(side="left")
        ctk.CTkLabel(col_header, text="Content (Value to Copy)", anchor="w", font=("Arial", 12, "bold")).pack(side="left", padx=10)

        self.scroll_frame = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # 3. Footer (Unified Action Buttons)
        footer = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        footer.pack(fill="x", padx=20, pady=20)
        footer.grid_columnconfigure(0, weight=1)
        footer.grid_columnconfigure(1, weight=1)
        
        # Add Button (Blue)
        ctk.CTkButton(footer, text="+ Add Row", height=40,
                     fg_color=self.c_accent, hover_color=self.c_accent_hover,
                     font=("Segoe UI", 14, "bold"),
                     command=self.add_row).grid(row=0, column=0, padx=10, sticky="ew")
        
        # Save Button (Green)
        ctk.CTkButton(footer, text="💾 Save & Update Menu", height=40,
                     fg_color="#27AE60", hover_color="#2ECC71",
                     font=("Segoe UI", 14, "bold"),
                     command=self.save_all).grid(row=0, column=1, padx=10, sticky="ew")

    def render_rows(self):
        # Clear existing
        for w in self.scroll_frame.winfo_children():
            w.destroy()
        self.rows = []
        
        for item in self.items:
            self._draw_row(item.get("label", ""), item.get("content", ""))

    def _draw_row(self, label_val, content_val):
        row_frame = ctk.CTkFrame(self.scroll_frame, fg_color=self.c_panel, corner_radius=6)
        row_frame.pack(fill="x", pady=4, padx=5)
        
        # Label Input
        e_lbl = ctk.CTkEntry(row_frame, width=150, placeholder_text="Label")
        e_lbl.pack(side="left", padx=10, pady=8)
        e_lbl.insert(0, label_val)
        
        # Content Input
        e_cnt = ctk.CTkEntry(row_frame, placeholder_text="Content")
        e_cnt.pack(side="left", fill="x", expand=True, padx=10, pady=8)
        e_cnt.insert(0, content_val)
        
        # Delete Button
        btn_del = ctk.CTkButton(row_frame, text="✕", width=30, height=30,
                               fg_color="transparent", text_color="#888", hover_color=self.c_danger,
                               command=lambda f=row_frame: self.delete_row(f))
        btn_del.pack(side="right", padx=5)
        
        self.rows.append((row_frame, e_lbl, e_cnt))

    def add_row(self):
        self._draw_row("", "")
        # Auto-scroll to bottom
        self.scroll_frame._parent_canvas.yview_moveto(1.0)
        # Focus on new label
        self.rows[-1][1].focus_set()

    def delete_row(self, frame):
        # Find and remove from self.rows
        for i, (f, l, c) in enumerate(self.rows):
            if f == frame:
                self.rows.pop(i)
                break
        frame.destroy()

    def save_all(self):
        new_items = []
        for frame, e_lbl, e_cnt in self.rows:
            label = e_lbl.get().strip()
            content = e_cnt.get().strip()
            
            # Skip completely empty rows
            if not label and not content:
                continue
            
            # Warn if label empty but content exists
            if not label:
                e_lbl.configure(placeholder_text_color=self.c_danger)
                return messagebox.showwarning("Missing Label", "Please provide a label for all items.")
                
            new_items.append({"label": label, "content": content})
            
        self.items = new_items
        
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump({"items": self.items}, f, indent=2, ensure_ascii=False)
                
            # Trigger Registry Refresh
            self.status_toast("Updating Registry...", 2000)
            self.after(100, self.refresh_registry)
            
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def refresh_registry(self):
        try:
            reg_man = RegistryManager(self.menu_config)
            reg_man.register_all()
            print("Registry Refreshed.")
            self.status_toast("✅ Menu Updated!", 1500)
        except Exception as e:
            print(f"Registry Refresh Failed: {e}")
            messagebox.showerror("Registry Error", str(e))

    def status_toast(self, msg, duration=1500):
        try:
            toast = ctk.CTkToplevel(self)
            toast.overrideredirect(True)
            toast.attributes('-topmost', True)
            w, h = 220, 45
            x = self.winfo_x() + (self.winfo_width()//2) - (w//2)
            y = self.winfo_y() + self.winfo_height() - 100
            toast.geometry(f"{w}x{h}+{x}+{y}")
            
            f = ctk.CTkFrame(toast, fg_color="#27AE60")
            f.pack(fill="both", expand=True)
            ctk.CTkLabel(f, text=msg, text_color="white", font=("Segoe UI", 13, "bold")).pack(expand=True)
            toast.after(duration, toast.destroy)
        except: pass

if __name__ == "__main__":
    app = InfoManagerApp()
    app.mainloop()
