# Doc Consistency Report - ContextUp

## Scope and Sources
- Docs reviewed: `README.md`, `시작하기.md`, `ContextUp/docs/user/README_KR.md`, `ContextUp/docs/user/INSTALL.md`, `ContextUp/docs/user/FEATURES.md`,
  `ContextUp/docs/dev/AGENT_GUIDELINES.md`, `ContextUp/docs/dev/DEVELOPMENT.md`,
  `ContextUp/docs/dev/TESTING_GUIDE.md`, `ContextUp/docs/dev/TROUBLESHOOTING.md`, `ContextUp/architecture.md`.
- Implementation sources: `ContextUp/config/categories/*.json`, `ContextUp/src/core/menu.py`,
  `ContextUp/src/tray/menu_builder.py`, `ContextUp/src/utils/external_tools.py`,
  `ContextUp/src/setup/install.py`, `ContextUp/src/core/paths.py`.

## Implementation Snapshot (current code)

### Hotkeys (actually registered)
- Quick Menu: `ctrl+shift+c` (`ContextUp/src/tray/agent.py`, `ContextUp/src/tray/hotkeys.py`)
- Open from Clipboard: `ctrl+alt+v` (`ContextUp/config/categories/clipboard.json`)
- Manager: `ctrl+alt+shift+f1` (`ContextUp/config/categories/system.json`)
- No `Alt+Space` Finder hotkey exists in code/config.

### Feature inventory (from `ContextUp/config/categories/*.json`)
Image (context menu, file/items):
- `image_convert` (file)
- `merge_to_exr` (items)
- `resize_power_of_2` (file)
- `split_exr` (file)
- `texture_packer_orm` (file)
- `normal_flip_green` (file)
- `simple_normal_roughness` (file)
- `image_compare` (items)

Sequence (context menu, items):
- `sequence_arrange`
- `sequence_find_missing`
- `sequence_to_video`
- `sequence_analyze`
- `sequence_renumber`

Video (context menu, file):
- `video_convert`
- `extract_audio`
- `interpolate_30fps`
- `create_proxy`
- `remove_audio`

Audio (context menu, file):
- `audio_convert`
- `extract_bgm`
- `extract_voice`
- `normalize_volume`

Document (context menu, file/items):
- `doc_convert`
- `pdf_merge`
- `pdf_split`

3D (context menu, file):
- `auto_lod`
- `cad_to_obj`
- `mesh_convert`
- `open_with_mayo`
- `extract_textures`
- `blender_bake_gui`

AI (context menu, file/background):
- `rife_interpolation`
- `whisper_subtitle`
- `esrgan_upscale`
- `rmbg_background`
- `marigold_pbr`
- `gemini_prompt_master` (background)
- `gemini_image_tool`
- `demucs_stems`
- `paddle_ocr`

System (context menu, background/directory/items):
- `clean_empty_folders` (directory)
- `move_to_new_folder` (items)
- `reopen_recent` (background, requires tray agent)
- `unwrap_folder` (directory)
- `finder` (background)
- `create_symlink` (background)
- `manager` (background)
- `batch_rename` (items)

Clipboard (context menu, background):
- `open_from_clipboard` (hotkey)
- `save_clipboard_image`
- `clipboard_to_new_folder`
- `copy_unc_path`

Tools (context menu + tray):
- `youtube_downloader` (background, tray)
- `ai_text_lab` (background, tray)
- `leave_manager` (background, tray)
- `copy_my_info` (tray_only)

ComfyUI (tray-only; `show_in_context_menu` is false):
- `seedvr2_upscaler`
- `z_image_turbo`
- `ace_audio_editor`
- `ai_icon_generator`
- `comfyui_dashboard`

### External tools and lookup paths (actual behavior)
- FFmpeg: `ContextUp/tools/ffmpeg/...` or PATH (`ContextUp/src/utils/external_tools.py`)
- Blender: `ContextUp/tools/blender/...` or system installs
- Mayo: `ContextUp/tools/mayo/...`
- Real-ESRGAN: `ContextUp/resources/bin/realesrgan/...` first, then `ContextUp/tools/realesrgan/...`
- ComfyUI: `ContextUp/tools/ComfyUI/...`

## Doc Mismatches and Required Updates

### `README.md`
- Mentions **AI Text Refiner** and **Gemini 2.5 Flash**; actual user-facing tool is `ai_text_lab` (Tools) with Gemini/Ollama/Google MT and API key requirements in `ContextUp/userdata/secrets.json`.
- "Smart Clipboard: Copy Path as Image" is not implemented; current feature is **Save Clipboard Image**.
- "AI Upscale w/ ComfyUI support" is misleading: ESRGAN upscaler is a separate Real-ESRGAN tool; ComfyUI tools are tray-only items.
- "Audio stems (Vocals/Drums)" should reference **Demucs Stem Separation** (AI) or **Video/Audio GUI** for simple FFmpeg filtering, not a dedicated video stem feature.

