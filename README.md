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
*   **Generate Prompt**: Uses Ollama (Vision) to generate descriptive prompts from images.
*   **Texture Tools**: Generates PBR texture maps (Normal, Roughness, etc.) or weathering effects using **Gemini 2.5 Flash**. Supports dynamic model selection for Analysis (v2.5) vs Generation (v2.5-Image).

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
*   **Real-time Translator**: A minimalist, always-on-top translator (Google Translate) with Auto-Clipboard detection. Features a compact UI, opacity control, and click-to-copy workflow.

### 🧊 3D Tools
*   **Convert Mesh**: Converts 3D models between OBJ, FBX, GLTF, and PLY formats using Blender.
*   **Extract Textures**: Extracts embedded textures from 3D model files.
*   **Convert CAD**: Converts STEP/IGES CAD files to OBJ mesh format using Mayo. Includes "Open with Mayo" for direct viewing.
*   **Open with Mayo**: Directly opens supported 3D files (.step, .obj, etc.) in the Mayo viewer.

### 🛠️ Installation (v0.3.2 Minimal Install)

ContextUp now follows a **Minimal Install** policy. The initial download is lightweight, and heavy libraries (like PyTorch, FFmpeg) are installed on-demand via the Manager.

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/ContextUp.git
    cd ContextUp
    ```
2.  **Run Setup**:
    ```bash
    python setup_all.py
    ```
    This sets up the core Python environment and the Manager.
3.  **Register Menu**:
    Run `ContextUpManager.bat` and click **"Register Menu"**.
4.  **Install Features**:
    *   Open the Context Menu and click any feature (e.g., "Remove Background").
    *   If dependencies are missing, the **Smart Dependency Manager** will prompt you to install them automatically.
    *   You can also manage libraries in the **Manager > Updates & Health** tab.

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
    - [Troubleshooting](docs/troubleshooting/TROUBLESHOOTING.md)

## 🛡️ Safe Save Policy
To prevent accidental data loss, ContextUp tools now implement a **"Rename on Conflict"** policy.
- If a file (e.g., `image_removed.png`) already exists, the tool will automatically save the new file as `image_removed_01.png`, `image_removed_02.png`, etc.
- This ensures your previous work is never overwritten without explicit confirmation.

## 🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
