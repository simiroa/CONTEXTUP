import os
import threading
import tkinter as tk
from pathlib import Path
import customtkinter as ctk
from tkinter import filedialog, messagebox

# Data & Logic
from .models import FinderGroup, FinderItem
from .scanner import scan_worker
from core.logger import setup_logger

# PIP: send2trash
try:
    from send2trash import send2trash
except ImportError:
    send2trash = None

logger = setup_logger("finder_ui")

class FinderApp(ctk.CTk):
    def __init__(self, target_path=""):
        super().__init__()
        self.title("ContextUp - Advanced Finder")
        self.geometry("1000x800")

        self.target_path = target_path
        
        self._setup_ui()
        
        if self.target_path:
            self.lbl_path.configure(text=str(self.target_path))
            self._start_scan_thread()

    def _setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Left Sidebar
        self.frm_sidebar = ctk.CTkFrame(self, width=300, corner_radius=0)
        self.frm_sidebar.grid(row=0, column=0, sticky="nsew")
        self.frm_sidebar.grid_rowconfigure(5, weight=1) # Spacer at bottom

        # 1. Scope
        ctk.CTkLabel(self.frm_sidebar, text="Scan Scope", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(15, 5), padx=15, anchor="w")
        
        self.btn_select_path = ctk.CTkButton(self.frm_sidebar, text="Select Folder", command=self._select_folder)
        self.btn_select_path.pack(pady=5, padx=15, fill="x")
        
        self.lbl_path = ctk.CTkLabel(self.frm_sidebar, text=self.target_path or "No path selected", text_color="gray", wraplength=250)
        self.lbl_path.pack(pady=5, padx=15)
        
        # 2. Mode (Tab view)
        self.tab_mode = ctk.CTkTabview(self.frm_sidebar, height=140)
        self.tab_mode.pack(pady=10, padx=15, fill="x")
        
        tab_simple = self.tab_mode.add("Simple")
        tab_smart = self.tab_mode.add("Smart")
        
        # Simple Tab Content
        self.var_chk_name = ctk.BooleanVar(value=True)
        self.var_chk_size = ctk.BooleanVar(value=True)
        self.var_chk_hash = ctk.BooleanVar(value=False)
        
        ctk.CTkCheckBox(tab_simple, text="Duplicate Name", variable=self.var_chk_name).pack(anchor="w", pady=2, padx=5)
        ctk.CTkCheckBox(tab_simple, text="Duplicate Size", variable=self.var_chk_size).pack(anchor="w", pady=2, padx=5)
        ctk.CTkCheckBox(tab_simple, text="Duplicate Hash (Slow)", variable=self.var_chk_hash).pack(anchor="w", pady=2, padx=5)
        
        # Smart Tab Content (Placeholder)
        ctk.CTkLabel(tab_smart, text="Smart Analysis\n(Coming Soon)", text_color="gray").pack(pady=20)
        
        # Start Button
        self.btn_start = ctk.CTkButton(self.frm_sidebar, text="START SCAN", fg_color="green", command=self._start_scan_thread)
        self.btn_start.pack(pady=10, padx=15, fill="x")
        
        # 3. Filter Tools
        ctk.CTkLabel(self.frm_sidebar, text="Selection Tools", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(15, 5), padx=15, anchor="w")
        
        self.entry_pattern = ctk.CTkEntry(self.frm_sidebar, placeholder_text="Name pattern...")
        self.entry_pattern.pack(pady=5, padx=15, fill="x")
        
        self.frm_btns = ctk.CTkFrame(self.frm_sidebar, fg_color="transparent")
        self.frm_btns.pack(pady=5, padx=15, fill="x")
        ctk.CTkButton(self.frm_btns, text="Select", width=60, command=lambda: self._action_pattern(False)).pack(side="left", padx=2, expand=True, fill="x")
        ctk.CTkButton(self.frm_btns, text="Keep", width=60, command=lambda: self._action_pattern(True)).pack(side="left", padx=2, expand=True, fill="x")
        
        # Quick Select
        self.frm_quick = ctk.CTkFrame(self.frm_sidebar, fg_color="transparent")
        self.frm_quick.pack(pady=5, padx=15, fill="x")
        ctk.CTkButton(self.frm_quick, text="All", width=50, command=lambda: self._select_all(True)).pack(side="left", padx=2, expand=True, fill="x")
        ctk.CTkButton(self.frm_quick, text="None", width=50, command=lambda: self._select_all(False)).pack(side="left", padx=2, expand=True, fill="x")
        ctk.CTkButton(self.frm_quick, text="Invert", width=50, command=self._invert_selection).pack(side="left", padx=2, expand=True, fill="x")
        
        # Keep Oldest/Newest
        self.frm_keep = ctk.CTkFrame(self.frm_sidebar, fg_color="transparent")
        self.frm_keep.pack(pady=5, padx=15, fill="x")
        ctk.CTkButton(self.frm_keep, text="Keep Oldest", width=80, command=self._select_keep_oldest).pack(side="left", padx=2, expand=True, fill="x")
        ctk.CTkButton(self.frm_keep, text="Keep Newest", width=80, command=self._select_keep_newest).pack(side="left", padx=2, expand=True, fill="x")

        # 4. Action
        self.lbl_stats = ctk.CTkLabel(self.frm_sidebar, text="Ready")
        self.lbl_stats.pack(side="bottom", pady=10)
        
        self.btn_delete = ctk.CTkButton(self.frm_sidebar, text="DELETE CHECKED", fg_color="red", state="disabled", command=self._delete_selected)
        self.btn_delete.pack(side="bottom", pady=10, padx=15, fill="x")
        
        # Right Panel
        self.frm_right = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.frm_right.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        self.scroll_results = ctk.CTkScrollableFrame(self.frm_right, label_text="Scan Results")
        self.scroll_results.pack(fill="both", expand=True)
        
        self.btn_load_more = ctk.CTkButton(self.frm_right, text="Load More", command=self._load_next_page)
        self.btn_load_more.pack_forget()

    def _select_folder(self):
        root = tk.Tk()
        root.withdraw()
        path = filedialog.askdirectory(initialdir=self.target_path)
        if path:
            self.target_path = path
            self.lbl_path.configure(text=path)

    def _start_scan_thread(self):
        if not self.target_path or not Path(self.target_path).exists():
            messagebox.showerror("Error", "Invalid path")
            return
            
        # Clear UI
        for widget in self.scroll_results.winfo_children():
            widget.destroy()
            
        self.ui_groups = []
        self.all_groups = []
        self.current_page = 0
        self.btn_load_more.pack_forget()
        
        self._set_tools_state("disabled")
        self.lbl_stats.configure(text="Scanning...")
        
        threading.Thread(target=self._scan_logic, daemon=True).start()

    def _set_tools_state(self, state):
        try:
            self.entry_pattern.configure(state=state)
            self.btn_delete.configure(state=state)
            
            for frm in [self.frm_btns, self.frm_quick, self.frm_keep]:
                for child in frm.winfo_children():
                    child.configure(state=state)
        except Exception:
            pass
            
    # _scan_logic follows...

    def _scan_logic(self):
        try:
            # Get Mode from Tab
            tab_name = self.tab_mode.get().lower() # "simple" or "smart"
            path = Path(self.target_path)
            
            criteria = {}
            if tab_name == "simple":
                criteria = {
                    'name': self.var_chk_name.get(),
                    'size': self.var_chk_size.get(),
                    'hash': self.var_chk_hash.get()
                }
            
            def status_update(msg):
                self.after(0, lambda: self.lbl_stats.configure(text=msg))
                
            groups = scan_worker(path, mode=tab_name, criteria=criteria, status_callback=status_update)
            self.all_groups = groups
            self.after(0, self._display_initial_results)

        except Exception as e:
            logger.error(f"Scan error: {e}")
            import traceback
            traceback.print_exc()
            self.after(0, lambda: self.lbl_stats.configure(text=f"Error: {e}"))

    def _display_initial_results(self):
        self.lbl_stats.configure(text=f"Found {len(self.all_groups)} groups.")
        self._set_tools_state("normal")
        if len(self.all_groups) > self.PAGE_SIZE:
             self.btn_load_more.pack(pady=5)
        self._load_next_page()

    # --- Actions (Delegate to Models) ---
    def _action_pattern(self, keep=False):
        pattern = self.entry_pattern.get().strip()
        if not pattern: return
        count = 0
        for grp in self.all_groups:
            count += grp.select_by_pattern(pattern, keep)
        self.lbl_stats.configure(text=f"{'Kept' if keep else 'Selected'} {count} changes.")
        self._refresh_visible_ui()

    def _select_all(self, state):
        for grp in self.all_groups:
            grp.select_all(state)
        self._refresh_visible_ui()

    def _invert_selection(self):
        for grp in self.all_groups:
            grp.invert_selection()
        self._refresh_visible_ui()

    def _select_keep_oldest(self):
        for grp in self.all_groups:
            grp.mark_all_except_oldest()
        self._refresh_visible_ui()

    def _select_keep_newest(self):
        for grp in self.all_groups:
            grp.mark_all_except_newest()
        self._refresh_visible_ui()

    def _refresh_visible_ui(self):
        # Update ONLY the currently rendered widgets to match Backend State
        for i, ui_data in enumerate(self.ui_groups):
            grp_backend = ui_data.get("backend_ref")
            if not grp_backend: continue

            # Update Checkboxes
            for item_data, item_backend in zip(ui_data["items"], grp_backend.items):
                 if item_data["var"].get() != item_backend.selected:
                     item_data["var"].set(item_backend.selected)
            
            self._update_group_status(i)

    def _load_next_page(self):
        start = self.current_page * self.PAGE_SIZE
        end = start + self.PAGE_SIZE
        subset = self.all_groups[start:end]
        
        if not subset:
            self.btn_load_more.pack_forget()
            return

        for grp in subset: # grp is FinderGroup
            group_index = len(self.ui_groups)
            group_items = []
            grp_var = ctk.BooleanVar(value=False) # Group master check
            
            for item in grp.items: # item is FinderItem
                var = ctk.BooleanVar(value=item.selected)
                
                # Trace UI -> Backend
                def on_change(*args, b_item=item, g_idx=group_index, v=var):
                     b_item.selected = v.get()
                     self._update_group_status(g_idx)

                var.trace_add("write", on_change)
                group_items.append({"path": item.path, "var": var, "mtime": item.mtime})
                
            self.ui_groups.append({
                "name": grp.name, 
                "backend_ref": grp,
                "items": group_items,
                "widgets_loaded": False,
                "frm_content": None,
                "chk_widgets": [],
                "grp_var": grp_var,
                "lbl_header": None,
                "btn_toggle": None
            })
            
            # --- Render Header ---
            frm_grp = ctk.CTkFrame(self.scroll_results, fg_color="gray25")
            frm_grp.pack(fill="x", pady=1, padx=5) # Reduced pady
            
            frm_header = ctk.CTkFrame(frm_grp, fg_color="transparent", height=28) # Fixed height for compactness
            frm_header.pack(fill="x", padx=2, pady=2) # Reduced padding
            
            # Components
            btn_toggle = ctk.CTkButton(frm_header, text="▶", width=24, height=20, fg_color="gray40", 
                                     font=("Arial", 10),
                                     command=lambda idx=group_index: self._toggle_group(idx))
            btn_toggle.pack(side="left", padx=(0, 2))
            self.ui_groups[group_index]["btn_toggle"] = btn_toggle

            chk_grp = ctk.CTkCheckBox(frm_header, text="", variable=grp_var, 
                                    width=20, height=20, checkbox_width=18, checkbox_height=18,
                                    command=lambda idx=group_index: self._toggle_entire_group(idx))
            chk_grp.pack(side="left", padx=(0, 5))

            if grp.badge:
                badge_color = "#3B8ED0" if grp.badge == "SEQ" else "#2CC985" if grp.badge == "VER" else "gray"
                ctk.CTkLabel(frm_header, text=grp.badge, fg_color=badge_color, text_color="white", corner_radius=4, 
                             height=18, font=("Arial", 10, "bold")).pack(side="left", padx=2)

            lbl_header = ctk.CTkLabel(frm_header, text=grp.name, font=("Arial", 12, "bold"))
            lbl_header.pack(side="left", padx=2)
            self.ui_groups[group_index]["lbl_header"] = lbl_header
            
            self._update_group_status(group_index) # Helper sets label text
            
            if grp.items:
                 p = grp.items[0].path
                 ctk.CTkButton(frm_header, text="Open", width=50, height=18, font=("Arial", 10),
                             fg_color="gray40", hover_color="gray50",
                             command=lambda path=p: self._open_folder(path)).pack(side="right", padx=2)

            self.ui_groups[group_index]["frm_content"] = ctk.CTkFrame(frm_grp, fg_color="transparent")
            
            if group_index % 10 == 0: self.update_idletasks()
        
        self.current_page += 1
        if (self.current_page * self.PAGE_SIZE) >= len(self.all_groups):
            self.btn_load_more.pack_forget()

    def _toggle_entire_group(self, idx):
        data = self.ui_groups[idx]
        grp = data["backend_ref"]
        target_state = data["grp_var"].get()
        grp.select_all(target_state) # Update Backend
        
        # Update UI Vars
        for item_data in data["items"]:
            item_data["var"].set(target_state)
        
        self._update_group_status(idx)

    def _update_group_status(self, idx):
        data = self.ui_groups[idx]
        grp = data.get("backend_ref")
        if not grp: return 

        selected_count = grp.get_selected_count()
        total = len(grp.items)
        
        new_text = f"{grp.clean_name} ({selected_count}/{total})"
        if data["lbl_header"]: data["lbl_header"].configure(text=new_text)

        # Sync Checkbox without trace loop
        is_all = (selected_count == total and total > 0)
        current_val = data["grp_var"].get()
        if current_val != is_all:
             data["grp_var"].set(is_all)
             
        # Trigger global stats update (could be throttled if slow, but simple math is fast)
        self.after(10, self._update_global_stats)

    def _toggle_group(self, idx):
        group_data = self.ui_groups[idx]
        frm_content = group_data["frm_content"]
        btn = group_data["btn_toggle"]
        
        if frm_content.winfo_ismapped():
            frm_content.pack_forget()
            btn.configure(text="▶")
        else:
            frm_content.pack(fill="x", padx=5, pady=2) # Reduced content padding
            btn.configure(text="▼")
            if not group_data["widgets_loaded"]:
                self._lazy_render_items(idx)

    def _lazy_render_items(self, idx):
        group_data = self.ui_groups[idx]
        frm_content = group_data["frm_content"]
        items = group_data["items"]
        
        MAX_DISPLAY = 20
        visible_items = items[:MAX_DISPLAY]
        
        for item in visible_items:
            f = item["path"]
            size_mb = 0
            try: size_mb = f.stat().st_size / (1024*1024)
            except: pass
            
            frm_item = ctk.CTkFrame(frm_content, fg_color="transparent", height=20) # Reduced Height
            frm_item.pack(fill="x", pady=0) # Removed pady
            
            display_name = f"{f.parent.name}/{f.name}"
            chk = ctk.CTkCheckBox(frm_item, text=display_name, variable=item["var"], font=("Arial", 11),
                                  width=20, height=20, checkbox_width=16, checkbox_height=16) # Smaller checkbox
            chk.pack(side="left", fill="x", expand=True) 
            group_data["chk_widgets"].append(chk)
            
            ctk.CTkLabel(frm_item, text=f"{size_mb:.2f} MB", text_color="gray", font=("Arial", 10)).pack(side="right")
        
        if len(items) > MAX_DISPLAY:
             ctk.CTkLabel(frm_content, text=f"... and {len(items) - MAX_DISPLAY} more (hidden)", 
                          text_color="gray", font=("Arial", 10, "italic")).pack(pady=2)
                          
        group_data["widgets_loaded"] = True

    def _open_folder(self, path):
        try:
            import subprocess
            subprocess.Popen(f'explorer /select,"{path}"')
        except: pass

    def _delete_selected(self):
        to_delete = []
        for grp in self.all_groups:
            for item in grp.items:
                if item.selected: to_delete.append(item.path)
                    
        if not to_delete:
            messagebox.showinfo("Info", "No files selected.")
            return
            
        if not messagebox.askyesno("Confirm", f"Trash {len(to_delete)} files?"):
            return
            
        success = 0
        errors = []
        for f in to_delete:
            try:
                if send2trash: send2trash(str(f))
                else: os.remove(f)
                success += 1
            except Exception as e:
                errors.append(str(e))
        
        self.lbl_stats.configure(text=f"Deleted {success} files.")
        messagebox.showinfo("Result", f"Deleted {success} files.")
        self._start_scan_thread()
