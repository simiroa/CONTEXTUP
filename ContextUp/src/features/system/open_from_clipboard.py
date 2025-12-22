import os
import win32clipboard
from pathlib import Path

def open_path_from_clipboard():
    """
    Get path from clipboard and open it in Windows Explorer.
    Supports both file/folder copied from Explorer (CF_HDROP) 
    and path strings (CF_TEXT/CF_UNICODETEXT).
    """
    try:
        win32clipboard.OpenClipboard()
        try:
            target_path = None
            
            # 1. Try CF_HDROP (Files copied in Explorer)
            if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_HDROP):
                data = win32clipboard.GetClipboardData(win32clipboard.CF_HDROP)
                if data:
                    target_path = data[0] # Open first item
            
            # 2. Try Text (Path string)
            elif win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
                text = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
                if text and os.path.exists(text.strip().replace('"', '')):
                    target_path = text.strip().replace('"', '')
            
            elif win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_TEXT):
                text = win32clipboard.GetClipboardData(win32clipboard.CF_TEXT)
                if text:
                    try:
                        text_str = text.decode('utf-8').strip().replace('"', '')
                        if os.path.exists(text_str):
                            target_path = text_str
                    except:
                        pass
            
            if target_path:
                path = Path(target_path)
                # If it's a file, open its parent and select it
                if path.is_file():
                    os.system(f'explorer /select,"{path}"')
                else:
                    os.startfile(str(path))
                    
        finally:
            win32clipboard.CloseClipboard()
            
    except Exception as e:
        print(f"Failed to open path from clipboard: {e}")

if __name__ == "__main__":
    open_path_from_clipboard()
