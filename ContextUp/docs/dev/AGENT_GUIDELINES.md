# Agent Guidelines & Constraints

> [!IMPORTANT]
> This document serves as the **Constitution** for any AI Agent working on the ContextUp project.
> Violating these rules will result in broken installations, corrupted registries, and unhappy users.

---

## 🚫 Strict Prohibitions (The "Thou Shalt Not"s)

### 1. Python Environment
*   **NEVER use the system Python.**
*   **NEVER create a new venv or conda environment.**
*   **ALWAYS** use the embedded Python environment located at:
    *   `ContextUp/tools/python/python.exe`
*   **Reason**: The project relies on a strictly isolated, portable Python build (IndyGreg's Standalone) to ensure it works on any user's machine without pre-requisites.

### 2. File Structure & Paths
*   **NEVER hardcode absolute paths** (e.g., `C:\Users\...`).
*   **ALWAYS** use relative paths derived from `pathlib.Path(__file__)`.
*   **NEVER** modify the project root structure without explicit user approval.
    *   Root must only contain: `install.bat`, `manager.bat`, `uninstall.bat`, `README.md`, `ContextUp/`, `tools/`.

### 3. Configuration
*   **NEVER modify `config/menu_config.json` directly.**
    *   This file is generated.
*   **ALWAYS** edit the specific category file in `config/menu/categories/` (e.g., `image.json`, `ai.json`).

### 4. External Binaries
*   **NEVER** ask the user to download FFmpeg or other tools manually and put them in `C:\`.
*   **ALWAYS** expect and place binaries in `ContextUp/resources/bin/`.

---

## ✅ Development Best Practices

### 1. Feature Implementation
*   **Imports**: Use lazy loading (`import` inside functions) for heavy libraries (torch, pandas, pillow) to keep the Context Menu snappy.
*   **Batch Processing**: Handle multiple files correctly using the `batch_runner` pattern (Mutex + Single GUI).
*   **GUI**: Use `customtkinter` for consistency.

### 2. Documentation
*   If you add a feature, you MUST update:
    1.  `ContextUp/docs/user/FEATURES.md`
    2.  `ContextUp/docs/user/README_KR.md` (if applicable)

### 3. Testing
*   Before marking a task as done, verify:
    1.  Does `manager.bat` launch?
    2.  Does the new feature crash correctly (check `logs/debug.log`)?
