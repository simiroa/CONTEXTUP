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

    # Initialize COM safely
    try:
        import pythoncom
        pythoncom.CoInitialize()
    except: pass

    anchor = Path(anchor_path).resolve()
    # If anchor is a file, parent is the folder.
    # If anchor is a folder, it might be the folder open in Explorer OR a selected folder.
    
    selected_paths = []
    
    try:
        shell = win32com.client.Dispatch("Shell.Application")
        # Retry logic or robust loop
        windows = shell.Windows()
        for i in range(windows.Count):
            try:
                window = windows.Item(i)
                if not window: continue
                
                # window.LocationURL might be empty or fail
                doc = window.Document
                if not doc: continue
                
                folder = doc.Folder
                if not folder: continue
                
                folder_path = folder.Self.Path
                if not folder_path: continue
                
                folder_path_obj = Path(folder_path).resolve()
                folder_path_str = str(folder_path).lower().replace('/', '\\')
                
                # Check if this window is relevant
                # Match by path string to be robust
                anchor_parent_str = str(anchor.parent).lower().replace('/', '\\')
                anchor_str = str(anchor).lower().replace('/', '\\')
                
                is_match = False
                
                # Direct path match
                if anchor_parent_str == folder_path_str:
                    is_match = True
                elif anchor_str == folder_path_str:
                    is_match = True
                    
                # URL Match Fallback
                if not is_match:
                    try:
                        loc_url = window.LocationURL
                        if loc_url and loc_url.lower().startswith("file:///"):
                            from urllib.request import url2pathname
                            decoded_path = url2pathname(loc_url[8:])
                            decoded_path = decoded_path.replace('/', '\\').lower()
                            
                            # Check against anchor parent or anchor
                            # Decode might return c:\foo even if input was C:\Foo
                            if decoded_path == anchor_parent_str or decoded_path == anchor_str:
                                is_match = True
                    except: pass
                    
                if is_match:
                    # Found the window! Get selection.
                    items = doc.SelectedItems()
                    if items.Count > 0:
                        for i in range(items.Count):
                            item_path = items.Item(i).Path
                            selected_paths.append(Path(item_path))
                        return selected_paths
                    else:
                        # No selection? Maybe background click.
                        pass
            except Exception:
                continue
                
    except Exception:
        pass
        
    # Fallback: just return the anchor
    return [anchor]



def select_and_rename(path):
    """
    Selects the file in the *existing* Explorer window and triggers Rename (F2).
    Avoids opening a new window if possible.
    """
    try:
        path = Path(path).resolve()
        if not path.exists(): return

        # Fallback for systems without pywin32
        if not win32com:
            import subprocess
            subprocess.Popen(f'explorer /select,"{str(path)}"')
            return

        # Initialize COM (Critical for scripts running in separate processes)
        try:
            import pythoncom
            pythoncom.CoInitialize()
        except: pass

        shell = win32com.client.Dispatch("Shell.Application")
        parent_path = str(path.parent).lower().replace('/', '\\')
        
        target_window = None
        
        # 1. Find the window displaying the folder
        # We wrap iteration in try-except because shell.Windows() can be flaky
        try:
            windows = shell.Windows()
            for i in range(windows.Count):
                try:
                    window = windows.Item(i)
                    if not window: continue
                    
                    # Check URL/Path
                    doc = window.Document
                    if not doc: continue
                    folder = doc.Folder
                    if not folder: continue
                    
                    win_path = folder.Self.Path
                    if not win_path: continue
                    
                    win_path_str = str(win_path).lower().replace('/', '\\')
                    
                    # Try matching by Path OR LocationURL (file:///...)
                    matched = False
                    if win_path_str == parent_path:
                        matched = True
                    else:
                        try:
                            # Convert win_path to file URI for comparison if parent_path is distinct?
                            # Or check LocationURL from window
                            loc_url = window.LocationURL
                            if loc_url:
                                from urllib.request import url2pathname
                                # Remove file:/// prefix
                                if loc_url.lower().startswith("file:///"):
                                    decoded_path = url2pathname(loc_url[8:]) # 8 for file:///
                                    decoded_path = decoded_path.replace('/', '\\').lower()
                                    if decoded_path == parent_path:
                                        matched = True
                        except: pass
                        
                    if matched:
                        target_window = window
                        break
                except Exception:
                    continue
        except Exception:
            pass
            
        # 2. If found, select and F2
        if target_window:
            try:
                # Select the item
                folder_item = target_window.Document.Folder.ParseName(path.name)
                if folder_item:
                    # Select(item, flags): 1=Select, 4=Deselect others, 8=Ensure visible, 16=Focus
                    target_window.Document.SelectItem(folder_item, 1 | 4 | 8 | 16)
                    
                    # Trigger Rename via SendKeys
                    time.sleep(0.1)
                    wscript = win32com.client.Dispatch("WScript.Shell")
                    
                    try:
                        wscript.AppActivate(target_window.LocationName)
                    except: pass
                    
                    wscript.SendKeys("{F2}")
                    
            except Exception as e:
                print(f"Selection/Rename COM failed: {e}")
        else:
            # Window not found? Maybe closed? Open it cleanly.
            import subprocess
            subprocess.Popen(f'explorer /select,"{str(path)}"')
            
            # Try to catch the new window and triggered rename?
            # It takes time to open. We can try sleeping and sending F2 blindly to active window?
            # Risky, but better than nothing if user really wants valid rename.
            # But let's stick to just opening for now if finding failed.
            pass
    except Exception as e:
        print(f"select_and_rename failed: {e}")



