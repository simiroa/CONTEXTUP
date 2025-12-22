import winreg
import logging
import argparse
import sys

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("cleanup")

def delete_key_recursive(root, key_path, dry_run=True):
    if dry_run:
        logger.info(f"[DRY-RUN] Will delete: {key_path}")
        return

    try:
        with winreg.OpenKey(root, key_path, 0, winreg.KEY_ALL_ACCESS) as key:
            while True:
                try:
                    subkey = winreg.EnumKey(key, 0)
                    delete_key_recursive(root, f"{key_path}\\{subkey}", dry_run=dry_run)
                except OSError:
                    break
        winreg.DeleteKey(root, key_path)
        logger.info(f"Deleted {key_path}")
    except FileNotFoundError:
        pass
    except Exception as e:
        logger.warning(f"Failed to delete {key_path}: {e}")

def cleanup(dry_run=True):
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

    # ONLY target specific application keys, NOT generic types like "Image" or "Video"
    keys_to_remove = [
        "CreatorTools", "CreatorTools_v2", "ContextUp"
    ]
    
    logger.info(f"Starting cleanup (Dry Run: {dry_run})...")
    
    for target in targets:
        # 1. Remove explicit keys (Legacy & Current App Names)
        for key_name in keys_to_remove:
            full_path = f"{base_path}\\{target}\\{key_name}"
            # Verify it exists before trying
            try:
                with winreg.OpenKey(root_key, full_path):
                    delete_key_recursive(root_key, full_path, dry_run=dry_run)
            except OSError:
                pass
        
        # 2. Scan for ContextUpManaged marker in ANY key
        shell_path = f"{base_path}\\{target}"
        try:
            with winreg.OpenKey(root_key, shell_path, 0, winreg.KEY_READ) as key:
                i = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        full_subkey = f"{shell_path}\\{subkey_name}"
                        
                        # Check for ContextUpManaged marker
                        should_delete = False
                        try:
                            with winreg.OpenKey(root_key, full_subkey) as sk:
                                val, _ = winreg.QueryValueEx(sk, "ContextUpManaged")
                                if str(val).lower() == "true":
                                    should_delete = True
                        except OSError:
                            pass
                        
                        if should_delete:
                            delete_key_recursive(root_key, full_subkey, dry_run=dry_run)
                            # When modifying the list while iterating, we need to be careful.
                            # EnumKey index relies on the current state.
                            # If we deleted it, the next key shifts to index 0 (or current index).
                            # Since recursive delete handles subkeys, but here we are iterating 'shell' children.
                            if not dry_run:
                                # Start over or decrement?
                                # Ideally, restart scan or just accept we might miss one until next run.
                                # Safe way: just increment per usual, but reset index if successful delete?
                                # Actually, deleting a key changes indices of subsequent keys.
                                # Simplest approach: Reset i = 0 after delete.
                                i = 0 
                                continue 
                        
                        i += 1
                    except OSError:
                        break
        except Exception:
            pass
            
    # Search for "Hello GUI" explicit legacy cleanup
    # Only if it strictly matches our legacy pattern to avoid false positives
    try:
        shell_path = f"{base_path}\\*\\shell"
        with winreg.OpenKey(root_key, shell_path) as key:
            i = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    if subkey_name.lower().startswith("contextup_hello"): # strict check
                         delete_key_recursive(root_key, f"{shell_path}\\{subkey_name}", dry_run=dry_run)
                         if not dry_run:
                             i = 0
                             continue
                    i += 1
                except OSError:
                    break
    except Exception:
        pass

    # Clean up ContextUp.CopyInfoMenu class
    copy_info_class = f"{base_path}\\ContextUp.CopyInfoMenu"
    try:
         with winreg.OpenKey(root_key, copy_info_class):
            delete_key_recursive(root_key, copy_info_class, dry_run=dry_run)
    except OSError:
        pass

    logger.info("Cleanup complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean up ContextUp registry keys.")
    parser.add_argument("--confirm", action="store_true", help="Actually delete keys (disable dry-run)")
    args = parser.parse_args()
    
    # Default is dry-run, strictly require --confirm
    cleanup(dry_run=not args.confirm)

