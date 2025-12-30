
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import sys
import os
import shutil
import time
from pathlib import Path

# Fix module imports
project_root = Path(__file__).resolve().parents[3] 
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

from features.comfyui.premium import PremiumComfyWindow, Colors, Fonts, GlassFrame, PremiumLabel, ActionButton
from utils.gui_lib import THEME_DROPDOWN_FG, THEME_DROPDOWN_BTN, THEME_DROPDOWN_HOVER
from features.comfyui import workflow_utils
from manager.helpers.comfyui_service import ComfyUIService

class SeedVR2_GUI(PremiumComfyWindow):
    def __init__(self):
        super().__init__(title="SeedVR2 Upscaler", width=800, height=700)
        self.video_path = None
        self.is_video = False
        
        self._setup_ui()
        
    def _setup_ui(self):
        # Centered Card Layout
        self.content_area.grid_columnconfigure(0, weight=1)
        self.content_area.grid_rowconfigure(0, weight=1)
        
        # Main Card
        self.card = GlassFrame(self.content_area)
        self.card.grid(row=0, column=0, sticky="nsew", padx=40, pady=20)
        self.card.grid_columnconfigure(0, weight=1)
        
        # 1. Hero Select
        self.hero_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        self.hero_frame.pack(fill="x", padx=30, pady=30)
        
        self.btn_file = ActionButton(self.hero_frame, text="📂 Open Media File", variant="secondary", height=60, command=self.select_file)
        self.btn_file.pack(fill="x")
        
        self.lbl_file_info = PremiumLabel(self.hero_frame, text="No file selected", style="secondary")
        self.lbl_file_info.pack(pady=10)
        
        # 2. Settings Grid
        self.settings = ctk.CTkFrame(self.card, fg_color="transparent")
        self.settings.pack(fill="x", padx=30, pady=10)
        
        # Model
        row1 = ctk.CTkFrame(self.settings, fg_color="transparent")
        row1.pack(fill="x", pady=5)
        PremiumLabel(row1, text="Upscale Model", style="body").pack(side="left")
        self.combo_model = ctk.CTkComboBox(row1, values=["seedvr2_ema_7b_sharp_fp16.safetensors"], width=250,
                                           fg_color=THEME_DROPDOWN_FG, button_color=THEME_DROPDOWN_BTN, button_hover_color=THEME_DROPDOWN_HOVER, border_color=THEME_DROPDOWN_BTN)
        self.combo_model.pack(side="right")
        
        # Resolution
        row2 = ctk.CTkFrame(self.settings, fg_color="transparent")
        row2.pack(fill="x", pady=5)
        PremiumLabel(row2, text="Target Res", style="body").pack(side="left")
        self.combo_res = ctk.CTkComboBox(row2, values=["1024", "2048", "3840"], width=250,
                                         fg_color=THEME_DROPDOWN_FG, button_color=THEME_DROPDOWN_BTN, button_hover_color=THEME_DROPDOWN_HOVER, border_color=THEME_DROPDOWN_BTN)
        self.combo_res.set("2048")
        self.combo_res.pack(side="right")
        
        # Progress
        self.progress_bar = ctk.CTkProgressBar(self.card, height=6, progress_color=Colors.ACCENT_PRIMARY)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=30, pady=(40, 5))
        
        # 3. Action
        self.btn_start = ActionButton(self.card, text="Start Upscale", variant="primary", command=self.start_process, state="disabled")
        self.btn_start.pack(fill="x", padx=30, pady=(10, 30))

    def select_file(self):
        path = filedialog.askopenfilename(filetypes=[("Media", "*.png *.jpg *.mp4 *.mkv")])
        if path:
            self.video_path = path
            self.lbl_file_info.configure(text=f"Selected: {os.path.basename(path)}")
            self.btn_start.configure(state="normal")
            
            # Auto-detect mode
            ext = os.path.splitext(path)[1].lower()
            self.is_video = ext in ['.mp4', '.mkv', '.avi']

    def start_process(self):
        if not self.video_path: return
        self.btn_start.configure(state="disabled", text="Processing")
        self.status_badge.set_status("Queued", "active")
        self.progress_bar.set(0)
        
        threading.Thread(target=self._run_thread, daemon=True).start()

    def _run_thread(self):
        try:
            # Ensure engine
            if not self.client.is_running():
                 service = ComfyUIService()
                 ok, port, _ = service.ensure_running(start_if_missing=True)
                 if ok: self.client.set_active_port(port)

            wf_name = "video_hd.json" if self.is_video else "image_simple.json"
            wf_path = project_root / "ContextUp" / "assets" / "workflows" / "seedvr2" / wf_name
            workflow = workflow_utils.load_workflow(wf_path)
            
            if not workflow: raise Exception("Workflow missing")

            # Input setup
            comfy_in = self.client.comfy_dir / "input"
            comfy_in.mkdir(parents=True, exist_ok=True)
            temp_name = f"uvr_{int(time.time())}{os.path.splitext(self.video_path)[1]}"
            shutil.copy(self.video_path, comfy_in / temp_name)
            
            # Simple updates (Mapping to logic in original file)
            # Assuming util functions handle node search if IDs match standard templates
            # Node 3/1 is Loader, Node 4 is Upscaler
            
            node_loader = "1" if self.is_video else "3"
            workflow_utils.update_node_value(workflow, node_loader, "video" if self.is_video else "image", temp_name)
            
            res = int(self.combo_res.get())
            workflow_utils.update_node_value(workflow, "4", "resolution", res)
            workflow_utils.update_node_value(workflow, "4", "max_resolution", res)
            
            def on_prog(val, max_v):
                self.progress_bar.set(val/max_v)
                
            self.client.generate_image(workflow, progress_callback=on_prog)
            
            self.after(0, lambda: self.status_badge.set_status("Done", "success"))
            self.after(0, lambda: messagebox.showinfo("Done", "Upscaling complete."))
            
        except Exception as e:
            self.after(0, lambda: self.status_badge.set_status("Error", "error"))
            self.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.after(0, lambda: self.btn_start.configure(state="normal", text="Start Upscale"))

if __name__ == "__main__":
    app = SeedVR2_GUI()
    app.mainloop()
