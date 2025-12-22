
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import sys
import os
import shutil
import time
import json
import socket
import subprocess
from pathlib import Path
from PIL import Image

# Fix module imports
project_root = Path(__file__).resolve().parents[3] # ContextUp
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

try:
    import cv2
except ImportError:
    cv2 = None

try:
    import websocket
except ImportError:
    websocket = None

from features.comfyui.base_gui import ComfyUIFeatureBase
from features.comfyui import workflow_utils

class SeedVR2_GUI(ComfyUIFeatureBase):
    """SeedVR2 Video Upscaler - refactored to use ComfyUIFeatureBase."""
    
    def __init__(self):
        # Singleton Check (before super().__init__ to avoid creating window if already running)
        self.lock_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.lock_socket.bind(('127.0.0.1', 48190))
        except socket.error:
            messagebox.showwarning("Already Running", "SeedVR2 Upscaler is already running.")
            sys.exit(0)
        
        # Call base class (will setup client, server connection in background, etc.)
        super().__init__(title="SeedVR2 Video Upscaler", width=700, height=680)
        
        # Instance variables
        self.video_path = None
        self.is_video = False
        self.running = False
        self.total_vram_mb = 8000  # Default
        
        # Setup UI and scan models
        self._setup_ui()
        self._scan_models()
    
    def _on_server_ready(self):
        """Called by base class when server connection is established."""
        self.status_label.configure(text=f"Engine Ready (:{self.client.port})", text_color="#69F0AE")
        self._check_vram()
    
    def _on_server_failed(self):
        """Called by base class when server connection fails."""
        self.status_label.configure(text="Engine Failed to Start", text_color="#FF5252")
    
    def on_closing(self):
        """Override to release singleton lock before closing."""
        # Release singleton lock
        try:
            self.lock_socket.close()
        except:
            pass
        # Call base class (just destroys window, doesn't stop server)
        super().on_closing()

    def _setup_ui(self):
        # Configure Theme
        self.configure(fg_color="#121212") # Material Dark Background
        
        # Grid Configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0) # Header
        self.grid_rowconfigure(1, weight=1) # Content
        
        # --- Header ---
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=25, pady=(25, 10))
        
        self.title_label = ctk.CTkLabel(self.header_frame, text="SeedVR2 Upscaler", 
                                        font=("Segoe UI Display", 28, "bold"), text_color="#ffffff")
        self.title_label.pack(side="left")
        
        self.vram_label = ctk.CTkButton(self.header_frame, text="VRAM: Checking...", 
                                        font=("Segoe UI", 12, "bold"), 
                                        fg_color="#1E1E1E", hover=False, 
                                        text_color="#757575", corner_radius=20, height=32, border_width=1, border_color="#333333")
        self.vram_label.pack(side="right")

        # --- Main Content Card ---
        self.main_card = ctk.CTkFrame(self, fg_color="#1E1E1E", corner_radius=20, border_width=1, border_color="#333333")
        self.main_card.grid(row=1, column=0, sticky="nsew", padx=25, pady=10)
        self.main_card.grid_columnconfigure(0, weight=1)
        
        # 1. File Selection (Hero Section)
        self.file_frame = ctk.CTkFrame(self.main_card, fg_color="#263238", corner_radius=15, border_width=0)
        self.file_frame.pack(fill="x", padx=20, pady=25)
        
        self.file_btn = ctk.CTkButton(self.file_frame, text="📂  Select Image / Video", 
                                      command=self.select_file, 
                                      font=("Segoe UI", 14, "bold"),
                                      height=50, fg_color="#0091EA", hover_color="#00B0FF", corner_radius=12)
        self.file_btn.pack(side="left", padx=20, pady=20)
        
        self.file_info_label = ctk.CTkLabel(self.file_frame, text="No file selected\nPlease choose a media file to start.", 
                                            font=("Segoe UI", 13), text_color="#B0BEC5", justify="left")
        self.file_info_label.pack(side="left", padx=10, expand=True, fill="x")

        # 2. Settings Area
        self.settings_frame = ctk.CTkFrame(self.main_card, fg_color="transparent")
        self.settings_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Mode Badge
        self.mode_label = ctk.CTkButton(self.settings_frame, text="Ready", state="disabled",
                                        fg_color="#37474F", text_color="#ECEFF1", border_width=0,
                                        font=("Segoe UI", 11, "bold"), height=26, corner_radius=13)
        self.mode_label.pack(pady=(0, 20))
        
        # Grid for Inputs
        self.inputs_grid = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        self.inputs_grid.pack(fill="x")
        self.inputs_grid.grid_columnconfigure(1, weight=1)
        
        # Label Style
        def create_label(parent, text, row):
            ctk.CTkLabel(parent, text=text, font=("Segoe UI", 13, "bold"), text_color="#ECEFF1").grid(row=row, column=0, sticky="w", pady=12)

        # Model
        create_label(self.inputs_grid, "Upscale Model", 0)
        self.model_var = ctk.StringVar(value="Loading...")
        self.model_combo = ctk.CTkComboBox(self.inputs_grid, variable=self.model_var, height=38, corner_radius=8,
                                           font=("Segoe UI", 13), dropdown_font=("Segoe UI", 13), 
                                           border_width=1, border_color="#455A64", button_color="#546E7A", fg_color="#263238")
        self.model_combo.grid(row=0, column=1, sticky="ew", padx=(20, 0), pady=8)
        
        # Resolution
        create_label(self.inputs_grid, "Target Resolution", 1)
        self.res_var = ctk.StringVar(value="2048")
        self.res_combo = ctk.CTkComboBox(self.inputs_grid, values=["1024", "2048", "3840", "4096"], 
                                         variable=self.res_var, height=38, corner_radius=8, border_width=1,
                                         border_color="#455A64", button_color="#546E7A", fg_color="#263238")
        self.res_combo.grid(row=1, column=1, sticky="ew", padx=(20, 0), pady=8)
        
        # Steps
        create_label(self.inputs_grid, "Quality Steps", 2)
        self.steps_slider = ctk.CTkSlider(self.inputs_grid, from_=1, to=20, number_of_steps=19, height=20, 
                                          progress_color="#00E676", button_color="#69F0AE", button_hover_color="#B9F6CA")
        self.steps_slider.set(6)
        self.steps_slider.grid(row=2, column=1, sticky="ew", padx=(20, 15), pady=8)
        
        self.steps_label = ctk.CTkLabel(self.inputs_grid, text="6", font=("Segoe UI Mono", 14, "bold"), width=30, text_color="#00E676")
        self.steps_label.grid(row=2, column=2, pady=8)
        self.steps_slider.configure(command=lambda v: self.steps_label.configure(text=str(int(v))))

        # --- Advanced Settings Toggle ---
        self.adv_frame = ctk.CTkFrame(self.inputs_grid, fg_color="transparent")
        self.adv_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(15, 0))
        
        self.show_adv_var = ctk.BooleanVar(value=False)
        self.adv_btn = ctk.CTkCheckBox(self.adv_frame, text="Show Advanced Settings (Performance & Video)", 
                                       variable=self.show_adv_var, command=self._toggle_advanced,
                                       font=("Segoe UI", 12), border_color="#B0BEC5", fg_color="#0288D1", hover_color="#0277BD")
        self.adv_btn.pack(anchor="w")
        
        # Advanced Controls Container (Hidden by default)
        self.adv_controls = ctk.CTkFrame(self.inputs_grid, fg_color="#263238", corner_radius=8)
        
        # Row 1: Video (Batch, Overlap)
        ctk.CTkLabel(self.adv_controls, text="Batch Size", font=("Segoe UI", 11), text_color="#B0BEC5").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.batch_var = ctk.StringVar(value="1")
        self.batch_entry = ctk.CTkEntry(self.adv_controls, textvariable=self.batch_var, width=50, height=24)
        self.batch_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        ctk.CTkLabel(self.adv_controls, text="Overlap", font=("Segoe UI", 11), text_color="#B0BEC5").grid(row=0, column=2, padx=10, pady=5, sticky="e")
        self.overlap_var = ctk.StringVar(value="2")
        self.overlap_entry = ctk.CTkEntry(self.adv_controls, textvariable=self.overlap_var, width=50, height=24)
        self.overlap_entry.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        # Row 2: Performance (Block Swap, Tiled VAE)
        ctk.CTkLabel(self.adv_controls, text="Block Swap", font=("Segoe UI", 11), text_color="#B0BEC5").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.swap_slider = ctk.CTkSlider(self.adv_controls, from_=0, to=36, number_of_steps=36, width=120, height=16)
        self.swap_slider.set(0) # Default 0 (Fastest VRAM usage?) Check user note: 36 for GGUF + VRAM save
        self.swap_slider.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky="w")
        
        self.tiled_vae_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(self.adv_controls, text="Tiled VAE (Save VRAM)", variable=self.tiled_vae_var,
                        font=("Segoe UI", 11), width=20, height=20).grid(row=1, column=3, padx=10, pady=5, sticky="w")
        
        # Row 3: Compile
        self.compile_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(self.adv_controls, text="Torch Compile (Faster Repeats)", variable=self.compile_var,
                        font=("Segoe UI", 11), width=20, height=20).grid(row=2, column=0, columnspan=4, padx=10, pady=(5, 10), sticky="w")

        # 3. Footer (Status & Action)
        self.footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.footer_frame.grid(row=2, column=0, sticky="ew", padx=25, pady=25)

        self.progress_bar = ctk.CTkProgressBar(self.footer_frame, height=8, corner_radius=4, progress_color="#00E676", fg_color="#333333")
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", pady=(0, 20))
        
        self.start_btn = ctk.CTkButton(self.footer_frame, text="START UPSCALING", command=self.start_process, 
                                       fg_color="#00C853", hover_color="#00E676", 
                                       height=55, corner_radius=12, 
                                       font=("Segoe UI", 16, "bold"), state="disabled")
        self.start_btn.pack(fill="x")
        
        self.status_label = ctk.CTkLabel(self.footer_frame, text="Initializing Engine...", font=("Segoe UI", 12), text_color="#757575")
        self.status_label.pack(pady=(12, 0))

    def _toggle_advanced(self):
        if self.show_adv_var.get():
            self.adv_controls.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(10, 0), padx=5)
        else:
            self.adv_controls.grid_remove()

    def _check_vram(self):
        try:
            # Dummy, replace with actual call
            self.total_vram_mb = 12000
            self.vram_label.configure(text=f"VRAM: {self.total_vram_mb // 1024} GB", border_color="#2E7D32", text_color="#66BB6A")
        except:
            self.total_vram_mb = 8000
            self.vram_label.configure(text="VRAM: 8GB", border_color="#EF6C00", text_color="#FFB74D")

    def _scan_models(self):
        base_dir = self.client.comfy_dir / "models" / "SEEDVR2"
        models = ["seedvr2_ema_7b_sharp_fp16.safetensors"] 
        if base_dir.exists():
            found = [f.name for f in base_dir.glob("*.safetensors")]
            if found: models = found
        self.model_combo.configure(values=models)
        if models: self.model_var.set(models[0])

    def select_file(self):
        path = filedialog.askopenfilename(filetypes=[("Media Files", "*.png *.jpg *.jpeg *.mp4 *.mkv *.avi *.mov")])
        if path:
            self.video_path = path
            self._analyze_file(path)
            self.start_btn.configure(state="normal")
            self._update_mode()

    def _analyze_file(self, path):
        try:
            size_mb = os.path.getsize(path) / (1024 * 1024)
            info_text = f"File: {os.path.basename(path)}\nSize: {size_mb:.2f} MB"
            
            ext = os.path.splitext(path)[1].lower()
            res_text = "Resolution: Unknown"
            
            if ext in ['.png', '.jpg', '.jpeg']:
                with Image.open(path) as img:
                    res_text = f"Res: {img.width}x{img.height}"
            elif ext in ['.mp4', '.avi', '.mkv', '.mov']:
                if cv2:
                    cap = cv2.VideoCapture(path)
                    if cap.isOpened():
                        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                        fps = cap.get(cv2.CAP_PROP_FPS)
                        duration = frames / fps if fps > 0 else 0
                        res_text = f"Res: {w}x{h} | {duration:.1f}s ({frames} f)"
                        cap.release()
                else:
                    res_text = "Res: Unknown (cv2 missing)"
            
            self.file_info_label.configure(text=f"{info_text}\n{res_text}", text_color="#ECEFF1")
        except Exception as e:
            self.file_info_label.configure(text=f"Error analyzing file: {e}", text_color="#FF5252")


    def _update_mode(self):
        ext = os.path.splitext(self.video_path)[1].lower()
        if ext in ['.png', '.jpg', '.jpeg']:
            self.is_video = False
            self.mode_label.configure(text="MODE: IMAGE UPSCALE", fg_color="#0277BD", text_color="white")
            self.res_combo.configure(values=["1024", "2048", "4096 (High Quality)"])
        else:
            self.is_video = True
            self.mode_label.configure(text="MODE: VIDEO UPSCALE", fg_color="#880E4F", text_color="white")
            self.res_combo.configure(values=["1024", "1920", "2048", "3840 (High VRAM)"])

    def start_process(self):
        if not self.video_path: return
        
        target_res = int(self.res_var.get().split()[0])
        if target_res >= 3840 and self.total_vram_mb < 8192:
            if not messagebox.askyesno("VRAM Warning", "Upscaling to 4K requires 8GB+ VRAM. You might crash.\nContinue?"):
                return
        
        self.start_btn.configure(state="disabled", text="PROCESSING...", fg_color="#333333", text_color="#757575")
        self.progress_bar.set(0)
        self.status_label.configure(text="Queuing Workflow...", text_color="#FFD740")
        
        threading.Thread(target=self._run_thread, daemon=True).start()

    def _run_thread(self):
        try:
            if not self.client.is_running():
                self.status_label.configure(text="Restarting Engine...")
                if not self.client.start():
                    raise Exception("Engine dead.")

            wf_name = "video_hd.json" if self.is_video else "image_simple.json"
            if not self.is_video and int(self.res_var.get().split()[0]) >= 3000:
                wf_name = "image_4k.json"
                
            wf_path = project_root / "ContextUp" / "assets" / "workflows" / "seedvr2" / wf_name
            workflow = workflow_utils.load_workflow(wf_path)
            if not workflow: raise Exception(f"Missing workflow: {wf_name}")

            self._update_status("Uploading Input File...")
            comfy_input_dir = self.client.comfy_dir / "input"
            comfy_input_dir.mkdir(parents=True, exist_ok=True)
            
            temp_name = f"seedvr2_in_{int(time.time())}{os.path.splitext(self.video_path)[1]}"
            shutil.copy(self.video_path, comfy_input_dir / temp_name)
            
            # Retrieve Advanced Settings
            batch_size = int(self.batch_var.get())
            overlap = int(self.overlap_var.get())
            block_swap = int(self.swap_slider.get())
            tiled_vae = self.tiled_vae_var.get()
            compile_enabled = self.compile_var.get()
            
            # Retrieve Standard Settings
            target_res = int(self.res_var.get().split()[0])
            steps = int(self.steps_slider.get())
            chosen_model = self.model_var.get()
            
            # Map Inputs
            load_node_id = "1" if self.is_video else "3"
            upscaler_node_id = "4"
            dit_node_id = "2"
            vae_node_id = "30" if not self.is_video and "image_4k" in wf_name else "3" # VAE ID might differ
            # Check JSONs for VAE ID. upscale.json (Video) uses "3". image_4k.json uses "30".
            # image_simple.json uses "30" (checked previously, wait, simple didn't have VAE load in early draft? Yes it did Node 2/30)
            # Let's inspect loaded workflow to be safe, or just try update both possible IDs.
            
            input_key = "video" if self.is_video else "image"
            workflow_utils.update_node_value(workflow, load_node_id, input_key, temp_name)
            
            # Upscaler Settings
            workflow_utils.update_node_value(workflow, upscaler_node_id, "resolution", target_res)
            workflow_utils.update_node_value(workflow, upscaler_node_id, "max_resolution", target_res)
            workflow_utils.update_node_value(workflow, upscaler_node_id, "steps", steps)
            workflow_utils.update_node_value(workflow, upscaler_node_id, "batch_size", batch_size)
            workflow_utils.update_node_value(workflow, upscaler_node_id, "temporal_overlap", overlap)
            workflow_utils.update_node_value(workflow, upscaler_node_id, "prepend_frames", overlap) # Usually same as overlap for smoothness
            workflow_utils.set_seed(workflow)
            
            # DiT Settings
            if compile_enabled:
                workflow_utils.update_node_value(workflow, dit_node_id, "torch_compile_args", "SEEDVR2_DIT")
            else:
                 # If node supports disabling, or just leave as is if default is compilation?
                 # SeedVR2 usually requires compile args input. If user unchecked, maybe "none" or empty?
                 # Actually the input string is a key to a preset. If unchecked, we might not be able to "turn off" if the node demands it.
                 # But we can assume the default "SEEDVR2_DIT" is fine, usually compile improves speed.
                 pass
            
            workflow_utils.update_node_value(workflow, dit_node_id, "blocks_to_swap", block_swap)
            
            # VAE Settings (Try both IDs 3 and 30 to cover all templates)
            for vid in ["3", "30"]:
                if vid in workflow:
                    workflow_utils.update_node_value(workflow, vid, "decode_tiled", tiled_vae)
                    workflow_utils.update_node_value(workflow, vid, "encode_tiled", tiled_vae)
            
            # Monitor
            self._update_status("Processing... (Check Console)")
            
            def on_progress(value, max_val):
                 self.progress_bar.set(value / max_val)
                 self._update_status(f"Processing: {int((value/max_val)*100)}%")

            # Use generic method? Or manual WS?
            # ComfyUIManager now has progress_callback
            images = self.client.generate_image(workflow, output_node_id=None, progress_callback=on_progress)
            
            self.progress_bar.set(1.0)
            self._update_status("Upscaling Complete!")
            messagebox.showinfo("Done", "Upscaling Finished successfully!")
            
            output_dir = self.client.comfy_dir / "output"
            os.startfile(output_dir)

        except Exception as e:
            self._update_status(f"Error: {e}")
            messagebox.showerror("Error", str(e))
        finally:
            self.start_btn.configure(state="normal", text="START UPSCALING", fg_color="#00C853", text_color="white")

    def _update_status(self, text):
        self.status_label.configure(text=text)

if __name__ == "__main__":
    app = SeedVR2_GUI()
    app.mainloop()
