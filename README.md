### 🛠️ System Utilities
*   **Folder: Move to New...**: Moves selected files to a new folder. Handles naming collisions automatically.
*   **Folder: Remove Empty**: Recursively removes empty subdirectories within the selected folder.
*   **Folder: Arrange Sequences**: Groups file sequences (e.g., `shot.001.png`, `shot.002.png`) into separate folders based on their prefix.
*   **Folder: Find Missing Frames**: Scans image sequences for missing frame numbers and reports gaps.
*   **Clipboard: Save Image**: Saves the current image in the clipboard to a file.
*   **Clipboard: Analyze Image**: Uses Ollama (Vision) to describe the image currently in the clipboard.
*   **Clipboard: Analyze Error**: Uses an LLM to analyze error messages captured in the clipboard and suggest solutions.
*   **Manager GUI**: A central hub to manage settings, toggle features, check system health, and update the registry. Now supports **Category Management**, **Grouped Views**, and **System Python** integration.

### 🏷️ Rename Tools
*   **Batch Rename...**: A unified GUI for adding prefixes, suffixes, or removing text from filenames. Includes real-time preview.
*   **Renumber...**: A unified GUI for renumbering file sequences. Supports both "Selected Files" and "Folder" modes with collision detection.

### 📄 Document Tools
*   **Merge PDFs**: Merges multiple selected PDF files into a single document.
*   **Split PDF**: Splits a PDF into individual pages or converts pages to images.
*   **Analyze Document**: Uses Ollama to summarize or chat with the content of a PDF file.

### 🖼️ Image Tools
*   **Convert Format**: Batch converts images to PNG, JPG, WEBP, BMP, TGA, TIFF, or ICO. Supports progress tracking.
*   **Resize to POT**: Resizes images to the nearest Power-of-Two dimensions (e.g., 512x512, 1024x1024). Useful for game textures. Supports "Stretch" and "Canvas/Pad" modes.
*   **Remove EXIF**: Strips metadata (EXIF) from images for privacy.
*   **EXR Split/Merge**: Splits multi-layer EXR files into separate images or merges multiple images into a layered EXR.
*   **Remove Background (AI)**: Uses **RMBG-2.0** (via isolated AI environment) to instantly remove backgrounds.
*   **Upscale (AI)**: Uses **Real-ESRGAN** to upscale images (x4) with high fidelity.
*   **Generate Prompt**: Uses Ollama (Vision) to generate descriptive prompts from images.
*   **Generate Prompt**: Uses Ollama (Vision) to generate descriptive prompts from images.
*   **Texture Tools**: Generates PBR texture maps (Normal, Roughness, etc.) using **Marigold (Diffusion-based)**. High-quality estimation from single images. Supports ORM packing and DirectX/OpenGL normal maps.

### 🎥 Video Tools
*   **Convert / Proxy**: A unified GUI to convert videos (MP4, MOV, etc.) or create 1/2 resolution proxies for editing.
*   **Sequence to Video**: Converts an image sequence into a video file. Includes "Skip First Frame" option for Unreal Engine exports.
*   **Audio Studio**: A comprehensive GUI for all audio needs:
    *   **Converter**: Batch convert audio formats (MP3, WAV, FLAC, etc.).
    *   **AI Separator**: Isolate vocals and accompaniment using **Spleeter**.
    *   **Video Audio**: Extract or remove audio tracks from video files.
*   **Frame Interpolation (RIFE)**: Uses **RIFE (Real-Time Intermediate Flow Estimation)** to smooth videos by generating intermediate frames (e.g., 30fps -> 60fps).
*   **Generate Subtitles**: Uses **Faster-Whisper** to automatically generate `.srt` subtitles for videos.

### 🌐 System Tools
*   **Real-time Translator**: A minimalist, always-on-top translator (Google Translate) with Auto-Clipboard detection.
*   **Global Hotkeys**: Supports system-wide shortcuts (e.g., `Ctrl+Alt+V` to open folder from clipboard, `Ctrl+Shift+Alt+F1` for Manager). Configurable via Manager.

### 🧊 3D Tools
*   **Convert Mesh**: Converts 3D models between OBJ, FBX, GLTF, and PLY formats using Blender.
*   **Extract Textures**: Extracts embedded textures from 3D model files.
*   **Convert CAD**: Converts STEP/IGES CAD files to OBJ mesh format using Mayo. Includes "Open with Mayo" for direct viewing.
*   **Open with Mayo**: Directly opens supported 3D files (.step, .obj, etc.) in the Mayo viewer.

