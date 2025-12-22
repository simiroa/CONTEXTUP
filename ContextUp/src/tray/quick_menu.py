"""
Frosted Glass Quick Menu for ContextUp
Displays a modern, translucent popup menu with blur effect
"""
import sys
import os
import subprocess
import ctypes
from pathlib import Path
import customtkinter as ctk

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.append(str(src_dir))

import socket
import threading
from core.config import MenuConfig
from core.logger import setup_logger
from core.paths import ROOT_DIR, LOGS_DIR, SRC_DIR
from utils.comfy_server import start_comfy, stop_comfy, is_comfy_running

QUICK_MENU_PORT = 54322  # Dedicated port for quick menu daemon

logger = setup_logger("quick_menu")

# Windows DWM API for blur effect
DWM_BB_ENABLE = 0x01
DWM_BB_BLURREGION = 0x02
ACCENT_ENABLE_BLURBEHIND = 3
ACCENT_ENABLE_ACRYLICBLURBEHIND = 4

class ACCENTPOLICY(ctypes.Structure):
    _fields_ = [
        ("AccentState", ctypes.c_uint),
        ("AccentFlags", ctypes.c_uint),
        ("GradientColor", ctypes.c_uint),
        ("AnimationId", ctypes.c_uint)
    ]

class WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
    _fields_ = [
        ("Attribute", ctypes.c_int),
        ("Data", ctypes.POINTER(ctypes.c_int)),
        ("SizeOfData", ctypes.c_size_t)
    ]

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


def apply_blur_effect(hwnd, opacity=230):
    """Apply Windows Acrylic blur effect to window"""
    try:
        # Try modern Acrylic (Windows 10+)
        accent = ACCENTPOLICY()
        accent.AccentState = ACCENT_ENABLE_ACRYLICBLURBEHIND
        accent.GradientColor = (opacity << 24) | 0x0D0D0D  # Dark with alpha
        
        data = WINDOWCOMPOSITIONATTRIBDATA()
        data.Attribute = 19  # WCA_ACCENT_POLICY
        data.SizeOfData = ctypes.sizeof(accent)
        data.Data = ctypes.cast(ctypes.pointer(accent), ctypes.POINTER(ctypes.c_int))
        
        # SetWindowCompositionAttribute
        ctypes.windll.user32.SetWindowCompositionAttribute(hwnd, ctypes.byref(data))
        return True
    except Exception as e:
        logger.warning(f"Acrylic effect failed: {e}")
        return False


