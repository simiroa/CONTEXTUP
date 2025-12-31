"""
Shared Tool Launcher for Tray and Quick Menu
Provides unified tool launching logic to ensure consistency between tray menu and quick menu.
"""
import sys
import subprocess
from pathlib import Path
from core.logger import setup_logger
from core.paths import SRC_DIR, LOGS_DIR

logger = setup_logger("launchers")

# Standard search directories for tool scripts
FEATURE_CATEGORIES = [
    "tools",
    "ai", 
    "system",
    "comfyui",
    "video",
    "image",
    "audio",
    "document",
    "sequence",
    "leave_manager",
    "prompt_master",
]


def find_script_path(tool_id: str, tool_script: str = None) -> Path:
    """
    Find the script path for a tool based on its ID and optional script field.
    
    Args:
        tool_id: The unique identifier of the tool (e.g., "leave_manager")
        tool_script: Optional script path from config (e.g., "src.features.comfyui.open_dashboard")
    
    Returns:
        Path to the script if found, None otherwise
    """
    src_dir = SRC_DIR
    script_path = None
    
    # 1. Try script field from config (e.g., "src.features.comfyui.open_dashboard")
    if tool_script:
        parts = tool_script.replace("src.", "").split(".")
        if len(parts) >= 2:
            # Fix: Don't add "features" if it's already in parts[0]
            base_idx = 0
            if parts[0] == "features":
                base_idx = 1
            
            # Convert dotted path to file path
            script_path = src_dir / "features" / "/".join(parts[base_idx:-1]) / f"{parts[-1]}.py"
            if script_path.exists():
                return script_path
            
            # Try direct path reconstruction (Fallback)
            alt_path = src_dir / f"{'/'.join(parts)}.py"
            if alt_path.exists():
                return alt_path
    
    # 2. Standard search paths
    search_paths = []
    
    # Category-based paths
    for cat in FEATURE_CATEGORIES:
        search_paths.extend([
            src_dir / "features" / cat / f"{tool_id}.py",
            src_dir / "features" / cat / f"{tool_id}_gui.py",
        ])
    
    # Package-based paths
    search_paths.extend([
        src_dir / "features" / tool_id / "gui.py",
        src_dir / "features" / tool_id / "main.py",
        src_dir / "features" / tool_id / "__init__.py",
    ])
    
    # Special mappings
    special_mappings = {
        "leave_manager": src_dir / "features" / "leave_manager" / "gui.py",
        "vacance": src_dir / "features" / "leave_manager" / "gui.py",
        "finder": src_dir / "features" / "finder" / "__init__.py",
        "prompt_master": src_dir / "features" / "prompt_master" / "main.py",
    }
    
    if tool_id in special_mappings:
        special_path = special_mappings[tool_id]
        if special_path.exists():
            return special_path
    
    # Search through all paths
    for sp in search_paths:
        if sp and sp.exists():
            return sp
    
    return None


def launch_tool(tool_id: str, tool_name: str = None, tool_script: str = None):
    """
    Launch a tool by finding and executing its script.
    
    Args:
        tool_id: The unique identifier of the tool
        tool_name: Display name for logging (optional)
        tool_script: Optional script path from config
    """
    display_name = tool_name or tool_id
    
    try:
        script_path = find_script_path(tool_id, tool_script)
        project_root = SRC_DIR.parent
        
        if script_path and script_path.exists():
            logger.info(f"Launching tool: {display_name} ({script_path})")
            
            # Use pythonw.exe for GUI apps to avoid console windows
            python_exe = sys.executable
            if python_exe.endswith("python.exe"):
                pythonw = Path(python_exe).parent / "pythonw.exe"
                if pythonw.exists():
                    python_exe = str(pythonw)

            # Redirect output for debugging
            debug_log = LOGS_DIR / "tool_launch_debug.log"
            # Fix: Keep file open for the subprocess!
            f = open(debug_log, "a", encoding="utf-8")
            f.write(f"\n--- Launching {display_name} ---\n")
            f.flush()
            
            subprocess.Popen(
                [python_exe, str(script_path)], 
                cwd=str(project_root),
                creationflags=0x08000000,
                stdout=f,
                stderr=subprocess.STDOUT
            )
        else:
            # Fallback: use menu.py dispatcher
            logger.info(f"Script not found, using menu.py dispatcher for {tool_id}")
            menu_py = SRC_DIR / "core" / "menu.py"
            
            # Resolve pythonw for menu.py as well
            python_exe = sys.executable
            if python_exe.endswith("python.exe"):
                pythonw = Path(python_exe).parent / "pythonw.exe"
                if pythonw.exists():
                    python_exe = str(pythonw)

            debug_log = LOGS_DIR / "tool_launch_debug.log"
            f = open(debug_log, "a", encoding="utf-8")
            f.write(f"\n--- Launching {display_name} (Dispatcher) ---\n")
            f.flush()
            
            subprocess.Popen(
                [python_exe, str(menu_py), tool_id, "background"],
                cwd=str(project_root),
                creationflags=0x08000000,
                stdout=f,
                stderr=subprocess.STDOUT
            )
    except Exception as e:
        logger.error(f"Failed to launch {display_name}: {e}")


def create_launcher(tool_id: str, tool_name: str, tool_script: str = None):
    """
    Create a launcher function (closure) for use in menu callbacks.
    
    Args:
        tool_id: The unique identifier of the tool
        tool_name: Display name for logging
        tool_script: Optional script path from config
    
    Returns:
        A callable function that launches the tool when invoked
    """
    def launcher():
        launch_tool(tool_id, tool_name, tool_script)
    return launcher


def open_manager():
    """Launch the ContextUp Manager."""
    try:
        manager_script = SRC_DIR / "manager" / "main.py"
        logger.info(f"Opening Manager: {manager_script}")
        subprocess.Popen(
            [sys.executable, str(manager_script)],
            creationflags=0x08000000
        )
    except Exception as e:
        logger.error(f"Failed to open manager: {e}")