### `ContextUp/docs/user/README_KR.md`
- Uses `ContextUpManager.bat`, but the actual launcher is `manager.bat` in repo root.
- External tool list includes **ExifTool**, but no code references or tool lookup exist for ExifTool.
- Feature list and hotkey claims are out of sync with config (see `ContextUp/docs/user/FEATURES.md` section).
- File encoding appears mojibake; convert to UTF-8 (preferably with BOM for Windows) to prevent garbled text.

### `ContextUp/docs/user/FEATURES.md`
- Lists **RT Translator (NLLB)** + `Ctrl+Alt+T`, but no translator feature or hotkey exists.
- Claims Finder hotkey `Alt+Space`, but no hotkey is defined for `finder`.
- Missing features: `interpolate_30fps`, `reopen_recent`, `pdf_split`, `save_clipboard_image`, `simple_normal_roughness`.
- ComfyUI list only covers SeedVR2/Z Image Turbo; missing `ace_audio_editor`, `ai_icon_generator`, `comfyui_dashboard`.
- **AI Text Refiner** should be renamed to **AI Text Lab** (Tools category) with Gemini/Ollama/Google MT behavior and API key dependency.
- **PDF OCR** should reference `paddle_ocr` (AI category) and clarify that `doc_convert` also performs OCR/metadata extraction.
- Tray access: `finder` is not `show_in_tray` but `youtube_downloader`, `ai_text_lab`, `leave_manager` are.
- Encoding issues (mojibake) are present; convert to UTF-8.

### `ContextUp/docs/user/INSTALL.md`
- Claims `install.bat` installs `requirements.txt`; actual package selection is in `ContextUp/src/setup/install.py` (tier + category based).
- External tool locations should point to `ContextUp/tools/*` (FFmpeg/Blender/Mayo/ComfyUI) with Real-ESRGAN allowed in `ContextUp/resources/bin/realesrgan`.
- Encoding issues (mojibake) are present; convert to UTF-8.

### `시작하기.md`
- References `ContextUpManager.bat`, but actual file is `manager.bat`.
- Installation tiers and sizes should match `ContextUp/config/install_tiers.json` values (Minimal/Standard/Full/Custom).
- Encoding issues (mojibake) are present; convert to UTF-8.

### `ContextUp/docs/dev/AGENT_GUIDELINES.md`
- Mentions `config/menu/categories` and `config/menu_config.json`, but actual config source is `ContextUp/config/categories/*.json`.
- External binary location says `ContextUp/resources/bin`, but tool lookup is `ContextUp/tools/*` (Real-ESRGAN only uses `resources/bin` first).
- Root structure rules mention `tools/` at repo root; actual tool path is `ContextUp/tools/`.

### `ContextUp/docs/dev/DEVELOPMENT.md`
- "resources/ is CRITICAL for external binaries" is outdated for FFmpeg/Blender/Mayo/ComfyUI; use `ContextUp/tools/*` with Real-ESRGAN fallback in `resources/bin`.
- Example fields like `show_in_context_menu` and `script` should clarify that registry/menu dispatch uses `ContextUp/src/core/menu.py` and `config/categories` only; `script` is only used by tray launchers.

### `ContextUp/docs/dev/TESTING_GUIDE.md`
- References `config/menu/categories`; actual config is `ContextUp/config/categories`.
- Includes non-existent IDs: `ai_text_refine`, `translator`, `vacance`, `video_audio_tools`.
- Missing actual IDs: `image_compare`, `interpolate_30fps`, `reopen_recent`, `save_clipboard_image`, ComfyUI items (`ace_audio_editor`, `ai_icon_generator`, `comfyui_dashboard`).
- Total feature count should be updated to match current config inventory (61 items, excluding the ComfyUI container object).

### `ContextUp/docs/dev/TROUBLESHOOTING.md`
- `crash_log.txt` -> actual log is `ContextUp/logs/manager_crash.log`.
- `tray_agent.py` -> actual entry is `ContextUp/src/tray/agent.py`.
- `src/manager/core/settings.py` -> actual path is `ContextUp/src/core/settings.py`.
- Mentions `reprod_restart.py`, which does not exist.

### `ContextUp/architecture.md`
- Path tree includes `features/vacance`, `features/tools/translator.py`, etc.; actual modules are `features/leave_manager` and `features/tools/ai_text_lab.py`, and there is no translator module.
- Feature table lists RT Translator and Vacance; these do not exist as current IDs.
- External tool guidance should align with `ContextUp/tools/*` + Real-ESRGAN `resources/bin` fallback.
- Encoding issues (mojibake) are present; convert to UTF-8.

## Suggested Update Checklist (ordered)
1. Normalize encoding to UTF-8 (especially `ContextUp/docs/user/*.md`, `ContextUp/architecture.md`, `시작하기.md`).
2. Fix launcher names and paths (`manager.bat`, `ContextUp/config/categories`, `ContextUp/logs/*`).
3. Replace outdated features with the canonical list above, including ComfyUI tray-only items and missing tools.
4. Update install docs to reflect tiered package install in `ContextUp/src/setup/install.py`.
5. Update dev/testing docs to match real feature IDs and config paths.
