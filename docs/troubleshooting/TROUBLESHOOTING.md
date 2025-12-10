# Troubleshooting Guide

## Manager GUI Won't Start

### Symptoms
- Double-clicking the script/EXE does nothing.
- Console window opens and closes immediately.

### Diagnosis
1. **Check Logs**:
   Look at `crash_log.txt` in the root folder. It captures the exact error (traceback) when the application crashes.

2. **Common Errors**:
   - `ModuleNotFoundError: No module named ...`
     - **Cause**: Missing Python file or `__init__.py`.
     - **Fix**: Ensure all subdirectories in `src/manager` have an `__init__.py` file.
   - `ImportError: cannot import name ...`
     - **Cause**: Circular imports or the function doesn't exist in the target file.
     - **Fix**: Check `src/manager/core/settings.py` (or similar) exists and contains the required functions.

### How to Debug Manually
Open a command prompt or PowerShell in the project folder and run:
```powershell
python src/manager/main.py
```
This will print the error message directly to the console so you can read it.

## Tray Agent Not Appearing
See [INSTALL.md](INSTALL.md) for dependency checking steps.

## Tray Agent Debugging (Dev Notes)

### Common Issues & Fixes
1.  **Restart Crash / Silent Exit**:
    *   **Cause**: `subprocess.check_output('tasklist')` hangs in some environments.
    *   **Fix**: Removed tasklist fallback. Now relies on **PID File** + **Handshake**.
    *   **Verify**: Run `reprod_restart.py` to test the Stop->Start cycle.

2.  **Manager Won't Open from Tray**:
    *   **Cause**: `pythonw.exe` missing or behaving erratically in embedded environment.
    *   **Fix**: Switched to `python.exe` with `CREATE_NO_WINDOW` flag.
    *   **Code**: `open_manager()` in `tray_agent.py`.

3.  **"Address already in use"**:
    *   **Cause**: Fixed port 54321 collision during rapid restart.
    *   **Fix**: Manager now assigns a **Dynamic Port** at launch. Check `logs/tray_info.json` to see the current port.
