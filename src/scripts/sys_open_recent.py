"""
System Tool: Open Recent Folders (Windows Recent Items).
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import os
import sys
import datetime

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.append(str(src_dir))

from utils.gui_lib import BaseWindow

def get_recent_folders():
    """
    Scans Windows Recent items for folders.
    Returns a list of (path, modified_time) tuples, sorted by modified_time desc.
    """
    recent_path = Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Recent"
    if not recent_path.exists():
        return []

    items = []
    
    try:
        import pythoncom
        from win32com.client import Dispatch

        shell = Dispatch("WScript.Shell")
        
        for link_file in recent_path.glob("*.lnk"):
            try:
                shortcut = shell.CreateShortcut(str(link_file))
                target = shortcut.TargetPath
                if not target: continue
                
                p = Path(target)
                if not p.exists(): continue
                
                # Use the link's modification time
                mod_time = link_file.stat().st_mtime
                
                if p.is_dir():
                    items.append((str(p), mod_time))
                elif p.is_file():
                    # If it's a file, add its parent folder
                    items.append((str(p.parent), mod_time))
            except:
                continue
                
    except ImportError:
        # Fallback if pywin32 is missing (though unlikely in system python)
        print("pywin32 not found, cannot resolve shortcuts.")
        return []
        
    # Sort by time desc
    items.sort(key=lambda x: x[1], reverse=True)
    
    # Deduplicate preserving order
    seen = set()
    unique_items = []
    for path, mod_time in items:
        if path.lower() not in seen:
            seen.add(path.lower())
            unique_items.append((path, mod_time))
            
    return unique_items[:20] # Return top 20

def get_unc_path(path_str):
    try:
        import win32wnet
        return win32wnet.WNetGetUniversalName(path_str, 1)
    except:
        # Fallback: if it's a local path, maybe just return absolute path
        # or try to construct admin share (e.g. C:\ -> \\localhost\C$)
        # But usually users just want the path they can share.
        # If it's a mapped drive that failed WNet, we return original.
        return str(Path(path_str).resolve())

class OpenRecentGUI(BaseWindow):
    def __init__(self):
        super().__init__(title="Open Recent Folders (Beta)", width=700, height=500)
        
        self.list_frame = None
        self.create_widgets()
        self.refresh_list()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_widgets(self):
        # Header Frame
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(header_frame, text="Recent Folders (Windows)", font=ctk.CTkFont(size=20, weight="bold")).pack(side="left")
        ctk.CTkButton(header_frame, text="↻ Refresh", width=80, command=self.refresh_list).pack(side="right")
        
        # Scrollable list container
        self.list_frame = ctk.CTkScrollableFrame(self.main_frame)
        self.list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Footer
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(btn_frame, text="Close", width=100, fg_color="transparent", border_width=1, border_color="gray", command=self.destroy).pack(side="right")
        self.btn_open_most = ctk.CTkButton(btn_frame, text="Open Most Recent", width=150, command=self.open_most_recent)
        self.btn_open_most.pack(side="left")
        
        self.status_label = ctk.CTkLabel(btn_frame, text="", text_color="gray", font=("", 11))
        self.status_label.pack(side="left", padx=20)

    def refresh_list(self):
        # Clear existing
        for widget in self.list_frame.winfo_children():
            widget.destroy()
            
        self.recent_folders = get_recent_folders()
        
        if not self.recent_folders:
            ctk.CTkLabel(self.list_frame, text="No recent folders found.").pack(pady=20)
            self.btn_open_most.configure(state="disabled")
            return
            
        self.btn_open_most.configure(state="normal")
        
        for path_str, mod_time in self.recent_folders:
            # Card style
            card = ctk.CTkFrame(self.list_frame, fg_color=("gray85", "gray25"))
            card.pack(fill="x", pady=2)
            
            # Format time
            dt = datetime.datetime.fromtimestamp(mod_time)
            time_str = dt.strftime("%Y-%m-%d %H:%M")
            
            # Layout: [Open Button (Path + Time)] [Copy UNC Button]
            
            # Open Button (Left, expands)
            # Use a frame for the button content to align text
            btn_text = f"[{time_str}]  {path_str}"
            btn_open = ctk.CTkButton(card, text=btn_text, anchor="w", fg_color="transparent", 
                              hover_color=("gray75", "gray35"), text_color=("black", "white"),
                              command=lambda p=path_str: self.open_folder(p))
            btn_open.pack(side="left", fill="both", expand=True, padx=5, pady=5)
            
            # Copy UNC Button (Right, fixed width)
            btn_copy = ctk.CTkButton(card, text="Copy UNC", width=80, fg_color=("gray70", "gray30"),
                                   hover_color=("gray60", "gray40"), text_color=("black", "white"),
                                   command=lambda p=path_str: self.copy_unc(p))
            btn_copy.pack(side="right", padx=5, pady=5)

    def open_most_recent(self):
        if self.recent_folders:
            self.open_folder(self.recent_folders[0][0])

    def open_folder(self, path_str):
        try:
            os.startfile(path_str)
            # Window stays open as requested
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open folder: {e}")

    def copy_unc(self, path_str):
        try:
            unc_path = get_unc_path(path_str)
            self.clipboard_clear()
            self.clipboard_append(unc_path)
            self.update() # Required for clipboard to finalize sometimes
            
            # Show feedback
            self.status_label.configure(text=f"Copied: {unc_path}")
            # Auto-clear status after 3s
            self.after(3000, lambda: self.status_label.configure(text=""))
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy UNC: {e}")

    def on_closing(self):
        self.destroy()

if __name__ == "__main__":
    try:
        app = OpenRecentGUI()
        app.mainloop()
    except Exception as e:
        messagebox.showerror("Error", f"Failed: {e}")
