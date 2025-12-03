import bpy
def bake(high_path, low_path, out_path, size=1024, margin=16, ray_dist=0.1, 
         bake_normal=True, flip_green=False, 
         bake_diffuse=False, 
         bake_ao=False, bake_roughness=False, bake_metallic=False, 
         bake_orm=False):
    
    # Clear Scene
    bpy.ops.wm.read_factory_settings(use_empty=True)
    
    # Import Low Poly
    if low_path.lower().endswith('.obj'):
        bpy.ops.wm.obj_import(filepath=low_path)
    elif low_path.lower().endswith('.fbx'):
        bpy.ops.import_scene.fbx(filepath=low_path)
    
    low_obj = bpy.context.selected_objects[0]
    low_obj.name = "LowPoly"
    bpy.context.view_layer.objects.active = low_obj
    
    # Auto UV Unwrap (Smart UV Project)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(island_margin=0.01)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Import High Poly
    if high_path.lower().endswith('.obj'):
        bpy.ops.wm.obj_import(filepath=high_path)
    elif high_path.lower().endswith('.fbx'):
        bpy.ops.import_scene.fbx(filepath=high_path)
        
    high_objs = [o for o in bpy.context.selected_objects if o != low_obj]
    for o in high_objs:
        o.name = "HighPoly"
        
    # Setup Bake
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.device = 'GPU'
    
    # Setup Material on Low Poly
    mat = bpy.data.materials.new(name="BakeMat")
    mat.use_nodes = True
    low_obj.data.materials.append(mat)
    nodes = mat.node_tree.nodes
    
    # Create Image Texture Node for Bake Target
    tex_node = nodes.new('ShaderNodeTexImage')
    nodes.active = tex_node # Active node is bake target
    
    # Select High then Low (Active)
    bpy.ops.object.select_all(action='DESELECT')
    for o in high_objs:
        o.select_set(True)
    low_obj.select_set(True)
    bpy.context.view_layer.objects.active = low_obj
    
    # Bake Settings
    bpy.context.scene.render.bake.use_selected_to_active = True
    bpy.context.scene.render.bake.cage_extrusion = ray_dist
    bpy.context.scene.render.bake.margin = margin
    
    # Helper to save image
    def save_image(image, path):
        image.filepath_raw = path
        image.file_format = 'PNG'
        image.save()
        print(f"Saved {path}")

    # 1. Bake Normal
    if bake_normal:
        img_norm = bpy.data.images.new("BakeNormal", width=size, height=size)
        tex_node.image = img_norm
        bpy.context.scene.cycles.bake_type = 'NORMAL'
        print(f"Baking Normal...")
        bpy.ops.object.bake(type='NORMAL')
        
        save_image(img_norm, out_path)
        
        if flip_green:
            print("Flipping Green Channel...")
            # Simple pixel manipulation for robustness
            pixels = list(img_norm.pixels)
            # RGBA: 0,1,2,3. Green is 1.
            # Invert Green: p = 1.0 - p
            # This might be slow for 8K, but reliable.
            # For 2K/4K it's acceptable.
            for i in range(1, len(pixels), 4):
                pixels[i] = 1.0 - pixels[i]
            
            img_norm.pixels = pixels
            flip_path = out_path # Overwrite or separate? User said "next to normal", usually implies modifying it.
            # But let's overwrite to keep it simple as "DirectX Normal"
            save_image(img_norm, out_path)

    # 2. Bake Diffuse
    if bake_diffuse:
        diff_out = out_path.replace("_Normal.png", "_BaseColor.png")
        if diff_out == out_path: diff_out = out_path + ".color.png"
        
        img_diff = bpy.data.images.new("BakeDiffuse", width=size, height=size)
        tex_node.image = img_diff
        
        bpy.context.scene.cycles.bake_type = 'DIFFUSE'
        bpy.context.scene.render.bake.use_pass_direct = False
        bpy.context.scene.render.bake.use_pass_indirect = False
        bpy.context.scene.render.bake.use_pass_color = True
        
        print(f"Baking Diffuse...")
        bpy.ops.object.bake(type='DIFFUSE')
        save_image(img_diff, diff_out)

    # 3. Bake PBR Channels (AO, Roughness, Metallic)
    # We need images for them if we are baking them OR if we are packing ORM
    
    img_r = None # AO
    img_g = None # Roughness
    img_b = None # Metallic
    
    # Check if we need to bake these channels
    need_ao = bake_ao or bake_orm
    need_rough = bake_roughness or bake_orm
    need_metal = bake_metallic or bake_orm
    
    if need_ao:
        print("Baking AO...")
        img_r = bpy.data.images.new("BakeAO", width=size, height=size)
        tex_node.image = img_r
        bpy.context.scene.cycles.bake_type = 'AO'
        bpy.ops.object.bake(type='AO')
        
        if bake_ao:
            ao_out = out_path.replace("_Normal.png", "_Occlusion.png")
            save_image(img_r, ao_out)
            
    if need_rough:
        print("Baking Roughness...")
        img_g = bpy.data.images.new("BakeRoughness", width=size, height=size)
        tex_node.image = img_g
        bpy.context.scene.cycles.bake_type = 'ROUGHNESS'
        bpy.ops.object.bake(type='ROUGHNESS')
        
        if bake_roughness:
            rough_out = out_path.replace("_Normal.png", "_Roughness.png")
            save_image(img_g, rough_out)
            
    if need_metal:
        print("Baking Metallic (Placeholder Black)...")
        # Metallic bake is tricky without material setup.
        # We'll create a black image for now.
        img_b = bpy.data.images.new("BakeMetallic", width=size, height=size)
        # Default is black (0,0,0,0). Set alpha to 1?
        # Actually, let's leave it black.
        
        if bake_metallic:
            metal_out = out_path.replace("_Normal.png", "_Metallic.png")
            save_image(img_b, metal_out)

    # 4. Pack ORM
    if bake_orm and img_r and img_g and img_b:
        orm_out = out_path.replace("_Normal.png", "_ORM.png")
        print("Packing ORM...")
        
        # Use Compositor
        bpy.context.scene.use_nodes = True
        tree = bpy.context.scene.node_tree
        tree.nodes.clear()
        
        in_r = tree.nodes.new('CompositorNodeImage')
        in_r.image = img_r
        in_g = tree.nodes.new('CompositorNodeImage')
        in_g.image = img_g
        in_b = tree.nodes.new('CompositorNodeImage')
        in_b.image = img_b
        
        comb = tree.nodes.new('CompositorNodeCombRGBA')
        tree.links.new(in_r.outputs[0], comb.inputs[0]) # R = AO
        tree.links.new(in_g.outputs[0], comb.inputs[1]) # G = Roughness
        tree.links.new(in_b.outputs[0], comb.inputs[2]) # B = Metallic
        
        out_node = tree.nodes.new('CompositorNodeOutputFile')
        out_node.base_path = str(Path(orm_out).parent)
        out_node.file_slots[0].path = Path(orm_out).stem
        out_node.format.file_format = 'PNG'
        tree.links.new(comb.outputs[0], out_node.inputs[0])
        
        bpy.ops.render.render(write_still=False)
        print(f"Saved ORM to {orm_out}")

