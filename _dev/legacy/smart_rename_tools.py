"""
Smart Rename GUI Tools.
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

class SmartRenameGUI(BaseWindow):
    def __init__(self, target_path):
        super().__init__(title="ContextUp Smart Rename", width=600, height=350)
        self.target_path = Path(target_path)
        
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Auto-start generation
        self.after(500, self.start_generation)
        
    def create_widgets(self):
        # Header
        self.add_header("AI Smart Rename")

        # Main Frame
        main_frame = ctk.CTkFrame(self.main_frame)
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Current Name
        ctk.CTkLabel(main_frame, text="Current Name:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", padx=15, pady=(15, 5))
        ctk.CTkLabel(main_frame, text=self.target_path.name).grid(row=0, column=1, sticky="w", padx=15, pady=(15, 5))
        
        # Suggestion
        ctk.CTkLabel(main_frame, text="New Name:", font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, sticky="w", padx=15, pady=5)
        self.name_var = ctk.StringVar()
        self.entry_name = ctk.CTkEntry(main_frame, textvariable=self.name_var, width=300)
        self.entry_name.grid(row=1, column=1, sticky="w", padx=15, pady=5)
        
        # Status
        self.status_var = ctk.StringVar(value="Ready")
        self.lbl_status = ctk.CTkLabel(main_frame, textvariable=self.status_var, text_color="gray")
        self.lbl_status.grid(row=2, column=0, columnspan=2, sticky="w", padx=15, pady=10)
        
        # Buttons
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20)
        
        self.btn_apply = ctk.CTkButton(btn_frame, text="Rename", command=self.apply_rename, state="disabled")
        self.btn_apply.pack(side="right", padx=5)
        
        self.btn_generate = ctk.CTkButton(btn_frame, text="Regenerate", command=self.start_generation, fg_color="transparent", border_width=1, border_color="gray")
        self.btn_generate.pack(side="right", padx=5)
        
        ctk.CTkButton(btn_frame, text="Cancel", command=self.destroy, fg_color="transparent", border_width=1, border_color="gray").pack(side="right", padx=5)
        
    def start_generation(self):
        self.btn_generate.configure(state="disabled")
        self.btn_apply.configure(state="disabled")
        self.status_var.set("Analyzing... (This may take a few seconds)")
        
        threading.Thread(target=self.run_generation, daemon=True).start()
        
    def run_generation(self):
        # Run with --dry-run to get suggestion
        args = ["smart_rename.py", str(self.target_path), "--dry-run"]
        
        success, output = run_ai_script(*args)
        
        self.after(0, lambda: self.show_suggestion(success, output))
        
    def show_suggestion(self, success, output):
        self.btn_generate.configure(state="normal")
        
        if success:
            # Parse suggestion from output
            # Output format: "Suggestion: new_name.ext"
            for line in output.splitlines():
                if line.startswith("Suggestion:"):
                    suggestion = line.split("Suggestion:", 1)[1].strip()
                    self.name_var.set(suggestion)
                    self.btn_apply.configure(state="normal")
                    self.status_var.set("Suggestion generated.")
                    return
            
            self.status_var.set("Could not parse suggestion.")
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

    def on_closing(self):
        self.destroy()

def smart_rename(target_path: str):
    """
    Open Smart Rename dialog.
    """
    if not target_path:
        return
        
    app = SmartRenameGUI(target_path)
    app.mainloop()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        smart_rename(sys.argv[1])
