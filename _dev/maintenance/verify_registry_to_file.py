import winreg
import sys

def check_registry():
    output = []
    output.append("Checking Registry for 'tool_translator'...")
    
    roots = [
        ("File (*)", r"Software\Classes\*\shell\ContextUp"),
        ("Folder (Directory)", r"Software\Classes\Directory\shell\ContextUp"),
        ("Background", r"Software\Classes\Directory\Background\shell\ContextUp")
    ]
    
    for label, root_path in roots:
        output.append(f"\n--- Scanning {label} ---")
        try:
            # Check Parent First
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, root_path) as key:
                output.append(f"  [OK] Submenu Key exists: {root_path}")
                try:
                    val, _ = winreg.QueryValueEx(key, "AppliesTo")
                    output.append(f"  [INFO] Submenu AppliesTo: {val}")
                except:
                    output.append(f"  [INFO] Submenu AppliesTo: (None)")
                
                # Check Shell Subkey
                shell_path = f"{root_path}\\shell"
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, shell_path) as shell_key:
                         i = 0
                         found_in_root = False
                         while True:
                            try:
                                subkey_cmd = winreg.EnumKey(shell_key, i)
                                if "tool_translator" in subkey_cmd:
                                    output.append(f"  [FOUND] Item: {subkey_cmd}")
                                    found_in_root = True
                                    
                                    # Check Item AppliesTo
                                    item_path = f"{shell_path}\\{subkey_cmd}"
                                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, item_path) as k:
                                        try:
                                            val, _ = winreg.QueryValueEx(k, "AppliesTo")
                                            output.append(f"    Item AppliesTo: {val}")
                                        except:
                                            output.append(f"    Item AppliesTo: (None)")
                                i += 1
                            except OSError:
                                break
                         
                         if not found_in_root:
                             output.append("  [MISSING] Item not found in this scope.")
                except FileNotFoundError:
                    output.append(f"  [MISSING] 'shell' subkey not found in {root_path}")

        except FileNotFoundError:
            output.append(f"  [MISSING] Submenu Key not found: {root_path}")
        except Exception as e:
            output.append(f"  [ERROR] {e}")

    with open("registry_report.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output))

if __name__ == "__main__":
    check_registry()