### 🛠️ Installation (v2.0 Hybrid Install)

ContextUp now uses a **Hybrid Environment Strategy** ensuring maximum stability and performance.

1.  **Download & Extract**:
    *   Download `ContextUp_Release.zip` and extract it to a folder (e.g., `C:\ContextUp`).
    *   *Tip: For offline installation, ensure `tools/python-3.11.9-amd64.exe` is present.*

2.  **Run Installer**:
    *   Double-click **`ContextUp_Install.bat`**.
    *   This will:
        *   Install a local **Embedded Python 3.11** (Core System).
        *   (Optional) Set up **AI Conda Environment**.
        *   Launch the **Manager**.

3.  **Register Menu**:
    *   In the Manager, click **"Register Menu"**.
    *   Right-click any file to see the new context menu!

4.  **Manage Updates**:
    *   Run `ContextUpManager.bat` anytime to update settings or check health.

---

## 🏗️ Technical Architecture

This project strictly prioritizes **Embedded Python** to ensure stability and portability:

1.  **Embedded Python (Primary)**:
    *   **ALL** features (GUI, System Tools, Media Processing) run in the local `tools/python` environment by default.
    *   This ensures the app works immediately after download, without relying on the user's system Python.
    *   **Automatic Installation**: If the embedded environment is missing, the setup script (`setup_all.py`) will automatically download and configure it.

2.  **AI Environment (Secondary/Isolated)**:
    *   Runs heavy AI workloads (PyTorch, CUDA) like Background Removal and Upscaling.
    *   Isolated to prevent dependency conflicts with the primary environment.
    *   Automatically activated only when needed via `src/utils/ai_runner.py`.

**Policy**: Embedded Python is the default. However, you can now configure the Manager to use your **System Python** via the **Settings** tab if you require specific system-installed libraries (e.g. for the Tray Agent).

For a detailed code map and file responsibilities, please refer to [**architecture.md**](architecture.md).

## 📚 Documentation

- **User Guide**:
    - [Features List](docs/user/FEATURES.md)
    - [Icon Reference](docs/user/ICONS.md)
    - [User Testing Guide](docs/user/USER_TESTING.md)

- **Installation**:
    - [Conda Environment Setup](docs/install/INSTALL_CONDA.md)
    - [Python Environment Guide](docs/install/PYTHON_ENV_GUIDE.md)

- **Development**:
    - [Contributing](docs/dev/CONTRIBUTING.md)
    - [Development Guide](docs/dev/DEVELOPMENT.md)
    - [GUI Guidelines](docs/dev/GUI_GUIDELINES.md)
    - [Embedded Python & Tkinter](docs/dev/EMBEDDED_PYTHON_TKINTER_GUIDE.md)

- **Support**:
    - [Troubleshooting & Crash Fixes](docs/troubleshooting/TROUBLESHOOTING.md)

## 🧭 Adding a New Menu Item (developer quick guide)
- Use the embedded Python (`tools/python/python.exe`) for any installs; avoid system Python.
- **Manager writes `config/menu_config.json` for you—follow the same fields when adding programmatically.
  > [!WARNING]
  > Do NOT edit `menu_config.json` directly. Edit `config/menu_categories/*.json` instead, then run `src/utils/config_builder.py`.
- Required per entry: `id` (unique, snake_case), `name` (UI label), `category` (must match CATEGORY_COLORS or “Custom”), `submenu` (`ContextUp`, `(Top Level)`, or custom), `command` (quote paths), `types` (e.g., `"*"` or `"image"`), `scope` (`file`, `folder`, or `both`), `enabled` (bool).
- Optional: `hotkey` (global), `icon` (e.g., `assets/icons/mytool.png`, 24–32px square PNG), `show_in_tray` (bool), `order` (int; Manager rebalances), `tags` (list), `description`.
- Flow to add safely: open Manager → Menu Editor → add item → pick category/submenu → set icon path → Apply Changes → right-click shell to verify. Use “Group by Category” / “Reset to Flat” to confirm ordering.
- Dependencies: import from `src/` using the embedded Python; if a new package is required, install via `tools/python/python.exe -m pip install <pkg>`. Add to `requirements.txt` only if it must be present at install time; otherwise install lazily inside the tool script.

## 🛡️ Safe Save Policy
To prevent accidental data loss, ContextUp tools now implement a **"Rename on Conflict"** policy.
- If a file (e.g., `image_removed.png`) already exists, the tool will automatically save the new file as `image_removed_01.png`, `image_removed_02.png`, etc.
- This ensures your previous work is never overwritten without explicit confirmation.

## 🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
