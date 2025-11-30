"""
Document Analysis GUI Tools.
"""
import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext
from pathlib import Path
import threading
from utils.ai_runner import run_ai_script

def _get_root_doc():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    root.lift()
    return root

class OllamaDocDialog(tk.Toplevel):
    def __init__(self, parent, file_path):
        super().__init__(parent)
        self.title("Document Analysis (Ollama)")
        self.geometry("600x600")
        self.file_path = file_path
        
        self.create_widgets()
        self.load_models()
        
    def create_widgets(self):
        self.action_combo = ttk.Combobox(top_frame, textvariable=self.action_var, values=actions, width=15, state="readonly")
        self.action_combo.pack(side=tk.LEFT, padx=5)
        self.action_combo.bind("<<ComboboxSelected>>", self.on_action_change)
        
        # Language Input (Hidden by default)
        self.lang_frame = ttk.Frame(top_frame)
        ttk.Label(self.lang_frame, text="To:").pack(side=tk.LEFT)
        self.lang_var = tk.StringVar(value="Korean")
        self.lang_entry = ttk.Entry(self.lang_frame, textvariable=self.lang_var, width=10)
        self.lang_entry.pack(side=tk.LEFT, padx=5)
        
        # Analyze Button
        self.btn_analyze = ttk.Button(top_frame, text="Run", command=self.start_analysis)
        self.btn_analyze.pack(side=tk.RIGHT, padx=10)
        
        # Source Info
        info_frame = ttk.Frame(self, padding="5")
        info_frame.pack(fill=tk.X)
        ttk.Label(info_frame, text=f"File: {Path(self.file_path).name}", foreground="gray").pack(anchor=tk.W, padx=5)
        
        # Result Area
        self.result_area = scrolledtext.ScrolledText(self, wrap=tk.WORD, font=("Consolas", 10))
        self.result_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Bottom frame: Actions
        btn_frame = ttk.Frame(self, padding="10")
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="Copy to Clipboard", command=self.copy_result).pack(side=tk.RIGHT)
        ttk.Button(btn_frame, text="Close", command=self.destroy).pack(side=tk.RIGHT, padx=5)
        
    def on_action_change(self, event=None):
        if self.action_var.get() == "translate":
            self.lang_frame.pack(side=tk.LEFT, padx=5)
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
                    self.model_combo['values'] = models
                    if "llama3" in models:
                        self.model_combo.set("llama3")
                    elif "mistral" in models:
                        self.model_combo.set("mistral")
                    else:
                        self.model_combo.set(models[0])
            else:
                self.result_area.insert(tk.END, "Error: Could not list models. Is Ollama running?\n")
                
        threading.Thread(target=_load, daemon=True).start()
        
    def start_analysis(self):
        self.btn_analyze.config(state="disabled")
        self.result_area.delete(1.0, tk.END)
        self.result_area.insert(tk.END, "Processing... Please wait.\n")
        
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
        self.btn_analyze.config(state="normal")
        self.result_area.delete(1.0, tk.END)
        
        if success:
            self.result_area.insert(tk.END, output)
        else:
            self.result_area.insert(tk.END, f"Error:\n{output}")

    def copy_result(self):
        text = self.result_area.get(1.0, tk.END).strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            messagebox.showinfo("Copied", "Result copied to clipboard!")

def analyze_document(target_path: str):
    """
    Open Document Analysis dialog.
    """
    try:
        if not target_path:
            return
            
        root = _get_root_doc()
        dialog = OllamaDocDialog(root, target_path)
        root.wait_window(dialog)
        root.destroy()
            
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open document tool: {e}")
