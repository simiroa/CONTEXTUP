"""
Mayo CAD conversion tools.
"""
import subprocess
import sys
from pathlib import Path
from tkinter import messagebox
import tkinter as tk
import customtkinter as ctk
import threading

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent
sys.path.append(str(src_dir))

from utils.external_tools import get_mayo

try:
    from core.settings import load_settings
    from utils.gui_lib import BaseWindow
    from utils.explorer import get_selection_from_explorer
except Exception as e:
    print(f"Failed to import local modules: {e}")

def open_with_mayo(target_path: str):
    """
    Open the selected file(s) with Mayo.
    """
    try:
        selection = get_selection_from_explorer(target_path)
        if not selection:
            selection = [target_path]
            
        mayo = get_mayo()
        if not mayo:
            messagebox.showerror("Error", "Mayo executable not found.")
            return

        # Open first file (Mayo might not support multiple args, or we launch one instance)
        # For now, let's try to open the first one.
        if selection:
            file_to_open = selection[0]
            subprocess.Popen([mayo, str(file_to_open)])
            
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open Mayo: {e}")

class CadConvertGUI(BaseWindow):
    def __init__(self, target_path):
        super().__init__(title="CAD Converter (Mayo)", width=600, height=400)
        self.target_path = target_path
        self.files_to_convert = []
        
        self.init_files()
        self.create_widgets()
        
    def init_files(self):
        selection = get_selection_from_explorer(self.target_path)
        if not selection:
            selection = [self.target_path]
            
        cad_exts = {'.step', '.stp', '.iges', '.igs'}
        self.files_to_convert = [Path(p) for p in selection if Path(p).suffix.lower() in cad_exts]
        
        if not self.files_to_convert:
            messagebox.showinfo("Info", "No CAD files selected.")
            self.destroy()
            return

    def create_widgets(self):
        # Header
        header = ctk.CTkLabel(self.main_frame, text=f"Selected {len(self.files_to_convert)} CAD Files", font=("Segoe UI", 18, "bold"))
        header.pack(pady=20)
        
        # File List
        scroll = ctk.CTkScrollableFrame(self.main_frame, height=150)
        scroll.pack(fill="x", padx=20, pady=10)
        
        for f in self.files_to_convert:
            lbl = ctk.CTkLabel(scroll, text=f.name, anchor="w")
            lbl.pack(fill="x")
            
        # Buttons
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(pady=20, fill="x", padx=20)
        
        self.btn_convert = ctk.CTkButton(btn_frame, text="Convert to OBJ", command=self.run_conversion, height=40, font=("Segoe UI", 14, "bold"))
        self.btn_convert.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.btn_open = ctk.CTkButton(btn_frame, text="Open with Mayo", command=self.open_in_mayo, height=40, fg_color="#444", hover_color="#555")
        self.btn_open.pack(side="right", fill="x", expand=True, padx=(10, 0))
        
        # Status
        self.status_label = ctk.CTkLabel(self.main_frame, text="Ready", text_color="gray")
        self.status_label.pack(side="bottom", pady=10)

    def open_in_mayo(self):
        mayo = get_mayo()
        if not mayo:
            messagebox.showerror("Error", "Mayo executable not found.")
            return
            
        if self.files_to_convert:
            # Open the first file in the list
            subprocess.Popen([mayo, str(self.files_to_convert[0])])

    def run_conversion(self):
        self.btn_convert.configure(state="disabled")
        self.status_label.configure(text="Converting...", text_color="yellow")
        
        def _process():
            mayo = get_mayo()
            success_count = 0
            errors = []
            
            for path in self.files_to_convert:
                try:
                    output_path = path.with_suffix('.obj')
                    cmd = [mayo, "-i", str(path), "-o", str(output_path), "--export-format", "obj"]
                    subprocess.run(cmd, check=True, capture_output=True, text=True)
                    success_count += 1
                except Exception as e:
                    errors.append(f"{path.name}: {e}")
            
            self.after(0, lambda: self._finish(success_count, errors))
            
        threading.Thread(target=_process, daemon=True).start()
        
    def _finish(self, success_count, errors):
        self.btn_convert.configure(state="normal")
        if errors:
            msg = f"Converted {success_count}/{len(self.files_to_convert)} files.\nErrors:\n" + "\n".join(errors[:3])
            messagebox.showwarning("Completed with Errors", msg)
            self.status_label.configure(text="Completed with Errors", text_color="orange")
        else:
            messagebox.showinfo("Success", f"Successfully converted {success_count} files.")
            self.status_label.configure(text="Success", text_color="green")
            self.destroy()

def convert_cad(target_path: str):
    """
    Entry point for CAD conversion. Launches the GUI.
    """
    app = CadConvertGUI(target_path)
    app.mainloop()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Check if we are opening or converting
        # For now, default to convert_cad which launches GUI
        # If we wanted a direct open, we'd need a flag or separate entry point
        # But the menu system calls specific functions or scripts.
        # If called as script, we assume conversion GUI.
        convert_cad(sys.argv[1])

