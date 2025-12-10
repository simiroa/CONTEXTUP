"""
Copy My Info - Personal Information Manager
Allows users to store and quickly copy personal information snippets.
"""
import sys
import json
from pathlib import Path
import customtkinter as ctk
from tkinter import messagebox
import pyperclip

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.append(str(src_dir))

from utils.gui_lib import BaseWindow

class CopyMyInfoGUI(BaseWindow):
    def __init__(self):
        super().__init__(title="Copy My Info", width=500, height=600)
        
        self.config_path = src_dir.parent / "config" / "copy_my_info.json"
        self.items = []
        
        self.load_config()
        self.create_widgets()
        
    def load_config(self):
        """Load saved information items from config file."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.items = data.get('items', [])
            except Exception as e:
                print(f"Error loading config: {e}")
                self.items = []
        
        # Default items if empty
        if not self.items:
            self.items = [
                {"label": "Email", "content": "user@example.com"},
                {"label": "IP", "content": "127.0.0.1"},
                {"label": "Phone", "content": "010-0000-0000"}
            ]
            self.save_config()
    
    def save_config(self):
        """Save information items to config file."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump({"items": self.items}, f, indent=2, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config: {e}")
    
    def create_widgets(self):
        """Create the main GUI widgets."""
        # Header
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkLabel(header_frame, text="Select info to copy:", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        
        ctk.CTkButton(header_frame, text="+ Add New", width=100, 
                     fg_color="#27AE60", hover_color="#2ECC71",
                     command=self.add_new_item).pack(side="right", padx=5)
        
        # Scrollable frame for items
        self.items_frame = ctk.CTkScrollableFrame(self.main_frame)
        self.items_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.refresh_items()
        
        # Bottom buttons
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=(10, 0))
        
        ctk.CTkButton(btn_frame, text="Close", width=100,
                     fg_color="transparent", border_width=1,
                     command=self.destroy).pack(side="right", padx=5)
    
    def refresh_items(self):
        """Refresh the display of all items."""
        # Clear existing widgets
        for widget in self.items_frame.winfo_children():
            widget.destroy()
        
        # Create item cards
        for idx, item in enumerate(self.items):
            self.create_item_card(idx, item)
    
    def create_item_card(self, idx, item):
        """Create a card for a single information item."""
        card = ctk.CTkFrame(self.items_frame, fg_color=("gray90", "gray20"), 
                           corner_radius=8)
        card.pack(fill="x", pady=5, padx=5)
        
        # Content area (clickable to copy)
        content_frame = ctk.CTkFrame(card, fg_color="transparent")
        content_frame.pack(fill="x", padx=15, pady=15)
        
        # Label
        label_entry = ctk.CTkEntry(content_frame, 
                                   placeholder_text="Label (e.g., Email)",
                                   font=ctk.CTkFont(size=12, weight="bold"))
        label_entry.pack(fill="x", pady=(0, 5))
        label_entry.insert(0, item.get('label', ''))
        label_entry.bind('<FocusOut>', lambda e, i=idx: self.update_item(i))
        
        # Content
        content_entry = ctk.CTkEntry(content_frame,
                                     placeholder_text="Content to copy")
        content_entry.pack(fill="x", pady=(0, 10))
        content_entry.insert(0, item.get('content', ''))
        content_entry.bind('<FocusOut>', lambda e, i=idx: self.update_item(i))
        
        # Store references for later retrieval
        label_entry._item_idx = idx
        label_entry._field = 'label'
        content_entry._item_idx = idx
        content_entry._field = 'content'
        
        # Buttons
        btn_row = ctk.CTkFrame(content_frame, fg_color="transparent")
        btn_row.pack(fill="x")
        
        ctk.CTkButton(btn_row, text="📋 Copy", width=100,
                     fg_color="#3498DB", hover_color="#5DADE2",
                     command=lambda c=item.get('content', ''): self.copy_to_clipboard(c)
                     ).pack(side="left", padx=(0, 5))
        
        ctk.CTkButton(btn_row, text="🗑️ Delete", width=100,
                     fg_color="#C0392B", hover_color="#E74C3C",
                     command=lambda i=idx: self.delete_item(i)
                     ).pack(side="right")
    
    def update_item(self, idx):
        """Update an item when its entry loses focus."""
        # Find the entry widgets for this item
        for widget in self.items_frame.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkFrame):
                        for entry in child.winfo_children():
                            if isinstance(entry, ctk.CTkEntry) and hasattr(entry, '_item_idx'):
                                if entry._item_idx == idx:
                                    field = entry._field
                                    value = entry.get()
                                    self.items[idx][field] = value
        
        self.save_config()
    
    def add_new_item(self):
        """Add a new information item."""
        new_item = {"label": "New Item", "content": ""}
        self.items.append(new_item)
        self.save_config()
        self.refresh_items()
    
    def delete_item(self, idx):
        """Delete an information item."""
        if messagebox.askyesno("Confirm Delete", 
                              f"Delete '{self.items[idx]['label']}'?"):
            self.items.pop(idx)
            self.save_config()
            self.refresh_items()
    
    def copy_to_clipboard(self, content):
        """Copy content to clipboard."""
        try:
            pyperclip.copy(content)
            # Show brief feedback
            self.show_copy_feedback()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy: {e}")
    
    def show_copy_feedback(self):
        """Show visual feedback that content was copied."""
        # Create temporary label
        feedback = ctk.CTkLabel(self.main_frame, text="✓ Copied to clipboard!",
                               font=ctk.CTkFont(size=12),
                               text_color="#27AE60")
        feedback.place(relx=0.5, rely=0.95, anchor="center")
        
        # Remove after 1.5 seconds
        self.after(1500, feedback.destroy)

if __name__ == "__main__":
    app = CopyMyInfoGUI()
    app.mainloop()
