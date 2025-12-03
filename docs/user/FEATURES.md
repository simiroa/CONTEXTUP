# Feature Status

| Category | Feature | ID | Status | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **System** | Folder: Move to New... | `sys_move_to_new_folder` | ✅ Ready | Collision alerts added |
| | Folder: Remove Empty | `sys_clean_empty_dir` | ✅ Ready | |
| | Folder: Arrange Sequences | `sys_arrange_sequences` | ✅ Ready | |
| | Folder: Find Missing Frames | `sys_find_missing_frames` | ✅ Ready | |
| | Clipboard: Save Image | `sys_save_clipboard` | ✅ Ready | |
| | Clipboard: Analyze Image | `sys_analyze_clipboard` | ✅ Ready | Uses Ollama Vision |
| | Clipboard: Analyze Error | `sys_analyze_error` | ✅ Ready | Uses LLM for analysis |
| | Open Creator Tools Manager | `sys_manager_gui` | ✅ Ready | **v3.2**: Smart Dependency Manager, Updates Tab, Library Cleaner |
| **Rename** | Batch Rename... | `sys_batch_rename` | ✅ Ready | **Unified GUI** with Preview |
| | Renumber... | `sys_renumber` | ✅ Ready | **Unified GUI** (Selection/Folder) |
| **Document** | Merge PDFs | `sys_pdf_merge` | ✅ Ready | |
| | Split PDF | `sys_pdf_split` | ✅ Ready | |
| | Analyze Document | `doc_analyze_ollama` | ✅ Ready | Summarize/Chat with PDF |
| **Image** | Convert Format | `image_format_convert` | ✅ Ready | **Progress Bar** added |
| | Resize to POT | `image_resize_pot` | ✅ Ready | **Stretch/Pad** options |
| | Remove EXIF | `image_remove_exif` | ✅ Ready | |
| | EXR Split/Merge | `image_exr_*` | ✅ Ready | |
| | Remove Background | `image_remove_bg_ai` | ✅ Ready | Uses RMBG-2.0 (AI Env) |
| | Upscale (AI) | `image_upscale_ai` | ✅ Ready | Uses Real-ESRGAN (AI Env) |
| | Generate Prompt | `image_analyze_ollama` | ✅ Ready | Uses Ollama Vision |
| | Auto Tag Metadata | `image_smart_tag` | ✅ Ready | Uses Ollama Vision |
| | Texture Tools | `image_texture_tools` | ✅ Ready | Gemini API (PBR/Weathering) |
| **Video** | Convert / Proxy | `video_convert` | ✅ Ready | **Unified GUI** (Convert/Proxy/Downscale) |
| | Sequence to Video | `video_seq_to_video` | ✅ Ready | Skip First Frame option |
| | Audio Tools | `video_audio_tools` | ✅ Ready | **Unified GUI** (Extract/Remove/Separate) |
| | Frame Interpolation | `video_frame_interp` | ✅ Ready | AI (RIFE) or 30fps Blend |
| | Generate Subtitles | `video_generate_subtitle` | ✅ Ready | Uses Faster-Whisper |
| **Audio** | Convert Format | `audio_convert_format` | ✅ Ready | Copy Metadata option |
| | Optimize Volume | `audio_optimize_vol` | ✅ Ready | Loudnorm normalization |
| **3D** | Convert Mesh | `mesh_convert_format` | ✅ Ready | OBJ, FBX, GLTF (Blender) |
| | Extract Textures | `mesh_extract_textures` | ✅ Ready | (Blender) |
| | Convert CAD | `cad_convert_obj` | ✅ Ready | Uses Mayo (STEP/IGES -> OBJ) |
| | Auto LOD Generator | `mesh_auto_lod` | ✅ Ready | PyMeshLab + Blender Baking |

> [!NOTE]
> **Custom Sorting**: You can rename any feature in the **Creator Tools Manager** (click the ✎ icon) to customize the sort order in the context menu.
