import json
import sys
import os
from pathlib import Path
import re

# Add src to path
sys.path.append(str(Path("src").resolve()))

def audit_menu():
    print("Starting Menu Audit...")
    
    # 1. Load Config
    try:
        with open("config/menu_config.json", "r", encoding="utf-8") as f:
            config_items = json.load(f)
    except Exception as e:
        print(f"[FATAL] Failed to load config: {e}")
        return

    config_ids = {item['id']: item for item in config_items if item.get('status') == 'COMPLETE' and item.get('enabled', True)}
    print(f"Loaded {len(config_ids)} active config items.")

    # 2. Parse Menu handlers (Static analysis to avoid running bad code)
    menu_path = Path("src/core/menu.py")
    if not menu_path.exists():
        print("[FATAL] src/core/menu.py not found.")
        return
        
    menu_content = menu_path.read_text(encoding="utf-8")
    
    # Extract the build_handler_map dictionary content
    # This is a bit rough, but safer than importing potentially broken code
    # We look for: "id": ...
    
    # Let's try to extract keys from the build_handler_map function
    handler_map_keys = []
    
    # Regex to find dictionary keys in python source
    # Matches: "some_id":
    matches = re.findall(r'"([^"]+)":', menu_content)
    # Filter out likely non-ID strings (common words, or part of other dicts if any)
    # We can check if these keys exist in our config_ids
    
    found_handlers = set()
    for m in matches:
        if m in config_ids:
            found_handlers.add(m)
            
    # Check for IDs in config that are NOT in menu.py
    missing_handlers = []
    for cid in config_ids:
        # Some items have a 'command' directly in config, so they don't need a handler
        if 'command' in config_ids[cid] and config_ids[cid]['command']:
            continue
            
        if cid not in found_handlers:
            # Double check if it's dynamic or handled generically?
            # For now, flag it.
            missing_handlers.append(cid)
            
    print("\n[Audit: Config IDs vs Handlers]")
    if missing_handlers:
        print(f"  [WARNING] The following IDs have NO handler in menu.py (and no custom command):")
        for mh in missing_handlers:
            print(f"    - {mh}")
    else:
        print("  [OK] All active config items have potential handlers.")

    # 3. Check for specific known file paths in menu.py
    # We want to see if the files referenced actually exist.
    # We'll regex for `src_dir / ...` or `scripts.<module>`
    
    print("\n[Audit: File Paths in menu.py]")
    
    # Find subprocess calls: src_dir / "scripts" / ...
    # Regex for: src_dir / "scripts" / "([^"]+)"
    script_refs = re.findall(r'src_dir / "scripts" / "([^"]+)"', menu_content)
    # Also nested: src_dir / "scripts" / "subdir" / "file.py"
    # The regex above splits by quotes.
    # Let's look for likely paths relative to src/scripts
    
    # Strategy: Find all strings ending in .py inside menu.py
    py_files = re.findall(r'"([^"]+\.py)"', menu_content)
    
    scripts_dir = Path("src/scripts")
    
    for pf in py_files:
        if pf == "menu.py": continue # ignore self
        
        # Check if it exists in scripts dir (recursively?)
        # Usually they are like "manager_gui.py" or "ai_standalone/gemini_img_tools.py"
        # Since menu.py constructs paths like `src_dir / "scripts" / ...`, the string might be just the filename.
        
        # Try direct match in src/scripts
        cand1 = scripts_dir / pf
        # Try recurisve match?
        
        found = False
        if cand1.exists():
            found = True
        else:
            # Check deeper
            for r, d, f in os.walk(scripts_dir):
                if pf in f:
                    found = True
                    break
        
        if not found:
             # It might be a false positive (just a string), but worth logging
             # Filter out common false positives if needed
             if pf not in ["setup.py"]:
                print(f"  [CHECK] Referenced script '{pf}' not found in simple check.")
                
    # 4. Check imports in menu.py (Lazy imports)
    # _lazy("scripts.gemini_image_tools", ...)
    print("\n[Audit: Lazy Import Modules]")
    lazy_imports = re.findall(r'_lazy\("([^"]+)"', menu_content)
    
    for mod_path in lazy_imports:
        # scripts.gemini_image_tools -> src/scripts/gemini_image_tools.py
        rel_path = mod_path.replace(".", "/") + ".py"
        full_path = Path("src") / rel_path
        
        if not full_path.exists():
            # Check if it's a directory (package)
            pkg_path = Path("src") / mod_path.replace(".", "/")
            if pkg_path.is_dir():
                pass # It's a package import
            else:
                 print(f"  [MISSING] Module '{mod_path}' -> {full_path} NOT FOUND")
        
    print("\nAudit Complete.")

if __name__ == "__main__":
    audit_menu()
