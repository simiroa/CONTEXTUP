# Tool Comparison: PyMeshLab vs Assimp vs Blender

## 1. Format Conversion

| Feature | **Blender** | **Assimp** | **PyMeshLab** | **Mayo** |
| :--- | :--- | :--- | :--- | :--- |
| **Supported Formats** | **Extensive** (FBX, OBJ, GLTF, USD, ABC, PLY, STL, DAE, etc.) | **Broad** (FBX, OBJ, GLTF, STL, PLY, 3DS, DAE, etc.) | **Good** (STL, OBJ, PLY, OFF, 3DS, VRML) | **CAD Focused** (STEP, IGES, BREP) -> Mesh (OBJ, GLTF) |
| **Proprietary Formats** | **Excellent** (Best FBX support via official SDK/Reverse Eng.) | **Good** (FBX support is decent but can fail on complex animations/nodes) | **Weak** (FBX support often requires plugins or is limited) | **N/A** (Focuses on CAD) |
| **Conversion Speed** | Slower (Requires full scene graph load) | **Fast** (C++ library, direct parsing) | Moderate | Fast (for CAD) |
| **Reliability** | **High** (Industry standard) | High for static meshes, Medium for complex scenes | High for geometry, Low for scene hierarchy | High for CAD geometry |

**Recommendation for Conversion:**
*   **General Mesh (FBX/OBJ/GLTF)**: **Blender** is the safest bet for reliability, especially with FBX. **Assimp** is faster if you only need static geometry.
*   **CAD (STEP/IGES)**: **Mayo** is the clear winner.
*   **Scientific/Scan Data (PLY/STL)**: **PyMeshLab** is excellent.

## 2. Mesh Optimization (Decimation/Cleaning)

| Feature | **Blender** | **PyMeshLab** | **Assimp** |
| :--- | :--- | :--- | :--- |
| **Decimation Algorithms** | **Collapse** (Fast), **Planar** (Clean), **Un-Subdivide** | **Quadric Edge Collapse** (Gold Standard for preserving shape), **Clustering** | Limited (Simple post-processing) |
| **Remeshing** | **Voxel**, **Quad** (Quadriflow - decent, not perfect) | **Isotropic**, **Screened Poisson** (Reconstruction) | N/A |
| **Cleaning** | **Merge by Distance**, **Fill Holes**, **Delete Loose** | **Extensive** (Remove non-manifold, close holes, remove isolated) | Basic (Triangulate, Sort) |
| **Texture Preservation** | **Excellent** (Can bake textures from high to low poly) | **Good** (Preserves UVs, but baking is less robust than Blender) | N/A |

**Recommendation for Optimization:**
*   **Geometry Reduction (preserving shape)**: **PyMeshLab** (Quadric Edge Collapse) is often superior mathematically for raw scans/dense meshes.
*   **Game/Visual Optimization**: **Blender** (Decimate modifier) is very controllable and visual.
*   **Remeshing (Quad)**: **QuadWild** (External tool) is best for Quad topology. Blender's Quadriflow is a fallback.

## 3. Proposed Workflow

### A. CAD to Mesh (STEP -> OBJ/GLTF)
*   **Tool**: **Mayo** (`mayo-conv.exe`)
*   **Command**: `mayo-conv input.step -o output.obj --export-format obj`

### B. General Format Conversion (FBX <-> GLTF <-> OBJ)
*   **Tool**: **Blender**
*   **Reason**: Best FBX support, preserves hierarchy/materials better than Assimp in many cases.
*   **Script**: `blender -b -P convert.py ...`

### C. Mesh Optimization (High Poly -> Low Poly)
*   **Tool**: **PyMeshLab** (if available/installed) OR **Blender**.
*   **Recommendation**: Use **Blender** for now to keep dependencies low (PyMeshLab requires installing a large python package). Blender's Decimate modifier is sufficient for 90% of use cases.

### D. Quad Remeshing
*   **Tool**: **QuadWild**
*   **Reason**: State-of-the-art auto-retopology.

## Summary
| Task | Recommended Tool |
| :--- | :--- |
| CAD Conversion | **Mayo** |
| General Conversion | **Blender** |
| Optimization | **Blender** (for simplicity) or **PyMeshLab** (for advanced algos) |
| Remeshing | **QuadWild** |
