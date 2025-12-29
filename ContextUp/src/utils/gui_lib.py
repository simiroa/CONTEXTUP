import customtkinter as ctk
from pathlib import Path
import sys

from core.settings import load_settings

# Standard Theme Settings
THEME_COLOR = "blue"
# Theme Constants (Premium Dark)
THEME_BG = "#050505"        # Deep Black Background
THEME_CARD = "#121212"      # Slightly Brighter Cards (for contrast)
THEME_BORDER = "#1a1a1a"    # Visible Borders
THEME_ACCENT = "#3498db"    # Default Blue
THEME_TEXT_MAIN = "#E0E0E0"
THEME_TEXT_DIM = "#666666"

TRANS_KEY = "#000001" # Transparency Key

def setup_theme():
    settings = load_settings()
    mode = settings.get("THEME", "System")
    if mode.lower() == "light": ctk.set_appearance_mode("Light")
    elif mode.lower() == "dark": ctk.set_appearance_mode("Dark")
    else: ctk.set_appearance_mode("System")
    
    ctk.set_default_color_theme(THEME_COLOR)

class BaseWindow(ctk.CTk):
    """
    Base window class for all ContextUp tools.
    Provides standard premium styling, geometry, custom title bar, and icon handling.
    """
    def __init__(self, title="ContextUp Tool", width=700, height=750, scrollable=False, icon_name=None):
        super().__init__()
        setup_theme()
        
        self.tool_title = title
        
        # Borderless Window Setup
        self.overrideredirect(True)
        self.wm_attributes("-transparentcolor", TRANS_KEY)
        self.configure(fg_color=TRANS_KEY)
        
        self._offsetx = 0
        self._offsety = 0
        
        # Main Outer Container (Rounded Border)
        self.outer_frame = ctk.CTkFrame(self, fg_color=THEME_BG, corner_radius=16, 
                                      border_width=1, border_color=THEME_BORDER)
        self.outer_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Custom Title Bar
        self.title_bar = ctk.CTkFrame(self.outer_frame, fg_color="transparent", height=40, corner_radius=0)
        self.title_bar.pack(fill="x", side="top", padx=10, pady=(5, 0))
        
        # Icon/Title
        self.title_label = ctk.CTkLabel(self.title_bar, text=f"✨ {title}", font=("Segoe UI", 12, "bold"), text_color=THEME_TEXT_MAIN)
        self.title_label.pack(side="left", padx=5)
        
        # Window Controls
        ctrl_frame = ctk.CTkFrame(self.title_bar, fg_color="transparent")
        ctrl_frame.pack(side="right")
        
        self.btn_min = ctk.CTkButton(ctrl_frame, text="─", width=32, height=28, 
                                   fg_color="transparent", hover_color="#222", 
                                   command=self.minimize_window, font=("Arial", 11), corner_radius=6)
        self.btn_min.pack(side="left", padx=2)
        
        self.btn_close = ctk.CTkButton(ctrl_frame, text="✕", width=32, height=28, 
                                     fg_color="transparent", hover_color="#922B21", 
                                     command=self.on_closing, font=("Arial", 11), corner_radius=6)
        self.btn_close.pack(side="left", padx=2)
        
        # Drag Logic
        for w in [self.title_bar, self.title_label, ctrl_frame]:
            w.bind("<Button-1>", self.start_move)
            w.bind("<B1-Motion>", self.do_move)

        # Set geometry logic handling
        self.geometry(f"{width}x{height}")
        
        # Taskbar Logic
        self._setup_taskbar_icon(icon_name)
        
        # Content Area
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1) # Outer frame handled by pack
        
        # We need to structure internal content. 
        # BaseWindow typically expects self.main_frame to be ready for children.
        
        container_args = {"fg_color": "transparent"}
        if scrollable:
            self.main_frame = ctk.CTkScrollableFrame(self.outer_frame, **container_args)
        else:
            self.main_frame = ctk.CTkFrame(self.outer_frame, **container_args)
            
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    def _setup_taskbar_icon(self, icon_name):
        # Set AppUserModelID
        try:
            import ctypes
            myappid = 'hg.contextup.tool.2.0' 
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except: pass

        # Icon loading
        try:
            assets_dir = Path(__file__).parent.parent.parent / "assets"
            icons_dir = assets_dir / "icons"
            icon_path = None
            if icon_name:
                feature_icon = icons_dir / f"icon_{icon_name}.ico"
                if feature_icon.exists(): icon_path = feature_icon
            
            if not icon_path:
                main_icon = icons_dir / "ContextUp.ico"
                if main_icon.exists(): icon_path = main_icon
            
            if icon_path:
                self.iconbitmap(icon_path)
        except: pass

    # Window Management Methods
    def start_move(self, event):
        self._offsetx = event.x
        self._offsety = event.y

    def do_move(self, event):
        x = self.winfo_x() + event.x - self._offsetx
        y = self.winfo_y() + event.y - self._offsety
        self.geometry(f"+{x}+{y}")

    def minimize_window(self):
        self.update_idletasks()
        self.withdraw()
        self.after(10, self.iconify)
        self.bind("<Map>", lambda e: self.deiconify())

    def on_closing(self):
        self.destroy() # Defaults, can be overridden

    def adjust_window_size(self):
        """Auto-adjust window height to fit content."""
        self.update_idletasks()
        width = 600
        height = self.main_frame.winfo_reqheight() + 80 
        if height < 400: height = 400
        self.geometry(f"{width}x{height}")

    def add_header(self, text, font_size=18):
        """Adds a standard header label."""
        label = ctk.CTkLabel(self.main_frame, text=text, text_color=THEME_TEXT_MAIN, 
                           font=ctk.CTkFont(size=font_size, weight="bold"))
        label.pack(anchor="w", padx=10, pady=(10, 15))
        return label

    def add_section(self, title):
        """Adds a section title."""
        label = ctk.CTkLabel(self.main_frame, text=title, text_color=THEME_ACCENT,
                           font=ctk.CTkFont(size=13, weight="bold"))
        label.pack(anchor="w", padx=10, pady=(10, 5))
        return label

    def create_card_frame(self, parent=None):
        """Creates a standardized card frame."""
        if parent is None: parent = self.main_frame
        return ctk.CTkFrame(parent, fg_color=THEME_CARD, corner_radius=12, 
                          border_width=1, border_color=THEME_BORDER)

