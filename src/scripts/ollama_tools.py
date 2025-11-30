"""
Ollama Vision GUI Tools.
"""
import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext
from pathlib import Path
import threading
from utils.ai_runner import run_ai_script
from utils.explorer import get_selection_from_explorer

def _get_root_ol():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    root.lift()
    return root

class OllamaVisionDialog(tk.Toplevel):
    def __init__(self, parent, image_path=None):
        super().__init__(parent)
        self.title("Ollama Vision Analysis")
        self.geometry("600x500")
        self.image_path = image_path
        self.result_text = None
        
        self.create_widgets()
        self.load_models()
        
    def create_widgets(self):
        self.type_combo = ttk.Combobox(top_frame, textvariable=self.type_var, values=types, width=15, state="readonly")
        self.type_combo.pack(side=tk.LEFT, padx=5)
        
        # Analyze Button
        self.btn_analyze = ttk.Button(top_frame, text="Analyze", command=self.start_analysis)
        self.btn_analyze.pack(side=tk.LEFT, padx=10)
        
        # Source Info
        info_frame = ttk.Frame(self, padding="5")
        info_frame.pack(fill=tk.X)
        src_text = f"Source: {Path(self.image_path).name}" if self.image_path else "Source: Clipboard"
        ttk.Label(info_frame, text=src_text, foreground="gray").pack(anchor=tk.W, padx=5)
        
        # Result Area
        self.result_area = scrolledtext.ScrolledText(self, wrap=tk.WORD, font=("Consolas", 10))
        self.result_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Bottom frame: Actions
        btn_frame = ttk.Frame(self, padding="10")
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="Copy to Clipboard", command=self.copy_result).pack(side=tk.RIGHT)
        ttk.Button(btn_frame, text="Close", command=self.destroy).pack(side=tk.RIGHT, padx=5)
        
    def load_models(self):
        """Load available models in background."""
        def _load():
            success, output = run_ai_script("ollama_vision.py", "--list-models")
            if success:
                models = []
                for line in output.splitlines():
                    if line.strip().startswith("-"):
                        models.append(line.strip("- ").strip())
                
                if models:
                    self.model_combo['values'] = models
                    if "llava" in models:
                        self.model_combo.set("llava")
                    else:
                        self.model_combo.set(models[0])
            else:
                self.result_area.insert(tk.END, "Error: Could not list models. Is Ollama running?\n")
                
        threading.Thread(target=_load, daemon=True).start()
        
    def start_analysis(self):
        self.btn_analyze.config(state="disabled")
        self.result_area.delete(1.0, tk.END)
        self.result_area.insert(tk.END, "Analyzing... Please wait.\n")
        
        threading.Thread(target=self.run_analysis, daemon=True).start()
        
    def run_analysis(self):
        args = ["ollama_vision.py"]
        
        if self.image_path:
            args.append(str(self.image_path))
        else:
            args.append("--clipboard")
            
        args.extend(["--model", self.model_var.get()])
        args.extend(["--type", self.type_var.get()])
        
        success, output = run_ai_script(*args)
        
        self.after(0, lambda: self.show_result(success, output))
        
    def show_result(self, success, output):
        self.btn_analyze.config(state="normal")
        self.result_area.delete(1.0, tk.END)
        
        if success:
            # Extract result between markers if present
            if "--- Result ---" in output:
                parts = output.split("--- Result ---")
                if len(parts) > 1:
                    result = parts[1].split("--------------")[0].strip()
                    self.result_area.insert(tk.END, result)
                    return
            
            self.result_area.insert(tk.END, output)
        else:
            self.result_area.insert(tk.END, f"Error:\n{output}")

    def copy_result(self):
        text = self.result_area.get(1.0, tk.END).strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            messagebox.showinfo("Copied", "Result copied to clipboard!")

def analyze_image(target_path: str = None):
    """
    Open Ollama Vision dialog.
    If target_path is None, uses clipboard.
    """
    try:
        if target_path:
            # Check if it's an image
            img_exts = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
            if Path(target_path).suffix.lower() not in img_exts:
                messagebox.showinfo("Info", "Selected file is not an image.")
                return
        
        root = _get_root_ol()
        dialog = OllamaVisionDialog(root, target_path)
        root.wait_window(dialog)
        root.destroy()
            
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open vision tool: {e}")

def analyze_clipboard():
    """Analyze image from clipboard."""
    analyze_image(None)
