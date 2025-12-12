# Installation Guide

## 🚀 Quick Start (Recommended)

**ContextUp** now features a unified, portable installation process.

1.  **Run Installer**:
    Double-click `install.bat`.
    *   It will download a portable version of Python 3.12.
    *   It will automatically install all dependencies (including AI libraries).
    *   It will register the Windows Context Menu.

2.  **Launch Manager**:
    After installation, `ContextUpManager.bat` will launch automatically.
    You can use this to check for updates or manage settings.

3.  **Verify**:
    Right-click any file or folder. You should see the **"ContextUp"** menu.

---

## 🛠️ Manual Installation (Developers)

If you prefer to set up manually or are developing:

1.  **Environment**:
    Ensure you have Python 3.12+ installed.
    
2.  **Dependencies**:
    ```powershell
    pip install -r requirements.txt
    ```

3.  **Register Menu**:
    ```powershell
    python manage.py register
    ```

## 📦 Portability & Moving

The entire `ContextUp` folder is portable. 
*   **To Move**: Simply move the folder to a new location (e.g., USB drive).
*   **To Re-activate**: Run `python manage.py register` in the new location to update registry paths.

## 🗑️ Uninstallation

To remove the context menu and clean up:

1.  Run `ContextUp_Uninstall.bat`.
2.  Select "Yes" to remove registry keys and the local python environment.

## ❓ Troubleshooting

*   **"Python not found"**: Ensure `install.bat` completed successfully and `tools/python` exists.
*   **Tray Icon not appearing**: Run `ContextUpManager.bat` manually and check the console for errors.

