"""
Blender mesh processing tools.
"""
import subprocess
from pathlib import Path
from tkinter import messagebox, simpledialog
import tkinter as tk

from utils.external_tools import get_blender
from utils.gui import ask_selection

def _get_root():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    root.lift()
    return root

def _get_blender_script(script_name):
    """Get path to blender script."""
    current_dir = Path(__file__).parent.parent
    return current_dir / "blender_scripts" / script_name

def convert_mesh(target_path: str):
    """Convert mesh between formats."""
    try:
        from utils.explorer import get_selection_from_explorer
        selection = get_selection_from_explorer(target_path)
        
        if not selection:
            selection = [target_path]
        
        mesh_exts = {'.fbx', '.obj', '.gltf', '.glb', '.usd', '.abc', '.ply', '.stl'}
        files = [Path(p) for p in selection if Path(p).suffix.lower() in mesh_exts]
        
        if not files:
            messagebox.showinfo("Info", "No mesh files selected.")
            return
        
        # Ask for output format
        formats = ["OBJ", "FBX", "GLTF", "GLB", "USD"]
        output_fmt = ask_selection("Convert Mesh", f"Select output format for {len(files)} file(s):", formats)
        if not output_fmt:
            return
        
        blender = get_blender()
        script = _get_blender_script("convert_mesh.py")
        
        success_count = 0
        errors = []
        
        for path in files:
            try:
                output_path = path.with_suffix(f".{output_fmt.lower()}")
                if output_path == path:
                    output_path = path.with_name(f"{path.stem}_converted.{output_fmt.lower()}")
                
                cmd = [blender, "-b", "-P", str(script), "--", str(path), str(output_path)]
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                success_count += 1
                
            except subprocess.CalledProcessError as e:
                errors.append(f"{path.name}: {e.stderr[:100] if e.stderr else str(e)}")
            except Exception as e:
                errors.append(f"{path.name}: {str(e)}")
        
        if errors:
            msg = f"Converted {success_count}/{len(files)} files.\n\nErrors:\n" + "\n".join(errors[:5])
            if len(errors) > 5:
                msg += "\n..."
            messagebox.showwarning("Completed with Errors", msg)
        else:
            messagebox.showinfo("Success", f"Successfully converted {success_count} mesh file(s).")
            
    except Exception as e:
        messagebox.showerror("Error", f"Failed: {e}")

def extract_textures(target_path: str):
    """Extract textures from FBX."""
    try:
        path = Path(target_path)
        
        if path.suffix.lower() != '.fbx':
            messagebox.showinfo("Info", "This tool only works with FBX files.")
            return
        
        output_folder = path.parent / f"{path.stem}_textures"
        
        blender = get_blender()
        script = _get_blender_script("extract_textures.py")
        
        cmd = [blender, "-b", "-P", str(script), "--", str(path), str(output_folder)]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        messagebox.showinfo("Success", f"Textures extracted to:\n{output_folder.name}")
        
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"Blender failed: {e.stderr[:200] if e.stderr else str(e)}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed: {e}")

def optimize_mesh(target_path: str):
    """Optimize mesh using decimation."""
    try:
        from utils.explorer import get_selection_from_explorer
        selection = get_selection_from_explorer(target_path)
        
        if not selection:
            selection = [target_path]
        
        mesh_exts = {'.fbx', '.obj', '.gltf', '.ply', '.stl'}
        files = [Path(p) for p in selection if Path(p).suffix.lower() in mesh_exts]
        
        if not files:
            messagebox.showinfo("Info", "No mesh files selected.")
            return
        
        # Ask for reduction ratio
        root = _get_root()
        ratio = simpledialog.askfloat(
            "Optimize Mesh",
            "Reduction ratio (0.1 = 90% reduction, 1.0 = no reduction):",
            initialvalue=0.5,
            minvalue=0.1,
            maxvalue=1.0,
            parent=root
        )
        
        if not ratio:
            return
        
        blender = get_blender()
        script = _get_blender_script("optimize_mesh.py")
        
        success_count = 0
        errors = []
        
        for path in files:
            try:
                output_path = path.with_name(f"{path.stem}_optimized{path.suffix}")
                
                cmd = [blender, "-b", "-P", str(script), "--", str(path), str(output_path), str(ratio)]
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                success_count += 1
                
            except subprocess.CalledProcessError as e:
                errors.append(f"{path.name}: {e.stderr[:100] if e.stderr else str(e)}")
            except Exception as e:
                errors.append(f"{path.name}: {str(e)}")
        
        if errors:
            msg = f"Optimized {success_count}/{len(files)} files.\n\nErrors:\n" + "\n".join(errors[:5])
            if len(errors) > 5:
                msg += "\n..."
            messagebox.showwarning("Completed with Errors", msg)
        else:
            messagebox.showinfo("Success", f"Successfully optimized {success_count} mesh file(s) to {int(ratio*100)}% of original.")
            
    except Exception as e:
        messagebox.showerror("Error", f"Failed: {e}")