class FileListFrame(ctk.CTkScrollableFrame):
    """
    Standard scrollable list for displaying selected files.
    """
    def __init__(self, master, files, height=150):
        super().__init__(master, height=height, fg_color="transparent") # Transparent background
        self.files = files
        self.populate()

    def populate(self):
        for widget in self.winfo_children():
            widget.destroy()
            
        for f in self.files:
            row = ctk.CTkFrame(self, fg_color=THEME_CARD, corner_radius=6)
            row.pack(fill="x", pady=2)
            
            # Icon based on extension
            icon = "📄"
            if f.suffix.lower() in ['.mp4', '.mov', '.avi', '.mkv']: icon = "🎥"
            elif f.suffix.lower() in ['.mp3', '.wav', '.flac']: icon = "🎵"
            elif f.suffix.lower() in ['.jpg', '.png', '.exr']: icon = "🖼️"
            
            ctk.CTkLabel(row, text=icon, width=30, text_color=THEME_TEXT_DIM).pack(side="left")
            ctk.CTkLabel(row, text=f.name, anchor="w", text_color=THEME_TEXT_MAIN).pack(side="left", fill="x", expand=True)
            
            size_str = self.format_size(f.stat().st_size)
            ctk.CTkLabel(row, text=size_str, text_color=THEME_TEXT_DIM, width=80).pack(side="right")

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
        
        # Premium styling for Dialog
        self.overrideredirect(True)
        self.wm_attributes("-transparentcolor", TRANS_KEY)
        self.configure(fg_color=TRANS_KEY)
        
        # Center on screen
        self.update_idletasks()
        width = 400
        height = 180
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{int(x)}+{int(y)}")
        
        # Frame
        self.outer_frame = ctk.CTkFrame(self, fg_color=THEME_BG, corner_radius=16, 
                                      border_width=1, border_color=THEME_ACCENT)
        self.outer_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        self.result = None
        
        # Header
        ctk.CTkLabel(self.outer_frame, text=title, font=("Segoe UI", 12, "bold"), text_color=THEME_TEXT_MAIN).pack(pady=(15, 5))
        
        ctk.CTkLabel(self.outer_frame, text=text, font=("Segoe UI", 11), text_color=THEME_TEXT_MAIN).pack(anchor="w", padx=20, pady=(5, 5))
        
        self.entry = ctk.CTkEntry(self.outer_frame, fg_color=THEME_CARD, border_color=THEME_BORDER, text_color=THEME_TEXT_MAIN)
        self.entry.pack(fill="x", padx=20, pady=(0, 15))
        if initial_value:
            self.entry.insert(0, initial_value)
        self.entry.bind("<Return>", self.on_ok)
        self.entry.focus_force()
        
        btn_frame = ctk.CTkFrame(self.outer_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkButton(btn_frame, text="OK", width=80, height=32, command=self.on_ok, 
                    fg_color=THEME_ACCENT).pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="Cancel", width=80, height=32, command=self.on_cancel, 
                    fg_color="transparent", border_width=1, border_color=THEME_BORDER, hover_color="#333").pack(side="right", padx=5)
        
        self.wait_visibility()
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
        if not ctk._default_root_arg:
            root = ctk.CTk()
            root.withdraw() # Hide it
        else:
            root = None
    except:
        root = ctk.CTk()
        root.withdraw()

    app = ModernInputDialog(title, text, initial_value)
    result = app.result
    
    if root:
        root.destroy()
        
    return result

