"""
Flatten Directory Tool.
Moves all files from subdirectories to the root folder and deletes empty subdirectories.
"""
import sys
import os
import shutil
import threading
from pathlib import Path
import customtkinter as ctk
from tkinter import messagebox

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.append(str(src_dir))

from utils.gui_lib import BaseWindow

class FlattenDirGUI(BaseWindow):
    def __init__(self, target_path=None):
        super().__init__(title="Flatten Directory", width=600, height=450)
        
        self.target_path = target_path
        if not self.target_path:
            # Ask for directory if not provided
            self.target_path = ctk.filedialog.askdirectory(title="Select Directory to Flatten")
            if not self.target_path:
                self.destroy()
                return
        
        self.target_path = Path(self.target_path)
        self.create_widgets()
        self.scan_directory()

    def create_widgets(self):
        # Header
        ctk.CTkLabel(self.main_frame, text="Flatten Directory", font=("", 20, "bold")).pack(pady=15)
        
        # Path Info
        path_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        path_frame.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(path_frame, text="Target:", font=("", 12, "bold")).pack(side="left")
        ctk.CTkLabel(path_frame, text=str(self.target_path), text_color="gray").pack(side="left", padx=10)
        
        # Stats
        self.lbl_stats = ctk.CTkLabel(self.main_frame, text="Scanning...", font=("", 14))
        self.lbl_stats.pack(pady=10)
        
        # Options
        opts_frame = ctk.CTkFrame(self.main_frame)
        opts_frame.pack(fill="x", padx=20, pady=10)
        
        self.var_delete_empty = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(opts_frame, text="Delete Empty Subdirectories", variable=self.var_delete_empty).pack(anchor="w", padx=20, pady=10)
        
        self.var_collision = ctk.StringVar(value="rename")
        ctk.CTkLabel(opts_frame, text="Collision Handling:").pack(anchor="w", padx=20, pady=(10, 5))
        ctk.CTkRadioButton(opts_frame, text="Rename (append _1, _2...)", variable=self.var_collision, value="rename").pack(anchor="w", padx=40, pady=2)
        ctk.CTkRadioButton(opts_frame, text="Skip", variable=self.var_collision, value="skip").pack(anchor="w", padx=40, pady=2)
        ctk.CTkRadioButton(opts_frame, text="Overwrite (Dangerous)", variable=self.var_collision, value="overwrite").pack(anchor="w", padx=40, pady=(2, 10))
        
        # Log/Preview
        self.log_text = ctk.CTkTextbox(self.main_frame, height=150)
        self.log_text.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Actions
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkButton(btn_frame, text="Flatten Now", command=self.run_flatten, fg_color="#C0392B", hover_color="#E74C3C").pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="Cancel", command=self.destroy, fg_color="transparent", border_width=1, text_color="gray").pack(side="right", padx=5)

    def scan_directory(self):
        self.files_to_move = []
        self.subdirs = []
        
        try:
            for root, dirs, files in os.walk(self.target_path):
                if Path(root) == self.target_path:
                    # Don't move files already in root
                    self.subdirs.extend([Path(root) / d for d in dirs])
                    continue
                    
                for f in files:
                    self.files_to_move.append(Path(root) / f)
                
                self.subdirs.append(Path(root))
                
            self.lbl_stats.configure(text=f"Found {len(self.files_to_move)} files in {len(self.subdirs)} subdirectories.")
            self.log_text.insert("0.0", f"Ready to move {len(self.files_to_move)} files to root.\n")
            
        except Exception as e:
            self.lbl_stats.configure(text=f"Error: {e}")

    def run_flatten(self):
        if not self.files_to_move:
            messagebox.showinfo("Info", "No files to move.")
            return
            
        if not messagebox.askyesno("Confirm Flatten", f"Move {len(self.files_to_move)} files to root?\nThis cannot be easily undone."):
            return
            
        collision_mode = self.var_collision.get()
        delete_empty = self.var_delete_empty.get()
        
        def _process():
            moved_count = 0
            skipped_count = 0
            errors = 0
            
            for src in self.files_to_move:
                dst = self.target_path / src.name
                
                if dst.exists():
                    if collision_mode == "skip":
                        skipped_count += 1
                        self.log("Skipped (Exists): " + src.name)
                        continue
                    elif collision_mode == "overwrite":
                        pass # Will overwrite
                    elif collision_mode == "rename":
                        base = dst.stem
                        ext = dst.suffix
                        counter = 1
                        while dst.exists():
                            dst = self.target_path / f"{base}_{counter}{ext}"
                            counter += 1
                
                try:
                    shutil.move(str(src), str(dst))
                    moved_count += 1
                    # self.log(f"Moved: {src.name}") # Too verbose for many files
                except Exception as e:
                    self.log(f"Error moving {src.name}: {e}")
                    errors += 1
            
            # Delete empty dirs
            deleted_dirs = 0
            if delete_empty:
                # Walk bottom-up to delete nested empty dirs
                for root, dirs, files in os.walk(self.target_path, topdown=False):
                    if Path(root) == self.target_path: continue
                    try:
                        os.rmdir(root)
                        deleted_dirs += 1
                    except:
                        pass # Not empty
            
            self.log(f"\nDone! Moved: {moved_count}, Skipped: {skipped_count}, Errors: {errors}")
            if delete_empty:
                self.log(f"Deleted {deleted_dirs} empty directories.")
                
            self.after(0, lambda: messagebox.showinfo("Complete", "Flatten operation finished."))
            
        threading.Thread(target=_process, daemon=True).start()

    def log(self, msg):
        self.after(0, lambda: self.log_text.insert("end", msg + "\n"))
        self.after(0, lambda: self.log_text.see("end"))

if __name__ == "__main__":
    path_arg = sys.argv[1] if len(sys.argv) > 1 else None
    app = FlattenDirGUI(path_arg)
    app.mainloop()
