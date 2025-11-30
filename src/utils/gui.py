import tkinter as tk
from tkinter import simpledialog, ttk

def ask_selection(title: str, prompt: str, options: list):
    """
    Shows a dialog with a combobox to select an option.
    Returns the selected string or None if cancelled.
    """
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    
    dialog = tk.Toplevel(root)
    dialog.title(title)
    dialog.geometry("300x150")
    dialog.resizable(False, False)
    
    # Center the dialog
    root.update_idletasks()
    width = dialog.winfo_width()
    height = dialog.winfo_height()
    x = (dialog.winfo_screenwidth() // 2) - (width // 2)
    y = (dialog.winfo_screenheight() // 2) - (height // 2)
    dialog.geometry(f"+{x}+{y}")
    
    dialog.attributes("-topmost", True)
    dialog.focus_force()
    
    tk.Label(dialog, text=prompt, pady=10).pack()
    
    selection = tk.StringVar()
    if options:
        selection.set(options[0])
        
    combo = ttk.Combobox(dialog, textvariable=selection, values=options, state="readonly")
    combo.pack(pady=5, padx=20, fill=tk.X)
    combo.focus_set()
    
    result = None
    
    def on_ok():
        nonlocal result
        result = selection.get()
        dialog.destroy()
        
    def on_cancel():
        dialog.destroy()
        
    btn_frame = tk.Frame(dialog)
    btn_frame.pack(pady=20)
    
    tk.Button(btn_frame, text="OK", width=10, command=on_ok).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="Cancel", width=10, command=on_cancel).pack(side=tk.LEFT, padx=5)
    
    dialog.protocol("WM_DELETE_WINDOW", on_cancel)
    dialog.bind('<Return>', lambda e: on_ok())
    dialog.bind('<Escape>', lambda e: on_cancel())
    
    root.wait_window(dialog)
    root.destroy()
    return result
