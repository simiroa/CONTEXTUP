import sys
import subprocess
import json
import logging
import threading
import os
from pathlib import Path
from tkinter import messagebox

logger = logging.getLogger("manager.core.packages")

class PackageManager:
    def __init__(self, root_dir):
        self.root_dir = Path(root_dir) if not isinstance(root_dir, Path) else root_dir
        self.req_path = self.root_dir / "requirements.txt"
        
    def get_installed_packages(self) -> dict:
        """Return dict of {package_name: version} using pip list --json."""
        try:
            # Use pip list --format=json for reliable detection
            python_exe = sys.executable
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            result = subprocess.check_output(
                [python_exe, "-m", "pip", "list", "--format=json"], 
                text=True, 
                startupinfo=startupinfo
            )
            packages = json.loads(result)
            return {pkg['name'].lower(): pkg['version'] for pkg in packages}
        except Exception as e:
            logger.error(f"Failed to list packages: {e}")
            return {}

    def check_dependencies(self, item: dict, installed_packages: dict) -> tuple[bool, list]:
        """Check if item's dependencies are met."""
        deps = item.get('dependencies', [])
        if not deps: return True, []
        
        missing = [d for d in deps if d.lower() not in installed_packages]
        return len(missing) == 0, missing

    def install_packages(self, deps: list, dep_metadata: dict, progress_callback=None, completion_callback=None):
        """
        Install list of packages in a background thread.
        Callback signature: progress(current_dependency_name, fraction_complete)
        """
        def run():
            python_exe = sys.executable
            total = len(deps)
            success = True
            
            for i, dep in enumerate(deps):
                meta = dep_metadata.get(dep, {})
                pip_name = meta.get('pip_name', dep)
                install_args = meta.get('install_args', [])
                
                if progress_callback:
                    progress_callback(dep, i/total)
                
                try:
                    cmd = [python_exe, "-m", "pip", "install", pip_name] + install_args
                    subprocess.check_call(cmd)
                except Exception as e:
                    logger.error(f"Failed to install {dep}: {e}")
                    success = False
                    break
                    
            if progress_callback:
                progress_callback("Done", 1.0)
                
            if completion_callback:
                completion_callback(success)

        threading.Thread(target=run, daemon=True).start()

    def update_system_libs(self, on_complete=None):
        """Run pip install -r requirements.txt using system python."""
        def run():
            try:
                subprocess.check_call(["python", "-m", "pip", "install", "-U", "-r", str(self.req_path)])
                if on_complete: on_complete(True, "System libraries updated!")
            except Exception as e:
                logger.error(f"System Update failed: {e}")
                if on_complete: on_complete(False, str(e))
                
        threading.Thread(target=run, daemon=True).start()

    def check_tray_dependencies(self, python_path: str) -> dict:
        """
        Check if required tray libs are installed in the given python environment.
        Returns: {'missing': [], 'valid': bool}
        """
        required = ['pystray', 'pillow', 'pywin32']
        start_flags = 0
        if os.name == 'nt':
            start_flags = subprocess.STARTF_USESHOWWINDOW # Hide window
            
        try:
            # Use pip freeze or list to check
            cmd = [str(python_path), "-m", "pip", "list", "--format=json"]
            result = subprocess.check_output(cmd, text=True, creationflags=0x08000000)
            installed = [p['name'].lower() for p in json.loads(result)]
            
            missing = [r for r in required if r not in installed]
            # Pillow is 'pillow' in pip list usually, but import is PIL
            # pywin32 might show as pywin32
            
            return {'missing': missing, 'valid': len(missing) == 0}
        except Exception as e:
            logger.error(f"Dependency check failed: {e}")
            return {'missing': ['Check Failed'], 'valid': False}
