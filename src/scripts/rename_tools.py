import os
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import sys
import uuid

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.append(str(src_dir))

from utils.explorer import get_selection_from_explorer
from utils.gui_lib import BaseWindow

class RenameGUI(BaseWindow):
    def __init__(self, target_path, mode="prefix"):
        super().__init__(title="ContextUp Rename Tools", width=700, height=600)
        
        self.target_path = target_path
        self.selection = get_selection_from_explorer(target_path)
        
        # Strict check: If no selection, do not run.
        if not self.selection:
            # If target_path is a file, use it.
            p = Path(target_path)
            if p.is_file():
                self.selection = [p]
            else:
                # Nothing selected, and target is likely a folder (background click)
                # User requested: "If nothing selected, do not expose this function"
                # We destroy and return.
                self.destroy()
                return

        self.preview_data = [] # List of (original, new) tuples
        self.mode = mode
        
        self.create_widgets()
        self.update_preview()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        # Header
        self.add_header(f"Renaming {len(self.selection)} files")

        # Tab Control
        self.tab_view = ctk.CTkTabview(self.main_frame)
        self.tab_view.pack(fill="x", padx=20, pady=10)
        
        self.tab_prefix = self.tab_view.add("Add Prefix")
        self.tab_suffix = self.tab_view.add("Add Suffix")
        self.tab_remove = self.tab_view.add("Remove Text")
        
        # Select default tab
        if self.mode == "prefix": self.tab_view.set("Add Prefix")
        elif self.mode == "suffix": self.tab_view.set("Add Suffix")
        elif self.mode == "remove": self.tab_view.set("Remove Text")
            
        # Bind tab change (CustomTkinter doesn't have a direct event for this, 
        # but we can bind to the command or just update on every keypress in any tab)
        # Actually CTkTabview has a command argument in constructor or configure? No.
        # We'll just update preview when inputs change.

        # --- Prefix Tab ---
        ctk.CTkLabel(self.tab_prefix, text="Text to Add:").pack(pady=5)
        self.prefix_entry = ctk.CTkEntry(self.tab_prefix, width=300)
        self.prefix_entry.pack(pady=5)
        self.prefix_entry.bind("<KeyRelease>", self.update_preview)

        # --- Suffix Tab ---
        ctk.CTkLabel(self.tab_suffix, text="Text to Add:").pack(pady=5)
        self.suffix_entry = ctk.CTkEntry(self.tab_suffix, width=300)
        self.suffix_entry.pack(pady=5)
        self.suffix_entry.bind("<KeyRelease>", self.update_preview)

        # --- Remove Tab ---
        ctk.CTkLabel(self.tab_remove, text="Text to Remove:").pack(pady=5)
        self.remove_entry = ctk.CTkEntry(self.tab_remove, width=300)
        self.remove_entry.pack(pady=5)
        self.remove_entry.bind("<KeyRelease>", self.update_preview)

        # --- Replace Tab ---
        self.tab_replace = self.tab_view.add("Replace Text")
        
        ctk.CTkLabel(self.tab_replace, text="Find:").pack(pady=5)
        self.find_entry = ctk.CTkEntry(self.tab_replace, width=300)
        self.find_entry.pack(pady=5)
        self.find_entry.bind("<KeyRelease>", self.update_preview)
        
        ctk.CTkLabel(self.tab_replace, text="Replace with:").pack(pady=5)
        self.replace_entry = ctk.CTkEntry(self.tab_replace, width=300)
        self.replace_entry.pack(pady=5)
        self.replace_entry.bind("<KeyRelease>", self.update_preview)

        # Select default tab
        if self.mode == "prefix": self.tab_view.set("Add Prefix")
        elif self.mode == "suffix": self.tab_view.set("Add Suffix")
        elif self.mode == "remove": self.tab_view.set("Remove Text")
        elif self.mode == "replace": self.tab_view.set("Replace Text")

        # --- Preview Area ---
        ctk.CTkLabel(self.main_frame, text="Preview:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(10, 5))
        
        frame_preview = ctk.CTkFrame(self.main_frame)
        frame_preview.pack(fill="both", expand=True, padx=20, pady=5)
        
        # Treeview for preview (Using ttk because ctk doesn't have a table yet)
        # We need to style it a bit to look decent in dark mode
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", borderwidth=0)
        style.map("Treeview", background=[("selected", "#1f538d")])
        style.configure("Treeview.Heading", background="#333333", foreground="white", relief="flat")
        style.map("Treeview.Heading", background=[("active", "#404040")])
        
        columns = ("original", "new")
        self.tree = ttk.Treeview(frame_preview, columns=columns, show="headings", selectmode="none")
        self.tree.heading("original", text="Original Name")
        self.tree.heading("new", text="New Name")
        self.tree.column("original", width=300)
        self.tree.column("new", width=300)
        
        scrollbar = ttk.Scrollbar(frame_preview, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True, padx=2, pady=2)
        scrollbar.pack(side="right", fill="y", padx=2, pady=2)

        # --- Buttons ---
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkButton(btn_frame, text="Apply Rename", command=self.apply_rename).pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="Cancel", fg_color="transparent", border_width=1, border_color="gray", command=self.destroy).pack(side="right", padx=5)
        
        # Bind tab clicks to update preview (workaround)
        # We need to preserve the original callback that handles tab switching
        self._original_tab_callback = self.tab_view._segmented_button._command
        self.tab_view._segmented_button.configure(command=self.on_tab_change)

    def on_tab_change(self, value):
        if self._original_tab_callback:
            self._original_tab_callback(value)
        self.update_preview()

    def update_preview(self, event=None):
        current_tab = self.tab_view.get()
        self.preview_data = []
        
        for path in self.selection:
            original_name = path.name
            new_name = original_name
            stem = path.stem
            suffix = path.suffix
            
            if current_tab == "Add Prefix":
                text = self.prefix_entry.get()
                if text:
                    new_name = f"{text}{original_name}"
            elif current_tab == "Add Suffix":
                text = self.suffix_entry.get()
                if text:
                    new_name = f"{stem}{text}{suffix}"
            elif current_tab == "Remove Text":
                text = self.remove_entry.get()
                if text:
                    new_name = original_name.replace(text, "")
            elif current_tab == "Replace Text":
                find_text = self.find_entry.get()
                replace_text = self.replace_entry.get()
                if find_text:
                    new_name = original_name.replace(find_text, replace_text)
            
            self.preview_data.append((path, new_name))

        # Update Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for path, new_name in self.preview_data:
            self.tree.insert("", "end", values=(path.name, new_name))

    def apply_rename(self):
        count = 0
        errors = []
        
        for path, new_name in self.preview_data:
            if path.name == new_name:
                continue
                
            try:
                new_path = path.parent / new_name
                if new_path.exists():
                    errors.append(f"Skipped {path.name}: {new_name} already exists.")
                    continue
                
                os.rename(path, new_path)
                count += 1
            except Exception as e:
                errors.append(f"Error renaming {path.name}: {e}")
        
        msg = f"Renamed {count} files."
        if errors:
            msg += "\n\nErrors:\n" + "\n".join(errors[:10])
            if len(errors) > 10:
                msg += f"\n...and {len(errors)-10} more."
            messagebox.showwarning("Rename Result", msg)
        else:
            messagebox.showinfo("Success", msg)
            
        self.destroy()
    
    def on_closing(self):
        self.destroy()


