"""
Subtitle Generation GUI Tools.
"""
import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext
from pathlib import Path
import threading
from utils.ai_runner import run_ai_script

def _get_root_sub():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    root.lift()
    return root

class SubtitleDialog(tk.Toplevel):
    def __init__(self, parent, video_path):
        super().__init__(parent)
        self.title("Subtitle Generation (Whisper)")
        self.geometry("600x500")
        self.video_path = video_path
        
        self.create_widgets()
        
    def create_widgets(self):
        # Top frame: Settings
        top_frame = ttk.Frame(self, padding="10")
        top_frame.pack(fill=tk.X)
        
        # Model Selection
        ttk.Label(top_frame, text="Model:").pack(side=tk.LEFT)
        self.model_var = tk.StringVar(value="small")
        models = ['tiny', 'base', 'small', 'medium', 'large-v2', 'large-v3']
        self.model_combo = ttk.Combobox(top_frame, textvariable=self.model_var, values=models, width=10, state="readonly")
        self.model_combo.pack(side=tk.LEFT, padx=5)
        
        # Task Selection
        ttk.Label(top_frame, text="Task:").pack(side=tk.LEFT, padx=(10, 0))
        self.task_var = tk.StringVar(value="transcribe")
        tasks = ["transcribe", "translate"]
        self.task_combo = ttk.Combobox(top_frame, textvariable=self.task_var, values=tasks, width=10, state="readonly")
        self.task_combo.pack(side=tk.LEFT, padx=5)
        
        # Device Selection
        ttk.Label(top_frame, text="Device:").pack(side=tk.LEFT, padx=(10, 0))
        self.device_var = tk.StringVar(value="cuda")
        self.device_combo = ttk.Combobox(top_frame, textvariable=self.device_var, values=["cuda", "cpu"], width=8, state="readonly")
        self.device_combo.pack(side=tk.LEFT, padx=5)
        
        # Run Button
        self.btn_run = ttk.Button(top_frame, text="Generate", command=self.start_generation)
        self.btn_run.pack(side=tk.RIGHT, padx=10)
        
        # Source Info
        info_frame = ttk.Frame(self, padding="5")
        info_frame.pack(fill=tk.X)
        ttk.Label(info_frame, text=f"File: {Path(self.video_path).name}", foreground="gray").pack(anchor=tk.W, padx=5)
        
        # Log Area
        self.log_area = scrolledtext.ScrolledText(self, wrap=tk.WORD, font=("Consolas", 9))
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Bottom frame: Actions
        btn_frame = ttk.Frame(self, padding="10")
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="Close", command=self.destroy).pack(side=tk.RIGHT, padx=5)
        
    def start_generation(self):
        self.btn_run.config(state="disabled")
        self.log_area.delete(1.0, tk.END)
        self.log_area.insert(tk.END, "Initializing Whisper... This may take a moment to load the model.\n")
        
        threading.Thread(target=self.run_generation, daemon=True).start()
        
    def run_generation(self):
        args = ["subtitle_gen.py", str(self.video_path)]
        args.extend(["--model", self.model_var.get()])
        args.extend(["--task", self.task_var.get()])
        args.extend(["--device", self.device_var.get()])
        
        success, output = run_ai_script(*args)
        
        self.after(0, lambda: self.show_result(success, output))
        
    def show_result(self, success, output):
        self.btn_run.config(state="normal")
        self.log_area.delete(1.0, tk.END)
        
        if success:
            self.log_area.insert(tk.END, output)
            self.log_area.insert(tk.END, "\nDone!")
            messagebox.showinfo("Success", "Subtitle generation complete!")
        else:
            self.log_area.insert(tk.END, f"Error:\n{output}")
            messagebox.showerror("Error", "Subtitle generation failed.")

def generate_subtitles(target_path: str):
    """
    Open Subtitle Generation dialog.
    """
    try:
        if not target_path:
            return
            
        root = _get_root_sub()
        dialog = SubtitleDialog(root, target_path)
        root.wait_window(dialog)
        root.destroy()
            
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open subtitle tool: {e}")