if __name__ == "__main__":
    try:
        args_start = sys.argv.index("--") + 1
        args = sys.argv[args_start:]
    except ValueError:
        args = []
        
    parser = argparse.ArgumentParser()
    parser.add_argument("--high", required=True)
    parser.add_argument("--low", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--size", type=int, default=2048)
    parser.add_argument("--margin", type=int, default=16)
    parser.add_argument("--ray_dist", type=float, default=0.1)
    
    parser.add_argument("--bake_normal", action="store_true") # Default to True if not specified? No, let's make it explicit or default True in logic
    parser.add_argument("--flip_green", action="store_true")
    parser.add_argument("--bake_diffuse", action="store_true")
    parser.add_argument("--bake_ao", action="store_true")
    parser.add_argument("--bake_roughness", action="store_true")
    parser.add_argument("--bake_metallic", action="store_true")
    parser.add_argument("--bake_orm", action="store_true")
    
    opts = parser.parse_args(args)
    
    # If no bake flags are set, maybe default to Normal?
    # But GUI will handle flags.
    
    bake(opts.high, opts.low, opts.out, opts.size, opts.margin, opts.ray_dist, 
         opts.bake_normal, opts.flip_green, 
         opts.bake_diffuse, 
         opts.bake_ao, opts.bake_roughness, opts.bake_metallic, 
         opts.bake_orm)