class RenumberGUI(BaseWindow):
    def __init__(self, target_path):
        super().__init__(title="ContextUp Renumber Tool", width=700, height=600)
        
        self.target_path = Path(target_path)
        
        # Determine if folder mode or selection mode
        self.selection = get_selection_from_explorer(target_path)
        
        # If no selection, check if target_path is a file
        if not self.selection:
            if self.target_path.is_file():
                self.selection = [self.target_path]
            else:
                # Nothing selected, and target is likely a folder (background click)
                # User requested: "If nothing selected, do not expose this function"
                self.destroy()
                return

        # If selection is just the folder itself, treat as folder mode (process all files inside)
        if len(self.selection) == 1 and self.selection[0] == self.target_path and self.target_path.is_dir():
             self.files_to_process = sorted([p for p in self.target_path.iterdir() if p.is_file()])
             self.mode = "Folder Sequence"
        else:
            self.files_to_process = sorted(self.selection)
            self.mode = "Selection"

        if not self.files_to_process:
            messagebox.showerror("Error", "No files to renumber.")
            self.destroy()
            return

        self.preview_data = []
        
        self.create_widgets()
        self.update_preview()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        self.add_header(f"Renumbering ({self.mode})")

        # Options Frame
        opt_frame = ctk.CTkFrame(self.main_frame)
        opt_frame.pack(fill="x", padx=20, pady=10)
        
        # Base Name
        ctk.CTkLabel(opt_frame, text="Base Name (Optional):").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.basename_entry = ctk.CTkEntry(opt_frame, width=200)
        self.basename_entry.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        self.basename_entry.bind("<KeyRelease>", self.update_preview)
        
        # Start Number
        ctk.CTkLabel(opt_frame, text="Start Number:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.start_entry = ctk.CTkEntry(opt_frame, width=100)
        self.start_entry.insert(0, "0")
        self.start_entry.grid(row=1, column=1, padx=10, pady=10, sticky="w")
        self.start_entry.bind("<KeyRelease>", self.update_preview)

        # Padding
        ctk.CTkLabel(opt_frame, text="Padding (Digits):").grid(row=2, column=0, padx=10, pady=10, sticky="e")
        self.pad_entry = ctk.CTkEntry(opt_frame, width=100)
        self.pad_entry.insert(0, "4")
        self.pad_entry.grid(row=2, column=1, padx=10, pady=10, sticky="w")
        self.pad_entry.bind("<KeyRelease>", self.update_preview)
        
        # Separator
        ctk.CTkLabel(opt_frame, text="Separator:").grid(row=3, column=0, padx=10, pady=10, sticky="e")
        self.sep_entry = ctk.CTkEntry(opt_frame, width=50)
        self.sep_entry.insert(0, "_")
        self.sep_entry.grid(row=3, column=1, padx=10, pady=10, sticky="w")
        self.sep_entry.bind("<KeyRelease>", self.update_preview)

        # Preview Area
        ctk.CTkLabel(self.main_frame, text="Preview:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(10, 5))
        
        frame_preview = ctk.CTkFrame(self.main_frame)
        frame_preview.pack(fill="both", expand=True, padx=20, pady=5)
        
        # Treeview (Styled)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", borderwidth=0)
        style.map("Treeview", background=[("selected", "#1f538d")])
        style.configure("Treeview.Heading", background="#333333", foreground="white", relief="flat")
        style.map("Treeview.Heading", background=[("active", "#404040")])
        
        columns = ("original", "new")
        self.tree = ttk.Treeview(frame_preview, columns=columns, show="headings", selectmode="none")
        self.tree.heading("original", text="Original Name")
        self.tree.heading("new", text="New Name")
        self.tree.column("original", width=300)
        self.tree.column("new", width=300)
        
        scrollbar = ttk.Scrollbar(frame_preview, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True, padx=2, pady=2)
        scrollbar.pack(side="right", fill="y", padx=2, pady=2)

        # Buttons
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkButton(btn_frame, text="Apply Renumber", command=self.apply_renumber).pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="Cancel", fg_color="transparent", border_width=1, border_color="gray", command=self.destroy).pack(side="right", padx=5)

    def update_preview(self, event=None):
        self.preview_data = []
        
        basename = self.basename_entry.get()
        separator = self.sep_entry.get()
        
        try:
            start_num = int(self.start_entry.get())
        except:
            start_num = 0
            
        try:
            padding = int(self.pad_entry.get())
        except:
            padding = 4
            
        for i, path in enumerate(self.files_to_process):
            num = start_num + i
            num_str = str(num).zfill(padding)
            suffix = path.suffix
            
            if basename:
                new_name = f"{basename}{separator}{num_str}{suffix}"
            else:
                new_name = f"{path.stem}{separator}{num_str}{suffix}"
            
            self.preview_data.append((path, new_name))
            
        # Update Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for path, new_name in self.preview_data:
            self.tree.insert("", "end", values=(path.name, new_name))

    def apply_renumber(self):
        count = 0
        errors = []
        
        # First pass: Rename to temp names
        temp_map = []
        
        for path, new_name in self.preview_data:
            if path.name == new_name:
                continue
                
            temp_name = f"{uuid.uuid4()}{path.suffix}"
            temp_path = path.parent / temp_name
            try:
                os.rename(path, temp_path)
                temp_map.append((temp_path, new_name))
            except Exception as e:
                errors.append(f"Error preparing {path.name}: {e}")
        
        # Second pass: Rename temp to final
        for temp_path, new_name in temp_map:
            final_path = temp_path.parent / new_name
            try:
                if final_path.exists():
                     errors.append(f"Collision for {new_name}")
                     continue
                os.rename(temp_path, final_path)
                count += 1
            except Exception as e:
                errors.append(f"Error finalizing {new_name}: {e}")

        msg = f"Renumbered {count} files."
        if errors:
            msg += "\n\nErrors:\n" + "\n".join(errors[:10])
            messagebox.showwarning("Renumber Result", msg)
        else:
            messagebox.showinfo("Success", msg)
            
        self.destroy()

    def on_closing(self):
        self.destroy()

def run_rename_gui(target_path, mode="prefix"):
    app = RenameGUI(target_path, mode)
    app.mainloop()

def run_renumber_gui(target_path):
    app = RenumberGUI(target_path)
    app.mainloop()

if __name__ == "__main__":
    if len(sys.argv) > 2:
        cmd = sys.argv[1]
        path = sys.argv[2]
        if cmd == "rename":
            run_rename_gui(path)
        elif cmd == "renumber":
            run_renumber_gui(path)
