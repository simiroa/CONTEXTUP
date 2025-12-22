"""
Blender script for mesh optimization (decimation).
Usage: blender -b -P optimize_mesh.py -- input.fbx output.fbx ratio
"""
import bpy
import sys

def main():
    argv = sys.argv
    if "--" not in argv:
        print("Error: No arguments provided")
        sys.exit(1)
    
    args = argv[argv.index("--") + 1:]
    if len(args) < 3:
        print("Error: Need input, output, and ratio")
        sys.exit(1)
    
    input_file = args[0]
    output_file = args[1]
    ratio = float(args[2])
    
    print(f"Optimizing {input_file} with ratio {ratio}")
    
    # Clear scene
    bpy.ops.wm.read_factory_settings(use_empty=True)
    
    # Import
    input_ext = input_file.lower().split('.')[-1]
    try:
        if input_ext in ['fbx']:
            bpy.ops.import_scene.fbx(filepath=input_file)
        elif input_ext in ['obj']:
            bpy.ops.import_scene.obj(filepath=input_file)
        elif input_ext in ['gltf', 'glb']:
            bpy.ops.import_scene.gltf(filepath=input_file)
        else:
            print(f"Unsupported format: {input_ext}")
            sys.exit(1)
    except Exception as e:
        print(f"Import failed: {e}")
        sys.exit(1)
    
    # Apply decimate modifier to all meshes
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            # Add decimate modifier
            mod = obj.modifiers.new(name="Decimate", type='DECIMATE')
            mod.ratio = ratio
            
            # Apply modifier
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.modifier_apply(modifier="Decimate")
            
            print(f"Decimated {obj.name}")
    
    # Export
    output_ext = output_file.lower().split('.')[-1]
    try:
        if output_ext in ['fbx']:
            bpy.ops.export_scene.fbx(filepath=output_file)
        elif output_ext in ['obj']:
            bpy.ops.export_scene.obj(filepath=output_file)
        elif output_ext in ['gltf', 'glb']:
            bpy.ops.export_scene.gltf(filepath=output_file, export_format='GLB' if output_ext == 'glb' else 'GLTF_SEPARATE')
        else:
            print(f"Unsupported output format: {output_ext}")
            sys.exit(1)
    except Exception as e:
        print(f"Export failed: {e}")
        sys.exit(1)
    
    print("Optimization complete!")

if __name__ == "__main__":
    main()
