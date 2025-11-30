"""
Texture Tools GUI.
"""
import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext
from pathlib import Path
import threading
import os
from utils.ai_runner import run_ai_script

def _get_root_tex():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    root.lift()
    return root

class TextureDialog(tk.Toplevel):
    def __init__(self, parent, image_path):
        super().__init__(parent)
        self.title("Texture Tools")
        self.geometry("600x500")
        self.image_path = image_path
        
        self.create_widgets()
        
    def create_widgets(self):
        # Top Info
        info_frame = ttk.Frame(self, padding="10")
        info_frame.pack(fill=tk.X)
        ttk.Label(info_frame, text=f"File: {Path(self.image_path).name}", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W)
        
        # API Key Check
        if not os.environ.get('GEMINI_API_KEY'):
            ttk.Label(info_frame, text="Warning: GEMINI_API_KEY not found in environment variables.", foreground="red").pack(anchor=tk.W)
        
        # Tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Tab 1: PBR Generation
        self.tab_pbr = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_pbr, text="PBR Generation")
        self.setup_pbr_tab()
        
        # Tab 2: Analysis (Gemini)
        self.tab_analyze = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_analyze, text="Analyze (Gemini)")
        self.setup_analyze_tab()
        
        # Close Button
        btn_frame = ttk.Frame(self, padding="10")
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="Close", command=self.destroy).pack(side=tk.RIGHT)

    def setup_pbr_tab(self):
        frame = ttk.Frame(self.tab_pbr, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Generate Normal, Roughness, and Displacement maps.").pack(anchor=tk.W, pady=10)
        
        self.btn_pbr = ttk.Button(frame, text="Generate PBR Maps", command=self.run_pbr)
        self.btn_pbr.pack(anchor=tk.W, pady=10)
        
        self.log_pbr = scrolledtext.ScrolledText(frame, height=10, width=60, font=("Consolas", 9))
        self.log_pbr.pack(fill=tk.BOTH, expand=True, pady=10)

    def setup_analyze_tab(self):
        frame = ttk.Frame(self.tab_analyze, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Analyze texture properties using Gemini Vision.").pack(anchor=tk.W, pady=10)
        
        self.btn_analyze = ttk.Button(frame, text="Analyze Texture", command=self.run_analyze)
        self.btn_analyze.pack(anchor=tk.W, pady=10)
        
        self.log_analyze = scrolledtext.ScrolledText(frame, height=10, width=60, font=("Consolas", 9))
        self.log_analyze.pack(fill=tk.BOTH, expand=True, pady=10)

    def run_pbr(self):
        self.btn_pbr.config(state="disabled")
        self.log_pbr.insert(tk.END, "Generating PBR maps...\n")
        threading.Thread(target=self._run_script, args=("pbr", self.log_pbr, self.btn_pbr), daemon=True).start()

    def run_analyze(self):
        self.btn_analyze.config(state="disabled")
        self.log_analyze.insert(tk.END, "Analyzing with Gemini...\n")
        threading.Thread(target=self._run_script, args=("analyze", self.log_analyze, self.btn_analyze), daemon=True).start()

    def _run_script(self, action, log_widget, btn_widget):
        args = ["texture_gen.py", str(self.image_path), "--action", action]
        success, output = run_ai_script(*args)
        
        self.after(0, lambda: self.update_ui(success, output, log_widget, btn_widget))

    def update_ui(self, success, output, log_widget, btn_widget):
        btn_widget.config(state="normal")
        if success:
            log_widget.insert(tk.END, output + "\nDone.\n")
        else:
            log_widget.insert(tk.END, f"Error:\n{output}\n")
        log_widget.see(tk.END)

def open_texture_tools(target_path: str):
    """
    Open Texture Tools dialog.
    """
    try:
        if not target_path:
            return
            
        root = _get_root_tex()
        dialog = TextureDialog(root, target_path)
        root.wait_window(dialog)
        root.destroy()
            
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open texture tools: {e}")
