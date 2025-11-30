import sys
from pathlib import Path
import time

try:
    import win32com.client
except ImportError:
    win32com = None

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
        
        # We need to find the active window.
        # This is tricky because "Active" might be the context menu host?
        # But usually the user just clicked, so the window is likely foreground or Z-ordered high.
        # However, we can iterate windows and check which one has focus?
        # Or just return selection from ALL windows? No, that's bad.
        
        # Heuristic: The window that contains the file passed as argument?
        # But we don't have the argument here easily unless passed.
        # Let's assume the user is interacting with the foreground window.
        
        # Better approach:
        # If we are launched via context menu, we usually get ONE file path as argument.
        # We can look for the window that contains this file.
        pass
        
    except Exception:
        return []
    return []

def get_selection_from_explorer(anchor_path: str):
    """
    Finds the Explorer window containing 'anchor_path' and returns all selected items in that window.
    If anchor_path is a directory, it might be the folder itself or a file inside.
    """
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
