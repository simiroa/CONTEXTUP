# Icon Generation Prompts (AI / Nanobanana)

This document provides prompts for generating icons using **Google Imagen / Gemini** via the automated batch script.

## Automation
You can automatically generate missing icons using the provided tool:
```bash
python tools/generate_icons_ai.py
```
This script respects the API rate limits (5s delay) and converts results to `.ico`.

---


This document provides optimized prompts for generating icons using **ComfyUI** (Stable Diffusion XL or similar models).
Each icon corresponds to a specific feature ID in `menu_config.json`.

## Global Settings
*   **Model**: SDXL 1.0 or Juggernaut XL (Recommended)
*   **Resolution**: 1024x1024 (Downscale to 256x256 for ICO)
*   **Steps**: 30-40
*   **CFG**: 7.0
*   **Sampler**: DPM++ 2M Karras

## Style Keywords (Append to all prompts)
> **Positive**: 3d render, glassmorphism, translucent, glossy, soft studio lighting, isometric view, rounded corners, minimalism, high quality, 8k, unreal engine 5 render, white background
> **Negative**: text, watermark, low quality, pixelated, blurry, noisy, distorted, realistic photo, complex details, shadow, dark background


## 1. AI Tools (Rainbow/Holographic Theme)

| ID | Prompt Subject |
| :--- | :--- |
| `icon_image_remove_bg_ai.ico` | A subject popping out of a frame, checkerboard background behind it |
| `icon_ai_pbr.ico` | A material sphere showing normal map bumps and roughness details |
| `icon_video_frame_interp.ico` | Two video frames with a glowing interpolated frame appearing in between |
| `icon_audio_separate_stems.ico` | A complex sound wave splitting into distinct colorful strands (vocals, drums, bass) |
| `icon_image_upscale_ai.ico` | A small pixelated square transforming into a large sharp diamond, upward arrow |
| `icon_doc_analyze_ollama.ico` | A document being scanned by an AI brain or eye |

## 2. Image Tools (Cyan/Blue Theme)

| ID | Prompt Subject |
| :--- | :--- |
| `icon_image_format_convert.ico` | A glowing blue image file icon transforming into another format, arrows cycling |
| `icon_image_remove_exif.ico` | A camera lens with a shield or lock symbol, privacy concept |
| `icon_image_resize_pot.ico` | A square image being stretched to a perfect power-of-two grid, arrows expanding |
| `icon_image_exr_split.ico` | A stack of colorful translucent layers separating from a main block |
| `icon_image_exr_merge.ico` | Multiple colorful translucent layers merging into a single solid block |
| `icon_image_upscale_ai.ico` | A small pixelated square transforming into a large sharp diamond, upward arrow |
| `icon_image_remove_bg_ai.ico` | A subject popping out of a frame, checkerboard background behind it |
| `icon_image_analyze_ollama.ico` | An eye or lens scanning a photograph, data lines connecting to it |
| `icon_image_smart_tag.ico` | An image file with a smart tag or label attached, glowing data points |
| `icon_image_texture_tools.ico` | A sphere showing material texture (roughness/normal), PBR concept |

## 2. Video Tools (Purple/Pink Theme)

| ID | Prompt Subject |
| :--- | :--- |
| `icon_video_convert.ico` | A film strip transforming into a digital file, purple glow |
| `icon_video_seq_to_video.ico` | A sequence of image frames merging into a film reel |
| `icon_video_frame_interp.ico` | Two video frames with a glowing interpolated frame appearing in between |
| `icon_video_audio_tools.ico` | A video file with a speaker or waveform icon, splitting or merging |
| `icon_video_generate_subtitle.ico` | A video screen with speech bubbles or text lines appearing at the bottom |

## 3. Audio Tools (Orange/Yellow Theme)

| ID | Prompt Subject |
| :--- | :--- |
| `icon_audio_convert_format.ico` | A musical note transforming into sound waves, orange glow |
| `icon_audio_optimize_vol.ico` | A volume knob or slider set to the perfect level, balanced waveform |

## 4. System Utilities (Silver/Gray Theme)

| ID | Prompt Subject |
| :--- | :--- |
| `icon_sys_batch_rename.ico` | A stack of files with new name tags being applied, glowing silver |
| `icon_sys_renumber.ico` | A sequence of files with glowing numbers (1, 2, 3) appearing on them |
| `icon_sys_clean_empty_dir.ico` | A broom sweeping away an empty transparent folder |
| `icon_sys_move_to_new_folder.ico` | Files flying into a new open folder |
| `icon_sys_find_missing_frames.ico` | A sequence of frames with a red warning sign on a missing gap |
| `icon_sys_arrange_sequences.ico` | Scattered files organizing themselves into neat stacks |
| `icon_sys_analyze_clipboard.ico` | A clipboard with a magnifying glass analyzing the content |
| `icon_sys_save_clipboard.ico` | A clipboard with a download arrow saving to a disk |
| `icon_sys_analyze_error.ico` | A warning triangle or bug icon being scanned by a magnifying glass |
| `icon_sys_manager_gui.ico` | A control panel or dashboard with gears and sliders |

## 5. 3D & PDF Tools (Green/Teal & Red Theme)

| ID | Prompt Subject |
| :--- | :--- |
| `icon_cad_convert_obj.ico` | A technical CAD drawing transforming into a 3D mesh object |
| `icon_mesh_convert_format.ico` | A wireframe cube transforming into a solid sphere |
| `icon_mesh_extract_textures.ico` | A 3D cube peeling off its texture map |
| `icon_sys_pdf_split.ico` | A red PDF document splitting into multiple pages |
| `icon_sys_pdf_merge.ico` | Multiple PDF pages combining into a single document |
| `icon_doc_analyze_ollama.ico` | A document being scanned by an AI brain or eye |
| `icon_mesh_lod.ico` | A high-poly sphere transitioning to a low-poly geometric shape |

## 6. Additional System Icons
| ID | Prompt Subject |
| :--- | :--- |
| `icon_sys_translator.ico` | A speech bubble with language symbols (A/文) and translation arrow |
| `icon_video_downloader.ico` | A red play button downloading into a file folder |
| `icon_ai_pbr.ico` | A material sphere showing normal map bumps and roughness details |
| `icon_sys_create_symlink.ico` | A folder icon with a shortcut arrow or chain link overlay |
| `icon_sys_copy_unc_path.ico` | A network path symbol (\\hostname\path) with a copy icon |
| `icon_sys_finder.ico` | A folder with a powerful searchlight or radar scanning it |
| `icon_sys_open_recent_folder.ico` | An open folder with a clock or history symbol |
| `ContextUp.ico` | Abstract geometric logo representing connections and "Up" arrow, C and U monogram, futuristic, cyan and purple gradient |
| `audio.ico` | A generic modern speaker or sound wave icon, orange theme |
| `video.ico` | A generic film clapperboard or play icon, purple theme |
