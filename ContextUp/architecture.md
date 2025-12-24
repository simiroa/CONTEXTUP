# System Architecture

> **Last Updated:** 2025-12-23  
> **Structure:** Double-Packaging (ContextUp subfolder)

## Directory Structure

```
HG_context_v2/                    # Root (user-facing)
|-- ContextUp/                    # Core Application
|   |-- src/
|   |   |-- core/                 # Core logic (menu, config, registry, paths)
|   |   |-- manager/              # Manager GUI
|   |   |-- features/             # Feature modules (categorized)
|   |   |   |-- ai/
|   |   |   |-- audio/
|   |   |   |-- comfyui/
|   |   |   |-- document/
|   |   |   |-- finder/
|   |   |   |-- image/
|   |   |   |-- leave_manager/
|   |   |   |-- mesh/
|   |   |   |-- prompt_master/
|   |   |   |-- sequence/
|   |   |   |-- system/
|   |   |   `-- video/
|   |   |-- scripts/              # CLI/utility scripts
|   |   |-- setup/                # Installation / Migration / Uninstallation
|   |   |-- tray/                 # Tray agent & Quick Menu
|   |   `-- utils/                # Shared utilities (logger, gui_lib)
|   |
|   |-- config/                   # Static app config (git managed)
|   |   |-- categories/           # Category & Feature JSON files (Flattened)
|   |   |-- presets/              # ComfyUI UI presets and mappings
|   |   `-- runtime/              # Legacy runtime files (migrated to userdata)
|   |
|   |-- userdata/                 # User data (git ignored)
|   |   |-- settings.json         # Global settings (Theme, Paths, API Keys)
|   |   |-- secrets.json          # Sensitive API Keys
|   |   |-- user_overrides.json   # Menu customizations
|   |   |-- gui_states.json       # GUI window states
|   |   |-- download_history.json # Downloader history
|   |   `-- copy_my_info.json     # Personal info for clipboard tools
|   |
|   |-- tools/                    # Bundled Python, FFmpeg, Blender, ComfyUI
|   |-- resources/                # External resources
|   |-- assets/                   # Icons & Media
|   |   |-- icons/                # Feature icons
|   |   `-- workflows/            # ComfyUI workflow JSONs (API format)
|   `-- logs/                     # Runtime logs
|
|-- README.md
|-- CHANGELOG.md
|-- CREDITS.md
|-- install.bat                   # Runs setup/install.py (Migration included)
|-- manager.bat                   # Runs manager/main.py
`-- uninstall.bat                 # Runs setup/uninstall.py (Registry cleanup)
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
| **AI** | RIFE, Whisper, ESRGAN, RMBG, Marigold, Gemini Image Tool, Demucs, Prompt Master | `ai/`, `prompt_master/` |
| **3D / Mesh** | Auto LOD, CAD to OBJ, Mesh Convert, Remesh & Bake | `mesh/` |
| **Image** | Format Convert, Merge/Split EXR, Texture Packer ORM, Normal Tools, Image Compare | `image/` |
| **Video** | Convert, Extract Audio, Interpolate 30fps, Proxy, Remove Audio | `video/` |
| **Audio** | Convert, Extract BGM/Voice, Normalize | `audio/` |
| **Document** | PDF Merge/Split, Convert Docs | `document/` |
| **Sequence** | Arrange, Missing Frames, To Video, Analyze, Renumber | `sequence/` |
| **System** | Batch Rename, Unwrap Folder, Symlink, Reopen Recent, Move to New Folder, Dup Finder | `system/` |
| **Clipboard** | Open from Clipboard, Paste to New Folder, Save Clipboard Image, Copy UNC Path | `system/` |
| **Tools** | Video Downloader, AI Text Lab, Leave Manager, Copy My Info | `tools/`, `leave_manager/` |
| **ComfyUI** | SeedVR2, Creative Studio (Z/Advanced), Creative Audio Studio (ACE), Open Web UI | `comfyui/` |

### Data Management
All code MUST use `src/core/paths.py` constants for file access.
- **App Data**: `config/` (Static properties, git-tracked)
- **User Data**: `userdata/` (User properties, git-ignored, persistent through updates)

## Important Notes

1. **Working Directory**: All bat files `cd ContextUp` before running Python.
2. **Centralized Paths**: No hardcoded relative paths strings (like `../../config`) should be used; use `core.paths`.
3. **External Tools**: Managed via `PackageManager` and detected in `tools/` or system PATH.
