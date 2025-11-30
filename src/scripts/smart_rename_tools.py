"""
Smart Rename GUI Tools.
"""
import tkinter as tk
from tkinter import messagebox, ttk
from pathlib import Path
import threading
from utils.ai_runner import run_ai_script

def _get_root_sr():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    root.lift()
    return root

class SmartRenameDialog(tk.Toplevel):
    def __init__(self, parent, target_path):
        super().__init__(parent)
        self.title("Smart Rename (AI)")
        self.geometry("500x250")
        self.target_path = Path(target_path)
        
        self.create_widgets()
        
    def create_widgets(self):
        # Main Frame
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Current Name
        ttk.Label(main_frame, text="Current Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Label(main_frame, text=self.target_path.name, font=("Consolas", 10, "bold")).grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # Suggestion
        ttk.Label(main_frame, text="New Name:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar()
        self.entry_name = ttk.Entry(main_frame, textvariable=self.name_var, width=40)
        self.entry_name.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Models (Hidden/Advanced or just default?)
        # Let's keep it simple for now, maybe add a "Regenerate" button
        
        # Status
        self.status_var = tk.StringVar(value="Ready")
        self.lbl_status = ttk.Label(main_frame, textvariable=self.status_var, foreground="gray")
        self.lbl_status.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=10)
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        self.btn_generate = ttk.Button(btn_frame, text="Generate Suggestion", command=self.start_generation)
        self.btn_generate.pack(side=tk.LEFT, padx=5)
        
        self.btn_apply = ttk.Button(btn_frame, text="Rename", command=self.apply_rename, state="disabled")
        self.btn_apply.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.LEFT, padx=5)
        
        # Auto-start generation
        self.after(500, self.start_generation)
        
    def start_generation(self):
        self.btn_generate.config(state="disabled")
        self.btn_apply.config(state="disabled")
        self.status_var.set("Analyzing... (This may take a few seconds)")
        
        threading.Thread(target=self.run_generation, daemon=True).start()
        
    def run_generation(self):
        # Run with --dry-run to get suggestion
        # We need to capture stdout
        args = ["smart_rename.py", str(self.target_path), "--dry-run"]
        
        success, output = run_ai_script(*args)
        
        self.after(0, lambda: self.show_suggestion(success, output))
        
    def show_suggestion(self, success, output):
        self.btn_generate.config(state="normal")
        
        if success:
            # Parse suggestion from output
            # Output format: "Suggestion: new_name.ext"
            for line in output.splitlines():
                if line.startswith("Suggestion:"):
                    suggestion = line.split("Suggestion:", 1)[1].strip()
                    self.name_var.set(suggestion)
                    self.btn_apply.config(state="normal")
                    self.status_var.set("Suggestion generated.")
                    return
            
            self.status_var.set("Could not parse suggestion.")
            # Show raw output in tooltip or print?
            print(output)
        else:
            self.status_var.set("Error generating suggestion.")
            messagebox.showerror("Error", f"Analysis failed:\n{output}")

    def apply_rename(self):
        new_name = self.name_var.get().strip()
        if not new_name:
            return
            
        new_path = self.target_path.parent / new_name
        
        try:
            if new_path.exists() and new_path != self.target_path:
                if not messagebox.askyesno("Confirm", f"File '{new_name}' already exists. Overwrite?"):
                    return
            
            self.target_path.rename(new_path)
            messagebox.showinfo("Success", f"Renamed to:\n{new_name}")
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Rename failed: {e}")

def smart_rename(target_path: str):
    """
    Open Smart Rename dialog.
    """
    try:
        if not target_path:
            return
            
        root = _get_root_sr()
        dialog = SmartRenameDialog(root, target_path)
        root.wait_window(dialog)
        root.destroy()
            
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open smart rename: {e}")
