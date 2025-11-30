"""
Metadata Tagger GUI Tools.
"""
import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext
from pathlib import Path
import threading
from utils.ai_runner import run_ai_script
from utils.explorer import get_selection_from_explorer

def _get_root_tag():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    root.lift()
    return root

class TaggingDialog(tk.Toplevel):
    def __init__(self, parent, file_paths):
        super().__init__(parent)
        self.title(f"Metadata Tagger ({len(file_paths)} files)")
        self.geometry("600x500")
        self.file_paths = file_paths
        
        self.create_widgets()
        
    def create_widgets(self):
        # Top frame
        top_frame = ttk.Frame(self, padding="10")
        top_frame.pack(fill=tk.X)
        
        ttk.Label(top_frame, text="Model:").pack(side=tk.LEFT)
        self.model_var = tk.StringVar(value="qwen3-vl:8b")
        self.model_combo = ttk.Combobox(top_frame, textvariable=self.model_var, values=["qwen3-vl:8b", "llava", "moondream"], width=15)
        self.model_combo.pack(side=tk.LEFT, padx=5)
        
        self.btn_run = ttk.Button(top_frame, text="Start Tagging", command=self.start_tagging)
        self.btn_run.pack(side=tk.RIGHT, padx=10)
        
        # File List / Log
        self.log_area = scrolledtext.ScrolledText(self, wrap=tk.WORD, font=("Consolas", 9))
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.log_area.insert(tk.END, f"Ready to tag {len(self.file_paths)} images.\n")
        for p in self.file_paths:
            self.log_area.insert(tk.END, f"- {Path(p).name}\n")
            
        # Bottom
        btn_frame = ttk.Frame(self, padding="10")
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="Close", command=self.destroy).pack(side=tk.RIGHT)
        
    def start_tagging(self):
        self.btn_run.config(state="disabled")
        self.log_area.insert(tk.END, "\nStarting batch processing...\n")
        
        threading.Thread(target=self.run_batch, daemon=True).start()
        
    def run_batch(self):
        total = len(self.file_paths)
        for i, file_path in enumerate(self.file_paths, 1):
            self.update_log(f"[{i}/{total}] Analyzing {Path(file_path).name}...")
            
            args = ["metadata_tagger.py", str(file_path), "--model", self.model_var.get()]
            success, output = run_ai_script(*args)
            
            if success:
                self.update_log(f"Done. Tags added.\n")
            else:
                self.update_log(f"Failed: {output}\n")
                
        self.update_log("\nBatch processing complete.")
        self.enable_button()
        
    def update_log(self, message):
        self.after(0, lambda: self.log_area.insert(tk.END, message + "\n"))
        self.after(0, lambda: self.log_area.see(tk.END))
        
    def enable_button(self):
        self.after(0, lambda: self.btn_run.config(state="normal"))

def tag_images(target_path: str):
    """
    Open Tagging dialog.
    """
    try:
        # Get selection
        selection = get_selection_from_explorer(target_path)
        if not selection:
            selection = [target_path]
            
        # Filter images
        img_exts = {'.jpg', '.jpeg', '.png', '.webp', '.tiff'}
        valid_files = [f for f in selection if Path(f).suffix.lower() in img_exts]
        
        if not valid_files:
            messagebox.showinfo("Info", "No valid images selected.")
            return
            
        root = _get_root_tag()
        dialog = TaggingDialog(root, valid_files)
        root.wait_window(dialog)
        root.destroy()
            
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open tagger: {e}")
