# User Testing Checklist

Use this checklist to verify that all features of ContextUp are working correctly.

## 1. System & Manager
- [ ] **ContextUp Manager** (`sys_manager_gui`)
    - [ ] Opens successfully.
    - [ ] "Register Menu" works.
    - [ ] **Updates & Health Tab** (v3.2):
        - [ ] "Update All Libraries" runs successfully.
        - [ ] "Library Cleaner" lists installed packages.
        - [ ] "Uninstall" button works (and protects critical libs).
    - [ ] **Smart Dependency System**:
        - [ ] Missing dependencies show "Setup Required" (Yellow).
        - [ ] Clicking inactive tool opens Install Dialog.
        - [ ] Installation completes and tool becomes active.
- [ ] **Open Recent Folders** (`sys_open_recent`)
    - [ ] Shows list of recently accessed folders.
    - [ ] Clicking a folder opens it.

## 2. File & Folder Operations
- [ ] **Move to New Folder** (`sys_move_to_new_folder`)
    - [ ] Moves selected files to a new folder.
    - [ ] Handles naming collisions.
- [ ] **Find Missing Frames** (`sys_find_missing_frames`)
    - [ ] Detects gaps in image sequences (e.g., `shot.001.png`, `shot.003.png`).
- [ ] **Arrange Sequences** (`sys_arrange_sequences`)
    - [ ] Groups files by prefix into folders.
- [ ] **Smart Rename** (`sys_smart_rename`)
    - [ ] Batch rename with prefix/suffix/replace.
    - [ ] Real-time preview works.

## 3. Image Tools
- [ ] **Convert Format** (`image_format_convert`)
    - [ ] Converts images (JPG, PNG, WEBP, etc.).
- [ ] **Resize to POT** (`image_resize_pot`)
    - [ ] Resizes to Power-of-Two (e.g., 512x512).
- [ ] **Remove EXIF** (`image_remove_exif`)
    - [ ] Strips metadata.
- [ ] **EXR Tools**
    - [ ] **Split Layers** (`image_exr_split`): Splits EXR into separate images.
    - [ ] **Merge Layers** (`image_exr_merge`): Merges images into one EXR.
- [ ] **AI Upscale** (`image_upscale_ai`)
    - [ ] Upscales image x2 or x4.
- [ ] **Remove Background** (`image_remove_bg_ai`)
    - [ ] Removes background using RMBG-2.0.
- [ ] **Analyze Image** (`image_analyze_ollama`)
    - [ ] Describes image content using Ollama.

## 4. Video & Audio Tools
- [ ] **YouTube Downloader** (`video_downloader_gui`)
    - [ ] Analyzes URL.
    - [ ] Downloads video (Best/4K/1080p).
    - [ ] Queue works.
    - [ ] History saves correctly.
- [ ] **Convert Video** (`video_convert`)
    - [ ] Converts video formats (MP4, MOV, etc.).
    - [ ] Creates Proxy (1/2 res).
- [ ] **Sequence to Video** (`video_seq_to_video`)
    - [ ] Converts image sequence to MP4.
- [ ] **Frame Interpolation** (`video_frame_interp`)
    - [ ] Increases framerate (AI).
- [ ] **Generate Subtitles** (`video_generate_subtitle`)
    - [ ] Generates .srt file from video.
- [ ] **Audio Tools** (`video_audio_tools`)
    - [ ] Extracts audio.
    - [ ] Removes audio.
- [ ] **Audio Converter** (`audio_convert_format`)
    - [ ] Converts audio formats.

## 5. 3D Tools
- [ ] **Convert Mesh** (`mesh_convert_format`)
    - [ ] Converts OBJ/FBX/GLTF.
- [ ] **Auto LOD Generator** (`mesh_auto_lod`)
    - [ ] Generates LODs (decimation).
    - [ ] Bakes textures (Normal/AO).
- [ ] **Convert CAD** (`cad_convert_obj`)
    - [ ] Converts STEP/IGES to OBJ.

## 6. AI Generation
- [ ] **PBR Generator** (`ai_pbr_gen`)
    - [ ] Generates Normal/Roughness maps from image.
- [ ] **Make Tileable** (`ai_maketile`)
    - [ ] Makes texture seamless.
- [ ] **Style Transfer** (`ai_style_change`)
    - [ ] Applies style to image.
- [ ] **Inpaint/Outpaint** (`ai_inpaint`, `ai_outpaint`)
    - [ ] Modifies image content.

## 7. Utilities
- [ ] **Real-time Translator** (`sys_translator`)
    - [ ] Translates clipboard text.
    - [ ] Overlay window works.
- [ ] **Clipboard AI** (`sys_clipboard_ai`)
    - [ ] Analyzes clipboard content.
- [ ] **PDF Tools**
    - [ ] **Merge PDFs** (`sys_pdf_merge`).
    - [ ] **Split PDF** (`sys_pdf_split`).

## 8. Stability Tiers (Unified Environment)

To ensure stability in the unified embedded environment, tools are classified into two tiers:

### 🟢 Safe Tier (Standard)
*   **Description**: Uses only standard Python libraries or lightweight dependencies (Pillow, Requests).
*   **Risk**: Low. Should work on any Windows machine.
*   **Tools**: Rename, File Ops, Document Tools, Basic Image/Audio conversion.

### 🟠 Sensitive Tier (AI/Heavy)
*   **Description**: Depends on complex binaries (PyTorch, CUDA, FFmpeg) running in the embedded environment.
*   **Risk**: Moderate. Sensitive to driver versions and path lengths.
*   **Tools**: Remove Background, AI Upscale, Frame Interpolation, Auto LOD, YouTube Downloader.
*   **Verification**: Run `tests/verify_ai_env.py` to check if these libraries load correctly.

---

## Feedback Log

| Date | Feature | Issue | Status |
|------|---------|-------|--------|
| | | | |
