# System Architecture

> **Last Updated:** 2025-12-22  
> **Structure:** Double-Packaging (ContextUp subfolder)

## Directory Structure

```
HG_context_v2/                    # Root (user-facing)
├── ContextUp/                    # Core Application
│   ├── src/
│   │   ├── core/                 # Core logic (menu, config, registry, paths)
│   │   ├── manager/              # Manager GUI
│   │   ├── features/             # Feature modules (categorized)
│   │   │   ├── audio/
│   │   │   ├── video/
│   │   │   ├── image/
│   │   │   ├── document/
│   │   │   ├── sequence/         # Sequence management tools
│   │   │   ├── mesh/             # 3D tools (Blender, Mayo, LOD)
│   │   │   ├── system/
│   │   │   ├── ai/               # AI tools (Ollama, Gemini, etc.)
│   │   │   ├── finder/           # Duplicate finder
│   │   │   ├── leave_manager/    # Leave Manager
│   │   │   ├── tools/            # AI Text Lab, Downloader
│   │   │   └── prompt_master/
│   │   ├── tray/                 # Tray agent & Quick Menu
│   │   ├── setup/                # Installation / Migration / Uninstallation
│   │   └── utils/                # Shared utilities (logger, gui_lib)
│   │
│   ├── config/                   # Static App Config (Git Managed)
│   │   ├── categories/           # Category & Feature JSON files (Flattened)
│   │   ├── install_tiers.json    # Installation tier definitions
│   │   ├── i18n/                 # Localization
│   │   └── ...
│   │
│   ├── userdata/                 # Dynamic User Data (Git Ignored)
│   │   ├── settings.json         # Global settings (Theme, Paths, API Keys)
│   │   ├── secrets.json          # Sensitive API Keys
│   │   ├── user_overrides.json   # Menu customizations
│   │   ├── gui_states.json       # GUI window states
│   │   ├── copy_my_info.json     # Personal info for clipboard tools
│   │   └── ...
│   │
│   ├── tools/                    # Python (Bundled 3.11), FFmpeg, Blender, ComfyUI
│   ├── resources/                # External resources
│   │   ├── ai_models/            # AI Models (Marigold, Rembg, Checkpoints)
│   │   ├── bin/                  # Binaries (Real-ESRGAN fallback, etc.)
│   ├── assets/                   # Icons & Media
│   ├── logs/                     # Runtime logs
│   └── dev/                      # Development (scripts, tests, docs)
│
├── README.md
├── install.bat                   # → Runs setup/install.py (Migration included)
├── manager.bat                   # → Runs manager/main.py
└── uninstall.bat                 # → Runs setup/uninstall.py (Registry cleanup)
```

## Entry Points

| File | Purpose |
|------|---------|
| `manager.bat` | Launch Manager GUI (Uses bundled Python) |
| `install.bat` | Run installation and migration of user data |
| `uninstall.bat` | Registry cleanup and optional file removal |
| Registry | `.../tools/python/python.exe .../src/core/menu.py <id> "%1"` |

## Key Modules

### Core (`src/core/`)
- `paths.py` - **Centralized Path Management**: All code uses this for absolute/relative paths.
- `menu.py` - Command dispatcher (context menu entry point).
- `config.py` - Loads `config/categories/*.json`.
- `registry.py` - Windows Registry operations.
- `user_overrides.py` - Manages user customizations in `userdata/user_overrides.json`.
- `settings.py` - Handles loading/saving of `userdata/settings.json`.

### Features (`src/features/`)

The following features are defined in `config/categories/*.json` and implemented in `src/features/`.

| Category | Key Features | Implementation |
| :--- | :--- | :--- |
| **AI** | RIFE(Interp), Whisper(Sub), ESRGAN(Upscale), RMBG(BG Remove), Marigold(PBR), OCR, Ollama/Gemini Refine | `ai/` |
| **3D / Mesh** | Auto LOD, CAD to OBJ, Mesh Convert, Remesh & Bake | `mesh/` |
| **Image** | Format Convert, Merge/Split EXR, Texture Packer ORM, PBR Utils, Image Compare | `image/` |
| **Video** | Format Convert, Extract Audio, Interpolate 30fps, Proxy, Remove Audio | `video/` |
| **Audio** | Format Convert, Extract BGM/Voice, Normalize | `audio/` |
| **Document** | PDF Merge/Split, Convert Docs (OCR/Docx/LLM) | `document/` |
| **Sequence** | Arrange Folder, Missing Frames, To Video, Analyze, Renumber | `sequence/` |
| **System** | Batch Rename, Unwrap Folder, Symlink, Reopen Recent, Move to Folder | `system/` |
| **Clipboard** | Paste to New Folder, Copy UNC Path, Save Clipboard Image | `system/`, `scripts/` |
| **Tools** | YouTube Downloader, AI Text Lab, Leave Manager | `tools/`, `leave_manager/` |
| **ComfyUI** | SeedVR2 Video Upscaler, Z Image Turbo, AI Audio Editor, Icon Gen | `comfyui/` |
| **Special** | Duplicate Finder, Gemini Prompt Master | `finder/`, `prompt_master/` |
| 🎨 AI | AI Text Lab(Gemini/Ollama), ESRGAN, PaddleOCR, ComfyUI Tools | `src/features/tools/ai_text_lab.py`, `src/features/ai/*`, `src/features/comfyui/*` |
| 🎞️ Sequence | Sequence Analyze, Missing Frames, Video Convert | `src/features/sequence/analyze.py`, `src/features/system/tools.py`, `src/features/video/convert.py` |
| 🛠️ Tools | YouTube Downloader, AI Text Lab, Leave Manager | `src/features/tools/downloader_gui.py`, `src/features/tools/ai_text_lab.py`, `src/features/leave_manager/gui.py` |
| 🎛️ Special | Manager, Global Finder | `src/manager/main.py`, `src/features/finder/*` |

### Data Management
All code MUST use `src/core/paths.py` constants for file access.
- **App Data**: `config/` (Static properties, git-tracked)
- **User Data**: `userdata/` (User properties, git-ignored, persistent through updates)

## Important Notes

1. **Working Directory**: All bat files `cd ContextUp` before running Python.
2. **Centralized Paths**: No hardcoded relative paths strings (like `../../config`) should be used; use `core.paths`.
3. **External Tools**: Managed via `PackageManager` and detected in `tools/` or system PATH.
