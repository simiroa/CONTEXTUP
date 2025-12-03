"""
Auto LOD Generator using PyMeshLab
Generates LODs (Level of Detail) for 3D meshes.
"""
import customtkinter as ctk
from tkinter import messagebox
import threading
import sys
import os
from pathlib import Path
import subprocess

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.append(str(src_dir))

import logging

# Setup logging
log_file = Path(__file__).parent.parent.parent / "debug_gui.log"
logging.basicConfig(filename=str(log_file), level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

from utils.gui_lib import BaseWindow
from utils.explorer import get_selection_from_explorer

class AutoLODGUI(BaseWindow):
    def __init__(self, target_path):
        logging.info(f"Initializing AutoLODGUI with target: {target_path}")
        try:
            super().__init__(title="ContextUp Auto LOD Generator", width=700, height=750)
            logging.info("BaseWindow init complete")
            
            self.target_path = Path(target_path)
            
            # Check if target is a direct mesh file
            mesh_exts = {'.obj', '.ply', '.stl', '.off', '.gltf', '.glb', '.fbx'} 
            
            if self.target_path.is_file() and self.target_path.suffix.lower() in mesh_exts:
                logging.info(f"Target is a direct mesh file: {self.target_path}")
                self.selection = [self.target_path]
            else:
                # Fallback to explorer selection or directory scan
                logging.info("Target is directory or non-mesh, checking explorer selection")
                self.selection = get_selection_from_explorer(target_path)
                if not self.selection:
                    self.selection = [self.target_path]
            
            logging.info(f"Selection: {self.selection}")
            
            self.files = [Path(p) for p in self.selection if Path(p).suffix.lower() in mesh_exts]
            logging.info(f"Filtered files: {self.files}")
            
            if not self.files:
                logging.error("No supported mesh files found.")
                # Show error but don't crash immediately, maybe allow browsing?
                # For now, just show error and close safely
                messagebox.showerror("Error", "No supported mesh files selected.\n(Supported: OBJ, PLY, STL, GLTF, FBX)")
                self.destroy()
                return

            if not self.check_pymeshlab():
                logging.error("PyMeshLab check failed")
                return

            self.create_widgets()
            self.protocol("WM_DELETE_WINDOW", self.on_closing)
            logging.info("Initialization complete, entering mainloop")
        except Exception as e:
            logging.exception("Error during initialization")
            # Ensure we don't hang
            try: self.destroy()
            except: pass
            raise e

    def check_pymeshlab(self):
        logging.info("Checking PyMeshLab dependency...")
        try:
            import pymeshlab
            self.pymeshlab = pymeshlab
            logging.info("PyMeshLab found.")
            return True
        except ImportError:
            logging.warning("PyMeshLab not found in current environment.")
            
            # Check if we can switch to embedded python
            embedded_python = self.get_embedded_python()
            if embedded_python and Path(sys.executable) != embedded_python:
                logging.info(f"Found embedded python at {embedded_python}. Relaunching...")
                try:
                    subprocess.Popen([str(embedded_python), __file__] + sys.argv[1:])
                    self.destroy()
                    sys.exit(0)
                except Exception as e:
                    logging.error(f"Failed to relaunch: {e}")
            
            # If we are here, either we are already in embedded python or relaunch failed
            ans = messagebox.askyesno("Dependency Missing", "PyMeshLab is required for this tool.\nDo you want to install it now?")
            if ans:
                try:
                    logging.info("Installing PyMeshLab...")
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "pymeshlab"])
                    import pymeshlab
                    self.pymeshlab = pymeshlab
                    messagebox.showinfo("Success", "PyMeshLab installed successfully.")
                    logging.info("PyMeshLab installed successfully.")
                    return True
                except Exception as e:
                    logging.error(f"Failed to install PyMeshLab: {e}")
                    messagebox.showerror("Error", f"Failed to install PyMeshLab: {e}")
                    self.destroy()
                    return False
            else:
                logging.info("User declined PyMeshLab installation.")
                self.destroy()
                return False

    def get_embedded_python(self):
        try:
            # Assuming standard structure: src/scripts/mesh_lod_gui.py -> tools/python/python.exe
            script_dir = Path(__file__).parent
            tools_dir = script_dir.parent.parent / "tools"
            python_exe = tools_dir / "python" / "python.exe"
            if python_exe.exists():
                return python_exe
        except:
            pass
        return None

    def create_widgets(self):
        # Main Container with Padding
        self.main_frame.pack_configure(padx=5, pady=5)
        
        # --- Bottom Section (Pack First to ensure visibility) ---
        # Action Buttons (Centered)
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x", padx=5, pady=10)
        
        # Inner frame for centering buttons
        btn_inner = ctk.CTkFrame(btn_frame, fg_color="transparent")
        btn_inner.pack(expand=True)
        
        ctk.CTkButton(btn_inner, text="Cancel", fg_color="transparent", border_width=1, border_color="gray", command=self.destroy, width=100).pack(side="left", padx=10)
        self.btn_run = ctk.CTkButton(btn_inner, text="Generate", command=self.start_generation, height=40, font=ctk.CTkFont(size=14, weight="bold"), width=160)
        self.btn_run.pack(side="left", padx=10)

        # Status Label
        self.lbl_status = ctk.CTkLabel(self.main_frame, text="Ready", text_color="gray")
        self.lbl_status.pack(side="bottom", pady=(0, 5))

        # Progress Bar
        self.progress = ctk.CTkProgressBar(self.main_frame)
        self.progress.pack(side="bottom", fill="x", padx=20, pady=(5, 5))
        self.progress.set(0)

        # Preservation & Policy Options (Centered)
        pres_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        pres_frame.pack(side="bottom", fill="x", padx=5, pady=5)
        
        # Inner frame for centering options
        pres_inner = ctk.CTkFrame(pres_frame, fg_color="transparent")
        pres_inner.pack(expand=True)
        
        # Policy
        ctk.CTkLabel(pres_inner, text="Policy:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(0, 5))
        self.var_policy = ctk.StringVar(value="Merge (Flatten)")
        ctk.CTkComboBox(pres_inner, variable=self.var_policy, values=["Merge (Flatten)", "Keep Separate"], width=130).pack(side="left", padx=(0, 20))

        # Preservation
        ctk.CTkLabel(pres_inner, text="Preservation:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(0, 5))
        
        self.var_uv = ctk.BooleanVar(value=True)
        self.var_normal = ctk.BooleanVar(value=True)
        self.var_boundary = ctk.BooleanVar(value=True)
        
        ctk.CTkCheckBox(pres_inner, text="UVs", variable=self.var_uv, width=50).pack(side="left", padx=5)
        ctk.CTkCheckBox(pres_inner, text="Normals", variable=self.var_normal, width=60).pack(side="left", padx=5)
        ctk.CTkCheckBox(pres_inner, text="Boundary", variable=self.var_boundary, width=60).pack(side="left", padx=5)

        # --- Top Section ---
        # Header
        self.add_header(f"Generate LODs for {len(self.files)} Files")
        
        # Analysis Label
        self.lbl_analysis = ctk.CTkLabel(self.main_frame, text="Analyzing input files...", text_color="gray", justify="center")
        self.lbl_analysis.pack(pady=(0, 5))
        
        # --- Middle Section (Tab View) ---
        self.tabview = ctk.CTkTabview(self.main_frame, width=650, height=400)
        self.tabview.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.tab_lod = self.tabview.add("LOD Chain")
        self.tab_remesh = self.tabview.add("Remesh & Bake")
        
        # === Tab 1: LOD Chain ===
        self.build_lod_tab()

        # === Tab 2: Remesh & Bake ===
        self.build_remesh_tab()
        
        # Start Analysis in Background
        threading.Thread(target=self.analyze_inputs, daemon=True).start()

    def build_lod_tab(self):
        # Center Container
        center_frame = ctk.CTkFrame(self.tab_lod, fg_color="transparent")
        center_frame.pack(expand=True)
        
        # LOD Count
        ctk.CTkLabel(center_frame, text="Number of LODs:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=10, pady=15, sticky="e")
        self.var_lod_count = ctk.IntVar(value=3)
        ctk.CTkComboBox(center_frame, variable=self.var_lod_count, values=["2", "3", "4", "5"], width=70).grid(row=0, column=1, padx=10, sticky="w")
        
        # Reduction Ratio
        ctk.CTkLabel(center_frame, text="Reduction per Step:", font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, padx=10, pady=15, sticky="e")
        
        ratio_frame = ctk.CTkFrame(center_frame, fg_color="transparent")
        ratio_frame.grid(row=1, column=1, columnspan=2, sticky="ew")
        
        self.var_ratio = ctk.DoubleVar(value=0.5)
        self.lbl_ratio = ctk.CTkLabel(ratio_frame, text="50%", width=40)
        self.lbl_ratio.pack(side="right", padx=5)
        
        self.slider_ratio = ctk.CTkSlider(ratio_frame, from_=0.1, to=0.9, variable=self.var_ratio, command=self.update_ratio_label)
        self.slider_ratio.pack(side="left", fill="x", expand=True, padx=5)
        
        ctk.CTkLabel(center_frame, text="(Higher % = Keep more details)", text_color="gray").grid(row=2, column=1, sticky="w", padx=10)

    def build_remesh_tab(self):
        # Center Container
        center_frame = ctk.CTkFrame(self.tab_remesh, fg_color="transparent")
        center_frame.pack(expand=True)
        
        # Target Face Count
        ctk.CTkLabel(center_frame, text="Target Face Count:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=10, pady=15, sticky="e")
        self.var_target_count = ctk.StringVar(value="10000")
        ctk.CTkEntry(center_frame, textvariable=self.var_target_count, width=120).grid(row=0, column=1, padx=10, sticky="w")
        
        # Bake Toggle
        self.var_bake = ctk.BooleanVar(value=False)
        self.chk_bake = ctk.CTkCheckBox(center_frame, text="Enable Baking (Blender)", variable=self.var_bake, command=self.toggle_bake_options, font=ctk.CTkFont(weight="bold", size=14))
        self.chk_bake.grid(row=1, column=0, columnspan=2, padx=10, pady=(15, 10))
        
        # Bake Options Container
        self.bake_frame = ctk.CTkFrame(center_frame, border_width=1, border_color="gray")
        self.bake_frame.grid(row=2, column=0, columnspan=3, padx=10, pady=5)
        
        # Use Grid for internal layout
        self.bake_frame.columnconfigure(1, weight=1)
        self.bake_frame.columnconfigure(3, weight=1)
        self.bake_frame.columnconfigure(5, weight=1)

        # --- Row 0: Settings ---
        ctk.CTkLabel(self.bake_frame, text="Resolution:").grid(row=0, column=0, padx=(15, 5), pady=10, sticky="e")
        self.var_bake_size = ctk.StringVar(value="2048")
        ctk.CTkComboBox(self.bake_frame, variable=self.var_bake_size, values=["1024", "2048", "4096", "8192"], width=80).grid(row=0, column=1, padx=5, pady=10, sticky="w")
        
        ctk.CTkLabel(self.bake_frame, text="Ray Dist:").grid(row=0, column=2, padx=(10, 5), pady=10, sticky="e")
        self.var_ray_dist = ctk.StringVar(value="0.1")
        ctk.CTkEntry(self.bake_frame, textvariable=self.var_ray_dist, width=50).grid(row=0, column=3, padx=5, pady=10, sticky="w")
        
        ctk.CTkLabel(self.bake_frame, text="Margin:").grid(row=0, column=4, padx=(10, 5), pady=10, sticky="e")
        self.var_margin = ctk.StringVar(value="16")
        ctk.CTkEntry(self.bake_frame, textvariable=self.var_margin, width=50).grid(row=0, column=5, padx=5, pady=10, sticky="w")

        # --- Separator ---
        ctk.CTkFrame(self.bake_frame, height=2, fg_color="#404040").grid(row=1, column=0, columnspan=6, sticky="ew", padx=10, pady=5)

        # --- Row 2: Base Color (Swapped) ---
        self.var_bake_diffuse = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(self.bake_frame, text="Base Color (Diffuse)", variable=self.var_bake_diffuse).grid(row=2, column=0, columnspan=2, padx=20, pady=5, sticky="w")

        # --- Row 3: Normal (Swapped) ---
        self.var_bake_normal = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(self.bake_frame, text="Normal Map", variable=self.var_bake_normal).grid(row=3, column=0, columnspan=2, padx=20, pady=5, sticky="w")
        
        self.var_flip_green = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(self.bake_frame, text="Flip Green Channel", variable=self.var_flip_green, font=ctk.CTkFont(size=11)).grid(row=3, column=2, columnspan=2, padx=5, pady=5, sticky="w")

        # --- Row 4: PBR ---
        self.var_bake_ao = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(self.bake_frame, text="AO", variable=self.var_bake_ao, width=50).grid(row=4, column=0, padx=20, pady=5, sticky="w")
        
        self.var_bake_rough = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(self.bake_frame, text="Roughness", variable=self.var_bake_rough, width=80).grid(row=4, column=1, padx=5, pady=5, sticky="w")
        
        self.var_bake_metal = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(self.bake_frame, text="Metallic", variable=self.var_bake_metal, width=60).grid(row=4, column=2, padx=5, pady=5, sticky="w")

        # --- Row 5: ORM ---
        self.var_bake_orm = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(self.bake_frame, text="Pack ORM (AO/Rough/Metal)", variable=self.var_bake_orm, font=ctk.CTkFont(weight="bold")).grid(row=5, column=0, columnspan=4, padx=20, pady=(5, 10), sticky="w")
        
        # Output Info
        ctk.CTkLabel(center_frame, text="Output: Same folder as input (suffix _Texture)", text_color="gray").grid(row=3, column=0, columnspan=3, padx=10, pady=10)
        
        # Initialize State
        self.toggle_bake_options()

    def toggle_bake_options(self):
        state = "normal" if self.var_bake.get() else "disabled"
        
        # Helper to recursively set state
        def set_state(widget, s):
            try:
                widget.configure(state=s)
            except:
                pass
            for child in widget.winfo_children():
                set_state(child, s)
                
        set_state(self.bake_frame, state)

    def update_ratio_label(self, value):
        self.lbl_ratio.configure(text=f"{int(value * 100)}%")

    def get_blender_path(self):
        # Try to find embedded blender
        try:
            script_dir = Path(__file__).parent
            tools_dir = script_dir.parent.parent / "tools"
            potential_paths = list(tools_dir.glob("**/blender.exe"))
            if potential_paths:
                return potential_paths[0]
        except:
            pass
        return None

    def analyze_inputs(self):
        try:
            ms = self.pymeshlab.MeshSet()
            total_faces = 0
            has_uv = False
            tex_count = 0
            sidecar_tex = 0
            
            if self.files:
                path = self.files[0]
                ms.load_new_mesh(str(path))
                m = ms.current_mesh()
                total_faces = m.face_number()
                
                has_uv = m.has_wedge_tex_coord()
                
                try:
                    tex_count = m.texture_number()
                except:
                    pass
                
                stem = path.stem
                parent = path.parent
                img_exts = ['.png', '.jpg', '.jpeg', '.tga', '.exr', '.tif', '.tiff', '.bmp']
                
                for f in parent.glob(f"{stem}*"):
                    if f.suffix.lower() in img_exts:
                        sidecar_tex += 1
                
                msg = f"Input: {path.name}\nFaces: {total_faces:,}"
                
                if has_uv:
                    msg += " | UVs: Yes"
                else:
                    msg += " | UVs: NO (Texture Bake may fail)"
                
                if tex_count > 0:
                    msg += f" | Textures (Mesh): {tex_count}"
                elif sidecar_tex > 0:
                    msg += f" | Textures (Folder): {sidecar_tex} found"
                else:
                    msg += " | Textures: None detected"
                
                if len(self.files) > 1:
                    msg += f"\n(+ {len(self.files)-1} other files)"
                
                color = "gray"
                if not has_uv:
                    color = "orange"
                elif tex_count == 0 and sidecar_tex == 0:
                    color = "yellow"
                
                self.after(0, lambda: self.lbl_analysis.configure(text=msg, text_color=color))
        except Exception as e:
            self.after(0, lambda: self.lbl_analysis.configure(text=f"Analysis failed: {e}"))

    def start_generation(self):
        # Capture all UI values on the main thread to ensure thread safety
        params = {}
        
        try:
            params['active_tab'] = self.tabview.get()
            params['policy'] = self.var_policy.get()
            params['count'] = self.var_lod_count.get()
            params['ratio'] = self.var_ratio.get()
            
            params['preserve_uv'] = self.var_uv.get()
            params['preserve_normal'] = self.var_normal.get()
            params['preserve_boundary'] = self.var_boundary.get()
            
            # Mode logic
            mode = "Single Proxy" if params['active_tab'] == "Remesh & Bake" else "LOD Chain"
            params['mode'] = mode
            
            params['do_bake'] = self.var_bake.get() if mode == "Single Proxy" else False
            
            params['bake_size'] = self.var_bake_size.get()
            params['bake_ray'] = self.var_ray_dist.get()
            params['bake_margin'] = self.var_margin.get()
            
            params['bake_normal'] = self.var_bake_normal.get()
            params['flip_green'] = self.var_flip_green.get()
            params['bake_diffuse'] = self.var_bake_diffuse.get()
            params['bake_ao'] = self.var_bake_ao.get()
            params['bake_rough'] = self.var_bake_rough.get()
            params['bake_metal'] = self.var_bake_metal.get()
            params['bake_orm'] = self.var_bake_orm.get()
            
            try:
                params['target_count'] = int(self.var_target_count.get())
            except:
                params['target_count'] = 10000
                
            params['blender_exe'] = self.get_blender_path()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read settings: {e}")
            return

        self.btn_run.configure(state="disabled", text="Processing...")
        threading.Thread(target=self.run_generation, args=(params,), daemon=True).start()

    def run_generation(self, params):
        ms = self.pymeshlab.MeshSet()
        
        # Unpack params for easier usage
        mode = params['mode']
        policy = params['policy']
        count = params['count']
        ratio = params['ratio']
        
        preserve_uv = params['preserve_uv']
        preserve_normal = params['preserve_normal']
        preserve_boundary = params['preserve_boundary']
        
        do_bake = params['do_bake']
        blender_exe = params['blender_exe']
        
        if do_bake and not blender_exe:
            print("Blender not found.")
        
        total_files = len(self.files)
        success_count = 0
        errors = []
        
        for i, path in enumerate(self.files):
            self.after(0, lambda p=path, idx=i: self.lbl_status.configure(text=f"Processing {idx+1}/{total_files}: {p.name}"))
            self.after(0, lambda val=i/total_files: self.progress.set(val))
            
            try:
                ms.clear()
                ms.load_new_mesh(str(path))
                
                if policy == "Merge (Flatten)":
                    try:
                        ms.flatten_visible_layers()
                    except:
                        pass 
                
                stem = path.stem
                if "_LOD" in stem:
                    stem = stem.split("_LOD")[0]
                
                out_suffix = path.suffix
                if out_suffix.lower() == '.fbx':
                    out_suffix = '.obj'

                if mode == "Single Proxy":
                    target_faces = params['target_count']
                    
                    if preserve_uv:
                        try:
                            ms.apply_filter('meshing_decimation_quadric_edge_collapse_with_texture', 
                                          targetfacenum=target_faces, 
                                          preserveboundary=preserve_boundary, 
                                          preservenormal=preserve_normal
                                          )
                        except Exception as e:
                            print(f"Texture decimation failed: {e}. Falling back to standard decimation.")
                            ms.apply_filter('meshing_decimation_quadric_edge_collapse', 
                                          targetfacenum=target_faces, 
                                          preserveboundary=preserve_boundary, 
                                          preservenormal=preserve_normal
                                          )
                    else:
                        ms.apply_filter('meshing_decimation_quadric_edge_collapse', 
                                      targetfacenum=target_faces, 
                                      preserveboundary=preserve_boundary, 
                                      preservenormal=preserve_normal
                                      )
                    
                    out_dir = path.parent
                    out_path = out_dir / f"{stem}_Proxy{out_suffix}"
                    ms.save_current_mesh(str(out_path))
                    
                    if do_bake and blender_exe:
                        self.after(0, lambda p=path: self.lbl_status.configure(text=f"Baking {p.name}..."))
                        bake_script = Path(__file__).parent / "blender_bake.py"
                        bake_out = out_dir / f"{stem}_Normal.png"
                        
                        cmd = [
                            str(blender_exe),
                            "--background",
                            "--python", str(bake_script),
                            "--",
                            "--high", str(path),
                            "--low", str(out_path),
                            "--out", str(bake_out),
                            "--size", str(params['bake_size']),
                            "--ray_dist", str(params['bake_ray']),
                            "--margin", str(params['bake_margin'])
                        ]
                        
                        if params['bake_normal']: cmd.append("--bake_normal")
                        if params['flip_green']: cmd.append("--flip_green")
                        if params['bake_diffuse']: cmd.append("--bake_diffuse")
                        if params['bake_ao']: cmd.append("--bake_ao")
                        if params['bake_rough']: cmd.append("--bake_roughness")
                        if params['bake_metal']: cmd.append("--bake_metallic")
                        if params['bake_orm']: cmd.append("--bake_orm")
                        
                        subprocess.run(cmd, check=True, capture_output=True)
                    
                else:
                    lod0_path = path.parent / f"{stem}_LOD0{out_suffix}"
                    ms.save_current_mesh(str(lod0_path))
                    
                    current_poly_count = ms.current_mesh().face_number()
                    
                    for lod_level in range(1, count):
                        target_faces = int(current_poly_count * (ratio ** lod_level))
                        if target_faces < 100: target_faces = 100
                        
                        if preserve_uv:
                            try:
                                ms.apply_filter('meshing_decimation_quadric_edge_collapse_with_texture', 
                                              targetfacenum=target_faces, 
                                              preserveboundary=preserve_boundary, 
                                              preservenormal=preserve_normal
                                              )
                            except Exception as e:
                                print(f"Texture decimation failed for LOD{lod_level}: {e}. Falling back.")
                                ms.apply_filter('meshing_decimation_quadric_edge_collapse', 
                                              targetfacenum=target_faces, 
                                              preserveboundary=preserve_boundary, 
                                              preservenormal=preserve_normal
                                              )
                        else:
                            ms.apply_filter('meshing_decimation_quadric_edge_collapse', 
                                          targetfacenum=target_faces, 
                                          preserveboundary=preserve_boundary, 
                                          preservenormal=preserve_normal
                                          )
                        
                        lod_path = path.parent / f"{stem}_LOD{lod_level}{out_suffix}"
                        ms.save_current_mesh(str(lod_path))
                
                success_count += 1
                
            except Exception as e:
                errors.append(f"{path.name}: {e}")
        
        self.after(0, lambda: self.progress.set(1.0))
        self.after(0, lambda: self.lbl_status.configure(text="Done"))
        self.after(0, lambda: self.btn_run.configure(state="normal", text="Generate LODs"))
        
        if errors:
            msg = f"Completed with errors ({success_count}/{total_files} success).\n\n" + "\n".join(errors[:5])
            self.after(0, lambda: messagebox.showwarning("Result", msg))
        else:
            self.after(0, lambda: messagebox.showinfo("Success", f"Successfully generated LODs for {success_count} files."))
            self.after(0, self.destroy)

    def on_closing(self):
        self.destroy()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        app = AutoLODGUI(sys.argv[1])
        app.mainloop()
    else:
        app = AutoLODGUI(str(Path.cwd()))
        app.mainloop()
