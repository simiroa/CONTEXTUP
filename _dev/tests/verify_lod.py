import pymeshlab
import os
from pathlib import Path

def create_dummy_obj(path):
    # Create a simple cube OBJ manually
    vertices = [
        "v -1 -1 -1", "v 1 -1 -1", "v 1 1 -1", "v -1 1 -1",
        "v -1 -1 1", "v 1 -1 1", "v 1 1 1", "v -1 1 1"
    ]
    faces = [
        "f 1 2 3 4", "f 5 8 7 6", "f 1 5 6 2",
        "f 2 6 7 3", "f 3 7 8 4", "f 5 1 4 8"
    ]
    with open(path, "w") as f:
        f.write("\n".join(vertices) + "\n" + "\n".join(faces))

def test_lod_generation():
    print("Testing PyMeshLab LOD Generation...")
    
    test_dir = Path("tests/temp_lod")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    input_path = test_dir / "cube.obj"
    create_dummy_obj(input_path)
    
    ms = pymeshlab.MeshSet()
    ms.load_new_mesh(str(input_path))
    
    print(f"Original Faces: {ms.current_mesh().face_number()}")
    
    # Apply Quadric Edge Collapse
    # Note: Cube has very few faces (6 quads -> 12 tris), decimation might not do much unless we subdivide first.
    # But we just want to check if the function runs without error.
    
    try:
        ms.apply_filter('meshing_decimation_quadric_edge_collapse', 
                      targetfacenum=6, 
                      preserveboundary=True, 
                      preservenormal=True, 
                      preservetexture=True)
        
        output_path = test_dir / "cube_LOD1.obj"
        ms.save_current_mesh(str(output_path))
        print(f"LOD1 Saved: {output_path}")
        print("Verification Successful!")
        
    except Exception as e:
        print(f"Verification Failed: {e}")
        exit(1)

if __name__ == "__main__":
    test_lod_generation()
