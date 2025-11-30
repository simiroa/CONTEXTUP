"""
Blender script for mesh format conversion.
Usage: blender -b -P convert_mesh.py -- input.fbx output.obj
"""
import bpy
import sys

def main():
    # Parse args after '--'
    argv = sys.argv
    if "--" not in argv:
        print("Error: No arguments provided. Use: blender -b -P convert_mesh.py -- input output")
        sys.exit(1)
    
    args = argv[argv.index("--") + 1:]
    if len(args) < 2:
        print("Error: Need input and output paths")
        sys.exit(1)
    
    input_file = args[0]
    output_file = args[1]
    
    print(f"Converting {input_file} -> {output_file}")
    
    # Clear scene
    bpy.ops.wm.read_factory_settings(use_empty=True)
    
    # Import based on extension
    input_ext = input_file.lower().split('.')[-1]
    
    try:
        if input_ext in ['fbx']:
            bpy.ops.import_scene.fbx(filepath=input_file)
        elif input_ext in ['obj']:
            bpy.ops.import_scene.obj(filepath=input_file)
        elif input_ext in ['gltf', 'glb']:
            bpy.ops.import_scene.gltf(filepath=input_file)
        elif input_ext in ['usd', 'usda', 'usdc']:
            bpy.ops.wm.usd_import(filepath=input_file)
        elif input_ext in ['abc']:
            bpy.ops.wm.alembic_import(filepath=input_file)
        elif input_ext in ['ply']:
            bpy.ops.import_mesh.ply(filepath=input_file)
        elif input_ext in ['stl']:
            bpy.ops.import_mesh.stl(filepath=input_file)
        else:
            print(f"Unsupported input format: {input_ext}")
            sys.exit(1)
    except Exception as e:
        print(f"Import failed: {e}")
        sys.exit(1)
    
    # Export based on extension
    output_ext = output_file.lower().split('.')[-1]
    
    try:
        if output_ext in ['fbx']:
            bpy.ops.export_scene.fbx(filepath=output_file)
        elif output_ext in ['obj']:
            bpy.ops.export_scene.obj(filepath=output_file)
        elif output_ext in ['gltf', 'glb']:
            bpy.ops.export_scene.gltf(filepath=output_file, export_format='GLB' if output_ext == 'glb' else 'GLTF_SEPARATE')
        elif output_ext in ['usd', 'usda', 'usdc']:
            bpy.ops.wm.usd_export(filepath=output_file)
        else:
            print(f"Unsupported output format: {output_ext}")
            sys.exit(1)
    except Exception as e:
        print(f"Export failed: {e}")
        sys.exit(1)
    
    print("Conversion complete!")

if __name__ == "__main__":
    main()
