"""
ContextUp Info Manager - Compact Table Version
"""
import sys
import json
import socket
from pathlib import Path
import customtkinter as ctk
from tkinter import messagebox
import tkinter as tk

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent  # src/scripts -> src
sys.path.append(str(src_dir))

try:
    from utils.gui_lib import BaseWindow
except ImportError:
    class BaseWindow(ctk.CTk):
        def __init__(self, title="App", width=500, height=400):
            super().__init__()
            self.title(title)
            self.geometry(f"{width}x{height}")
            self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
            self.main_frame.pack(fill="both", expand=True)

from core.registry import RegistryManager
from core.config import MenuConfig

def send_reload_signal():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(b"reload", ("127.0.0.1", 54321))
        sock.close()
    except Exception as e:
        print(f"Failed to send reload signal: {e}")

class InfoManagerApp(BaseWindow):
    def __init__(self):
        super().__init__(title="Copy My Info", width=500, height=400, icon_name="sys_copy_info")
        
        self.config_path = src_dir.parent / "userdata" / "copy_my_info.json"
        try:
            self.menu_config = MenuConfig()
        except:
            self.menu_config = None
        
        # Compact Colors
        self.c_bg = "#1A1A1A"
        self.c_row_even = "#252525"
        self.c_row_odd = "#2A2A2A"
        self.c_accent = "#3498DB"
        self.c_danger = "#E74C3C"
        
        ctk.set_appearance_mode("Dark")
        
        self.items = []
        self.rows = []
        
        self.load_config()
        self.setup_ui()
        self.render_rows()

    def load_config(self):
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.items = json.load(f).get('items', [])
            except: pass

    def setup_ui(self):
        # Header - Minimal
        header = ctk.CTkFrame(self.main_frame, fg_color="transparent", height=30)
        header.pack(fill="x", padx=10, pady=(8, 4))
        ctk.CTkLabel(header, text="Label", width=120, anchor="w", 
                    font=("Segoe UI", 11), text_color="#888").pack(side="left", padx=(5, 0))
        ctk.CTkLabel(header, text="Content", anchor="w",
                    font=("Segoe UI", 11), text_color="#888").pack(side="left", padx=10)

        # Table Area - Compact
        self.scroll_frame = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=5, pady=2)

        # Footer - Compact Buttons
        footer = ctk.CTkFrame(self.main_frame, fg_color="transparent", height=40)
        footer.pack(fill="x", padx=10, pady=8)
        
        ctk.CTkButton(footer, text="+ Add", height=28, width=80,
                     fg_color=self.c_accent,
                     font=("Segoe UI", 12),
                     command=self.add_row).pack(side="left", padx=2)
        
        ctk.CTkButton(footer, text="Save", height=28, width=80,
                     fg_color="#27AE60",
                     font=("Segoe UI", 12),
                     command=self.save_all).pack(side="right", padx=2)

    def render_rows(self):
        for w in self.scroll_frame.winfo_children():
            w.destroy()
        self.rows = []
        
        for i, item in enumerate(self.items):
            self._draw_row(item.get("label", ""), item.get("content", ""), i)

    def _draw_row(self, label_val, content_val, idx=0):
        bg = self.c_row_even if idx % 2 == 0 else self.c_row_odd
        row = ctk.CTkFrame(self.scroll_frame, fg_color=bg, corner_radius=0, height=28)
        row.pack(fill="x", pady=0)
        row.pack_propagate(False)
        
        e_lbl = ctk.CTkEntry(row, width=120, height=24, border_width=0,
                            fg_color="transparent", placeholder_text="Name")
        e_lbl.pack(side="left", padx=4, pady=2)
        e_lbl.insert(0, label_val)
        
        e_cnt = ctk.CTkEntry(row, height=24, border_width=0,
                            fg_color="transparent", placeholder_text="Value")
        e_cnt.pack(side="left", fill="x", expand=True, padx=4, pady=2)
        e_cnt.insert(0, content_val)
        
        btn_del = ctk.CTkButton(row, text="×", width=24, height=24,
                               fg_color="transparent", text_color="#666",
                               hover_color=self.c_danger,
                               command=lambda r=row: self.delete_row(r))
        btn_del.pack(side="right", padx=2)
        
        self.rows.append((row, e_lbl, e_cnt))

    def add_row(self):
        idx = len(self.rows)
        self._draw_row("", "", idx)
        try: 
            self.scroll_frame._parent_canvas.yview_moveto(1.0)
            self.rows[-1][1].focus_set()
        except: pass

    def delete_row(self, row):
        for i, (r, _, _) in enumerate(self.rows):
            if r == row:
                self.rows.pop(i)
                break
        row.destroy()
        # Recolor remaining rows
        for i, (r, _, _) in enumerate(self.rows):
            bg = self.c_row_even if i % 2 == 0 else self.c_row_odd
            r.configure(fg_color=bg)

    def save_all(self):
        new_items = []
        for _, e_lbl, e_cnt in self.rows:
            label = e_lbl.get().strip()
            content = e_cnt.get().strip()
            if not label and not content:
                continue
            if not label:
                return messagebox.showwarning("Error", "Label cannot be empty")
            new_items.append({"label": label, "content": content})
        
        self.items = new_items
        
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump({"items": self.items}, f, indent=2, ensure_ascii=False)
            
            send_reload_signal()
            
            if self.menu_config:
                RegistryManager(self.menu_config).register_all()
            
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    app = InfoManagerApp()
    app.mainloop()
