"""
Metadata Tagger GUI Tools.
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import threading
import sys

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent  # features/system -> src
sys.path.append(str(src_dir))

from utils.ai_runner import run_ai_script
from utils.explorer import get_selection_from_explorer
from utils.gui_lib import BaseWindow, THEME_DROPDOWN_FG, THEME_DROPDOWN_BTN, THEME_DROPDOWN_HOVER, THEME_TEXT_DIM

class TaggingGUI(BaseWindow):
    def __init__(self, target_path):
        super().__init__(title="ContextUp Metadata Tagger", width=600, height=500, icon_name="image_smart_tag")
        
        # Get selection
        selection = get_selection_from_explorer(target_path)
        if not selection:
            selection = [target_path]
            
        # Filter images
        img_exts = {'.jpg', '.jpeg', '.png', '.webp', '.tiff'}
        self.file_paths = [f for f in selection if Path(f).suffix.lower() in img_exts]
        
        if not self.file_paths:
            messagebox.showinfo("Info", "No valid images selected.")
            self.destroy()
            return
            
        self.title(f"ContextUp Metadata Tagger ({len(self.file_paths)} files)")
        
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_widgets(self):
        # Header
        self.add_header(f"Tagging {len(self.file_paths)} Images")
        
        # Top frame
        top_frame = ctk.CTkFrame(self.main_frame)
        top_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(top_frame, text="Model:").pack(side="left", padx=(20, 5), pady=10)
        self.model_var = ctk.StringVar(value="qwen3-vl:8b")
        self.model_combo = ctk.CTkComboBox(top_frame, variable=self.model_var, values=["qwen3-vl:8b", "llava", "moondream"], width=150,
                                           fg_color=THEME_DROPDOWN_FG, button_color=THEME_DROPDOWN_BTN, button_hover_color=THEME_DROPDOWN_HOVER, border_color=THEME_DROPDOWN_BTN)
        self.model_combo.pack(side="left", padx=5)
        
        self.btn_run = ctk.CTkButton(top_frame, text="Start Tagging", command=self.start_tagging)
        self.btn_run.pack(side="right", padx=20)
        
        # File List / Log
        ctk.CTkLabel(self.main_frame, text="Log Output:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(10, 5))
        
        self.log_area = ctk.CTkTextbox(self.main_frame, font=("Consolas", 10))
        self.log_area.pack(fill="both", expand=True, padx=20, pady=5)
        self.log_area.insert("end", f"Ready to tag {len(self.file_paths)} images.\n")
        for p in self.file_paths:
            self.log_area.insert("end", f"- {Path(p).name}\n")
            
        # Bottom
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(btn_frame, text="Close", fg_color="transparent", border_width=1, border_color=THEME_TEXT_DIM, command=self.destroy).pack(side="right", padx=5)
        
    def start_tagging(self):
        self.btn_run.configure(state="disabled", text="Running...")
        self.log_area.insert("end", "\nStarting batch processing...\n")
        
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
        self.after(0, lambda: self.log_area.insert("end", message + "\n"))
        self.after(0, lambda: self.log_area.see("end"))
        
    def enable_button(self):
        self.after(0, lambda: self.btn_run.configure(state="normal", text="Start Tagging"))

    def on_closing(self):
        self.destroy()

def tag_images(target_path: str):
    """
    Open Tagging dialog.
    """
    try:
        app = TaggingGUI(target_path)
        app.mainloop()
            
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open tagger: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        tag_images(sys.argv[1])
