"""
Tray Menu Builder
Constructs the pystray menu with all items.
"""
import sys
import subprocess
from pathlib import Path

import pystray

from core.config import MenuConfig
from core.paths import SRC_DIR
from core.logger import setup_logger
from manager.mgr_core.packages import PackageManager
from tray.launchers import create_launcher, open_manager
from utils import i18n

logger = setup_logger("menu_builder")

# Module paths
src_dir = SRC_DIR


class TrayAgentWrapper:
    """Simple wrapper for icon to provide notify method for modules."""
    
    def __init__(self, icon):
        self._icon = icon
    
    def notify(self, title, message):
        try:
            if self._icon:
                self._icon.notify(f"{title}: {message}")
        except Exception as e:
            logger.error(f"Notify failed: {e}")


def build_menu(icon_ref=None, reload_callback=None, exit_callback=None):
    """
    Build the menu structure.
    
    Args:
        icon_ref: Reference to the pystray Icon instance (for notifications)
        reload_callback: Function to call for Reload
        exit_callback: Function to call for Exit
    """
    # Hot-reload launchers (Removed for stability - reliable restart required)
    from tray.launchers import create_launcher, open_manager

    menu_entries = []
    
    # Global Agent Wrapper for modules
    if icon_ref:
        agent_wrapper = TrayAgentWrapper(icon_ref)
    else:
        # Dummy wrapper if icon not ready
        class DummyWrapper:
            def notify(self, msg): pass
        agent_wrapper = DummyWrapper()
    
    if icon_ref and not hasattr(icon_ref, '_modules'):
        icon_ref._modules = []

    # 1. Load tray modules (Recent Folders, Copy My Info, Clipboard Opener)
    try:
        # agent_wrapper = TrayAgentWrapper(icon_ref) if icon_ref else None # This line is now handled above
        
        # if icon_ref and not hasattr(icon_ref, '_modules'): # This line is now handled above
        #     icon_ref._modules = []

        # --- Recent Folders ---
        try:
            from tray.modules.recent_folders import RecentFolders
            recent_module = RecentFolders(agent_wrapper)
            recent_module.start()
            if icon_ref:
                icon_ref._modules.append(recent_module)
            
            recent_items = recent_module.get_menu_items()
            if recent_items:
                menu_entries.extend(recent_items)
                menu_entries.append(pystray.Menu.SEPARATOR)
        except Exception as e:
            logger.error(f"Failed to load RecentFolders: {e}")

    except Exception as e:
        logger.error(f"Failed to load Tray Modules: {e}")

    # 2. Dynamic Tools from JSON (show_in_tray: true)
    try:
        menu_config = MenuConfig()
        tray_tools = [
            item for item in menu_config.items
            if item.get("show_in_tray", False) and item.get("enabled", True)
        ]
        
        # Filter by dependencies
        pm = PackageManager(src_dir.parent)
        installed_packages = pm.get_installed_packages()
        
        valid_tools = []
        for tool in tray_tools:
            if tool.get("category") == "Comfyui":
                valid_tools.append(tool)
                continue
            valid, _ = pm.check_dependencies(tool, installed_packages)
            if valid:
                valid_tools.append(tool)
        tray_tools = valid_tools
        
        # Group by category for submenu structure
        categories = {}
        for tool in tray_tools:
            cat = tool.get("category", "Other")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(tool)
        
        # Sort tools within each category by order
        for cat in categories:
            categories[cat].sort(key=lambda x: x.get("order", 9999))
        
        # Build category submenus
        category_order = ["Comfyui", "Tools", "AI", "System", "Other"]
        added_any = False
        
        def build_category_submenu(cat_name, tools):
            """Build a submenu for a category."""
            submenu_items = []
            
            # SPECIAL: Add ComfyUI server controls (Static items to avoid blocking startup)
            if cat_name == "Comfyui":
                def start_server_action():
                    try:
                        from manager.helpers.comfyui_service import ComfyUIService
                        service = ComfyUIService()
                        ok, port, started = service.ensure_running(start_if_missing=True)
                        if ok and started:
                            agent_wrapper.notify("ComfyUI", f"Started on port {port}")
                        elif ok:
                            agent_wrapper.notify("ComfyUI", f"Already running on port {port}")
                        else:
                            agent_wrapper.notify("ComfyUI", "Failed to start server")
                    except Exception as e:
                        logger.error(f"Start server failed: {e}")
                        agent_wrapper.notify("ComfyUI", f"Start failed: {e}")

                def stop_server_action():
                    try:
                        from manager.helpers.comfyui_service import ComfyUIService
                        service = ComfyUIService()
                        ok, reason = service.stop(only_if_owned=True)
                        if ok:
                            agent_wrapper.notify("ComfyUI", "Server stopped")
                        elif reason == "not_owned":
                            agent_wrapper.notify("ComfyUI", "Not owned by ContextUp. Use Force Kill if needed.")
                        else:
                            agent_wrapper.notify("ComfyUI", "Failed to stop server")
                    except Exception as e:
                        logger.error(f"Stop server failed: {e}")
                        agent_wrapper.notify("ComfyUI", f"Stop failed: {e}")

                def unload_vram_action():
                    try:
                        from manager.helpers.comfyui_service import ComfyUIService
                        import urllib.request
                        service = ComfyUIService()
                        running, port = service.is_running()
                        if running and port:
                            url = f"http://127.0.0.1:{port}/free"
                            urllib.request.urlopen(url, timeout=2)
                            agent_wrapper.notify("ComfyUI", "VRAM unload requested")
                        else:
                            agent_wrapper.notify("ComfyUI", "Server is not running")
                    except Exception as e:
                        logger.error(f"VRAM unload failed: {e}")
                        agent_wrapper.notify("ComfyUI", f"VRAM unload failed: {e}")

                def force_cleanup_action():
                    try:
                        from manager.helpers.comfyui_service import ComfyUIService
                        service = ComfyUIService()
                        service.force_kill_all()
                        agent_wrapper.notify("ComfyUI", "Force cleanup requested")
                    except Exception as e:
                        logger.error(f"Cleanup failed: {e}")
                        agent_wrapper.notify("ComfyUI", f"Cleanup error: {e}")

                def open_console_action():
                    try:
                        from manager.helpers.comfyui_service import ComfyUIService
                        service = ComfyUIService()
                        ok, reason = service.open_console()
                        if ok and reason == "already_open":
                            agent_wrapper.notify("ComfyUI", "Console already open")
                        elif ok:
                            agent_wrapper.notify("ComfyUI", "Console opened")
                        else:
                            agent_wrapper.notify("ComfyUI", "Failed to open console")
                    except Exception as e:
                        logger.error(f"Open console failed: {e}")
                        agent_wrapper.notify("ComfyUI", f"Open console failed: {e}")

                def close_console_action():
                    try:
                        from manager.helpers.comfyui_service import ComfyUIService
                        service = ComfyUIService()
                        ok, reason = service.close_console()
                        if ok:
                            agent_wrapper.notify("ComfyUI", "Console closed")
                        elif reason == "not_running":
                            agent_wrapper.notify("ComfyUI", "Console is not running")
                        else:
                            agent_wrapper.notify("ComfyUI", "Failed to close console")
                    except Exception as e:
                        logger.error(f"Close console failed: {e}")
                        agent_wrapper.notify("ComfyUI", f"Close console failed: {e}")

                # Add static items
                submenu_items.append(pystray.MenuItem(i18n.t("features.comfyui.start_server", "🚀 Start Server"), lambda: start_server_action()))
                submenu_items.append(pystray.MenuItem(i18n.t("features.comfyui.stop_server", "🛑 Stop Server"), lambda: stop_server_action()))
                submenu_items.append(pystray.MenuItem(i18n.t("features.comfyui.open_console", "Open Console"), lambda: open_console_action()))
                submenu_items.append(pystray.MenuItem(i18n.t("features.comfyui.close_console", "Close Console"), lambda: close_console_action()))
                submenu_items.append(pystray.MenuItem(i18n.t("features.comfyui.unload_vram", "🧹 Unload VRAM"), lambda: unload_vram_action()))
                submenu_items.append(pystray.MenuItem(i18n.t("features.comfyui.force_kill", "☠️ Force Kill All"), lambda: force_cleanup_action()))
                submenu_items.append(pystray.Menu.SEPARATOR)
            for tool in tools:
                tool_id = tool.get("id", "")
                tool_name = tool.get("name", "Tool")
                tool_script = tool.get("script", "")
                
                # SPECIAL HANDLING for Copy My Info - render as interactive submenu
                if tool_id == "copy_my_info":
                    try:
                        from tray.modules.copy_my_info import CopyMyInfoModule
                        info_mod = CopyMyInfoModule(agent_wrapper)
                        items = info_mod.get_menu_items()
                        if items:
                            submenu_items.extend(items)
                        continue
                    except Exception as e:
                        logger.error(f"Failed to load CopyMyInfo submenu: {e}")
                
                if tool.get("category"):
                    i18n_key = f"features.{tool['category'].lower()}.{tool_id}"
                else:
                    i18n_key = f"features.other.{tool_id}"
                
                display_name = i18n.t(i18n_key, default=tool_name)
                display_name = i18n.get_localized_name(display_name)
                
                submenu_items.append(
                    pystray.MenuItem(display_name, create_launcher(tool_id, tool_name, tool_script))
                )
            return submenu_items
        
        for cat_name in category_order:
            if cat_name in categories and categories[cat_name]:
                submenu_items = build_category_submenu(cat_name, categories[cat_name])
                cat_display = i18n.t(f"categories.{cat_name.lower()}", default=cat_name)
                menu_entries.append(
                    pystray.MenuItem(cat_display, pystray.Menu(*submenu_items))
                )
                added_any = True
        
        for cat_name, tools in categories.items():
            if cat_name not in category_order and tools:
                submenu_items = build_category_submenu(cat_name, tools)
                cat_display = i18n.t(f"categories.{cat_name.lower()}", default=cat_name)
                menu_entries.append(
                    pystray.MenuItem(cat_display, pystray.Menu(*submenu_items))
                )
                added_any = True
        
        if added_any:
            menu_entries.append(pystray.Menu.SEPARATOR)
            
    except Exception as e:
        logger.error(f"Failed to load tray tools from JSON: {e}")

    # 3. ContextUp Manager
    menu_entries.append(pystray.MenuItem(i18n.t("features.system.manager", "ContextUp Manager"), lambda: open_manager()))
    menu_entries.append(pystray.Menu.SEPARATOR)

    # 4. System (Reload, Exit)
    if reload_callback:
        menu_entries.append(pystray.MenuItem(i18n.t("common.reload", "Reload"), reload_callback))
    if exit_callback:
        menu_entries.append(pystray.MenuItem(i18n.t("common.exit", "Exit"), exit_callback))
    
    return menu_entries
