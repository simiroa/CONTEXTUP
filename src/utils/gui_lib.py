import customtkinter as ctk
from pathlib import Path
import sys

from core.settings import load_settings

# Standard Theme Settings
THEME_COLOR = "blue"

def setup_theme():
    settings = load_settings()
    mode = settings.get("THEME", "System")
    # Map 'light'/'dark' to ctk values if needed, though ctk supports them directly usually
    # Capitalize just in case (Dark, Light, System)
    if mode.lower() == "light": ctk.set_appearance_mode("Light")
    elif mode.lower() == "dark": ctk.set_appearance_mode("Dark")
    else: ctk.set_appearance_mode("System")
    
    ctk.set_default_color_theme(THEME_COLOR)

class BaseWindow(ctk.CTk):
    """
    Base window class for all ContextUp tools.
    Provides standard styling, geometry, and icon handling.
    """
    def __init__(self, title="ContextUp Tool", width=700, height=750):
        super().__init__()
        setup_theme()
        self.title(title)
        self.geometry(f"{width}x{height}")
        
        # Set AppUserModelID for Windows Taskbar Icon
        try:
            import ctypes
            myappid = 'hg.contextup.tool.2.0' # arbitrary string
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except:
            pass

        # Set icon if available
        try:
            # Priority: assets/icons/icon_context_up.ico -> assets/icon.ico
            assets_dir = Path(__file__).parent.parent.parent / "assets"
            main_icon = assets_dir / "icons" / "icon_context_up.ico"
            legacy_icon = assets_dir / "icon.ico"
            
            if main_icon.exists():
                self.iconbitmap(main_icon)
            elif legacy_icon.exists():
                self.iconbitmap(legacy_icon)
        except:
            pass
            
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Main container with standard padding
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_columnconfigure(0, weight=1)

    def add_header(self, text):
        """Adds a standard header label."""
        label = ctk.CTkLabel(self.main_frame, text=text, font=ctk.CTkFont(size=20, weight="bold"))
        label.pack(anchor="w", padx=20, pady=(10, 20))
        return label

    def add_section(self, title):
        """Adds a section title."""
        label = ctk.CTkLabel(self.main_frame, text=title, font=ctk.CTkFont(size=14, weight="bold"))
        label.pack(anchor="w", padx=20, pady=(10, 5))
        return label

class FileListFrame(ctk.CTkScrollableFrame):
    """
    Standard scrollable list for displaying selected files.
    """
    def __init__(self, master, files, height=150):
        super().__init__(master, height=height)
        self.files = files
        self.populate()

    def populate(self):
        for widget in self.winfo_children():
            widget.destroy()
            
        for f in self.files:
            row = ctk.CTkFrame(self, fg_color="transparent")
            row.pack(fill="x", pady=2)
            
            # Icon based on extension
            icon = "📄"
            if f.suffix.lower() in ['.mp4', '.mov', '.avi', '.mkv']: icon = "🎥"
            elif f.suffix.lower() in ['.mp3', '.wav', '.flac']: icon = "🎵"
            elif f.suffix.lower() in ['.jpg', '.png', '.exr']: icon = "🖼️"
            
            ctk.CTkLabel(row, text=icon, width=30).pack(side="left")
            ctk.CTkLabel(row, text=f.name, anchor="w").pack(side="left", fill="x", expand=True)
            
            size_str = self.format_size(f.stat().st_size)
            ctk.CTkLabel(row, text=size_str, text_color="gray", width=80).pack(side="right")

    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024: return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

class ModernInputDialog(ctk.CTkToplevel):
    """
    A modern replacement for simpledialog.askstring using CustomTkinter.
    """
    def __init__(self, title="Input", text="Enter value:", initial_value=""):
        super().__init__()
        setup_theme()
        self.title(title)
        self.geometry("400x200")
        self.resizable(False, False)
        
        # Center on screen
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"+{x}+{y}")
        
        self.result = None
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(self.main_frame, text=text, font=ctk.CTkFont(size=14)).pack(anchor="w", pady=(10, 5))
        
        self.entry = ctk.CTkEntry(self.main_frame)
        self.entry.pack(fill="x", pady=(5, 20))
        if initial_value:
            self.entry.insert(0, initial_value)
        self.entry.bind("<Return>", self.on_ok)
        self.entry.focus_force()
        
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        ctk.CTkButton(btn_frame, text="OK", width=100, command=self.on_ok).pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="Cancel", width=100, fg_color="transparent", border_width=1, border_color="gray", command=self.on_cancel).pack(side="right", padx=5)
        
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.transient(self.master)
        self.grab_set()
        self.wait_window()
        
    def on_ok(self, event=None):
        self.result = self.entry.get()
        self.destroy()
        
    def on_cancel(self):
        self.result = None
        self.destroy()

def ask_string_modern(title, text, initial_value=""):
    # Check if a root window exists
    try:
        # This is a hacky way to check if a root exists in CustomTkinter/Tkinter
        # If no root exists, CTkToplevel will create a default Tk root which is ugly.
        # We want to create a hidden CTk root instead.
        if not ctk._default_root_arg:
            root = ctk.CTk()
            root.withdraw() # Hide it
        else:
            root = None
    except:
        root = ctk.CTk()
        root.withdraw()

    app = ModernInputDialog(title, text, initial_value)
    
    # If we created a temporary root, we need to destroy it after the dialog closes
    # But app.wait_window() blocks.
    # So we can destroy root after app.result is set?
    # ModernInputDialog calls destroy() on itself.
    
    result = app.result
    
    if root:
        root.destroy()
        
    return result