class QuickMenu(ctk.CTkToplevel):
    def __init__(self, is_daemon=False):
        super().__init__()
        self.is_daemon = is_daemon
        
        # Window config
        self.title("")
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        self.attributes('-alpha', 0.95)
        # Fix transparent background artifact
        self.config(bg='#000001')
        self.attributes('-transparentcolor', '#000001')
        
        self.pinned = False
        
        # Get mouse position accurately using Win32 API
        
        pt = POINT()

        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        mouse_x = pt.x
        mouse_y = pt.y
        
        # Multi-monitor safe positioning
        # We use a fixed width/height but adjust if close to edge
        menu_width = 280
        menu_height = 450
        
        # Simple bounds checking against virtual screen
        # GetSystemMetrics(78) = SM_CXVIRTUALSCREEN, (79) = SM_CYVIRTUALSCREEN
        v_width = ctypes.windll.user32.GetSystemMetrics(78)
        v_height = ctypes.windll.user32.GetSystemMetrics(79)
        v_left = ctypes.windll.user32.GetSystemMetrics(76) # SM_XVIRTUALSCREEN
        v_top = ctypes.windll.user32.GetSystemMetrics(77)  # SM_YVIRTUALSCREEN
        
        x = mouse_x + 10
        y = mouse_y + 10
        
        # Adjust if off screen
        if x + menu_width > v_left + v_width:
            x = mouse_x - menu_width - 10
        if y + menu_height > v_top + v_height:
            y = mouse_y - menu_height - 10
            
        self.geometry(f"{menu_width}x{menu_height}+{x}+{y}")
        
        # Apply blur after window is created
        self.after(50, self._apply_blur)
        
        # Main frame
        self.main_frame = ctk.CTkFrame(
            self, 
            fg_color=("#E8E8E8", "#0D0D0D"),
            corner_radius=10,
            border_width=1,
            border_color=("#CCCCCC", "#2A2A2A")
        )
        self.main_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Title bar (Pin button)
        self._build_title_bar()
        
        # Build menu
        self.build_menu()
        
        # Focus
        self.focus_force()
        
        if self.is_daemon:
            self.withdraw() # Start hidden in daemon mode
            self._start_udp_listener()

    def _start_udp_listener(self):
        def listener():
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                sock.bind(("127.0.0.1", QUICK_MENU_PORT))
                logger.info(f"Quick Menu Daemon listening on port {QUICK_MENU_PORT}")
                while True:
                    data, addr = sock.recvfrom(1024)
                    if data.strip() == b"show":
                        self.after(0, self.show_at_mouse)
                    elif data.strip() == b"quit":
                        self.after(0, self.destroy)
                        break
            except Exception as e:
                logger.error(f"Quick Menu UDP listener error: {e}")
            finally:
                sock.close()
        
        threading.Thread(target=listener, daemon=True).start()

    def show_at_mouse(self):
        """Show and reposition window at current mouse position"""
        # Get mouse position
        pt = POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        
        # Recalculate geometry
        menu_width = 280
        menu_height = 450
        v_width = ctypes.windll.user32.GetSystemMetrics(78)
        v_height = ctypes.windll.user32.GetSystemMetrics(79)
        v_left = ctypes.windll.user32.GetSystemMetrics(76)
        v_top = ctypes.windll.user32.GetSystemMetrics(77)
        
        x = pt.x + 10
        y = pt.y + 10
        logger.info(f"Showing Quick Menu at: {x}, {y} (Mouse: {pt.x}, {pt.y})")

        if x + menu_width > v_left + v_width: x = pt.x - menu_width - 10
        if y + menu_height > v_top + v_height: y = pt.y - menu_height - 10
        
        # Try to handle High DPI
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except: pass

        self.geometry(f"{menu_width}x{menu_height}+{x}+{y}")
        self.deiconify()
        self.lift()
        self.attributes('-topmost', True)
        self.focus_force()
        self.attributes('-alpha', 0.95)
        self._apply_blur()
        
        # Double ensure visibility
        self.after(100, lambda: self.attributes('-topmost', True))
        self.after(100, lambda: self.lift())

    
    def _build_title_bar(self):
        title_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent", height=30)
        title_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        # Make title bar draggable
        title_frame.bind("<Button-1>", self._start_move)
        title_frame.bind("<B1-Motion>", self._on_move)
        self.main_frame.bind("<Button-1>", self._start_move)
        self.main_frame.bind("<B1-Motion>", self._on_move)
        
        # Close button (Rightmost)
        btn_close = ctk.CTkButton(
            title_frame,
            text="✕",
            width=30,
            height=30,
            fg_color="transparent",
            hover_color=("#D0D0D0", "#C0392B"),
            text_color="gray",
            command=self.destroy
        )
        btn_close.pack(side="right", padx=(5, 0))
        
        # Pin button (Left of Close)
        self.btn_pin = ctk.CTkButton(
            title_frame,
            text="📌",
            width=30,
            height=30,
            fg_color="transparent",
            hover_color=("#D0D0D0", "#333333"),
            text_color="gray",
            command=self._toggle_pin
        )
        self.btn_pin.pack(side="right")
        
        # Title or Logo (Optional, currently just 'ContextUp' text?)
        # Let's keep it minimal as requested, maybe just blank or small label
        # ctk.CTkLabel(title_frame, text="ContextUp", font=("Segoe UI", 10, "bold")).pack(side="left")

    def _toggle_pin(self):
        self.pinned = not self.pinned
        if self.pinned:
            self.btn_pin.configure(text_color="#2ECC71", fg_color=("#E0E0E0", "#222222")) # Greenish when pinned
        else:
            self.btn_pin.configure(text_color="gray", fg_color="transparent")

    def _on_focus_out(self, event):
        if not self.pinned:
            if self.is_daemon:
                self.withdraw()
            else:
                self.destroy()

    def _apply_blur(self):
        """Apply Windows blur effect"""
        try:
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            apply_blur_effect(hwnd, opacity=200) # Slightly more transparent
        except Exception as e:
            logger.debug(f"Blur effect error: {e}")
    
    def build_menu(self):
        """Build menu items from JSON config"""
        scrollable = ctk.CTkScrollableFrame(
            self.main_frame,
            fg_color="transparent",
            corner_radius=0
        )
        scrollable.pack(fill="both", expand=True, padx=4, pady=(0, 10))
        
        try:
            menu_config = MenuConfig()
            
            # Get all tray items, excluding manager (bottom) and copy_my_info (top section)
            tray_items = [
                item for item in menu_config.items 
                if item.get("show_in_tray", False) 
                and item.get("id") != "manager"
                and item.get("id") != "copy_my_info"
            ]
            
            # Group by category
            categories = {}
            for item in tray_items:
                cat = item.get("category", "Other")
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(item)
            
            # Sort within categories
            for cat in categories:
                categories[cat].sort(key=lambda x: x.get("order", 9999))
            
            # 1. Quick Actions (config-based special items)
            quick_actions = [
                ("🔄  Reopen Last Closed Folder", self._reopen_recent, "reopen_recent"),
                ("📂  Open from Clipboard", self._open_clipboard, "open_from_clipboard"),
            ]
            for text, handler, _ in quick_actions:
                self._add_menu_button(scrollable, text, handler)
            
            self._add_separator(scrollable)
            
            
            # 3. Category-based Tools (ComfyUI, Tools, etc.)
            category_order = ["Comfyui", "Tools", "AI", "System", "Other"]
            added_any_category = False
            
            for cat_name in category_order:
                if cat_name in categories and categories[cat_name]:
                    # Add category header
                    self._add_category_header(scrollable, cat_name)
                    
                    for item in categories[cat_name]:
                        name = item.get("name", "Tool")
                        item_id = item.get("id", "")
                        
                        # SPECIAL HANDLING for Copy My Info - render as collapsible section
                        if item_id == "copy_my_info":
                            self._add_copy_my_info_section(scrollable)
                            continue

                        self._add_menu_button(
                            scrollable,
                            f"   {name}",
                            lambda i=item: self._launch_tool(i)
                        )
                    
                    # Add ComfyUI specific background server controls
                    if cat_name == "Comfyui":
                        self._add_menu_button(
                            scrollable,
                            "   🚀  Start ComfyUI Server",
                            self._start_comfy_server
                        )
                        self._add_menu_button(
                            scrollable,
                            "   🛑  Stop ComfyUI Server",
                            self._stop_comfy_server
                        )
                        
                    added_any_category = True
            
            # Add remaining categories not in order
            for cat_name, items in categories.items():
                if cat_name not in category_order and items:
                    self._add_category_header(scrollable, cat_name)
                    for item in items:
                        name = item.get("name", "Tool")
                        item_id = item.get("id", "")
                        
                        # SPECIAL HANDLING for Copy My Info
                        if item_id == "copy_my_info":
                            self._add_copy_my_info_section(scrollable)
                            continue

                        self._add_menu_button(
                            scrollable,
                            f"   {name}",
                            lambda i=item: self._launch_tool(i)
                        )
                    added_any_category = True
            
            if added_any_category:
                self._add_separator(scrollable)

            # 4. System
            self._add_menu_button(scrollable, "🎛  Manager", self._open_manager)
            
            
        except Exception as e:
            logger.error(f"Failed to build menu: {e}")
            ctk.CTkLabel(scrollable, text=f"Error: {e}").pack()
    
    def _add_separator(self, parent):
        padding = ctk.CTkFrame(parent, height=1, fg_color=("#CCCCCC", "#333333"))
        padding.pack(fill="x", pady=6, padx=10)
    
    def _add_category_header(self, parent, category_name):
        """Add a category header label"""
        label = ctk.CTkLabel(
            parent,
            text=f"━ {category_name} ━",
            font=("Segoe UI", 10, "bold"),
            text_color=("gray40", "gray60"),
            anchor="w"
        )
        label.pack(fill="x", pady=(8, 2), padx=10)

    def _add_menu_button(self, parent, text, command):
        """Add a menu button - larger font, indented"""
        btn = ctk.CTkButton(
            parent,
            text=text,
            command=lambda: self._on_click(command),
            anchor="w",
            fg_color="transparent",
            hover_color=("#D0D0D0", "#1F1F1F"),
            text_color=("gray10", "#E0E0E0"),
            height=34, # Taller
            corner_radius=6,
            font=("Segoe UI", 12), # Larger font
        )
        # Indent by padding x inside pack
        btn.pack(fill="x", pady=1, padx=5)
    
    def _on_click(self, command):
        command()
        if not self.pinned:
            if self.is_daemon:
                self.withdraw()
            else:
                self.destroy()

    def _add_copy_my_info_section(self, parent):
        """Add Copy My Info as collapsible submenu"""
        try:
            from tray.modules.copy_my_info import CopyMyInfoModule
            info_mod = CopyMyInfoModule(None)
            items = info_mod._load_items()
            
            if items:
                # Create a frame for the submenu
                submenu_frame = ctk.CTkFrame(parent, fg_color="transparent")
                submenu_frame.pack(fill="x", pady=1, padx=5)
                
                # Toggle state
                self.info_expanded = False
                self.info_items_frame = None
                
                def toggle_submenu():
                    self.info_expanded = not self.info_expanded
                    if self.info_expanded:
                        toggle_btn.configure(text="📋  Copy My Info  ▼")
                        # Show items
                        self.info_items_frame = ctk.CTkFrame(submenu_frame, fg_color=("gray85", "#181818"), corner_radius=6)
                        self.info_items_frame.pack(fill="x", padx=(10, 0), pady=(2, 0))
                        
                        for item in items:
                            label = item.get("label", "")
                            content = item.get("content", "")
                            btn = ctk.CTkButton(
                                self.info_items_frame,
                                text=f"📄 {label}",
                                command=lambda c=content: self._on_click(lambda: self._copy_to_clipboard(c)),
                                anchor="w",
                                fg_color="transparent",
                                hover_color=("#C0C0C0", "#2A2A2A"),
                                text_color=("gray10", "gray90"),
                                height=30,
                                corner_radius=4,
                                font=("Segoe UI", 11)
                            )
                            btn.pack(fill="x", pady=1, padx=2)
                    else:
                        toggle_btn.configure(text="📋  Copy My Info  ▶")
                        if self.info_items_frame:
                            self.info_items_frame.destroy()
                            self.info_items_frame = None
                
                toggle_btn = ctk.CTkButton(
                    submenu_frame,
                    text="📋  Copy My Info  ▶",
                    command=toggle_submenu,
                    anchor="w",
                    fg_color="transparent",
                    hover_color=("#D0D0D0", "#1F1F1F"),
                    text_color=("gray10", "#E0E0E0"),
                    height=34,
                    corner_radius=6,
                    font=("Segoe UI", 12)
                )
                toggle_btn.pack(fill="x")
                
        except Exception as e:
            logger.debug(f"Copy My Info not available: {e}")
    
    def _reopen_recent(self):
        try:
            log_file = LOGS_DIR / "recent_folders.log"
            if log_file.exists():
                with open(log_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                if lines:
                    last_line = lines[-1].strip()
                    if "\t" in last_line:
                        folder_path = last_line.split("\t", 1)[1]
                        if Path(folder_path).exists():
                            subprocess.Popen(f'explorer "{folder_path}"', shell=True)
        except Exception as e:
            logger.error(f"Reopen failed: {e}")
    
    def _open_clipboard(self):
        try:
            import pyperclip
            content = pyperclip.paste().strip().strip('"')
            path = Path(content)
            if path.exists() and path.is_dir():
                subprocess.Popen(f'explorer "{path}"', shell=True)
        except Exception as e:
            logger.error(f"Open clipboard failed: {e}")
    
    def _copy_to_clipboard(self, content):
        try:
            import pyperclip
            pyperclip.copy(content)
        except:
            pass
    
    def _launch_tool(self, item):
        """Launch a tool using shared launcher logic."""
        from tray.launchers import launch_tool
        tool_id = item.get("id", "")
        tool_name = item.get("name", "")
        tool_script = item.get("script", "")
        launch_tool(tool_id, tool_name, tool_script)
    
    def _open_manager(self):
        try:
            manager_script = src_dir / "manager" / "main.py"
            subprocess.Popen([sys.executable, str(manager_script)], creationflags=0x08000000)
        except Exception as e:
            logger.error(f"Manager launch failed: {e}")
    
    def _start_comfy_server(self):
        success, msg = start_comfy()
        logger.info(f"Start ComfyUI: {msg}")
        # Optionally show a small toast or message, but for now just log

    def _stop_comfy_server(self):
        success, msg = stop_comfy()
        logger.info(f"Stop ComfyUI: {msg}")
    
    def _on_focus_out(self, event):
        # Only close if not pinned and focuses out to another app
        # But tkinter focus-out is tricky, sometimes fires on internal clicks
        # We check widget to ensure it's the toplevel losing focus
        if event.widget == self and not self.pinned:
            self.destroy()

    def _start_move(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _on_move(self, event):
        try:
            deltax = event.x - self._drag_x
            deltay = event.y - self._drag_y
            x = self.winfo_x() + deltax
            y = self.winfo_y() + deltay
            self.geometry(f"+{x}+{y}")
        except:
            pass

def show_quick_menu():
    """Show the Quick Menu - Use UDP signal if daemon is running, else launch process"""
    try:
        # Try sending UDP signal
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(None) # Blocking for reliability? No, fast fail is better.
        sock.sendto(b"show", ("127.0.0.1", QUICK_MENU_PORT))
        sock.close()
    except Exception:
        # Daemon not running, launch it
        # Check if we already tried launching it to avoid infinite recursion risk? 
        # But here we just launch process.
        script_path = str(Path(__file__).resolve())
        subprocess.Popen(
            [sys.executable, script_path, "--daemon"],
            creationflags=0x08000000
        )
        
        # Initial Launch Optimization:
        # Wait a bit and try sending show signal again so user doesn't have to press twice
        def retry_show():
            import time
            time.sleep(0.5) # Wait for process to start
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.sendto(b"show", ("127.0.0.1", QUICK_MENU_PORT))
                sock.close()
            except: pass
            
        threading.Thread(target=retry_show, daemon=True).start()

def _run_menu():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--daemon", action="store_true")
    args = parser.parse_args()

    import tkinter as tk
    root = tk.Tk()
    root.withdraw()
    menu = QuickMenu(is_daemon=args.daemon)
    
    if args.daemon:
        logger.info("Quick Menu Daemon Started")
        menu.mainloop()
    else:
        # One-shot mode
        menu.show_at_mouse()
        menu.mainloop()


if __name__ == "__main__":
    _run_menu()
