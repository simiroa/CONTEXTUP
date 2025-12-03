# Enabling Tkinter in Embedded Python

The "Embedded Python" distribution used in ContextUp (`tools\python`) is a minimal version of Python that **does not include Tkinter** (the standard GUI library) by default. This is why the "Real-time Translator" GUI cannot run directly in the embedded environment without manual modification.

If you wish to run GUI tools using the embedded Python (e.g., for full offline portability), you must manually add the Tkinter files.

## Prerequisites
1.  **Download Python 3.12.9 Windows Installer**:
    *   Go to [Python.org Downloads](https://www.python.org/downloads/release/python-3129/)
    *   Download the **Windows installer (64-bit)**.
2.  **Install or Extract**:
    *   Install it to a temporary location (e.g., `C:\Temp\Python312`) OR use 7-Zip to extract the installer contents if you don't want to install it.

## Steps to Copy Files

You need to copy specific files from the **Standard Python 3.12** installation to your **ContextUp Embedded Python** folder (`tools\python`).

### 1. Copy DLLs
From `C:\Temp\Python312\DLLs` (or extracted folder), copy the following files to `ContextUp\tools\python`:
*   `_tkinter.pyd`
*   `tcl86t.dll`
*   `tk86t.dll`
*   `zlib1.dll` (Critical dependency)

### 2. Copy Lib Files
From `C:\Temp\Python312\Lib`, copy the following **folders** to `ContextUp\tools\python\Lib`:
*   `tkinter` (Folder)
*   `tcl8.6` (Folder - *Note: In standard python this is in `tcl` folder usually, check `tcl/tcl8.6`*)
    *   *Correction*: In standard Windows install, `tcl` folder is at root `C:\Temp\Python312\tcl`.
    *   Copy the **entire `tcl` folder** from `C:\Temp\Python312` to `ContextUp\tools\python`.

### 3. Configure Path
The embedded python needs to know where to find the Tcl/Tk libraries.
1.  Open `ContextUp\tools\python\python312._pth` in a text editor.
2.  Uncomment `import site` (remove the `#`).
3.  Add the path to the `tcl` folder if necessary, but usually `import site` handles it if the structure matches.

**Recommended Structure in `tools\python`:**
```
tools\python\
  ├── python.exe
  ├── _tkinter.pyd
  ├── tcl86t.dll
  ├── tk86t.dll
  ├── Lib\
  │   └── tkinter\
  └── tcl\
      ├── tcl8.6\
      └── tk8.6\
```

## Verification
Run the following command in `ContextUp` root:
```powershell
.\tools\python\python.exe -c "import tkinter; tkinter._test()"
```
If a small window appears, Tkinter is successfully installed.

---

## Alternative: Use System Python (Current Solution)
Currently, ContextUp is configured to use your **System Python (3.14)** for the GUI, which already has Tkinter. This is the easiest solution if you don't need strict portability.
