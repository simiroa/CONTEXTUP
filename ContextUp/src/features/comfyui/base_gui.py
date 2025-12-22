import customtkinter as ctk
from tkinter import messagebox
import atexit
import sys
import threading
from pathlib import Path

# Add src to path if needed (though usually handled by entry script)
current_dir = Path(__file__).resolve().parent
src_dir = current_dir.parent.parent
if str(src_dir) not in sys.path:
    sys.path.append(str(src_dir))

from utils.gui_lib import BaseWindow
from manager.helpers.comfyui_client import ComfyUIManager

class ComfyUIFeatureBase(BaseWindow):
    """
    Base class for all ComfyUI-integrated features.
    Handles:
    - ComfyUIManager initialization (start/connect) in BACKGROUND
    - GUI displays immediately while server starts
    - Automatic cleanup on exit
    - Standardized error reporting
    """
    def __init__(self, title="ComfyUI Feature", width=800, height=600):
        super().__init__(title=title, width=width, height=height)
        
        # Initialize Client
        self.client = ComfyUIManager()
        self.server_ready = False
        self.server_status = "Connecting..."
        
        # Create a status label that subclasses can use (optional)
        self._status_var = ctk.StringVar(value="⏳ Connecting to ComfyUI...")
        
        # Safety: Ensure stop is called on abrupt python exit
        atexit.register(self._safety_cleanup)
        
        # Standard Protocol
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Start server connection in background thread (NON-BLOCKING)
        self._start_server_thread()
        
        # Add Status Bar (Default)
        self._setup_status_bar()

    def _setup_status_bar(self):
        """Create a default status bar at the bottom."""
        # Use a frame for status bar to ensure it sticks to bottom
        self.status_frame = ctk.CTkFrame(self, height=30, corner_radius=0, fg_color="transparent")
        self.status_frame.pack(side="bottom", fill="x", padx=5, pady=5)
        
        self.status_label_widget = ctk.CTkLabel(
            self.status_frame, 
            textvariable=self._status_var,
            text_color="gray",
            anchor="w",
            font=("Segoe UI", 12)
        )
        self.status_label_widget.pack(side="left", fill="x", expand=True)

    def _start_server_thread(self):
        """Start server connection in background - GUI shows immediately."""
        def connect():
            try:
                if self.client.is_running():
                    self.server_ready = True
                    self.server_status = f"✅ Connected (:{self.client.port})"
                    self._status_var.set(self.server_status)
                    if hasattr(self, 'status_label_widget'): 
                        self.status_label_widget.configure(text_color="#69F0AE") # Green
                    self._on_server_ready()
                elif self.client.start():
                    self.server_ready = True
                    self.server_status = f"✅ Server Started (:{self.client.port})"
                    self._status_var.set(self.server_status)
                    if hasattr(self, 'status_label_widget'): 
                        self.status_label_widget.configure(text_color="#69F0AE") # Green
                    self._on_server_ready()
                else:
                    self.server_status = "❌ Server Not Available (Check Logs)"
                    self._status_var.set(self.server_status)
                    if hasattr(self, 'status_label_widget'): 
                        self.status_label_widget.configure(text_color="#FF5252") # Red
                    self._on_server_failed()
            except Exception as e:
                self.server_status = f"❌ Connection Error: {e}"
                self._status_var.set(self.server_status)
                if hasattr(self, 'status_label_widget'): 
                    self.status_label_widget.configure(text_color="#FF5252") # Red
                self._on_server_failed()
        
        thread = threading.Thread(target=connect, daemon=True)
        thread.start()
    
    def _on_server_ready(self):
        """Override in subclass to handle server ready event."""
        pass
    
    def _on_server_failed(self):
        """Override in subclass to handle server failure."""
        # Intrusive popup removed. User can see status bar.
        pass

    def _safety_cleanup(self):
        """Called by atexit to ensure resources are freed."""
        # We no longer stop the ComfyUI server on GUI close.
        # The server is shared across multiple features and should remain running.
        pass

    def on_closing(self):
        """Standard cleanup on window close."""
        # Do NOT stop ComfyUI server - it's shared across features
        self.destroy()

    def check_requirements(self, dependencies=None):
        """
        Optional helper to check if libraries are installed.
        dependencies: list of module names strings
        """
        if not dependencies: return True
        
        missing = []
        for dep in dependencies:
            try:
                __import__(dep)
            except ImportError:
                missing.append(dep)
        
        if missing:
            messagebox.showerror("Missing Dependencies", 
                               f"The following required libraries are missing:\\n{', '.join(missing)}\\n\\nPlease install them via ContextUp Manager.")
            return False
        return True

