import pymeshlab
import os

def create_textured_plane(path):
    # Create a simple OBJ with UVs manually
    with open(path, 'w') as f:
        f.write("v -1 -1 0\n")
        f.write("v 1 -1 0\n")
        f.write("v 1 1 0\n")
        f.write("v -1 1 0\n")
        f.write("vt 0 0\n")
        f.write("vt 1 0\n")
        f.write("vt 1 1\n")
        f.write("vt 0 1\n")
        f.write("f 1/1 2/2 3/3 4/4\n")

def test_lod_uv():
    test_file = "test_plane.obj"
    out_file = "test_plane_lod.obj"
    
    create_textured_plane(test_file)
    
    ms = pymeshlab.MeshSet()
    ms.load_new_mesh(test_file)
    
    print(f"Original UVs: {ms.current_mesh().vertex_tex_coord_matrix() is not None or ms.current_mesh().wedge_tex_coord_matrix() is not None}")
    
    # Apply decimation
    # Note: Quadric Edge Collapse on a single quad might not do much unless we subdivide it first.
    # Let's subdivide first to give it something to collapse.
    ms.apply_filter('meshing_surface_subdivision_midpoint', iterations=2)
    print("Subdivided.")
    
    # Now collapse
    ms.apply_filter('meshing_decimation_quadric_edge_collapse_with_texture', targetfacenum=2)
    
    ms.save_current_mesh(out_file)
    
    # Reload to check UVs
    ms.load_new_mesh(out_file)
    m = ms.current_mesh()
    
    has_uv = (m.vertex_tex_coord_matrix() is not None) or (m.wedge_tex_coord_matrix() is not None)
    print(f"Result UVs Preserved: {has_uv}")
    
    # Cleanup
    try:
        os.remove(test_file)
        os.remove(out_file)
    except:
        pass

if __name__ == "__main__":
    test_lod_uv()
