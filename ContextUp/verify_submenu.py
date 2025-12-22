import winreg

def check_submenu_structure():
    """Verify that ContextUp submenu structure is correct"""
    
    targets = [
        ("Files", "Software\\Classes\\*\\shell\\ContextUp"),
        ("Folders", "Software\\Classes\\Directory\\shell\\ContextUp"),
        ("Background", "Software\\Classes\\Directory\\Background\\shell\\ContextUp")
    ]
    
    print("=== ContextUp Submenu Structure Check ===\n")
    
    for name, path in targets:
        print(f"[{name}] {path}")
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path) as key:
                # Check essential values
                try:
                    muiverb, _ = winreg.QueryValueEx(key, "MUIVerb")
                    print(f"  ✓ MUIVerb: {muiverb}")
                except:
                    print(f"  ✗ MUIVerb: MISSING")
                
                try:
                    subcommands, _ = winreg.QueryValueEx(key, "SubCommands")
                    print(f"  ✓ SubCommands: '{subcommands}'")
                except:
                    print(f"  ✗ SubCommands: MISSING (서브메뉴가 안보이는 원인!)")
                
                # Check shell subkey
                shell_path = f"{path}\\shell"
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, shell_path) as shell_key:
                        # Count sub-items
                        count = 0
                        while True:
                            try:
                                winreg.EnumKey(shell_key, count)
                                count += 1
                            except:
                                break
                        print(f"  ✓ Shell items: {count}")
                except:
                    print(f"  ✗ Shell subkey: MISSING")
                    
        except FileNotFoundError:
            print(f"  ✗ Key not found!")
        
        print()

if __name__ == "__main__":
    check_submenu_structure()
