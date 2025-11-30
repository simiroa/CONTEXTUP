# Phase 3: External Tools Integration Plan

## Goal
Expand context menu functionality using external open-source tools (Blender, QuadWild, RealESRGAN) for advanced media processing.

## 1. Tool Availability Status
*   **Blender**: Available (`tools/blender/blender-4.5.5-windows-x64/blender.exe`)
*   **QuadWild**: Available (`tools/quadwild/quadwild.exe`)
*   **RealESRGAN**: Available (`tools/realesrgan/realesrgan-ncnn-vulkan.exe`)
*   **Mayo**: **MISSING** (`tools/mayo` not found).
    *   *Action*: Proceed with Blender/QuadWild/RealESRGAN. Defer CAD (IGES) conversion until Mayo is installed.

## 2. Proposed Features & Implementation

### 2.1 Blender Tools (`src/scripts/blender_tools.py`)
*   **Mechanism**: `subprocess.run([blender_exe, "-b", "-P", python_script, "--", args])`
*   **Features**:
    *   **Convert Mesh**: Supports FBX, OBJ, GLTF, USD, ABC.
        *   *Logic*: Import source -> Export target.
    *   **Extract Textures (FBX)**:
        *   *Logic*: Import FBX -> Iterate Materials -> Unpack/Save Images.
    *   **Render Thumbnail**:
        *   *Logic*: Import mesh -> Setup Camera/Light -> Render single frame.

### 2.2 QuadWild Tools (`src/scripts/quadwild_tools.py`)
*   **Mechanism**: `subprocess.run([quadwild_exe, "-i", input.obj, "-o", output.obj])`
*   **Features**:
    *   **Auto Remesh**: Convert arbitrary mesh to Quad mesh.
        *   *Note*: QuadWild typically requires OBJ input. Might need Blender to convert to OBJ first if input is FBX.

### 2.3 RealESRGAN Tools (`src/scripts/upscale_tools.py`)
*   **Mechanism**: `subprocess.run([realesrgan_exe, "-i", input, "-o", output, "-s", scale])`
*   **Features**:
    *   **Upscale Image (4x)**: AI upscaling.

### 2.4 CAD Conversion (Pending Mayo)
*   **Goal**: IGES/STEP -> USD.
*   **Workflow**: IGES -> (Mayo) -> OBJ -> (Blender) -> USD.
*   *Status*: Blocked.

## 3. Development Steps
1.  **Helper Setup**: Create `utils.external_tools` to manage paths to these executables.
2.  **Blender Scripts**: Write internal python scripts for Blender (e.g., `src/blender_scripts/convert.py`).
3.  **Integration**: Implement `blender_tools.py` calling these scripts.
4.  **QuadWild/RealESRGAN**: Implement wrapper scripts.
5.  **Menu Config**: Register new tools in `menu_config.json`.

## 4. Verification
*   Test FBX -> OBJ conversion.
*   Test FBX Texture Extraction.
*   Test QuadWild on a simple OBJ.
*   Test RealESRGAN on a low-res image.
