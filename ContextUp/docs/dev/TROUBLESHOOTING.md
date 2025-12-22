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
See [INSTALL.md](../user/INSTALL.md) for dependency checking steps.

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
## Installation Issues

### Python Not Found
**Symptoms**: `install.bat` fails immediately.
**Fix**:
1. Ensure the `tools/python` folder was created.
2. If not, run `src/setup/install.py` manually with a system Python (3.10+) to bootstrap the embedded environment.

### Module ImportError
**Symptoms**: `ModuleNotFoundError` during usage.
**Fix**:
```bash
.\tools\python\python.exe -m pip install [package_name]
```

### GPU Acceleration Failed
**Symptoms**: processing is slow or `torch.cuda.is_available()` returns False.
**Fix**:
1. Check CUDA version (requires CUDA 12.1 compatible driver).
2. Reinstall PyTorch:
   ```bash
   .\tools\python\python.exe -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121 --force-reinstall
   ```

## Feature GUI Not Opening

### Symptoms
- Right-click context menu feature shows error or nothing happens.
- `ModuleNotFoundError: No module named 'utils'` in console.

### Cause
The `sys.path` configuration in feature GUI files was incorrectly pointing to `features/` instead of `src/`.

### Fix (Already Applied)
All files in `src/features/*/` should have:
```python
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent  # features/[category] -> src
sys.path.append(str(src_dir))
```

If you encounter this issue, verify the path calculation in the affected file and ensure it points to the `src/` directory.
