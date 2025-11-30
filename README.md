# Creator Tools v2

**Creator Tools v2** is a powerful Windows Context Menu extension designed for content creators, developers, and power users. It integrates advanced AI features, system utilities, and media processing tools directly into your right-click menu, streamlining your workflow.

## 🚀 Getting Started

### Installation

1.  **Download**: Clone or download this repository to a permanent location (e.g., `C:\Tools\CreatorTools`).
2.  **Setup**: Run `INSTALL.bat` (or `python tools/setup_python.py`) to initialize the environment.
    *   This will set up the embedded Python environment and install necessary dependencies.
3.  **Register**: Run `manage.py register` (or use the **Manager GUI**) to add the tools to your Windows Context Menu.
    *   *Note: You may need to restart Explorer or sign out/in for changes to take effect.*

### Usage

1.  **Right-Click**: Select any file or folder in Windows Explorer.
2.  **Navigate**: Go to the **Creator Tools** menu item.
3.  **Select Tool**: Choose the desired tool from the categorized submenus (Image, Video, Audio, System, etc.).

### Configuration

*   **Manager Launcher**: Run `CreatorToolsManager.bat` in the project root to open the **Creator Tools Manager**.
*   **Context Menu**: You can also access "Open Creator Tools Manager" directly from the System submenu.
*   **Rename & Sort**: Use the Manager GUI to rename tools (click the ✎ icon). This allows you to customize the sort order in the context menu.

---

## ✨ Feature Specifications

### 🛠️ System Utilities
*   **Folder: Move to New...**: Moves selected files to a new folder. Handles naming collisions automatically.
*   **Folder: Remove Empty**: Recursively removes empty subdirectories within the selected folder.
*   **Folder: Arrange Sequences**: Groups file sequences (e.g., `shot.001.png`, `shot.002.png`) into separate folders based on their prefix.
*   **Folder: Find Missing Frames**: Scans image sequences for missing frame numbers and reports gaps.
*   **Clipboard: Save Image**: Saves the current image in the clipboard to a file.
*   **Clipboard: Analyze Image**: Uses Ollama (Vision) to describe the image currently in the clipboard.
*   **Clipboard: Analyze Error**: Uses an LLM to analyze error messages captured in the clipboard and suggest solutions.
*   **Manager GUI**: A central hub to manage settings, toggle features, check system health, and update the registry.

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
*   **Auto Tag Metadata**: Automatically generates and embeds metadata tags for images using AI.
*   **Texture Tools**: Generates PBR texture maps (Normal, Roughness, etc.) or weathering effects using Gemini API.

### 🎥 Video Tools
*   **Convert / Proxy**: A unified GUI to convert videos (MP4, MOV, etc.) or create 1/2 resolution proxies for editing.
*   **Sequence to Video**: Converts an image sequence into a video file. Includes "Skip First Frame" option for Unreal Engine exports.
*   **Audio Tools**: A unified GUI to extract audio, remove audio, or separate Voice/BGM using AI.
*   **Frame Interpolation**: Increases video frame rate using AI (RIFE) or simple frame blending.
*   **Generate Subtitles**: Uses **Faster-Whisper** to automatically generate `.srt` subtitles for videos.

### 🧊 3D Tools
*   **Convert Mesh**: Converts 3D models between OBJ, FBX, GLTF, and PLY formats using Blender.
*   **Extract Textures**: Extracts embedded textures from 3D model files.
*   **Convert CAD**: Converts STEP/IGES CAD files to OBJ mesh format using Mayo.

---

## 🏗️ Technical Architecture

This project uses a **Dual-Environment Architecture** to balance performance and compatibility:

1.  **System Environment (Python 3.14)**:
    *   Runs the core logic, GUI (Tkinter), system utilities, and standard media processing (FFmpeg, Pillow).
    *   Fast startup and low overhead.
2.  **AI Environment (Conda Python 3.10)**:
    *   Runs heavy AI workloads (PyTorch, CUDA) like Background Removal and Upscaling.
    *   Isolated to prevent dependency conflicts.
    *   Automatically activated only when needed via `src/utils/ai_runner.py`.

For a detailed code map and file responsibilities, please refer to [**architecture.md**](architecture.md).
