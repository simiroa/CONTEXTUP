"""
My Info Module.
Quickly copy personal info from config.
"""
import json
import pyperclip
from pathlib import Path
from pystray import MenuItem as item, Menu as menu
from .base import TrayModule

class MyInfo(TrayModule):
    def __init__(self, agent):
        super().__init__(agent)
        self.name = "My Info"
        self.info_data = {}
        self.load_data()

    def load_data(self):
        # Load from my_info.json in config folder
        config_path = Path(__file__).parent.parent.parent.parent / "config" / "my_info.json"
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.info_data = json.load(f)
            except Exception as e:
                print(f"Failed to load my_info.json: {e}")
        else:
            # Create default
            self.info_data = {
                "Email": "user@example.com",
                "IP": "127.0.0.1",
                "Phone": "010-0000-0000"
            }
            try:
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(self.info_data, f, indent=4)
            except: pass

    def copy_info(self, key, value):
        pyperclip.copy(value)
        self.agent.notify("My Info", f"Copied {key}")

    def get_menu_items(self):
        if not self.info_data:
            return [item("My Info (Empty)", lambda: None)]
            
        # Create submenu items
        sub_items = []
        for k, v in self.info_data.items():
            sub_items.append(item(f"{k}: {v}", lambda _, v=v, k=k: self.copy_info(k, v)))
            
        return [item("My Info", menu(*sub_items))]

# Standalone function for context menu integration
def show_my_info_menu():
    """Show My Info selection menu and copy selected value"""
    import tkinter as tk
    from tkinter import messagebox
    
    # Load data
    config_path = Path(__file__).parent.parent.parent.parent / "config" / "my_info.json"
    info_data = {}
    
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                info_data = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load my_info.json: {e}")
            return
    else:
        # Create default
        info_data = {
            "Email": "user@example.com",
            "IP": "127.0.0.1",
            "Phone": "010-0000-0000"
        }
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(info_data, f, indent=4, ensure_ascii=False)
        except: pass
    
    if not info_data:
        messagebox.showinfo("My Info", "No info configured. Edit config/my_info.json")
        return
    
    # Create selection window
    root = tk.Tk()
    root.withdraw()
    root.title("Copy My Info")
    
    # Create dialog
    dialog = tk.Toplevel(root)
    dialog.title("Copy My Info")
    dialog.geometry("300x200")
    dialog.resizable(False, False)
    
    tk.Label(dialog, text="Select info to copy:", font=("Arial", 11, "bold")).pack(pady=10)
    
    def copy_and_close(key, value):
        pyperclip.copy(value)
        messagebox.showinfo("Copied", f"Copied {key}: {value}")
        dialog.destroy()
        root.destroy()
    
    # Add buttons for each info item
    for key, value in info_data.items():
        btn = tk.Button(
            dialog, 
            text=f"{key}: {value}",
            command=lambda k=key, v=value: copy_and_close(k, v),
            width=30,
            height=2
        )
        btn.pack(pady=5)
    
    # Center dialog
    dialog.update_idletasks()
    x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
    y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
    dialog.geometry(f"+{x}+{y}")
    
    dialog.mainloop()
