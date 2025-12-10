import time
import win32com.client
import pythoncom
import os
import urllib.parse
from pathlib import Path

def get_open_folders():
    paths = set()
    try:
        pythoncom.CoInitialize()
        shell = win32com.client.Dispatch("Shell.Application")
        windows = shell.Windows()
        
        for window in windows:
            try:
                location = window.LocationURL
                if location and location.startswith("file:///"):
                    path = urllib.parse.unquote(location[8:])
                    path = path.replace("/", "\\")
                    if os.path.isdir(path):
                        paths.add(path)
            except:
                pass
    except Exception as e:
        print(f"Error: {e}")
    finally:
        pythoncom.CoUninitialize()
    return paths

print("Tracking open folders for 10 seconds...")
print("Please open/close some folders now.")

previous = get_open_folders()
print(f"Initial: {previous}")

start = time.time()
while time.time() - start < 10:
    current = get_open_folders()
    
    # Check for new
    new_folders = current - previous
    if new_folders:
        print(f"[OPENED] {new_folders}")
        
    # Check for closed
    closed_folders = previous - current
    if closed_folders:
        print(f"[CLOSED] {closed_folders}")
        
    previous = current
    time.sleep(0.5)

print("Test complete.")
