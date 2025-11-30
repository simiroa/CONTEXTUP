# Phase 3: Advanced Media Tools Feature List

## 1. CAD Tools (Mayo)
*   **Convert CAD to OBJ**
    *   **Input**: `.step`, `.stp`, `.iges`, `.igs`
    *   **Output**: `.obj`
    *   **Tool**: `tools/mayo/mayo-conv.exe`
    *   **Logic**: Direct CLI conversion.

## 2. Mesh Tools (Blender)
*   **Convert Mesh Format**
    *   **Input**: `.fbx`, `.obj`, `.gltf`, `.glb`, `.usd`, `.usdc`, `.usda`, `.abc`, `.ply`, `.stl`
    *   **Output**: `.fbx`, `.obj`, `.gltf`, `.usd`
    *   **Tool**: `tools/blender/blender.exe` (via python script)
    *   **Logic**: Import using Blender's importers -> Export using Blender's exporters.
*   **Optimize Mesh (Decimate)**
    *   **Input**: Mesh files
    *   **Parameters**: Ratio (0.0 - 1.0)
    *   **Tool**: Blender
    *   **Logic**: Apply `Decimate` modifier -> Export.
*   **Extract Textures**
    *   **Input**: `.fbx`
    *   **Output**: Folder of images
    *   **Tool**: Blender
    *   **Logic**: Iterate materials -> Unpack images -> Save to disk.

## 3. Remeshing Tools (QuadWild)
*   **Auto Quad Remesh**
    *   **Input**: `.obj` (High poly / Triangulated)
    *   **Output**: `.obj` (Quad topology)
    *   **Tool**: `tools/quadwild/quadwild.exe`
    *   **Logic**: CLI execution.

## 4. Image Tools (RealESRGAN)
*   **Upscale Image (4x)**
    *   **Input**: `.jpg`, `.png`
    *   **Output**: `.png` (High Res)
    *   **Tool**: `tools/realesrgan/realesrgan-ncnn-vulkan.exe`
    *   **Logic**: CLI execution.

## 5. Integration Strategy
*   **Helper**: `src/utils/external_tools.py` to locate executables.
*   **Scripts**:
    *   `src/scripts/blender_tools.py` (Wrapper)
    *   `src/scripts/mayo_tools.py` (Wrapper)
    *   `src/scripts/quadwild_tools.py` (Wrapper)
    *   `src/scripts/upscale_tools.py` (Wrapper)
    *   `src/blender_scripts/` (Internal Blender Python scripts)
