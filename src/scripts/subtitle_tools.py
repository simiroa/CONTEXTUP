"""
Subtitle Generation GUI Tools.
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import threading
import sys

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.append(str(src_dir))

from utils.ai_runner import run_ai_script
from utils.gui_lib import BaseWindow

class SubtitleGUI(BaseWindow):
    def __init__(self, target_path):
        super().__init__(title="ContextUp Subtitle Generation", width=700, height=600)
        self.video_path = Path(target_path)
        
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_widgets(self):
        # Header
        self.add_header(f"File: {self.video_path.name}")
        
        # Settings Frame
        settings_frame = ctk.CTkFrame(self.main_frame)
        settings_frame.pack(fill="x", padx=20, pady=10)
        
        # Model Selection
        ctk.CTkLabel(settings_frame, text="Model:").pack(side="left", padx=(20, 5), pady=10)
        self.model_var = ctk.StringVar(value="small")
        models = ['tiny', 'base', 'small', 'medium', 'large-v2', 'large-v3']
        self.model_combo = ctk.CTkComboBox(settings_frame, variable=self.model_var, values=models, width=100)
        self.model_combo.pack(side="left", padx=5)
        
        # Task Selection
        ctk.CTkLabel(settings_frame, text="Task:").pack(side="left", padx=(20, 5))
        self.task_var = ctk.StringVar(value="transcribe")
        tasks = ["transcribe", "translate"]
        self.task_combo = ctk.CTkComboBox(settings_frame, variable=self.task_var, values=tasks, width=120)
        self.task_combo.pack(side="left", padx=5)
        
        # Device Selection
        ctk.CTkLabel(settings_frame, text="Device:").pack(side="left", padx=(20, 5))
        self.device_var = ctk.StringVar(value="cuda")
        self.device_combo = ctk.CTkComboBox(settings_frame, variable=self.device_var, values=["cuda", "cpu"], width=80)
        self.device_combo.pack(side="left", padx=5)
        
        # Run Button
        self.btn_run = ctk.CTkButton(settings_frame, text="Generate", command=self.start_generation)
        self.btn_run.pack(side="right", padx=20)
        
        # Log Area
        ctk.CTkLabel(self.main_frame, text="Log Output:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(10, 5))
        
        self.log_area = ctk.CTkTextbox(self.main_frame, font=("Consolas", 10))
        self.log_area.pack(fill="both", expand=True, padx=20, pady=5)
        
        # Bottom frame: Actions
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(btn_frame, text="Close", fg_color="transparent", border_width=1, border_color="gray", command=self.destroy).pack(side="right", padx=5)
        
    def start_generation(self):
        self.btn_run.configure(state="disabled", text="Running...")
        self.log_area.delete("1.0", "end")
        self.log_area.insert("end", "Initializing Whisper... This may take a moment to load the model.\n")
        
        threading.Thread(target=self.run_generation, daemon=True).start()
        
    def run_generation(self):
        args = ["subtitle_gen.py", str(self.video_path)]
        args.extend(["--model", self.model_var.get()])
        args.extend(["--task", self.task_var.get()])
        args.extend(["--device", self.device_var.get()])
        
        success, output = run_ai_script(*args)
        
        self.after(0, lambda: self.show_result(success, output))
        
    def show_result(self, success, output):
        self.btn_run.configure(state="normal", text="Generate")
        self.log_area.delete("1.0", "end")
        
        if success:
            self.log_area.insert("end", output)
            self.log_area.insert("end", "\nDone!")
            messagebox.showinfo("Success", "Subtitle generation complete!")
        else:
            self.log_area.insert("end", f"Error:\n{output}")
            messagebox.showerror("Error", "Subtitle generation failed.")

    def on_closing(self):
        self.destroy()

def generate_subtitles(target_path: str):
    """
    Open Subtitle Generation dialog.
    """
    if not target_path:
        return
        
    app = SubtitleGUI(target_path)
    app.mainloop()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        generate_subtitles(sys.argv[1])
