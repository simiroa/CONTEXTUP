"""
Mayo CAD conversion tools.
"""
import subprocess
from pathlib import Path
from tkinter import messagebox
import tkinter as tk

from utils.external_tools import get_mayo

def _get_root():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    root.lift()
    return root

def convert_cad(target_path: str):
    """
    Convert CAD file (STEP/IGES) to OBJ format.
    """
    try:
        from utils.explorer import get_selection_from_explorer
        selection = get_selection_from_explorer(target_path)
        
        if not selection:
            selection = [target_path]
        
        # Filter for CAD files
        cad_exts = {'.step', '.stp', '.iges', '.igs'}
        files_to_convert = [Path(p) for p in selection if Path(p).suffix.lower() in cad_exts]
        
        if not files_to_convert:
            messagebox.showinfo("Info", "No CAD files selected.")
            return
        
        mayo = get_mayo()
        success_count = 0
        errors = []
        
        for path in files_to_convert:
            try:
                output_path = path.with_suffix('.obj')
                
                # Mayo command: mayo-conv -i input.step -o output.obj --export-format obj
                cmd = [
                    mayo,
                    "-i", str(path),
                    "-o", str(output_path),
                    "--export-format", "obj"
                ]
                
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                success_count += 1
                
            except subprocess.CalledProcessError as e:
                error_msg = e.stderr if e.stderr else str(e)
                errors.append(f"{path.name}: {error_msg}")
            except Exception as e:
                errors.append(f"{path.name}: {str(e)}")
        
        # Show results
        if errors:
            msg = f"Converted {success_count}/{len(files_to_convert)} files.\n\nErrors:\n" + "\n".join(errors[:5])
            if len(errors) > 5:
                msg += "\n..."
            messagebox.showwarning("Completed with Errors", msg)
        else:
            messagebox.showinfo("Success", f"Successfully converted {success_count} CAD file(s) to OBJ.")
            
    except FileNotFoundError as e:
        messagebox.showerror("Error", f"Mayo not found: {e}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed: {e}")
