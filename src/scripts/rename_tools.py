import os
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import sys

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.append(str(src_dir))

from utils.explorer import get_selection_from_explorer

class RenameGUI(tk.Tk):
    def __init__(self, target_path, mode="prefix"):
        super().__init__()
        self.title("Rename Tools")
        self.geometry("600x500")
        
        self.target_path = target_path
        self.selection = get_selection_from_explorer(target_path)
        if not self.selection:
            messagebox.showerror("Error", "No files selected.")
            self.destroy()
            return

        self.preview_data = [] # List of (original, new) tuples
        
        # UI Setup
        self.create_widgets(mode)
        self.update_preview()
        
        # Center window
        self.eval('tk::PlaceWindow . center')

    def create_widgets(self, mode):
        # Tab Control
        tab_control = ttk.Notebook(self)
        
        self.tab_prefix = ttk.Frame(tab_control)
        self.tab_suffix = ttk.Frame(tab_control)
        self.tab_remove = ttk.Frame(tab_control)
        
        tab_control.add(self.tab_prefix, text='Add Prefix')
        tab_control.add(self.tab_suffix, text='Add Suffix')
        tab_control.add(self.tab_remove, text='Remove Text')
        
        tab_control.pack(expand=1, fill="both", padx=10, pady=5)
        
        # Select default tab based on mode
        if mode == "prefix":
            tab_control.select(self.tab_prefix)
        elif mode == "suffix":
            tab_control.select(self.tab_suffix)
        elif mode == "remove":
            tab_control.select(self.tab_remove)
            
        # Bind tab change to update preview
        tab_control.bind("<<NotebookTabChanged>>", self.on_tab_change)
        self.tab_control = tab_control

        # --- Prefix Tab ---
        ttk.Label(self.tab_prefix, text="Text to Add:").pack(pady=5)
        self.prefix_entry = ttk.Entry(self.tab_prefix, width=40)
        self.prefix_entry.pack(pady=5)
        self.prefix_entry.bind("<KeyRelease>", self.update_preview)

        # --- Suffix Tab ---
        ttk.Label(self.tab_suffix, text="Text to Add:").pack(pady=5)
        self.suffix_entry = ttk.Entry(self.tab_suffix, width=40)
        self.suffix_entry.pack(pady=5)
        self.suffix_entry.bind("<KeyRelease>", self.update_preview)

        # --- Remove Tab ---
        ttk.Label(self.tab_remove, text="Text to Remove:").pack(pady=5)
        self.remove_entry = ttk.Entry(self.tab_remove, width=40)
        self.remove_entry.pack(pady=5)
        self.remove_entry.bind("<KeyRelease>", self.update_preview)

        # --- Preview Area ---
        frame_preview = ttk.LabelFrame(self, text="Preview")
        frame_preview.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Treeview for preview
        columns = ("original", "new")
        self.tree = ttk.Treeview(frame_preview, columns=columns, show="headings")
        self.tree.heading("original", text="Original Name")
        self.tree.heading("new", text="New Name")
        self.tree.column("original", width=250)
        self.tree.column("new", width=250)
        
        scrollbar = ttk.Scrollbar(frame_preview, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- Buttons ---
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Apply Rename", command=self.apply_rename).pack(side="right", padx=5)

    def on_tab_change(self, event):
        self.update_preview()

    def update_preview(self, event=None):
        current_tab = self.tab_control.index(self.tab_control.select())
        self.preview_data = []
        
        for path in self.selection:
            original_name = path.name
            new_name = original_name
            stem = path.stem
            suffix = path.suffix
            
            if current_tab == 0: # Prefix
                text = self.prefix_entry.get()
                if text:
                    new_name = f"{text}{original_name}"
            elif current_tab == 1: # Suffix
                text = self.suffix_entry.get()
                if text:
                    new_name = f"{stem}{text}{suffix}"
            elif current_tab == 2: # Remove
                text = self.remove_entry.get()
                if text:
                    new_name = original_name.replace(text, "")
            
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


class RenumberGUI(tk.Tk):
    def __init__(self, target_path):
        super().__init__()
        self.title("Renumber Tool")
        self.geometry("600x500")
        
        self.target_path = Path(target_path)
        
        # Determine if folder mode or selection mode
        self.selection = get_selection_from_explorer(target_path)
        
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
        self.eval('tk::PlaceWindow . center')

    def create_widgets(self):
        # Options Frame
        opt_frame = ttk.LabelFrame(self, text=f"Renumber Options ({self.mode})")
        opt_frame.pack(fill="x", padx=10, pady=5)
        
        # Base Name
        ttk.Label(opt_frame, text="Base Name (Optional):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.basename_entry = ttk.Entry(opt_frame)
        self.basename_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.basename_entry.bind("<KeyRelease>", self.update_preview)
        
        # Start Number
        ttk.Label(opt_frame, text="Start Number:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.start_spin = ttk.Spinbox(opt_frame, from_=0, to=99999, width=10)
        self.start_spin.set(0)
        self.start_spin.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.start_spin.bind("<KeyRelease>", self.update_preview)
        self.start_spin.bind("<<Increment>>", self.update_preview)
        self.start_spin.bind("<<Decrement>>", self.update_preview)

        # Padding
        ttk.Label(opt_frame, text="Padding (Digits):").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.pad_spin = ttk.Spinbox(opt_frame, from_=1, to=10, width=5)
        self.pad_spin.set(4)
        self.pad_spin.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        self.pad_spin.bind("<KeyRelease>", self.update_preview)
        self.pad_spin.bind("<<Increment>>", self.update_preview)
        self.pad_spin.bind("<<Decrement>>", self.update_preview)
        
        # Separator
        ttk.Label(opt_frame, text="Separator:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.sep_entry = ttk.Entry(opt_frame, width=5)
        self.sep_entry.insert(0, "_")
        self.sep_entry.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        self.sep_entry.bind("<KeyRelease>", self.update_preview)

        opt_frame.columnconfigure(1, weight=1)

        # Preview Area
        frame_preview = ttk.LabelFrame(self, text="Preview")
        frame_preview.pack(fill="both", expand=True, padx=10, pady=5)
        
        columns = ("original", "new")
        self.tree = ttk.Treeview(frame_preview, columns=columns, show="headings")
        self.tree.heading("original", text="Original Name")
        self.tree.heading("new", text="New Name")
        self.tree.column("original", width=250)
        self.tree.column("new", width=250)
        
        scrollbar = ttk.Scrollbar(frame_preview, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Apply Renumber", command=self.apply_renumber).pack(side="right", padx=5)

    def update_preview(self, event=None):
        self.preview_data = []
        
        basename = self.basename_entry.get()
        separator = self.sep_entry.get()
        
        try:
            start_num = int(self.start_spin.get())
        except:
            start_num = 0
            
        try:
            padding = int(self.pad_spin.get())
        except:
            padding = 4
            
        for i, path in enumerate(self.files_to_process):
            num = start_num + i
            num_str = str(num).zfill(padding)
            suffix = path.suffix
            
            if basename:
                new_name = f"{basename}{separator}{num_str}{suffix}"
            else:
                # If no basename, keep original name but append number? 
                # Or replace name with number? 
                # Usually renumber implies replacing name or appending to original stem.
                # Let's assume replacing name if basename is empty is NOT what we want usually if we just want to sequence.
                # Actually, "Renumber" usually means "Name_0001", "Name_0002".
                # If basename is empty, let's use the original stem of the FIRST file? Or just Number?
                # Let's default to: if basename empty, use "File" or keep original stem?
                # Let's try: If basename empty, use original stem + separator + number.
                new_name = f"{path.stem}{separator}{num_str}{suffix}"
            
            self.preview_data.append((path, new_name))
            
        # Update Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for path, new_name in self.preview_data:
            self.tree.insert("", "end", values=(path.name, new_name))

    def apply_renumber(self):
        # To avoid collisions (e.g. renaming 1->2 when 2 exists), we might need a temp rename strategy
        # or sort carefully. Reverse order might help if increasing, but not always.
        # Safest is rename to temp, then rename to final.
        
        count = 0
        errors = []
        
        # First pass: Rename to temp names
        temp_map = []
        import uuid
        
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
                     # Try to revert?
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
