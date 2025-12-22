"""
QuadWild remeshing tools.
"""
import subprocess
import traceback
from pathlib import Path
import customtkinter as ctk
from tkinter import messagebox
import threading
import shutil
import tempfile
import sys

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.append(str(src_dir))

from utils.external_tools import get_quadwild
from utils.gui_lib import BaseWindow

class QuadWildGUI(BaseWindow):
    def __init__(self, target_path):
        super().__init__(title="ContextUp QuadWild Remesher", width=600, height=600)
        
        self.path = Path(target_path)
        if self.path.suffix.lower() != '.obj':
            messagebox.showinfo("Info", "QuadWild only works with OBJ files.\nConvert your mesh to OBJ first.")
            self.destroy()
            return
            
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_widgets(self):
        # Header
        self.add_header(f"Remeshing: {self.path.name}")
        
        # Options Frame
        opt_frame = ctk.CTkFrame(self.main_frame)
        opt_frame.pack(fill="x", padx=20, pady=10)
        
        # Mesh Type
        ctk.CTkLabel(opt_frame, text="Mesh Type:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", padx=20, pady=(10, 5))
        self.mesh_type = ctk.StringVar(value="organic")
        ctk.CTkRadioButton(opt_frame, text="Organic (Smooth surfaces)", variable=self.mesh_type, value="organic").grid(row=1, column=0, sticky="w", padx=20, pady=2)
        ctk.CTkRadioButton(opt_frame, text="Mechanical (Sharp edges)", variable=self.mesh_type, value="mechanical").grid(row=2, column=0, sticky="w", padx=20, pady=2)
        
        # Quad Size
        ctk.CTkLabel(opt_frame, text="Quad Size:", font=ctk.CTkFont(weight="bold")).grid(row=3, column=0, sticky="w", padx=20, pady=(15, 5))
        self.quad_size = ctk.DoubleVar(value=1.0)
        
        size_frame = ctk.CTkFrame(opt_frame, fg_color="transparent")
        size_frame.grid(row=4, column=0, sticky="w", padx=20)
        ctk.CTkLabel(size_frame, text="Small").pack(side="left")
        ctk.CTkSlider(size_frame, from_=0.5, to=2.0, number_of_steps=15, variable=self.quad_size, width=200).pack(side="left", padx=10)
        ctk.CTkLabel(size_frame, text="Large").pack(side="left")
        
        # Detail Preservation
        ctk.CTkLabel(opt_frame, text="Detail Preservation:", font=ctk.CTkFont(weight="bold")).grid(row=5, column=0, sticky="w", padx=20, pady=(15, 5))
        self.preserve_detail = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(opt_frame, text="Preserve original detail (disable remesh)", variable=self.preserve_detail).grid(row=6, column=0, sticky="w", padx=20, pady=2)
        
        # Cleanup Options
        ctk.CTkLabel(opt_frame, text="Cleanup:", font=ctk.CTkFont(weight="bold")).grid(row=7, column=0, sticky="w", padx=20, pady=(15, 5))
        self.cleanup_mode = ctk.StringVar(value="folder")
        ctk.CTkRadioButton(opt_frame, text="Move intermediate files to subfolder", variable=self.cleanup_mode, value="folder").grid(row=8, column=0, sticky="w", padx=20, pady=2)
        ctk.CTkRadioButton(opt_frame, text="Delete intermediate files", variable=self.cleanup_mode, value="delete").grid(row=9, column=0, sticky="w", padx=20, pady=2)
        ctk.CTkRadioButton(opt_frame, text="Keep all files", variable=self.cleanup_mode, value="keep").grid(row=10, column=0, sticky="w", padx=20, pady=2)
        
        # Log Area
        ctk.CTkLabel(self.main_frame, text="Log:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(10, 5))
        self.log_area = ctk.CTkTextbox(self.main_frame, height=100, font=("Consolas", 10))
        self.log_area.pack(fill="both", expand=True, padx=20, pady=5)
        
        # Buttons
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        
        self.btn_run = ctk.CTkButton(btn_frame, text="Start Remeshing", command=self.start_remeshing)
        self.btn_run.pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="Close", fg_color="transparent", border_width=1, border_color="gray", command=self.destroy).pack(side="right", padx=5)

    def log(self, msg):
        self.log_area.insert("end", msg + "\n")
        self.log_area.see("end")

    def start_remeshing(self):
        self.btn_run.configure(state="disabled", text="Running...")
        self.log("Starting QuadWild process...")
        threading.Thread(target=self.run_process, daemon=True).start()

    def run_process(self):
        try:
            options = {
                'mesh_type': self.mesh_type.get(),
                'quad_size': self.quad_size.get(),
                'preserve_detail': self.preserve_detail.get(),
                'cleanup_mode': self.cleanup_mode.get()
            }
            
            quadwild_dir = Path(get_quadwild()).parent
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
            
            # Main config
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
            
            # Step 1
            self.after(0, lambda: self.log("Step 1: Analyzing geometry..."))
            quadwild_exe = get_quadwild()
            cmd1 = [quadwild_exe, str(self.path), "2", str(prep_config)]
            
            try:
                subprocess.run(cmd1, check=True, capture_output=True, text=True, cwd=str(quadwild_dir))
            except subprocess.CalledProcessError as e:
                self.after(0, lambda: self.log(f"Error in Step 1: {e.stderr}"))
                self.after(0, lambda: self.btn_run.configure(state="normal", text="Start Remeshing"))
                return
            
            # Step 2
            self.after(0, lambda: self.log("Step 2: Generating quads..."))
            rem_p0_file = self.path.with_name(f"{self.path.stem}_rem_p0.obj")
            
            if not rem_p0_file.exists():
                self.after(0, lambda: self.log(f"Error: Step 1 output not found: {rem_p0_file.name}"))
                self.after(0, lambda: self.btn_run.configure(state="normal", text="Start Remeshing"))
                return
            
            quad_from_patches = quadwild_dir / "quad_from_patches.exe"
            cmd2 = [str(quad_from_patches), str(rem_p0_file), str(main_config)]
            
            try:
                subprocess.run(cmd2, check=True, capture_output=True, text=True, cwd=str(quadwild_dir))
            except subprocess.CalledProcessError:
                pass # May fail but produce output
            
            # Check outputs
            output_smooth = self.path.with_name(f"{self.path.stem}_rem_p0_1_quadrangulation_smooth.obj")
            output_regular = self.path.with_name(f"{self.path.stem}_rem_p0_1_quadrangulation.obj")
            final_output = self.path.with_name(f"{self.path.stem}_quad.obj")
            
            # Cleanup
            intermediate_files = [
                rem_p0_file,
                self.path.with_name(f"{self.path.stem}_rem.obj"),
                self.path.with_name(f"{self.path.stem}_rem.rosy"),
                self.path.with_name(f"{self.path.stem}_rem.sharp"),
                self.path.with_name(f"{self.path.stem}_rem_p0.corners"),
                self.path.with_name(f"{self.path.stem}_rem_p0.c_feature"),
                self.path.with_name(f"{self.path.stem}_rem_p0.feature"),
                self.path.with_name(f"{self.path.stem}_rem_p0.patch"),
                output_smooth,
                output_regular
            ]
            
            existing_intermediates = [f for f in intermediate_files if f.exists()]
            
            if output_smooth.exists() or output_regular.exists():
                src = output_smooth if output_smooth.exists() else output_regular
                shutil.copy2(str(src), str(final_output))
                
                cleanup_msg = ""
                if options['cleanup_mode'] == 'folder':
                    cleanup_folder = self.path.parent / f"{self.path.stem}_quadwild_intermediate"
                    cleanup_folder.mkdir(exist_ok=True)
                    for f in existing_intermediates:
                        try:
                            shutil.move(str(f), str(cleanup_folder / f.name))
                        except: pass
                    cleanup_msg = f"Intermediates moved to {cleanup_folder.name}/"
                    
                elif options['cleanup_mode'] == 'delete':
                    for f in existing_intermediates:
                        try:
                            f.unlink()
                        except: pass
                    cleanup_msg = "Intermediates deleted."
                
                self.after(0, lambda: self.log(f"Success! Output: {final_output.name}"))
                self.after(0, lambda: self.log(cleanup_msg))
                self.after(0, lambda: messagebox.showinfo("Success", f"Quad remesh complete!\nOutput: {final_output.name}"))
                
            else:
                self.after(0, lambda: self.log("Warning: Output files not found."))
                self.after(0, lambda: messagebox.showwarning("Warning", "QuadWild completed but output files not found."))
            
        except Exception as e:
            self.after(0, lambda: self.log(f"Error: {e}"))
            self.after(0, lambda: messagebox.showerror("Error", f"Failed: {e}"))
            
        self.after(0, lambda: self.btn_run.configure(state="normal", text="Start Remeshing"))

    def on_closing(self):
        self.destroy()

def remesh_quad(target_path: str):
    """Auto quad remeshing using QuadWild."""
    try:
        app = QuadWildGUI(target_path)
        app.mainloop()
    except Exception as e:
        messagebox.showerror("Error", f"Failed: {e}")

