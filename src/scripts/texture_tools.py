"""
Texture Tools GUI.
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import threading
import os
import sys

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.append(str(src_dir))

from utils.ai_runner import run_ai_script
from utils.gui_lib import BaseWindow

class TextureGUI(BaseWindow):
    def __init__(self, target_path):
        super().__init__(title="ContextUp Texture Tools", width=700, height=600)
        self.image_path = Path(target_path)
        
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_widgets(self):
        # Header
        self.add_header(f"File: {self.image_path.name}")
        
        # API Key Check
        if not os.environ.get('GEMINI_API_KEY'):
            ctk.CTkLabel(self.main_frame, text="Warning: GEMINI_API_KEY not found in environment variables.", text_color="#E74C3C").pack(anchor="w", padx=20)
        
        # Tabs
        self.tab_view = ctk.CTkTabview(self.main_frame)
        self.tab_view.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.tab_pbr = self.tab_view.add("PBR Generation")
        self.tab_analyze = self.tab_view.add("Analyze (Gemini)")
        
        self.setup_pbr_tab()
        self.setup_analyze_tab()
        
        # Close Button
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(btn_frame, text="Close", fg_color="transparent", border_width=1, border_color="gray", command=self.destroy).pack(side="right", padx=5)

    def setup_pbr_tab(self):
        ctk.CTkLabel(self.tab_pbr, text="Generate Normal, Roughness, and Displacement maps.").pack(anchor="w", padx=20, pady=10)
        
        self.btn_pbr = ctk.CTkButton(self.tab_pbr, text="Generate PBR Maps", command=self.run_pbr)
        self.btn_pbr.pack(anchor="w", padx=20, pady=10)
        
        self.log_pbr = ctk.CTkTextbox(self.tab_pbr, font=("Consolas", 10))
        self.log_pbr.pack(fill="both", expand=True, padx=20, pady=10)

    def setup_analyze_tab(self):
        ctk.CTkLabel(self.tab_analyze, text="Analyze texture properties using Gemini Vision.").pack(anchor="w", padx=20, pady=10)
        
        self.btn_analyze = ctk.CTkButton(self.tab_analyze, text="Analyze Texture", command=self.run_analyze)
        self.btn_analyze.pack(anchor="w", padx=20, pady=10)
        
        self.log_analyze = ctk.CTkTextbox(self.tab_analyze, font=("Consolas", 10))
        self.log_analyze.pack(fill="both", expand=True, padx=20, pady=10)

    def run_pbr(self):
        self.btn_pbr.configure(state="disabled", text="Generating...")
        self.log_pbr.insert("end", "Generating PBR maps...\n")
        threading.Thread(target=self._run_script, args=("pbr", self.log_pbr, self.btn_pbr), daemon=True).start()

    def run_analyze(self):
        self.btn_analyze.configure(state="disabled", text="Analyzing...")
        self.log_analyze.insert("end", "Analyzing with Gemini...\n")
        threading.Thread(target=self._run_script, args=("analyze", self.log_analyze, self.btn_analyze), daemon=True).start()

    def _run_script(self, action, log_widget, btn_widget):
        args = ["texture_gen.py", str(self.image_path), "--action", action]
        success, output = run_ai_script(*args)
        
        self.after(0, lambda: self.update_ui(success, output, log_widget, btn_widget))

    def update_ui(self, success, output, log_widget, btn_widget):
        btn_widget.configure(state="normal")
        if action := "Generate PBR Maps" if btn_widget == self.btn_pbr else "Analyze Texture":
             btn_widget.configure(text=action)
             
        if success:
            log_widget.insert("end", output + "\nDone.\n")
        else:
            log_widget.insert("end", f"Error:\n{output}\n")
        log_widget.see("end")

    def on_closing(self):
        self.destroy()

def open_texture_tools(target_path: str):
    """
    Open Texture Tools dialog.
    """
    if not target_path:
        return
        
    app = TextureGUI(target_path)
    app.mainloop()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        open_texture_tools(sys.argv[1])
