<div align="center">

# ContextUp

**Windows Context Menu on Steroids ⚡**

> "Why click 10 times when you can just Right-Click once?"

[![Version](https://img.shields.io/badge/version-4.0.1-green.svg)](CHANGELOG.md)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey.svg)

[**✨ Full Feature List**](ContextUp/docs/user/FEATURES.md) | [**🇰🇷 한국어 설명서 (Korean Manual)**](README.md)

<br>

**ContextUp** is an all-in-one productivity suite that turns your Windows right-click menu into a productivity hub.

> **💡 From daily repetitive tasks to advanced open-source AI features.**
> <br>Solve it instantly with a single Right-Click, without opening heavy software.

Currently in **Test Version (v4.0.1)**.<br>
We are continuously updating with new features and external tool integrations. Feedback is welcome.

<br>

> Check [Changelog](CHANGELOG.md) for updates.

</div>

---

## Key Features

| Category | Example Features |
|----------|-----------|
| **AI** | Remove Background, Upscale (ComfyUI compatible), PBR Generation, Subtitles, AI Text Lab (Gemini/Ollama), **Creative Studio (Z/Advanced)** |
| **Image** | Format Convert (DDS/EXR/WebP etc.), EXR Merge/Split, Texture Packer, Power of 2 Resize |
| **Sequence** | Render Sequence Sorting, Missing Frame Detection, Video Conversion, Analysis & Renumbering |
| **Video** | ProRes Convert, Proxy Generation, Frame Interpolation (RIFE), YouTube Downloader |
| **Audio** | Format Convert, Vocal/Stem Separation, Volume Normalization |
| **3D** | Auto LOD, CAD→OBJ, Mesh Convert, Texture Extraction, Blender Link |
| **System** | Batch Rename, Copy My Info, Copy UNC Path, Symlink, Search Files |

---

## 🚀 Installation

### Requirements

| Item | Requirement |
|------|------|
| **OS** | Windows 10/11 (64-bit) |
| **Python** | 3.9 ~ 3.12 (For running install script) |
| **Disk** | Min 2GB (5GB+ with AI models) |

> After installation, it uses an embedded Python 3.11 in `tools/python/`, completely isolated from your system environment.

### 1. Download (Get Code)

**Option A: Git Clone (Recommended)**
```bash
git clone https://github.com/simiroa/ContextUp.git
cd ContextUp
```

**Option B: Download ZIP**
1. Click `Code` button -> `Download ZIP`
2. Extract and move to the folder.

---

### 2. Setup & Migration

Double-click **`install.bat`** in the root directory.<br>
For existing users, configuration files will be automatically migrated to the `userdata/` folder.

> Or run via terminal:
```bash
python ContextUp/src/setup/install.py
```

### 3. Menu Manager

Once installed, use the Manager GUI to register/unregister the menu from the registry.

**Run Manager:**
Execute `manager.bat` in the root folder.

**Key Features:**
- **Refresh Menu**: Re-register menus checking current config and dependencies.
- **Item Editor**: Toggle visibility, change order, or edit icons for each feature.
- **Dependency Scan**: Check if required external tools are installed at a glance.
- **Change Tier**: Adjust the scope of features (Minimal / Standard / Full).

### Core Interfaces (Context / Tray / Quick Menu)

- **Unified Control**: Access features via Right-Click Menu, System Tray, or Quick Menu.
- **Tray/Quick Menu Config**: Control activation via `user_overrides.json` or Manager.
- **Tray Agent**: Runs in the background to manage tasks and provide quick access.
- **Reload**: Click **Reload** in the Tray menu to apply setting changes instantly.

### 4. CLI (Command Line Interface)

You can also manage via command line:
```bash
# Register Menu
ContextUp\tools\python\python.exe ContextUp\manage.py register
# Unregister Menu
ContextUp\tools\python\python.exe ContextUp\manage.py unregister
```

---

## Uninstallation

```bash
# Unregister Menu
python ContextUp/manage.py unregister

# (Optional) Delete installed tools
ContextUp\tools\python\python.exe ContextUp\src\setup\uninstall.py
```

---

## 🔧 External Tools

Some advanced features use external tools that need separate installation.
Place them in `ContextUp/tools/` and they will be auto-detected.

> **💡 Tip**: Use Symbolic Links for large tools (Blender, ComfyUI).

| Tool | Usage | Recommended Setup |
|------|------|----------|
| **FFmpeg** | Video/Audio Convert | **Auto-installed** (or [Download](https://ffmpeg.org/download.html)) |
| **Real-ESRGAN** | AI Image Upscale | **Auto-installed** (or [Download](https://github.com/xinntao/Real-ESRGAN/releases)) |
| **Blender** | 3D Mesh Convert, LOD | Link existing path (or [Download](https://www.blender.org/download/)) |
| **ComfyUI** | AI Upscale/Gen | Link existing path (or [Download](https://github.com/comfyanonymous/ComfyUI)) |
| **Mayo** | CAD Viewer (STEP/IGES) | [Download](https://github.com/fougue/mayo/releases) and link |

### Install Path Structure

```
ContextUp/tools/
├─ ffmpeg/         # ffmpeg.exe, ffprobe.exe
├─ blender/        # blender-x.x.x-windows-x64/
├─ Mayo/           # mayo.exe
├─ realesrgan/     # realesrgan-ncnn-vulkan.exe
└─ ComfyUI/        # (Symbolic Link Recommended)
```

> **⚠️ Note**: Menu items requiring missing tools will be disabled.

---

## Shortcuts

| Shortcut | Action |
|--------|------|
| `Ctrl+Shift+C` | Open Quick Menu |
| `Ctrl+Alt+V` | Open Clipboard Path |
| `Ctrl+Alt+Shift+F1` | Open Manager |

---

## 📂 Folder Structure

```
[Root]/
├─ install.bat          # Install & Migration
├─ manager.bat          # Run Manager
├─ uninstall.bat        # Uninstaller
└─ ContextUp/
   ├─ src/              # Source Code (Core, Features, Manager, Tray)
   ├─ config/           # Default App Config (Git tracked)
   │  └─ categories/    # Menu Category Config
   ├─ userdata/         # User Settings & Secrets (Git ignored)
   │  ├─ secrets.json   # API Keys
   │  ├─ user_overrides.json # Custom Menu Overrides
   │  ├─ gui_states.json # GUI State Save
   │  ├─ download_history.json # Download logs
   │  └─ copy_my_info.json # Personal Info Template
   ├─ tools/            # Embedded Python & External Tools
   ├─ resources/        # AI Models & Resources
   └─ manage.py         # Server/Registry CLI
```

---

## Credits

ContextUp stands on the shoulders of giants. A huge thank you to the open-source community.

See [**CREDITS.md**](CREDITS.md) for the full list.
