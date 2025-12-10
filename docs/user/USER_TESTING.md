# User Testing Checklist

Use this checklist to verify that all features of ContextUp are working correctly.

## 1. 3D Tools
- [ ] **Auto LOD Generator** (`mesh_auto_lod`)
    - [ ] Generates simplified mesh (LOD).
- [ ] **Convert CAD to OBJ** (`3d_convert_obj`)
    - [ ] Converts STEP/IGES files to OBJ.
- [ ] **Convert Mesh Format** (`mesh_convert_format`)
    - [ ] Converts between OBJ, FBX, GLTF, etc.
- [ ] **Extract Textures from FBX** (`mesh_extract_textures`)
    - [ ] Extracts embedded textures from binary FBX.
- [ ] **Open with Mayo** (`mayo_open`)
    - [ ] Launches Mayo 3D viewer.

## 2. AI Tools
- [ ] **Gemini Image Tool** (`ai_img_lab`)
    - [ ] Analyzes/Processes image using Gemini API.
- [ ] **Prompt Master** (`prompt_master`)
    - [ ] Opens prompt management interface.
- [ ] **Remove Background** (`img_remove_bg`)
    - [ ] Removes image background using RMBG-2.0.
- [ ] **Marigold PBR Gen** (`img_marigold_pbr`)
    - [ ] Generates PBR maps (Normal/Depth/Displacement) from image.
- [ ] **Frame Interpolation (AI)** (`vid_frame_interp`)
    - [ ] Increases video framerate using AI Interpolation.
- [ ] **Separate Stems (AI)** (`aud_separate_stems`)
    - [ ] Separates audio into stems (Vocals, Drums, Bass, Other) using AI.

## 3. Audio Tools
- [ ] **Convert Format** (`aud_convert`)
    - [ ] Converts audio files (WAV, MP3, etc.).
- [ ] **Extract BGM (Filter)** (`aud_extract_bgm`)
    - [ ] Filters out voice using FFmpeg/demucs algorithms.
- [ ] **Extract Voice (Filter)** (`aud_extract_voice`)
    - [ ] Filters out BGM.
- [ ] **Normalize Volume** (`aud_normalize`)
    - [ ] Normalizes audio volume (Loudnorm).
- [ ] **Separate Stems (AI)** (`aud_separate_stems`)
    - [ ] Separates audio into stems (Vocals, Drums, Bass, Other) using AI.

## 4. Clipboard Tools
- [ ] **Analyze Clipboard Error** (`tool_analyze_error`)
    - [ ] Analyzes error message in clipboard.
- [ ] **Copy My Info** (`clipboard_copy_info`)
    - [ ] Copies user info/system info to clipboard.
- [ ] **Open Path from Clipboard** (`clipboard_open_from_path`)
    - [ ] Opens file/folder path from clipboard content.
- [ ] **Save Clipboard Image Here** (`clipboard_save_image`)
    - [ ] Saves image in clipboard to current folder.

## 5. Document Tools
- [ ] **Analyze Document (Ollama)** (`doc_analyze_ollama`)
    - [ ] Summarizes/Analyzes PDF content using Ollama.
- [ ] **Merge PDFs** (`doc_pdf_merge`)
    - [ ] Merges multiple PDF files.
- [ ] **Split PDF** (`doc_pdf_split`)
    - [ ] Splits PDF into pages or ranges.

## 6. Tools
- [ ] **Realtime Translator** (`tool_translator`)
    - [ ] Real-time translation tool (Window/Item scope).
- [ ] **YouTube Downloader** (`video_downloader_gui`)
    - [ ] Downloads video from URL.

## 7. Image Tools
- [ ] **AI Upscale** (`img_upscale_ai`)
    - [ ] Upscales image using Real-ESRGAN.
- [ ] **Marigold PBR Gen** (`img_marigold_pbr`)
    - [ ] Generates PBR maps (Normal/Depth/Displacement) from image.
- [ ] **Merge to EXR** (`img_merge_exr`)
    - [ ] Merges multiple images into layers of one EXR file.
- [ ] **Remove Background** (`img_remove_bg`)
    - [ ] Removes image background using RMBG-2.0.
- [ ] **Remove Metadata (EXIF)** (`img_remove_exif`)
    - [ ] Strips EXIF data.
- [ ] **Resize (Power of 2)** (`img_resize_pot`)
    - [ ] Resizes image to nearest Power of 2 dimensions.
- [ ] **Split EXR Layers** (`img_split_exr`)
    - [ ] Extracts layers from EXR to separate images.

## 8. Rename Tools
- [ ] **Batch Rename...** (`rename_batch`)
    - [ ] Renames multiple files with pattern.
- [ ] **Renumber Sequence...** (`rename_sequence`)
    - [ ] Renumbers file sequences.

## 9. System Tools
- [ ] **ContextUp Manager** (`app_manager`)
    - [ ] Opens settings and dependency manager.
- [ ] **Copy UNC Path** (`sys_copy_unc_path`)
    - [ ] Copies network path to clipboard.
- [ ] **Create Symlink Folder** (`file_create_symlink`)
    - [ ] Creates symbolic link for selected folder.
- [ ] **Move into New Folder** (`file_move_in_new_folder`)
    - [ ] Moves selection to a new folder.
- [ ] **Power Finder** (`tool_finder`)
    - [ ] Advanced file search tool.
- [ ] **Remove Empty Subfolders** (`dir_clean_empty`)
    - [ ] Recursively removes empty directories.
- [ ] **Reopen Last Closed Folder** (`file_reopen_recent`)
    - [ ] Reopens the most recently closed explorer window path.
- [ ] **Unwrap Folder** (`dir_flatten`)
    - [ ] Moves content up one level and deletes folder.

## 10. Video Tools
- [ ] **Arrange Image Sequences** (`vid_arrange_sequence`)
    - [ ] Organizes image sequences into folders.
- [ ] **Convert Format** (`vid_convert`)
    - [ ] Converts video formats.
- [ ] **Create Proxy Media** (`vid_create_proxy`)
    - [ ] Creates lower resolution proxy for editing.
- [ ] **Extract Audio** (`vid_extract_audio`)
    - [ ] Extracts audio track from video.
- [ ] **Find Missing Frames** (`vid_find_missing_frames`)
    - [ ] Identifies gaps in image sequences.
- [ ] **Frame Interpolation (30fps)** (`vid_frame_interp_30fps`)
    - [ ] Standard frame blending interpolation.

- [ ] **Generate Subtitles (AI)** (`vid_subtitle_gen`)
    - [ ] Generates SRT subtitles using Whisper.
- [ ] **Image Sequence to Video** (`vid_from_sequence`)
    - [ ] Compiles image sequence into video file.
- [ ] **Remove Audio Track** (`vid_mute`)
    - [ ] Removes audio from video file.

---

## Feedback Log

| Date | Feature | Issue | Status |
|------|---------|-------|--------|
| | | | |