class MissingDependencyWindow(BaseWindow):
    """
    A specific window to show when a tool cannot run due to missing dependencies.
    """
    def __init__(self, tool_name, missing_items):
        super().__init__(title=f"Missing Requirements - {tool_name}", width=500, height=400)
        
        # Icon (Error/Warning)
        self.lbl_icon = ctk.CTkLabel(self.main_frame, text="⚠️", font=("Segoe UI Emoji", 64))
        self.lbl_icon.pack(pady=(20, 10))
        
        self.add_header(f"{tool_name} Unavailable", font_size=24)
        
        msg = f"This feature requires external tools that are not currently installed or connected."
        ctk.CTkLabel(self.main_frame, text=msg, wraplength=400, justify="center", text_color=THEME_TEXT_DIM).pack(pady=(0, 20))
        
        # Missing List using Card style
        bg_frame = self.create_card_frame(self.main_frame)
        bg_frame.pack(fill="x", padx=40, pady=10)
        
        ctk.CTkLabel(bg_frame, text="Missing Components:", font=("Segoe UI", 12, "bold"), text_color=THEME_TEXT_MAIN).pack(anchor="w", padx=15, pady=(10,0))
        
        for item in missing_items:
            ctk.CTkLabel(bg_frame, text=f"• {item}", anchor="w", text_color="#ff5555").pack(anchor="w", padx=25, pady=2)
            
        ctk.CTkLabel(bg_frame, text="").pack(pady=5) # Spacer
        
        # Action Arguments
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=20)
        
        # Open Manager Button
        ctk.CTkButton(btn_frame, text="Open Manager", command=self.open_manager, fg_color="#2cc985", hover_color="#22a36b").pack(side="top", pady=5)
        
        # Close
        ctk.CTkButton(btn_frame, text="Close", command=self.destroy, fg_color="transparent", border_width=1, border_color=THEME_BORDER).pack(side="top", pady=5)
        
    def open_manager(self):
        """Attempts to launch the Manager."""
        try:
            # We assume manage.py is in the root
            root = Path(__file__).resolve().parents[3]
            manage_script = root / "manage.py"
            if manage_script.exists():
                import subprocess
                subprocess.Popen([sys.executable, str(manage_script)])
                self.destroy()
        except Exception as e:
            print(f"Failed to open manager: {e}")
