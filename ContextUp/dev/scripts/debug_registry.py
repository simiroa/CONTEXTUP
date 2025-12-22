import winreg
import sys

def scan_registry():
    roots = [
        "Software\\Classes\\*\\shell\\ContextUp\\shell",
        "Software\\Classes\\Directory\\shell\\ContextUp\\shell",
        "Software\\Classes\\Directory\\Background\\shell\\ContextUp\\shell"
    ]
    
    found_any = False
    
    for root in roots:
        print(f"Scanning {root}...")
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, root) as key:
                i = 0
                while True:
                    try:
                        name = winreg.EnumKey(key, i)
                        if "copy_my_info" in name.lower() or "clipboard_copy_info" in name.lower():
                            print(f"  Found 'Copy My Info' key: {name}")
                            # Check SubCommands
                            sub_path = f"{root}\\{name}"
                            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_path) as subkey:
                                try:
                                    val, _ = winreg.QueryValueEx(subkey, "SubCommands")
                                    print(f"    SubCommands: '{val}'")
                                except:
                                    print("    SubCommands: (missing)")
                                    
                                # Check for interfering command key
                                try:
                                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, f"{sub_path}\\command") as cmd_key:
                                        print("    [WARNING] 'command' subkey EXISTS! This might block SubCommands.")
                                except:
                                    print("    'command' subkey: (clean)")
                            
                            # Check shell children
                            shell_path = f"{sub_path}\\shell"
                            print(f"    Scanning children in {shell_path}...")
                            try:
                                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, shell_path) as shell_key:
                                    j = 0
                                    child_count = 0
                                    while True:
                                        try:
                                            child = winreg.EnumKey(shell_key, j)
                                            print(f"      - {child}")
                                            child_count += 1
                                            j += 1
                                        except OSError: break
                                    print(f"    Total children: {child_count}")
                            except Exception as e:
                                print(f"    Failed to open shell key: {e}")
                                
                            found_any = True
                        i += 1
                    except OSError: break
        except Exception as e:
            print(f"  Root not found or error: {e}")
            
    if not found_any:
        print("Copy My Info key not found in expected locations.")

if __name__ == "__main__":
    scan_registry()
