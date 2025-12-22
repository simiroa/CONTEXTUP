"""
Blender script for extracting textures from FBX.
Usage: blender -b -P extract_textures.py -- input.fbx output_folder
"""
import bpy
import sys
import os
from pathlib import Path

def main():
    argv = sys.argv
    if "--" not in argv:
        print("Error: No arguments provided")
        sys.exit(1)
    
    args = argv[argv.index("--") + 1:]
    if len(args) < 2:
        print("Error: Need input file and output folder")
        sys.exit(1)
    
    input_file = args[0]
    output_folder = args[1]
    
    print(f"Extracting textures from {input_file} to {output_folder}")
    
    # Create output folder
    Path(output_folder).mkdir(parents=True, exist_ok=True)
    
    # Clear scene
    bpy.ops.wm.read_factory_settings(use_empty=True)
    
    # Import FBX
    try:
        bpy.ops.import_scene.fbx(filepath=input_file)
    except Exception as e:
        print(f"Import failed: {e}")
        sys.exit(1)
    
    # Extract textures
    extracted_count = 0
    
    for mat in bpy.data.materials:
        if mat.use_nodes:
            for node in mat.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image:
                    img = node.image
                    
                    # Save image
                    if img.packed_file:
                        # Unpack and save
                        img_name = img.name if img.name else f"texture_{extracted_count}"
                        # Ensure extension
                        if not any(img_name.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.tga', '.bmp']):
                            img_name += '.png'
                        
                        output_path = os.path.join(output_folder, img_name)
                        img.filepath_raw = output_path
                        img.file_format = 'PNG'
                        img.save()
                        extracted_count += 1
                        print(f"Extracted: {img_name}")
                    elif img.filepath:
                        # Copy existing file
                        import shutil
                        src = bpy.path.abspath(img.filepath)
                        if os.path.exists(src):
                            dst = os.path.join(output_folder, os.path.basename(src))
                            shutil.copy2(src, dst)
                            extracted_count += 1
                            print(f"Copied: {os.path.basename(src)}")
    
    print(f"Extracted {extracted_count} textures")

if __name__ == "__main__":
    main()
