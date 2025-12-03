# ContextUp Python Environment Guide

This document outlines the dual-Python architecture used in ContextUp and lists which features utilize which environment.

## Architecture Overview

ContextUp utilizes two distinct Python environments to balance system integration with feature portability.

### 1. System Python (External)
*   **Path**: `C:\Python314\python.exe` (or user's system python)
*   **Version**: Python 3.14.0 (Latest)
*   **Purpose**: Handles GUI applications (`tkinter` based) and system-level integrations.
*   **Why**: The embedded Python often lacks full `tkinter` support or specific system DLLs required for complex GUIs.

### 2. Embedded Python (Internal)
*   **Path**: `[ProjectRoot]\tools\python\python.exe`
*   **Version**: Python 3.12.9
*   **Purpose**: Runs portable, self-contained logic, AI models, and heavy dependencies.
*   **Why**: Ensures consistent behavior across different user machines regardless of their installed Python version. Supports libraries like `ctranslate2` that may not yet support 3.14.

---

## Feature Mapping

| Feature | Environment | Key Libraries | Notes |
| :--- | :--- | :--- | :--- |
| **Context Menu Manager** | System Python | `tkinter`, `customtkinter` | Main GUI for managing menu items. |
| **Real-time Translator** | Embedded Python | `ctranslate2`, `sentencepiece`, `deep-translator` | Uses embedded env for offline NLLB model support. |
| **Texture Tools (AI)** | Embedded Python | `google-genai`, `pillow`, `opencv-python` | Image processing and Gemini API calls. |
| **System Utilities** | Embedded Python | `pathlib`, `shutil` | File operations (Clean, Move, Rename). |
| **Mesh/CAD Converters** | Embedded Python | `open3d` (planned), `trimesh` | 3D file processing. |

---

## Managing the Embedded Environment

To install new packages into the embedded environment, use the `pip` executable located in `tools\python\Scripts` or run python with the `-m pip` module.

**Command Example:**
```powershell
# Install a package to embedded python
.\tools\python\python.exe -m pip install package_name
```

### Installed Essential Libraries
The following libraries are pre-installed in the embedded environment for offline capabilities:
*   **Translation**: `ctranslate2`, `sentencepiece`, `deep-translator` (Offline NLLB + Google).
*   **AI/Image**: `google-genai` (Gemini), `pillow`, `opencv-python`, `rembg` (Background Removal).
*   **Documents**: `PyPDF2` (Merge/Split), `pdf2image` (Preview).
*   **Media**: `pydub` (Audio), `yt-dlp` (Video Download).
*   **Utilities**: `send2trash` (Safe Delete), `watchdog` (Monitoring), `pyperclip` (Clipboard), `requests`, `beautifulsoup4`.
*   **Core**: `transformers`, `huggingface_hub`, `numpy`.
