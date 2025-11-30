"""
Clipboard Tools GUI.
"""
import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext
import threading
from utils.ai_runner import run_ai_script

def _get_root_cb():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    root.lift()
    return root

class ClipboardDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Clipboard Error Analysis")
        self.geometry("600x500")
        
        self.create_widgets()
        self.start_analysis()
        
    def create_widgets(self):
        # Result Area
        self.result_area = scrolledtext.ScrolledText(self, wrap=tk.WORD, font=("Consolas", 10))
        self.result_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Buttons
        btn_frame = ttk.Frame(self, padding="10")
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="Copy Result", command=self.copy_result).pack(side=tk.RIGHT)
        ttk.Button(btn_frame, text="Close", command=self.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Retry", command=self.start_analysis).pack(side=tk.LEFT)
        
    def start_analysis(self):
        self.result_area.delete(1.0, tk.END)
        self.result_area.insert(tk.END, "Analyzing clipboard content... Please wait.\n")
        threading.Thread(target=self.run_analysis, daemon=True).start()
        
    def run_analysis(self):
        args = ["clipboard_error.py"]
        success, output = run_ai_script(*args)
        self.after(0, lambda: self.show_result(success, output))
        
    def show_result(self, success, output):
        self.result_area.delete(1.0, tk.END)
        if success:
            # Extract result
            if "--- Analysis Result ---" in output:
                output = output.split("--- Analysis Result ---")[1].strip()
            self.result_area.insert(tk.END, output)
        else:
            self.result_area.insert(tk.END, f"Error:\n{output}")

    def copy_result(self):
        text = self.result_area.get(1.0, tk.END).strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            messagebox.showinfo("Copied", "Result copied to clipboard!")

def analyze_error():
    """
    Open Clipboard Analysis dialog.
    """
    try:
        root = _get_root_cb()
        dialog = ClipboardDialog(root)
        root.wait_window(dialog)
        root.destroy()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open clipboard tool: {e}")
