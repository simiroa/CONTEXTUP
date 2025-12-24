
<div align="center">

# ContextUp

**Windows Context Menu on Steroids. ⚡**

> "Why click 10 times when you can just Right-Click once?"

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6.svg)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)]()

[**🇰🇷 한국어 설명서 (Korean Manual)**](ContextUp/docs/user/README_KR.md) | [**✨ Full Feature List**](ContextUp/docs/user/FEATURES.md)

</div>

---

## 💡 What is ContextUp?

**ContextUp** is an all-in-one productivity suite that supercharges your Windows right-click menu.

It integrates powerful tools—from **AI-powered image upscaling** and **background removal** to **PDF conversion** and **smart renaming**—directly into your daily workflow.

Each feature is designed to be **Zero-Friction**:
*   No opening heavy apps.
*   No uploading files to sketchy websites.
*   Just **Right-Click** and go.

---

## 🚀 Key Features

### 🧠 AI Powerhouse
| Feature | Description | Engine |
| :--- | :--- | :--- |
| **AI Text Lab** | Refine, translate, and summarize text instantly. | **Gemini / Ollama** |
| **Background Removal** | Remove backgrounds from images with one click. | **Rembg (U2Net)** |
| **AI Upscale** | High-quality upscaling with ComfyUI support. | **RealESRGAN / ComfyUI** |
| **Marigold PBR** | Generate Normal & Depth maps from flat images. | **Marigold** |
| **Frame Interpolation** | Smoothen animations/videos (30fps -> 60fps). | **RIFE** |

### 🎨 Creative Tools
*   **ComfyUI Creative Studio**: Unified workspace for prompt layers, LoRA stacking, and advanced workflows.
*   **Format Conversion**: Supports **EXR, HDR, RAW, HEIC, WebP, DDS** and more.
*   **Sequence Tools**: Professional tools for **Render Sequences** (Arrange, Renumber, To Video, Analyze).
*   **Texture Packing**: Merge channels (ORM) or split EXR layers.
*   **Video Tools**: Convert to ProRes, extract audio stems (Vocals/Drums), generate subtitles.

### 💼 Productivity & System
*   **Quick Menu (`Ctrl+Shift+C`)**: A beautiful **Frosted Glass** overlay for quick actions.
*   **Duplicate Finder**: Smartly find and clean up duplicate files (Name, Size, Hash).
*   **Document Tools**: PDF Merge, Split, Convert to Markdown/Images.
*   **Smart Clipboard**: "Copy Path as Image", "Paste to New Folder", "Copy My Info".
*   **Batch Rename**: Powerful Regex-based bulk renaming.
*   **Quick Actions**: Clean empty folders, unwrap folders, create symlinks.

---

## 🛠️ Usage

### The Workflow
1.  **Right-Click** any file, folder, or background.
2.  Navigate to the **ContextUp** menu.
3.  Select your tool.

### System Tray Agent
The **ContextUp Agent** runs in the background to provide:
*   **Quick Menu (`Ctrl+Shift+C`)**: Access recently used folders and clipboard tools.
*   **Notification**: Status updates for background tasks (e.g., downloads, conversions).
*   **Management**: Open the main Manager / Config app.

---

## 📥 Installation

**Zero Config Required.** The installer handles everything, including an isolated Python environment.

1.  **Clone/Download** the repository.
2.  Double-click **`install.bat`** in the root folder.
3.  Follow the prompts.

> **Note**: The installation creates a self-contained environment in `ContextUp/tools/python`. It **does not** interfere with your system Python.

---

## 📚 Documentation

### For Users
*   [**Feature Manual**](ContextUp/docs/user/FEATURES.md): Detailed usage guide for every tool.
*   [**Installation Guide**](ContextUp/docs/user/INSTALL.md): Advanced setup options.
*   [**Troubleshooting**](ContextUp/docs/dev/TROUBLESHOOTING.md): Fix common issues.

### For Developers
*   [**Architecture**](ContextUp/architecture.md): System design overview.
*   [**Developer Guide**](ContextUp/docs/dev/DEVELOPMENT.md): How to add new features.
*   [**GUI Guidelines**](ContextUp/docs/dev/GUI_GUIDELINES.md): UX/UI standards.

---

## 🤝 Credits

ContextUp stands on the shoulders of giants. A huge thank you to the open-source community.

See [**CREDITS.md**](CREDITS.md) for the full list of libraries and projects used.

---

<div align="center">

**Made with 💻 and ☕ by Simiroa.**

</div>
