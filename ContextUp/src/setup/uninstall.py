import sys
import os
import shutil
import logging
import winreg
from pathlib import Path

# Setup simple logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("uninstall")

ROOT_DIR = Path(__file__).parent.parent.parent
TOOLS_DIR = ROOT_DIR / "tools"

def run_registry_cleanup():
    """
    Removes all ContextUp registry entries using the proper RegistryManager logic.
    """
    print("--- Removing Registry Entries ---")
    
    try:
        # Try to use the proper RegistryManager
        sys.path.insert(0, str(ROOT_DIR / "src"))
        from core.config import MenuConfig
        from core.registry import RegistryManager
        
        config = MenuConfig()
        manager = RegistryManager(config)
        manager.unregister_all()
        print("Registry entries removed via RegistryManager.")
    except Exception as e:
        logger.warning(f"RegistryManager unavailable ({e}), using fallback cleanup...")
        _fallback_registry_cleanup()
    
    # Always clean up the CopyInfoMenu class
    _cleanup_copy_info_class()

def _fallback_registry_cleanup():
    """Fallback if RegistryManager is not available."""
    root_key = winreg.HKEY_CURRENT_USER
    base_path = "Software\\Classes"
    
    targets = [
        "*\\shell",
        "Directory\\shell",
        "Directory\\Background\\shell",
    ]
    
    legacy_keys = ["CreatorTools", "CreatorTools_v2", "ContextUp", "Sequence", "ComfyUI"]
    
    for target in targets:
        shell_path = f"{base_path}\\{target}"
        try:
            with winreg.OpenKey(root_key, shell_path, 0, winreg.KEY_ALL_ACCESS) as key:
                i = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        full_path = f"{shell_path}\\{subkey_name}"
                        
                        should_delete = subkey_name in legacy_keys
                        
                        # Check for ContextUpManaged marker
                        if not should_delete:
                            try:
                                with winreg.OpenKey(root_key, full_path) as sk:
                                    val, _ = winreg.QueryValueEx(sk, "ContextUpManaged")
                                    if val == "true":
                                        should_delete = True
                            except: pass
                        
                        if should_delete:
                            _delete_key_recursive(root_key, full_path)
                            i = 0  # Reset after deletion
                        else:
                            i += 1
                    except OSError:
                        break
        except FileNotFoundError:
            pass
        except Exception as e:
            logger.warning(f"Error cleaning {shell_path}: {e}")

def _cleanup_copy_info_class():
    """Remove the ContextUp.CopyInfoMenu class from registry."""
    class_path = "Software\\Classes\\ContextUp.CopyInfoMenu"
    try:
        _delete_key_recursive(winreg.HKEY_CURRENT_USER, class_path)
        print("Removed ContextUp.CopyInfoMenu class.")
    except:
        pass  # May not exist

def _delete_key_recursive(root, key_path):
    """Recursively delete a registry key and all its subkeys."""
    try:
        with winreg.OpenKey(root, key_path, 0, winreg.KEY_ALL_ACCESS) as key:
            while True:
                try:
                    subkey = winreg.EnumKey(key, 0)
                    _delete_key_recursive(root, f"{key_path}\\{subkey}")
                except OSError:
                    break
        winreg.DeleteKey(root, key_path)
        logger.info(f"Deleted: {key_path}")
    except FileNotFoundError:
        pass
    except Exception as e:
        logger.debug(f"Could not delete {key_path}: {e}")

def remove_temp_files():
    print("--- Removing Temporary Files ---")
    patterns = ["*.log", "*.pyc", "__pycache__"]
    
    count = 0
    for root, dirs, files in os.walk(ROOT_DIR):
        # Remove __pycache__ dirs
        if "__pycache__" in dirs:
            p = Path(root) / "__pycache__"
            try:
                shutil.rmtree(p)
                dirs.remove("__pycache__")
                count += 1
            except Exception as e:
                logger.warning(f"Failed to remove {p}: {e}")
                
    print(f"Cleaned {count} cache directories.")
    
    # Also clean .pyc and .log files
    f_count = 0
    for root, dirs, files in os.walk(ROOT_DIR):
        for file in files:
            if file.endswith(".pyc") or file.endswith(".log"):
                try:
                    os.remove(Path(root) / file)
                    f_count += 1
                except Exception:
                    pass
    print(f"Removed {f_count} temporary files (.pyc, .log).")

def is_junction(path):
    """
    Check if the path is a junction or symlink.
    """
    try:
        return os.path.islink(path)
    except:
        return False

def safe_remove_directory(path):
    """
    Safely remove a directory, handling junctions/symlinks by unlinking them
    instead of recursively deleting contents.
    """
    path_obj = Path(path)
    if not path_obj.exists():
        return

    if is_junction(path) or path_obj.is_symlink():
        try:
            # It's a link/junction, just remove the pointer
            os.remove(path) # For file symlinks
        except OSError:
            try:
                os.rmdir(path) # For directory junctions/symlinks on Windows
            except Exception as e:
                print(f"Failed to unlink {path}: {e}")
        print(f"Unlinked junction/symlink: {path}")
    else:
        # Standard directory, delete recursively
        try:
            shutil.rmtree(path)
            print(f"Deleted directory: {path}")
        except Exception as e:
            print(f"Failed to delete {path}: {e}")

def remove_external_tools():
    """Detailed prompt to remove individual heavy tools"""
    print("\n--- Removing External Tools ---")
    
    # Check for heavy folders
    targets = {
        "ComfyUI": TOOLS_DIR / "ComfyUI",
        "Blender": TOOLS_DIR / "blender",
        "FFmpeg": TOOLS_DIR / "ffmpeg",
        "Ollama Models": TOOLS_DIR / "ollama", 
    }
    
    found = {k: v for k, v in targets.items() if v.exists()}
    
    if not found:
        return

    print("Found external tools:")
    for name in found:
        print(f" - {name}")
        
    choice = input("Do you want to remove these external tools/models? (y/N): ").strip().lower()
    if choice == 'y':
        for name, path in found.items():
            print(f"Removing {name}...")
            safe_remove_directory(path)

def main():
    print("=== ContextUp Uninstaller ===")
    print("This will remove:")
    print("1. Context Menu Registry Entries")
    print("2. Temporary Cache Files")
    print("3. (Optional) External Tools")
    print("4. (In next step) Python Environment")
    
    confirm = input("Are you sure? (y/N): ").strip().lower()
    if confirm != 'y':
        print("Uninstall cancelled.")
        sys.exit(1) # Signal BAT to stop
        
    run_registry_cleanup()
    remove_temp_files()
    remove_external_tools()
    
    print("\nRegistry and Tools cleanup complete.")
    print("Proceeding to remove python environment...")

if __name__ == "__main__":
    main()
