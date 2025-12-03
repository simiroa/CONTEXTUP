"""
Document Analysis GUI Tools.
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

class DocAnalysisGUI(BaseWindow):
    def __init__(self, target_path):
        super().__init__(title="ContextUp Document Analysis", width=700, height=800)
        self.file_path = Path(target_path)
        
        self.create_widgets()
        self.load_models()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_widgets(self):
        # Header
        self.add_header(f"Analyzing: {self.file_path.name}")
        
        # Options Frame
        opt_frame = ctk.CTkFrame(self.main_frame)
        opt_frame.pack(fill="x", padx=20, pady=10)
        
        # Action Selection
        ctk.CTkLabel(opt_frame, text="Action:").pack(side="left", padx=10, pady=10)
        self.action_var = ctk.StringVar(value="summarize")
        actions = ["summarize", "translate", "explain", "analyze_tone"]
        self.action_combo = ctk.CTkComboBox(opt_frame, variable=self.action_var, values=actions, width=150, command=self.on_action_change)
        self.action_combo.pack(side="left", padx=5)
        
        # Language Input (Hidden by default)
        self.lang_frame = ctk.CTkFrame(opt_frame, fg_color="transparent")
        ctk.CTkLabel(self.lang_frame, text="To:").pack(side="left", padx=5)
        self.lang_var = ctk.StringVar(value="Korean")
        self.lang_entry = ctk.CTkEntry(self.lang_frame, textvariable=self.lang_var, width=100)
        self.lang_entry.pack(side="left", padx=5)
        
        # Model Selection
        ctk.CTkLabel(opt_frame, text="Model:").pack(side="left", padx=(20, 10))
        self.model_var = ctk.StringVar(value="llama3")
        self.model_combo = ctk.CTkComboBox(opt_frame, variable=self.model_var, values=["llama3", "mistral"], width=150)
        self.model_combo.pack(side="left", padx=5)
        
        # Run Button
        self.btn_analyze = ctk.CTkButton(opt_frame, text="Run Analysis", command=self.start_analysis)
        self.btn_analyze.pack(side="right", padx=10)
        
        # Result Area
        ctk.CTkLabel(self.main_frame, text="Analysis Result:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(10, 5))
        
        self.result_area = ctk.CTkTextbox(self.main_frame, font=("Consolas", 14))
        self.result_area.pack(fill="both", expand=True, padx=20, pady=5)
        
        # Bottom Actions
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(btn_frame, text="Copy to Clipboard", command=self.copy_result).pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="Close", fg_color="transparent", border_width=1, border_color="gray", command=self.destroy).pack(side="right", padx=5)
        
    def on_action_change(self, choice):
        if choice == "translate":
            self.lang_frame.pack(side="left", padx=5)
        else:
            self.lang_frame.pack_forget()
            
    def load_models(self):
        """Load available models in background."""
        def _load():
            success, output = run_ai_script("doc_analysis.py", "--list-models")
            if success:
                models = []
                for line in output.splitlines():
                    if line.strip().startswith("-"):
                        models.append(line.strip("- ").strip())
                
                if models:
                    self.model_combo.configure(values=models)
                    if "llama3" in models:
                        self.model_combo.set("llama3")
                    elif "mistral" in models:
                        self.model_combo.set("mistral")
                    else:
                        self.model_combo.set(models[0])
            else:
                self.result_area.insert("end", "Error: Could not list models. Is Ollama running?\n")
                
        threading.Thread(target=_load, daemon=True).start()
        
    def start_analysis(self):
        self.btn_analyze.configure(state="disabled", text="Running...")
        self.result_area.delete("1.0", "end")
        self.result_area.insert("end", "Processing... Please wait.\n")
        
        threading.Thread(target=self.run_analysis, daemon=True).start()
        
    def run_analysis(self):
        args = ["doc_analysis.py", str(self.file_path)]
        args.extend(["--action", self.action_var.get()])
        args.extend(["--model", self.model_var.get()])
        
        if self.action_var.get() == "translate":
            args.extend(["--lang", self.lang_var.get()])
        
        success, output = run_ai_script(*args)
        
        self.after(0, lambda: self.show_result(success, output))
        
    def show_result(self, success, output):
        self.btn_analyze.configure(state="normal", text="Run Analysis")
        self.result_area.delete("1.0", "end")
        
        if success:
            self.result_area.insert("end", output)
        else:
            self.result_area.insert("end", f"Error:\n{output}")

    def copy_result(self):
        text = self.result_area.get("1.0", "end").strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            messagebox.showinfo("Copied", "Result copied to clipboard!")

    def on_closing(self):
        self.destroy()

def analyze_document(target_path: str):
    """
    Open Document Analysis dialog.
    """
    if not target_path:
        return
        
    app = DocAnalysisGUI(target_path)
    app.mainloop()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        analyze_document(sys.argv[1])
