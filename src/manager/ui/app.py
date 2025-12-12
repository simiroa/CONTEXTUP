import customtkinter as ctk
import sys
import logging
from pathlib import Path
from tkinter import messagebox

# Core
# Core
from manager.core.config import ConfigManager
from core.config import MenuConfig
from manager.core.packages import PackageManager
from manager.core.process import TrayProcessManager
from manager.core.settings import load_settings, save_settings
from core.registry import RegistryManager

# UI Handles
from .frames.editor import MenuEditorFrame
from .frames.settings import SettingsFrame
from .frames.updates import UpdatesFrame
from .frames.categories import CategoriesFrame
from .frames.logs import LogsFrame

class ContextUpManager(ctk.CTk):
    def __init__(self, root_dir: Path):
        super().__init__()
        self.root_dir = root_dir
        
        # Load Settings
        self.settings = load_settings()
        
        # Initialize Core Managers
        self.config_manager = ConfigManager(root_dir)
        self.package_manager = PackageManager(root_dir)
        self.process_manager = TrayProcessManager(root_dir, self.settings)
        
        # Registry needs MenuConfig (Lazy init now)
        self.registry_manager = None
        # was: self.registry_manager = RegistryManager(menu_config)
        
        # Setup Window
        self.title("ContextUp Manager v3.0")
        self.geometry("1100x800")
        ctk.set_default_color_theme("blue")
        
        # Set window icon - single ContextUp icon for all
        self._set_app_icon()
        
        # --- Category Sync Logic ---
        # Ensure all categories in the config exist in settings
        # and ensure CATEGORY_ORDER exists
        self._sync_categories()
        
        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self._create_sidebar()
        self._create_main_area()
        
        # Resize debounce for performance
        self._resize_timer = None
        self.bind("<Configure>", self._on_resize)
        
        # Lazy frame initialization - frames created on first access
        self.frames = {}
        self._frame_factories = {
            "editor": lambda: MenuEditorFrame(
                self.main_frame, 
                self.config_manager, 
                self.settings,
                on_save_registry=self.apply_registry_changes
            ),
            "categories": lambda: CategoriesFrame(self.main_frame, self.settings, self.config_manager),
            "settings": lambda: SettingsFrame(self.main_frame, self.settings, self.package_manager),
            "updates": lambda: UpdatesFrame(self.main_frame, self.package_manager),
            "logs": lambda: LogsFrame(self.main_frame, self.root_dir),
        }
        
        # Default View (only editor frame created at startup)
        self.show_frame("editor")
        
        # Status Check Loop
        self.after(1000, self._check_tray_status)
        
        # Auto-start Tray if enabled
        if self.settings.get("TRAY_ENABLED", False):
            self.after(2000, self._auto_start_tray)

    def _set_app_icon(self):
        """Set window icon and Windows taskbar icon."""
        try:
            # Set AppUserModelID for Windows Taskbar Icon grouping
            import ctypes
            myappid = 'hg.contextup.manager.3.0'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except:
            pass
        
        try:
            # Main ContextUp icon - single source of truth
            icon_path = self.root_dir / "assets" / "icons" / "ContextUp.ico"
            if icon_path.exists():
                self.iconbitmap(str(icon_path))
        except Exception as e:
            logging.warning(f"Failed to set app icon: {e}")
    
    def _on_resize(self, event):
        """Debounced resize handler to prevent layout thrashing."""
        # Only handle main window resize (not child widgets)
        if event.widget != self:
            return
        
        if self._resize_timer:
            self.after_cancel(self._resize_timer)
        
        # Delay layout update by 150ms
        self._resize_timer = self.after(150, self._on_resize_complete)
    
    def _on_resize_complete(self):
        """Called after resize debounce period."""
        self._resize_timer = None
        self.update_idletasks()

    def _auto_start_tray(self):
        if not self.process_manager.is_running():
            self.process_manager.start()
            self._update_tray_ui()

    def _create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # Spacer at row 10 gets the weight to push Tray Controls down
        self.sidebar.grid_rowconfigure(10, weight=1)
        
        # Logo / Title
        ctk.CTkLabel(self.sidebar, text="ContextUp", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Nav Buttons
        self.nav_buttons = {}
        self._add_nav_btn("Menu Editor", "editor", 1)
        self._add_nav_btn("Categories", "categories", 2)
        self._add_nav_btn("Settings", "settings", 3)
        self._add_nav_btn("Updates", "updates", 4)
        self._add_nav_btn("Logs", "logs", 5)
        
        # Spacer
        ctk.CTkLabel(self.sidebar, text="").grid(row=8, column=0)
        ctk.CTkLabel(self.sidebar, text="").grid(row=9, column=0)
        ctk.CTkLabel(self.sidebar, text="").grid(row=10, column=0)

        
        # Tray Controls
        self.tray_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.tray_frame.grid(row=11, column=0, padx=20, pady=20, sticky="s")
        
        ctk.CTkLabel(self.tray_frame, text="Tray Agent Status:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
        self.lbl_status = ctk.CTkLabel(self.tray_frame, text="● Checking...", text_color="gray")
        self.lbl_status.pack(anchor="w", pady=(0, 5))
        
        self.btn_tray = ctk.CTkButton(self.tray_frame, text="Start", command=self.toggle_tray_agent)
        self.btn_tray.pack(fill="x")

    def _add_nav_btn(self, text, name, row):
        btn = ctk.CTkButton(self.sidebar, text=text, height=40, border_spacing=10, fg_color="transparent", 
                          text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"), anchor="w",
                          command=lambda n=name: self.show_frame(n))
        btn.grid(row=row, column=0, sticky="ew")
        self.nav_buttons[name] = btn

    def _create_main_area(self):
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

    def apply_registry_changes(self):
        """Cleanly re-apply all registry changes."""
        try:
            # 1. Initialize Registry Manager if needed
            if self.registry_manager is None:
                try:
                    menu_config = MenuConfig()
                    self.registry_manager = RegistryManager(menu_config)
                except Exception as e:
                    logging.error(f"Failed to init RegistryManager: {e}")
                    messagebox.showerror("Error", f"Failed to initialize Registry Manager: {e}")
                    return

            # 2. Re-load Config (Ensure we have latest from disk)
            # The manager might have cached an old version? 
            # Actually RegistryManager creates its own MenuConfig instance which loads from disk.
            # So as long as we saved to disk (which MenuEditor does), we are good.
            self.registry_manager.config.load() 

            # 3. Clean Cleanup
            self.registry_manager.unregister_all()
            
            # 4. Register
            self.registry_manager.register_all()
            
            messagebox.showinfo("Success", "Registry updated successfully!")
            
        except Exception as e:
            logging.error(f"Registry Update Failed: {e}")
            messagebox.showerror("Error", f"Failed to update registry: {e}")

    def _create_frame_lazy(self, name: str):
        """Create a frame on-demand (lazy initialization)."""
        if name in self._frame_factories:
            frame = self._frame_factories[name]()
            frame.grid(row=0, column=0, sticky="nsew")
            return frame
        return None

    def show_frame(self, name):
        # Lazy create frame if not exists
        if name not in self.frames:
            frame = self._create_frame_lazy(name)
            if frame:
                self.frames[name] = frame
                logging.info(f"Lazy-loaded frame: {name}")
        
        frame = self.frames.get(name)
        if frame:
            frame.tkraise()
            
            # Trigger on_visible callback if frame supports it (for deferred loading)
            if hasattr(frame, 'on_visible'):
                frame.on_visible()
            
            # Highlight button
            for n, btn in self.nav_buttons.items():
                if n == name:
                    btn.configure(fg_color=("gray75", "gray25"))
                else:
                    btn.configure(fg_color="transparent")

    def toggle_tray_agent(self):
        running = self.process_manager.is_running()
        if running:
            success, msg = self.process_manager.stop()
            if not success: messagebox.showerror("Error", msg)
            self.settings["TRAY_ENABLED"] = False
        else:
            success, msg = self.process_manager.start()
            if not success: messagebox.showerror("Error", msg)
            self.settings["TRAY_ENABLED"] = True
            
        save_settings(self.settings)
            
        self._update_tray_ui()
        
    def _check_tray_status(self):
        self._update_tray_ui()
        self.after(10000, self._check_tray_status)  # 10s instead of 5s for performance

    def _update_tray_ui(self):
        running = self.process_manager.is_running()
        if running:
            self.lbl_status.configure(text="● Running", text_color="#2ECC71")
            self.btn_tray.configure(text="Stop", fg_color=("#C0392B", "#E74C3C"), hover_color=("#E74C3C", "#C0392B"))
        else:
            self.lbl_status.configure(text="● Stopped", text_color="#e74c3c")
            self.btn_tray.configure(text="Start", fg_color=("#27AE60", "#2ECC71"), hover_color=("#2ECC71", "#27AE60"))

    def _sync_categories(self):
        """Ensure all categories found in config are present in settings with a color and order."""
        try:
            items = self.config_manager.load_config()
            found_cats = set()
            for item in items:
                found_cats.add(item.get("category", "Uncategorized"))
                
            settings_cats = self.settings.setdefault("CATEGORY_COLORS", {})
            settings_order = self.settings.setdefault("CATEGORY_ORDER", [])
            
            changed = False
            
            # 1. Add missing colors
            defaults = ["#3498DB", "#E74C3C", "#2ECC71", "#F1C40F", "#9B59B6", "#1ABC9C", "#E67E22"]
            i = 0
            for cat in found_cats:
                if cat not in settings_cats:
                    settings_cats[cat] = defaults[i % len(defaults)]
                    i += 1
                    changed = True
                    
            # 2. Add missing order
            for cat in found_cats:
                if cat not in settings_order:
                    settings_order.append(cat)
                    changed = True
                    
            # 3. Clean up order (remove deleted cats? Maybe keep for robustness)
            # User can delete manually in Categories tab.
            
            if changed:
                save_settings(self.settings)
                
        except Exception as e:
            logging.error(f"Failed to sync categories: {e}")

    def refresh_app(self):
        """Reload configuration from disk and refresh UI and Registry."""
        try:
            # 1. Reload Config
            self.config_manager.load_config(force_reload=True)
            self._sync_categories()
            
            # 2. Refresh UI frames
            if "editor" in self.frames:
                self.frames["editor"].load_items()
               
            # 3. Re-apply Registry
            # reusing apply_registry_changes but suppressing its success msg would be nice, 
            # but for now let's just use it as is or copy logic to avoid double popup if we want custom msg.
            # actually apply_registry_changes does exactly what we need for registry.
            self.apply_registry_changes()
            
        except Exception as e:
            logging.error(f"Refresh failed: {e}")
            messagebox.showerror("Error", f"Refresh failed: {e}")

    def save_app_settings(self):
        """Global save for settings.json"""
        try:
            save_settings(self.settings)
            # Re-init process manager settings in case python path changed
            self.process_manager.settings = self.settings 
            messagebox.showinfo("Success", "Settings saved.")
            
            # Lazy Init Registry
            if self.registry_manager is None:
                try:
                    # Determine python path if needed (though registry handles it)
                    # We need to import here to avoid startup cost? Or just init.
                    # Imports were at top, so just init.
                    menu_config = MenuConfig()
                    self.registry_manager = RegistryManager(menu_config)
                except Exception as e:
                    logging.error(f"Failed to init RegistryManager: {e}")
            
            if self.registry_manager:
                self.registry_manager.register_all() # Re-register to apply changes
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")
