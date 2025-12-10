# ContextUp

**ContextUp** is a powerful Windows Context Menu extension suite that boosts productivity by adding essential tools directly to your right-click menu.

It operates entirely on a **local Embedded Python** environment, ensuring zero conflict with your system settings and maximum portability.

---

## ✨ Features

### 🛠️ System & Management
*   **Copy My Info**: (New) Quickly copy personal snippets (Email, IP, Phone) via a cascading menu. Includes a modern GUI Manager.
*   **Manager GUI**: Central dashboard to toggle features, check updates, and manage the registry.
*   **Folder Tools**: "Move to New Folder", "Remove Empty Folders", "Arrange File Sequences".
*   **Global Hotkeys**: Custom keyboard shortcuts for system-wide actions.

### � Clipboard Tools
*   **Save Image**: Instantly save clipboard images to a file.
*   **Analyze Error**: (AI) Diagnose error messages in your clipboard.
*   **Open Path**: Open the folder path currently in your clipboard.

### 🖼️ Image & 3D
*   **Batch Convert**: Images to PNG, JPG, WEBP, ICO, etc.
*   **Resize**: Smart resizing (Power-of-Two, etc.) for game dev.
*   **Remove Background**: AI-powered background removal.
*   **Upscale**: AI Super-resolution.
*   **Texture Tools**: Generate PBR maps from images.
*   **3D Converters**: CAD (STEP/IGES) to OBJ, Mesh conversions.

### 🎥 Video & Audio
*   **Video Proxy**: Create lightweight proxy files for editing.
*   **Audio Studio**: Separate vocals (Spleeter), convert formats, extract audio.
*   **Subtitles**: Auto-generate .srt subtitles using Whisper.

### � Documents
*   **PDF Tools**: Merge, Split, and Analyze PDFs.
*   **Renaming**: Batch Rename and Renumbering tools with preview.

---

## � Installation

1.  **Download & Extract**:
    *   Unzip the release to a permanent location (e.g., `C:\ContextUp`).

2.  **Initialize**:
    *   Run **`ContextUp_Install.bat`**.
    *   This sets up the **local Embedded Python** environment automatically.

3.  **Activate**:
    *   The **ContextUp Manager** will launch.
    *   Click **"Register Menu"** to Add ContextUp to your right-click menu.

---

## ⚙️ Configuration

ContextUp uses a modular configuration system for easy customization.

*   **Menu Categories**: 
    *   Tools are defined in `config/menu_categories/*.json` (e.g., `image.json`, `system.json`).
    *   The system loads these files to build the context menu.
*   **Personal Data**:
    *   "Copy My Info" data is stored in `config/copy_my_info.json`.
    *   This file is local-only and not shared.

---

## 👨‍💻 Development Policies

### 1. Python Environment
*   **Strictly Embedded**: To ensure stability, this project uses **ONLY** the embedded Python located in `tools/python/`.
*   **No System Python**: Scripts should not rely on the user's installed Python. All dependencies must be installed into the embedded environment.

### 2. Adding New Tools
1.  **Create Script**: Write your Python script in `src/scripts/`.
2.  **Define Config**: Create or edit a JSON file in `config/menu_categories/`.
    ```json
    {
        "id": "my_tool_id",
        "name": "My New Tool",
        "category": "Custom",
        "submenu": "ContextUp",
        "command": "python src/scripts/my_tool.py",
        "scope": "file"
    }
    ```
3.  **Apply**: Open Manager and click **"Apply Menu Changes"**.

### 3. Icon Architecture
*   Place icons in `assets/icons/`.
*   Recommended format: `.ico` or `.png` (24x24 or 32x32).

---

## 📄 License
This project is licensed under the MIT License.
