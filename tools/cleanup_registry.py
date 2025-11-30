import winreg
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cleanup")

def delete_key_recursive(root, key_path):
    try:
        with winreg.OpenKey(root, key_path, 0, winreg.KEY_ALL_ACCESS) as key:
            while True:
                try:
                    subkey = winreg.EnumKey(key, 0)
                    delete_key_recursive(root, f"{key_path}\\{subkey}")
                except OSError:
                    break
        winreg.DeleteKey(root, key_path)
        logger.info(f"Deleted {key_path}")
    except FileNotFoundError:
        pass
    except Exception as e:
        logger.warning(f"Failed to delete {key_path}: {e}")

def cleanup():
    root_key = winreg.HKEY_CURRENT_USER
    base_path = "Software\\Classes"
    
    targets = [
        "*\\shell",
        "Directory\\shell",
        "Directory\\Background\\shell",
        "Drive\\shell",
        "LibraryFolder\\shell"
    ]
    
    # Also check SystemFileAssociations
    try:
        with winreg.OpenKey(root_key, f"{base_path}\\SystemFileAssociations") as key:
            i = 0
            while True:
                try:
                    ext = winreg.EnumKey(key, i)
                    targets.append(f"SystemFileAssociations\\{ext}\\shell")
                    i += 1
                except OSError:
                    break
    except Exception:
        pass

    keys_to_remove = ["CreatorTools", "CreatorTools_v2"]
    
    logger.info("Starting cleanup...")
    
    for target in targets:
        for key_name in keys_to_remove:
            full_path = f"{base_path}\\{target}\\{key_name}"
            delete_key_recursive(root_key, full_path)
            
    # Search for "Hello GUI" explicitly in *
    # This is a bit more aggressive, scanning all shell keys?
    # Maybe just check *\\shell for any key that has "Hello GUI" as default value
    try:
        shell_path = f"{base_path}\\*\\shell"
        with winreg.OpenKey(root_key, shell_path) as key:
            i = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    # Check if this key looks suspicious
                    if "hello" in subkey_name.lower():
                        delete_key_recursive(root_key, f"{shell_path}\\{subkey_name}")
                    i += 1
                except OSError:
                    break
    except Exception:
        pass

    logger.info("Cleanup complete.")

if __name__ == "__main__":
    cleanup()
