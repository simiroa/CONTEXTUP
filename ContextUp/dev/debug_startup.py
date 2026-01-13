import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

try:
    print("Attempting to import wmi...")
    import wmi
    print("Success: wmi")
    
    print("Attempting to import win32api...")
    import win32api
    print("Success: win32api")

except ImportError as e:
    print(f"IMPORT ERROR: {e}")
    sys.exit(1)

try:
    print("Importing MonitorController...")
    # Adjust path for module import
    from features.tools.monitor_widget.monitor_controls import MonitorController
    print("Success. Initializing...")
    ctrl = MonitorController()
    print("Initialized successfully.")
except Exception as e:
    import traceback
    traceback.print_exc()
