"""
Unwrap Folder GUI - Clean minimal dialog
"""
import os
import sys
import shutil
import threading
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

try:
    import customtkinter as ctk
except ImportError:
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Error", "CustomTkinter library is missing.")
    sys.exit(1)

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent
if str(src_dir) not in sys.path:
    sys.path.append(str(src_dir))

from utils.files import get_safe_path
from utils.i18n import t
from core.logger import setup_logger

logger = setup_logger("unwrap_folder")


class UnwrapFolderGUI(ctk.CTk):
    """Clean minimal GUI for unwrapping folders."""
    
    def __init__(self, folders):
        super().__init__()
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        self.folders = [Path(f) for f in folders if Path(f).is_dir()]
        self.recursive_var = tk.BooleanVar(value=False)
        
        self.title(t("unwrap_folder.title"))
        self.geometry("320x180")
        self.resizable(False, False)
        
        self._build_ui()
        self._center_window()
        
        self.lift()
        self.attributes("-topmost", True)
        self.focus_force()

    def _center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 320) // 2
        y = (self.winfo_screenheight() - 180) // 2
        self.geometry(f"+{x}+{y}")

    def _build_ui(self):
        # Main container with padding
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=15, pady=10)
        
        # Title
        ctk.CTkLabel(main, text=t("unwrap_folder.title"), 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")
        
        # Folder info
        folder_text = f"📁 {len(self.folders)}개 폴더 선택됨"
        if len(self.folders) == 1:
            folder_text = f"📁 {self.folders[0].name}"
        ctk.CTkLabel(main, text=folder_text, text_color="#888", 
                    font=ctk.CTkFont(size=11)).pack(anchor="w", pady=(2, 8))
        
        # Recursive checkbox
        ctk.CTkCheckBox(main, text=t("unwrap_folder.recursive"),
                       variable=self.recursive_var, 
                       font=ctk.CTkFont(size=11)).pack(anchor="w", pady=(0, 10))
        
        # Buttons row - fixed at bottom
        btn_row = ctk.CTkFrame(main, fg_color="transparent")
        btn_row.pack(fill="x", side="bottom")
        
        ctk.CTkButton(btn_row, text=t("common.cancel"), width=80, height=28,
                     fg_color="transparent", border_width=1,
                     command=self.destroy).pack(side="right")
        
        self.btn_run = ctk.CTkButton(btn_row, text=t("unwrap_folder.run"), 
                                    width=80, height=28,
                                    fg_color="#27ae60", hover_color="#1e8449",
                                    command=self._run)
        self.btn_run.pack(side="right", padx=(0, 8))

    def _run(self):
        self.btn_run.configure(state="disabled", text="...")
        threading.Thread(target=self._do_unwrap, daemon=True).start()

    def _do_unwrap(self):
        is_recursive = self.recursive_var.get()
        total = 0
        
        for folder in self.folders:
            try:
                target = folder.parent
                items = []
                
                if is_recursive:
                    for root, _, files in os.walk(folder):
                        for name in files:
                            items.append(Path(root) / name)
                else:
                    items = list(folder.iterdir())
                
                for item in items:
                    dest = target / item.name
                    if dest.exists():
                        dest = get_safe_path(dest)
                    shutil.move(str(item), str(dest))
                    total += 1
                
                # Cleanup
                if folder.exists():
                    try:
                        if is_recursive:
                            for r, d, _ in os.walk(folder, topdown=False):
                                for name in d:
                                    try: (Path(r) / name).rmdir()
                                    except: pass
                        folder.rmdir()
                    except:
                        shutil.rmtree(folder, ignore_errors=True)
                        
            except Exception as e:
                logger.error(f"Failed: {folder}: {e}")
        
        self.after(0, lambda: self._done(total))

    def _done(self, count):
        messagebox.showinfo("완료", f"{count}개 항목 이동 완료")
        self.destroy()


def launch_unwrap_gui(target_path: str = None, selection=None):
    """Entry point for menu.py"""
    from utils.batch_runner import collect_batch_context
    
    paths = collect_batch_context("unwrap_folder", target_path)
    if not paths:
        return
    
    folders = [p for p in paths if Path(p).is_dir()]
    if not folders:
        messagebox.showwarning("경고", "폴더를 선택해주세요.")
        return
    
    gui = UnwrapFolderGUI(folders)
    gui.mainloop()


if __name__ == "__main__":
    if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
        gui = UnwrapFolderGUI([sys.argv[1]])
        gui.mainloop()
    else:
        print("Usage: unwrap_folder_gui.py <folder_path>")
