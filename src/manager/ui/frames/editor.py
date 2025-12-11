import customtkinter as ctk
import tkinter.messagebox
from tkinter import Menu
from ..dialogs.item_editor import ItemEditorDialog
from manager.helpers.icons import IconManager

class MenuEditorFrame(ctk.CTkFrame):
    def __init__(self, parent, config_manager, settings, on_save_registry=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.settings = settings
        self.on_save_registry = on_save_registry
        
        self.items = [] 
        self.filtered_items = []
        self.item_vars = {} # {id: BooleanVar}
        self.row_widgets = {} # {id: widget}
        self.view_mode = "Grouped" # Grouped | Flat
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1) 
        
        self._setup_toolbar()
        self._setup_filters()
        self._setup_list()
        
        # Initial Load
        self.load_items()

    def load_items(self):
        self.items = self.config_manager.load_config()
        self.refresh_list()

    def _setup_toolbar(self):
        toolbar = ctk.CTkFrame(self, height=40)
        toolbar.grid(row=0, column=0, sticky="ew", padx=20, pady=(10,0))
        
        # Left: Bulk Actions
        ctk.CTkButton(toolbar, text="Select All", width=70, fg_color="gray", command=self.select_all).pack(side="left", padx=5, pady=5)
        
        # Bulk Menu (Move/Toggle)
        self.btn_bulk = ctk.CTkButton(toolbar, text="Bulk Action ▼", width=100, command=self.show_bulk_menu)
        self.btn_bulk.pack(side="left", padx=5, pady=5)
        
        # Right: Core Actions
        ctk.CTkButton(toolbar, text="Save Changes", width=100, command=self.save_final).pack(side="right", padx=5, pady=5)
        ctk.CTkButton(toolbar, text="Auto Organize", width=100, fg_color="#F39C12", hover_color="#D68910", 
                    command=self.auto_organize).pack(side="right", padx=5, pady=5)
        ctk.CTkButton(toolbar, text="+ Add Item", fg_color="#2ECC71", hover_color="#27AE60", width=90,
                    command=self.open_add_dialog).pack(side="right", padx=10, pady=5)

    def _setup_filters(self):
        filter_frame = ctk.CTkFrame(self, height=40, fg_color="transparent")
        filter_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(5,0))
        
        # View Mode Toggle
        self.btn_view = ctk.CTkButton(filter_frame, text=f"View: {self.view_mode}", width=100, fg_color="gray", command=self.toggle_view)
        self.btn_view.pack(side="left", padx=5)

        ctk.CTkLabel(filter_frame, text="Filter:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(15, 5))
        
        # Categories (Only relevant in Flat view mostly, but keep for search)
        self.filter_cat_var = ctk.StringVar(value="All Categories")
        # Populate later based on settings
        
        self.entry_search = ctk.CTkEntry(filter_frame, placeholder_text="Search Name...", width=150)
        self.entry_search.pack(side="left", padx=5)
        self.entry_search.bind("<Return>", self.refresh_list)
        
        ctk.CTkButton(filter_frame, text="🔍", width=30, command=self.refresh_list).pack(side="left", padx=2)
        # Renamed to Clear to avoid confusion with 'Reset Settings'
        ctk.CTkButton(filter_frame, text="✖", width=30, fg_color="gray", command=self.reset_filters).pack(side="left", padx=5)

    def _setup_list(self):
        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="Menu Items")
        self.scroll_frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=5)
        self.scroll_frame.grid_columnconfigure(0, weight=1)

    def toggle_view(self):
        self.view_mode = "Flat" if self.view_mode == "Grouped" else "Grouped"
        self.btn_view.configure(text=f"View: {self.view_mode}")
        self.refresh_list()

    def reset_filters(self):
        self.entry_search.delete(0, "end")
        self.item_vars.clear() # Also clear selection? User might expect this.
        self.refresh_list()
        
    def show_bulk_menu(self):
        menu = Menu(self, tearoff=0)
        menu.add_command(label="Select All", command=self.select_all)
        menu.add_command(label="Deselect All", command=self.deselect_all)
        menu.add_separator()
        menu.add_command(label="Enable Selected", command=lambda: self.bulk_toggle(True, selected_only=True))
        menu.add_command(label="Disable Selected", command=lambda: self.bulk_toggle(False, selected_only=True))
        menu.add_separator()
        menu.add_command(label="Enable All (Except Beta)", command=lambda: self.bulk_toggle(True, beta_filter=True))
        menu.add_command(label="Disable All", command=lambda: self.bulk_toggle(False))
        menu.add_separator()
        
        # Move to Category Submenu
        move_menu = Menu(menu, tearoff=0)
        cats = sorted(self.settings.get("CATEGORY_COLORS", {}).keys())
        for cat in cats:
            move_menu.add_command(label=cat, command=lambda c=cat: self.bulk_move(c))
        
        menu.add_cascade(label="Move Selected to...", menu=move_menu)
        
        try:
            menu.tk_popup(self.btn_bulk.winfo_rootx(), self.btn_bulk.winfo_rooty() + self.btn_bulk.winfo_height())
        finally:
            menu.grab_release()

    def select_all(self):
        for v in self.item_vars.values(): v.set(True)

    def deselect_all(self):
        for v in self.item_vars.values(): v.set(False)

    def bulk_toggle(self, state, selected_only=False, beta_filter=False):
        changed = False
        target_items = self.filtered_items if self.filtered_items else self.items
        
        for item in target_items:
            # Check Selection
            if selected_only:
                var = self.item_vars.get(item['id'])
                if not var or not var.get():
                    continue
            
            # Check Beta
            if beta_filter:
                # Assuming 'Beta' is in name or status
                name = item.get('name', '').lower()
                status = item.get('status', '').lower() # Assuming 'status' field might be used
                if 'beta' in name or 'beta' in status:
                    # If enabling except beta, skip this
                    if state: continue 
                    
            if item.get('enabled', True) != state:
                item['enabled'] = state
                changed = True
                
        if changed:
            self.refresh_list()
            # self.save_final() # Optional: Auto-save? Better to let user click save.
            tkinter.messagebox.showinfo("Bulk Action", "Status updated. Click 'Save Changes' to apply.")

    def bulk_move(self, category):
        changed = False
        target_items = self.filtered_items if self.filtered_items else self.items
        
        for item in target_items:
            var = self.item_vars.get(item['id'])
            if var and var.get():
                if item.get('category') != category:
                    item['category'] = category
                    changed = True
                    
        if changed:
            self.recalculate_orders()
            self.refresh_list()
            tkinter.messagebox.showinfo("Bulk Move", f"Moved selected items to '{category}'.")
    
    # Removed duplicate select_all which was below

    def refresh_list(self, _=None):
        # Clear
        for widget in self.scroll_frame.winfo_children(): widget.destroy()
        self.item_vars.clear()
        self.row_widgets.clear()
        
        search = self.entry_search.get().lower()
        
        # Filter
        filtered = []
        for item in self.items:
            if search and search not in item.get('name', '').lower(): continue
            filtered.append(item)
            
        # --- AUTO ORDER RENDER ---
        # Sort key: (Category Index, Item Name) OR (Category Index, Current Order)
        # We want to respect existing order within category if possible, or name.
        # But the Requirement is "Use category list to determine first digits, rest is auto".
        
        order_list = self.settings.get("CATEGORY_ORDER", [])
        
        def sort_key(x):
            c = x.get('category', 'Other')
            try: c_idx = order_list.index(c)
            except: c_idx = 99
            
            # Secondary sort: existing order
            return (c_idx, int(x.get('order', 9999)))

        filtered.sort(key=sort_key)
        self.filtered_items = filtered
        
        if self.view_mode == "Grouped":
            self._render_grouped(filtered, order_list)
        else:
            self._render_flat(filtered)
            
    def _render_grouped(self, items, order_list):
        # We prefer to iterate through order_list to maintain category order
        # group items first
        groups = {cat: [] for cat in order_list}
        groups['Other'] = []
        
        for item in items:
            c = item.get('category', 'Other')
            if c in groups: groups[c].append(item)
            else: groups['Other'].append(item)
            
        for cat in order_list + ['Other']:
            group_items = groups.get(cat, [])
            if not group_items: continue
            
            # Header
            color = self.settings.get("CATEGORY_COLORS", {}).get(cat, "gray")
            header = ctk.CTkFrame(self.scroll_frame, height=30, fg_color="transparent")
            header.pack(fill="x", pady=(10, 2))
            
            # Show Priority Range?
            # Show Priority Range?
            try: idx = order_list.index(cat) 
            except: idx = 99
            # prio_text = f"[{ (idx+1)*1000 }s]" if idx != 99 else "[Last]"
            # ctk.CTkLabel(header, text=prio_text, text_color="gray", width=50).pack(side="left")
            
            ctk.CTkLabel(header, text=f"{cat}", font=ctk.CTkFont(size=14, weight="bold"), 
                       fg_color=color, corner_radius=6, text_color="white").pack(side="left")
            ctk.CTkLabel(header, text=f" ({len(group_items)}) items", text_color="gray").pack(side="left", padx=5)
            
            # Items
            for idx, item in enumerate(group_items):
                self._create_item_row(self.scroll_frame, item, idx, len(group_items), flat=False)

    def _render_flat(self, items):
        for idx, item in enumerate(items):
            self._create_item_row(self.scroll_frame, item, idx, len(items), flat=True)

    def _create_item_row(self, parent, item, index, total, flat):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=5, pady=2)
        self.row_widgets[item['id']] = row
        
        # [Select]
        chk_var = ctk.BooleanVar(value=False)
        self.item_vars[item['id']] = chk_var
        ctk.CTkCheckBox(row, text="", variable=chk_var, width=24).pack(side="left", padx=2)
        
        # [Enabled Toggle]
        # Use BooleanVar for robust state tracking
        enabled_var = ctk.BooleanVar(value=item.get('enabled', True))
        
        def on_toggle_switch():
            item['enabled'] = enabled_var.get()
            # print(f"Toggled {item['name']}: {item['enabled']}") # Debug
            
        switch = ctk.CTkSwitch(row, text="", width=40, height=20, variable=enabled_var, command=on_toggle_switch)
        switch.pack(side="left", padx=5)
        
        # [Icon]
        icon_path = item.get('icon', '')
        icon_img = IconManager.load_icon(icon_path)
        
        if icon_img:
            ctk.CTkLabel(row, text="", image=icon_img, width=30).pack(side="left", padx=2)
        else:
            ctk.CTkLabel(row, text="📄", width=30).pack(side="left", padx=2)
        
        # [Name]
        name_frame = ctk.CTkFrame(row, fg_color="transparent")
        name_frame.pack(side="left", fill="x", expand=True)
        
        name_txt = item.get('name', 'Unnamed')
        if flat:
             cat = item.get('category', 'Custom')
             color = self.settings.get("CATEGORY_COLORS", {}).get(cat, "gray")
             ctk.CTkLabel(name_frame, text="█", text_color=color).pack(side="left", padx=2)
             
        ctk.CTkLabel(name_frame, text=name_txt, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        
         # [Hotkey]
        hotkey = item.get('hotkey', '')
        if hotkey:
             ctk.CTkLabel(row, text=f"{hotkey}", text_color="orange", width=60).pack(side="left", padx=5)

        # [Order Control]
        # Up/Down Arrows
        order_frame = ctk.CTkFrame(row, fg_color="transparent")
        order_frame.pack(side="left", padx=5)
        
        btn_up = ctk.CTkButton(order_frame, text="▲", width=20, height=20, fg_color="transparent", text_color="gray", hover_color="#333",
                             command=lambda i=item: self.move_item(i, -1))
        btn_up.pack(side="left", padx=0)
        
        btn_down = ctk.CTkButton(order_frame, text="▼", width=20, height=20, fg_color="transparent", text_color="gray", hover_color="#333",
                               command=lambda i=item: self.move_item(i, 1))
        btn_down.pack(side="left", padx=0)

        # Removed raw number display as requested

        # [Edit]
        ctk.CTkButton(row, text="Edit", width=50, height=24, 
                    command=lambda i=item: self.open_edit_dialog(i)).pack(side="left", padx=5)
                    
        # [Location] (Subtitle)
        sub = item.get('submenu', 'ContextUp')
        ctk.CTkLabel(row, text=sub, text_color="gray", width=80).pack(side="right", padx=5)

    def recalculate_orders(self):
        """Force apply the category priority logic to all items.
           Format: (CategoryIndex + 1) * 100 + (ItemIndex + 1)"""
        order_list = self.settings.get("CATEGORY_ORDER", [])
        
        # Group first
        groups = {cat: [] for cat in order_list}
        groups['Other'] = []
        
        # Sort items based on current list order or temporary order to maintain stability
        # But actually, self.filtered_items reflects what the user sees. 
        # If we are just recalculating based on arbitrary 'items', we might lose visual order.
        # Ideally we respect the current sort of 'items' if it's already sorted, or 'filtered_items' if visible.
        # But 'items' is the source of truth.
        
        # Let's rely on self.items being relatively sorted or stable.
        # To be safe, we sort self.items by their *current* order first to ensure stability before re-indexing.
        self.items.sort(key=lambda x: int(x.get('order', 9999)))

        for item in self.items:
            c = item.get('category', 'Other')
            if c in groups: groups[c].append(item)
            else: groups['Other'].append(item)
            
        # Assign IDs
        for cat_idx, cat in enumerate(order_list):
            base_id = (cat_idx + 1) * 100
            for item_idx, item in enumerate(groups[cat]):
                # +1 so it starts at .01
                item['order'] = base_id + (item_idx + 1)
                
        # Handle 'Other' - 9000s
        for idx, item in enumerate(groups['Other']):
            item['order'] = 9000 + (idx + 1)

    def move_item(self, item, direction):
        """Move item up (-1) or down (+1) within its category group using Smart Swap."""
        
        # 1. Find neighbors in *visible* filtered list
        try:
            current_idx = self.filtered_items.index(item)
        except ValueError:
            return # Should not happen

        target_idx = current_idx + direction
        
        # 2. Check bounds
        if not (0 <= target_idx < len(self.filtered_items)):
            return

        neighbor = self.filtered_items[target_idx]
        
        # 3. Restrict to same category
        if item.get('category', 'Other') != neighbor.get('category', 'Other'):
            # Cannot jump categories in this logic
            return

        # 4. Swap Logic
        # A. Update Data Model (filtered list) matches visual
        self.filtered_items[current_idx], self.filtered_items[target_idx] = self.filtered_items[target_idx], self.filtered_items[current_idx]
        
        # B. Update 'order' keys to persist this change
        # We swap the order values so that next full-sort respects this position
        item['order'], neighbor['order'] = neighbor['order'], item['order']

        # C. Update UI (Visual Swap) without rebuild
        w1 = self.row_widgets.get(item['id'])
        w2 = self.row_widgets.get(neighbor['id'])
        
        if w1 and w2:
            if direction > 0: # Down: w1 should be after w2
                w1.pack(after=w2)
            else: # Up: w1 should be before w2
                w1.pack(before=w2)
        
        # D. Skip full refresh!
        # Status update? Maybe subtle.
        pass


    def auto_organize(self):
        self.recalculate_orders()
        self.refresh_list()
        tkinter.messagebox.showinfo("Organize", "Items re-ordered (Hundreds for Category, Units for Items).")
        
    def open_add_dialog(self):
        ItemEditorDialog(self.winfo_toplevel(), on_save=self.add_item)

    def open_edit_dialog(self, item):
        ItemEditorDialog(self.winfo_toplevel(), item_data=item, 
                        on_save=lambda new_data: self.update_item(item, new_data), 
                        on_delete=lambda: self.delete_item(item))

    def add_item(self, new_item):
        self.items.append(new_item)
        self.recalculate_orders() # Auto calc on add
        self.refresh_list()

    def update_item(self, old_item, new_data):
        for k, v in new_data.items(): old_item[k] = v
        self.recalculate_orders() # Category might have changed
        self.refresh_list()
        
    def delete_item(self, item):
        if item in self.items: self.items.remove(item)
        self.refresh_list()

    def save_final(self):
        # Ensure order is fresh
        self.recalculate_orders()
        
        # save_config now returns (success, message) tuple
        result = self.config_manager.save_config(self.items, self.settings)
        
        if isinstance(result, tuple):
            success, message = result
        else:
            # Backward compatibility
            success, message = result, "Configuration saved."
        
        if success:
            # Trigger Registry Update if available
            if self.on_save_registry:
                self.on_save_registry()
            else:
                tkinter.messagebox.showinfo("Success", message)
        else:
            tkinter.messagebox.showerror("Error", message)

