# Feature Status

| Category | Feature | ID | Status | Tier | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **3D** | Auto LOD Generator | `mesh_auto_lod` | ✅ Ready | 🟠 AI/Bin | PyMeshLab |
| | Convert CAD to OBJ | `3d_convert_obj` | ✅ Ready | 🟢 Std | |
| | Convert Mesh Format | `mesh_convert_format` | ✅ Ready | 🟢 Std | |
| | Extract Textures from FBX | `mesh_extract_textures` | ✅ Ready | 🟢 Std | |
| | Open with Mayo | `mayo_open` | ✅ Ready | 🟢 Std | |
| **AI** | Gemini Image Tool | `ai_img_lab` | ✅ Ready | 🟢 Std | Google Gemini API |
| | Prompt Master | `prompt_master` | ✅ Ready | 🟢 Std | |
| | Remove Background | `img_remove_bg` | ✅ Ready | 🟠 AI/Bin | RMBG-2.0 / Torch |
| | Marigold PBR Gen | `img_marigold_pbr` | ✅ Ready | 🟠 AI/Bin | Marigold Depth |
| | Frame Interpolation (AI) | `vid_frame_interp` | ✅ Ready | 🟠 AI/Bin | RIFE / Torch |
| | Separate Stems (AI) | `aud_separate_stems` | ✅ Ready | 🟠 AI/Bin | Spleeter / Demucs |
| **Audio** | Convert Format | `aud_convert` | ✅ Ready | 🟢 Std | |
| | Extract BGM (Filter) | `aud_extract_bgm` | ✅ Ready | 🟢 Std | FFmpeg filter |
| | Extract Voice (Filter) | `aud_extract_voice` | ✅ Ready | 🟢 Std | FFmpeg filter |
| | Normalize Volume | `aud_normalize` | ✅ Ready | 🟢 Std | Loudnorm |
| | Normalize Volume | `aud_normalize` | ✅ Ready | 🟢 Std | Loudnorm |
| **Clipboard** | Analyze Clipboard Error | `tool_analyze_error` | ✅ Ready | 🟢 Std | |
| | Copy My Info | `clipboard_copy_info` | ✅ Ready | 🟢 Std | |
| | Open Path from Clipboard | `clipboard_open_from_path` | ✅ Ready | 🟢 Std | Hotkey: `Ctrl+Alt+V` |
| | Save Clipboard Image Here | `clipboard_save_image` | ✅ Ready | 🟢 Std | |
| **Document** | Analyze Document (Ollama) | `doc_analyze_ollama` | ✅ Ready | 🟠 AI/Bin | Requires Ollama |
| | Merge PDFs | `doc_pdf_merge` | ✅ Ready | 🟢 Std | |
| | Split PDF | `doc_pdf_split` | ✅ Ready | 🟢 Std | |
| **Tools** | Realtime Translator | `tool_translator` | ✅ Ready | 🟢 Std | |
| | YouTube Downloader | `video_downloader_gui` | ✅ Ready | 🟠 AI/Bin | yt-dlp |
| **Image** | AI Upscale | `img_upscale_ai` | ✅ Ready | 🟠 AI/Bin | Real-ESRGAN / Torch |

| | Merge to EXR | `img_merge_exr` | ✅ Ready | 🟢 Std | |
| | Merge to EXR | `img_merge_exr` | ✅ Ready | 🟢 Std | |
| | Remove Metadata (EXIF) | `img_remove_exif` | ✅ Ready | 🟢 Std | |
| | Resize (Power of 2) | `img_resize_pot` | ✅ Ready | 🟢 Std | |
| | Split EXR Layers | `img_split_exr` | ✅ Ready | 🟢 Std | |
| **Rename** | Batch Rename... | `rename_batch` | ✅ Ready | 🟢 Std | |
| | Renumber Sequence... | `rename_sequence` | ✅ Ready | 🟢 Std | |
| **System** | ContextUp Manager | `app_manager` | ✅ Ready | 🟢 Std | Hotkey: `Ctrl+Alt+Shift+F1` |
| | Copy UNC Path | `sys_copy_unc_path` | ✅ Ready | 🟢 Std | |
| | Create Symlink Folder | `file_create_symlink` | ✅ Ready | 🟢 Std | |
| | Move into New Folder | `file_move_in_new_folder` | ✅ Ready | 🟢 Std | |
| | Power Finder | `tool_finder` | ✅ Ready | 🟢 Std | |
| | Remove Empty Subfolders | `dir_clean_empty` | ✅ Ready | 🟢 Std | |
| | Reopen Last Closed Folder | `file_reopen_recent` | ✅ Ready | 🟢 Std | |
| | Unwrap Folder | `dir_flatten` | ✅ Ready | 🟢 Std | |
| **Video** | Arrange Image Sequences | `vid_arrange_sequence` | ✅ Ready | 🟢 Std | |
| | Convert Format | `vid_convert` | ✅ Ready | 🟢 Std | |
| | Create Proxy Media | `vid_create_proxy` | ✅ Ready | 🟢 Std | |
| | Extract Audio | `vid_extract_audio` | ✅ Ready | 🟢 Std | |
| | Find Missing Frames | `vid_find_missing_frames` | ✅ Ready | 🟢 Std | |
| | Frame Interpolation (30fps) | `vid_frame_interp_30fps` | ✅ Ready | 🟢 Std | Blending |

| | Generate Subtitles (AI) | `vid_subtitle_gen` | ✅ Ready | 🟠 AI/Bin | Faster-Whisper |
| | Image Sequence to Video | `vid_from_sequence` | ✅ Ready | 🟢 Std | |
| | Remove Audio Track | `vid_mute` | ✅ Ready | 🟢 Std | |

> [!NOTE]
> **Tier Legend**:
> *   🟢 **Std (Standard)**: Lightweight, runs on standard Python environment.
> *   🟠 **AI/Bin (Heavy)**: Requires complex binaries (PyTorch/CUDA) or AI models.
