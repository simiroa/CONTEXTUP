import winreg

def check_registry():
    targets = ["Directory\\shell", "Directory\\Background\\shell", "*\\shell"]
    print("Checking Registry for ContextUp entries...")
    
    for target in targets:
        path = f"Software\\Classes\\{target}"
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path) as key:
                print(f"\n--- {target} ---")
                i = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        print(f"  [{subkey_name}]")
                        
                        # Check inside ContextUp
                        if subkey_name == "ContextUp":
                            sub_path = f"{path}\\ContextUp\\shell"
                            try:
                                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_path) as subkey:
                                    j = 0
                                    while True:
                                        try:
                                            item_name = winreg.EnumKey(subkey, j)
                                            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, f"{sub_path}\\{item_name}") as item_key:
                                                val, _ = winreg.QueryValueEx(item_key, "")
                                                print(f"    - {item_name} -> {val}")
                                            j += 1
                                        except OSError:
                                            break
                            except FileNotFoundError:
                                print("    (No shell subkey)")
                        
                        i += 1
                    except OSError:
                        break
        except FileNotFoundError:
            print(f"Path not found: {path}")

if __name__ == "__main__":
    check_registry()
