import sys
from pathlib import Path
import time
import json
import os

try:
    import win32com.client
except ImportError:
    win32com = None

def get_history_file():
    return Path(__file__).parent.parent / "history.json"

def save_history(path_str):
    """Save path to history.json"""
    try:
        p = Path(path_str).resolve()
        if p.is_file():
            p = p.parent
        
        history_file = get_history_file()
        history = []
        
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except:
                history = []
        
        # Add to top, remove duplicates
        str_p = str(p)
        if str_p in history:
            history.remove(str_p)
        history.insert(0, str_p)
        
        # Limit to 20
        history = history[:20]
        
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2)
            
    except Exception:
        pass

def get_selected_files():
    """
    Returns a list of Path objects representing the selected files in the active Explorer window.
    If no selection or error, returns empty list.
    """
    if not win32com:
        return []

    try:
        shell = win32com.client.Dispatch("Shell.Application")
        windows = shell.Windows()
        pass
        
    except Exception:
        return []
    return []

def get_selection_from_explorer(anchor_path: str):
    """
    Finds the Explorer window containing 'anchor_path' and returns all selected items in that window.
    If anchor_path is a directory, it might be the folder itself or a file inside.
    Also saves the accessed folder to history.
    """
    
    # Save history
    save_history(anchor_path)

    if not win32com:
        return [Path(anchor_path)]

    anchor = Path(anchor_path).resolve()
    # If anchor is a file, parent is the folder.
    # If anchor is a folder, it might be the folder open in Explorer OR a selected folder.
    
    # We want to find an Explorer window where:
    # 1. The LocationURL matches anchor's parent (if anchor is file)
    # 2. The LocationURL matches anchor (if anchor is folder and open)
    
    # Convert path to URL format for comparison (file:///C:/...)
    # Actually, LocationURL is usually URL encoded.
    
    selected_paths = []
    
    try:
        shell = win32com.client.Dispatch("Shell.Application")
        for window in shell.Windows():
            try:
                # window.LocationURL might be empty or fail
                doc = window.Document
                if not doc: continue
                
                folder_path = doc.Folder.Self.Path
                if not folder_path: continue
                
                folder_path = Path(folder_path).resolve()
                
                # Check if this window is relevant
                # Case 1: Anchor is a file in this folder
                # Case 2: Anchor is a folder in this folder (selected)
                # Case 3: Anchor IS this folder (background click)
                
                is_parent = False
                if anchor.parent == folder_path:
                    is_parent = True
                elif anchor == folder_path:
                    is_parent = True
                    
                if is_parent:
                    # Found the window! Get selection.
                    items = doc.SelectedItems()
                    if items.Count > 0:
                        for i in range(items.Count):
                            item_path = items.Item(i).Path
                            selected_paths.append(Path(item_path))
                        return selected_paths
                    else:
                        # No selection? Maybe background click.
                        # If background click, return just the folder?
                        # Or if anchor was passed, return anchor.
                        pass
            except Exception:
                continue
                
    except Exception:
        pass
        
    # Fallback: just return the anchor
    return [anchor]

def select_and_rename(path):
    """
    Selects the file in Explorer and triggers Rename (F2).
    """
    try:
        path = Path(path).resolve()
        if not path.exists(): return

        # 1. Open Explorer and select the file
        # 'explorer /select,"path"' usually activates the window if already open, or opens new.
        import subprocess
        subprocess.Popen(f'explorer /select,"{str(path)}"')
        
        # 2. Wait for window to focus
        time.sleep(0.5)
        
        # 3. Send F2
        if win32com:
            try:
                wscript = win32com.client.Dispatch("WScript.Shell")
                wscript.SendKeys("{F2}")
            except Exception as e:
                print(f"SendKeys failed: {e}")
                
    except Exception as e:
        print(f"select_and_rename failed: {e}")

