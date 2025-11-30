"""
QuadWild remeshing tools.
"""
import subprocess
import traceback
from pathlib import Path
from tkinter import messagebox
import tkinter as tk

from utils.external_tools import get_quadwild

def _get_root():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    root.lift()
    return root

class QuadWildOptionsDialog(tk.simpledialog.Dialog):
    """Dialog for QuadWild remeshing options."""
    
    def __init__(self, parent, title="QuadWild Options"):
        self.result = None
        super().__init__(parent, title)
    
    def body(self, master):
        # Mesh Type
        tk.Label(master, text="Mesh Type:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.mesh_type = tk.StringVar(value="organic")
        tk.Radiobutton(master, text="Organic (Smooth surfaces)", variable=self.mesh_type, value="organic").grid(row=1, column=0, sticky=tk.W, padx=20)
        tk.Radiobutton(master, text="Mechanical (Sharp edges)", variable=self.mesh_type, value="mechanical").grid(row=2, column=0, sticky=tk.W, padx=20)
        
        # Quad Size
        tk.Label(master, text="Quad Size:", font=("Arial", 10, "bold")).grid(row=3, column=0, sticky=tk.W, pady=(10, 5))
        self.quad_size = tk.DoubleVar(value=1.0)
        size_frame = tk.Frame(master)
        size_frame.grid(row=4, column=0, sticky=tk.W, padx=20)
        tk.Label(size_frame, text="Small").pack(side=tk.LEFT)
        tk.Scale(size_frame, from_=0.5, to=2.0, resolution=0.1, orient=tk.HORIZONTAL, variable=self.quad_size, length=150).pack(side=tk.LEFT, padx=5)
        tk.Label(size_frame, text="Large").pack(side=tk.LEFT)
        
        # Detail Preservation
        tk.Label(master, text="Detail Preservation:", font=("Arial", 10, "bold")).grid(row=5, column=0, sticky=tk.W, pady=(10, 5))
        self.preserve_detail = tk.BooleanVar(value=False)
        tk.Checkbutton(master, text="Preserve original detail (disable remesh)", variable=self.preserve_detail).grid(row=6, column=0, sticky=tk.W, padx=20)
        
        # Cleanup Options
        tk.Label(master, text="Cleanup:", font=("Arial", 10, "bold")).grid(row=7, column=0, sticky=tk.W, pady=(10, 5))
        self.cleanup_mode = tk.StringVar(value="folder")
        tk.Radiobutton(master, text="Move intermediate files to subfolder", variable=self.cleanup_mode, value="folder").grid(row=8, column=0, sticky=tk.W, padx=20)
        tk.Radiobutton(master, text="Delete intermediate files", variable=self.cleanup_mode, value="delete").grid(row=9, column=0, sticky=tk.W, padx=20)
        tk.Radiobutton(master, text="Keep all files", variable=self.cleanup_mode, value="keep").grid(row=10, column=0, sticky=tk.W, padx=20)
        
        return None
    
    def apply(self):
        self.result = {
            'mesh_type': self.mesh_type.get(),
            'quad_size': self.quad_size.get(),
            'preserve_detail': self.preserve_detail.get(),
            'cleanup_mode': self.cleanup_mode.get()
        }

def remesh_quad(target_path: str):
    """Auto quad remeshing using QuadWild (2-step process with options)."""
    try:
        path = Path(target_path)
        
        if path.suffix.lower() != '.obj':
            messagebox.showinfo("Info", "QuadWild only works with OBJ files.\nConvert your mesh to OBJ first.")
            return
        
        # Show options dialog
        root = _get_root()
        dialog = QuadWildOptionsDialog(root)
        
        if not dialog.result:
            return
        
        options = dialog.result
        quadwild_dir = Path(get_quadwild()).parent
        
        # Create custom config files based on user options
        import tempfile
        temp_dir = Path(tempfile.gettempdir())
        
        # Prep config
        prep_config = temp_dir / "quadwild_prep.txt"
        sharp_thr = "35" if options['mesh_type'] == 'mechanical' else "-1"
        do_remesh = "0" if options['preserve_detail'] else "1"
        
        with open(prep_config, 'w') as f:
            f.write(f"do_remesh {do_remesh}\n")
            f.write(f"sharp_feature_thr {sharp_thr}\n")
            f.write(f"alpha 0.02\n")
            f.write(f"scaleFact {options['quad_size']}\n")
        
        # Main config (copy from flow.txt and modify scaleFact)
        base_config = quadwild_dir / "config" / "main_config" / "flow.txt"
        main_config = temp_dir / "quadwild_main.txt"
        
        with open(base_config, 'r') as f:
            config_lines = f.readlines()
        
        with open(main_config, 'w') as f:
            for line in config_lines:
                if line.startswith('scaleFact'):
                    f.write(f"scaleFact {options['quad_size']}\n")
                else:
                    f.write(line)
        
        # Step 1: Preparation
        quadwild_exe = get_quadwild()
        cmd1 = [quadwild_exe, str(path), "2", str(prep_config)]
        
        try:
            result1 = subprocess.run(cmd1, check=True, capture_output=True, text=True, cwd=str(quadwild_dir))
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"QuadWild Step 1 failed:\n{e.stderr[:300] if e.stderr else str(e)}")
            return
        
        # Step 2: Quad mesh generation
        rem_p0_file = path.with_name(f"{path.stem}_rem_p0.obj")
        
        if not rem_p0_file.exists():
            messagebox.showerror("Error", f"Step 1 output not found:\n{rem_p0_file.name}")
            return
        
        quad_from_patches = quadwild_dir / "quad_from_patches.exe"
        cmd2 = [str(quad_from_patches), str(rem_p0_file), str(main_config)]
        
        try:
            result2 = subprocess.run(cmd2, check=True, capture_output=True, text=True, cwd=str(quadwild_dir))
        except subprocess.CalledProcessError:
            pass  # May "fail" but still produce output
        
        # Look for output files
        output_smooth = path.with_name(f"{path.stem}_rem_p0_1_quadrangulation_smooth.obj")
        output_regular = path.with_name(f"{path.stem}_rem_p0_1_quadrangulation.obj")
        final_output = path.with_name(f"{path.stem}_quad.obj")
        
        # Collect intermediate files for cleanup
        intermediate_files = [
            rem_p0_file,
            path.with_name(f"{path.stem}_rem.obj"),
            path.with_name(f"{path.stem}_rem.rosy"),
            path.with_name(f"{path.stem}_rem.sharp"),
            path.with_name(f"{path.stem}_rem_p0.corners"),
            path.with_name(f"{path.stem}_rem_p0.c_feature"),
            path.with_name(f"{path.stem}_rem_p0.feature"),
            path.with_name(f"{path.stem}_rem_p0.patch"),
            output_smooth,
            output_regular
        ]
        
        # Filter to only existing files
        existing_intermediates = [f for f in intermediate_files if f.exists()]
        
        if output_smooth.exists():
            import shutil
            shutil.copy2(str(output_smooth), str(final_output))
            
            # Cleanup based on user preference
            cleanup_msg = ""
            if options['cleanup_mode'] == 'folder':
                # Move to subfolder
                cleanup_folder = path.parent / f"{path.stem}_quadwild_intermediate"
                cleanup_folder.mkdir(exist_ok=True)
                
                for f in existing_intermediates:
                    try:
                        shutil.move(str(f), str(cleanup_folder / f.name))
                    except:
                        pass
                cleanup_msg = f"\n\nIntermediate files moved to:\n{cleanup_folder.name}/"
                
            elif options['cleanup_mode'] == 'delete':
                # Delete intermediate files
                deleted_count = 0
                for f in existing_intermediates:
                    try:
                        f.unlink()
                        deleted_count += 1
                    except:
                        pass
                cleanup_msg = f"\n\nCleaned up {deleted_count} intermediate files"
            
            else:  # keep
                cleanup_msg = f"\n\nIntermediate files kept in place"
            
            settings_info = f"Settings:\n- Type: {options['mesh_type'].title()}\n- Quad Size: {options['quad_size']}x\n- Detail: {'Preserved' if options['preserve_detail'] else 'Remeshed'}"
            messagebox.showinfo("Success", f"Quad remesh complete!\n\n{settings_info}\n\nOutput: {final_output.name}{cleanup_msg}")
        elif output_regular.exists():
            import shutil
            shutil.copy2(str(output_regular), str(final_output))
            messagebox.showinfo("Success", f"Quad remesh complete!\n\nOutput: {final_output.name}")
        else:
            messagebox.showwarning("Warning", "QuadWild completed but output files not found.\nCheck the mesh folder for *_quadrangulation*.obj files.")
        
    except FileNotFoundError as e:
        messagebox.showerror("Error", f"QuadWild not found: {e}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed: {e}\n\n{traceback.format_exc()[:300]}")
