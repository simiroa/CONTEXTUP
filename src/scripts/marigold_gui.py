import customtkinter as ctk
import os

from tkinter import messagebox
from pathlib import Path
import sys
import threading
from PIL import Image

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.append(str(src_dir))

from utils.gui_lib import BaseWindow, FileListFrame
from utils.ai_runner import run_ai_script

class CTkToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        if self.tooltip_window or not self.text:
            return
        
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        self.tooltip_window = ctk.CTkToplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        label = ctk.CTkLabel(self.tooltip_window, text=self.text, fg_color="#333333", text_color="#ffffff", corner_radius=5, padx=10, pady=5, font=("Arial", 11))
        label.pack()

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


class MarigoldGUI(BaseWindow):
    def __init__(self, target_path):
        super().__init__(title="Marigold PBR Generator", width=500, height=750)
        
        self.target_path = Path(target_path)
        if not self.target_path.exists():
            messagebox.showerror("Error", "File not found.")
            self.destroy()
            return
            
        self.files = [self.target_path]
        
        # UI State
        self.var_depth = ctk.BooleanVar(value=True)
        self.var_normal = ctk.BooleanVar(value=True)
        self.var_flip_y = ctk.BooleanVar(value=False)
        
        self.var_albedo = ctk.BooleanVar(value=False)
        self.var_roughness = ctk.BooleanVar(value=False)
        self.var_metallicity = ctk.BooleanVar(value=False)
        self.var_orm = ctk.BooleanVar(value=False)
        
        self.var_model_ver = ctk.StringVar(value="v1-1")
        self.var_processing_res = ctk.IntVar(value=768) # Default Marigold
        self.var_steps = ctk.IntVar(value=10) # Speed default
        self.var_ensemble = ctk.IntVar(value=1) # Speed default
        self.var_fp16 = ctk.BooleanVar(value=True) # Checkbox for Half Precision
        
        self.create_widgets()
        

    def create_widgets(self):
        # 1. File Info (Minimal Header)
        # Use Entry for compact path display instead of bulky list
        target_name = self.files[0].name if self.files else "Unknown"
        
        info_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        info_frame.pack(fill="x", padx=10, pady=(15, 5))
        
        # Icon
        icon_lbl = ctk.CTkLabel(info_frame, text="📄", font=("Arial", 16))
        icon_lbl.pack(side="left", padx=(5, 10))
        
        # Filename Entry (Read-only)
        self.ent_file = ctk.CTkEntry(info_frame, height=30)
        self.ent_file.pack(side="left", fill="x", expand=True)
        self.ent_file.insert(0, target_name)
        self.ent_file.configure(state="readonly")
        
        # Main Content
        content = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=10, pady=0)
        
        # --- TOP SECTION: OUTPUTS ---
        top_frame = ctk.CTkFrame(content, fg_color="transparent")
        top_frame.pack(fill="x", pady=(5, 5))
        
        # Use Grid for equal 50/50 split to avoid right-side clipping
        top_frame.grid_columnconfigure(0, weight=1)
        top_frame.grid_columnconfigure(1, weight=1)
        
        # 1A. Target Maps (Left)
        map_frame = ctk.CTkFrame(top_frame)
        map_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=0)
        
        ctk.CTkLabel(map_frame, text="Target Maps", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(8, 2))
        
        map_inner = ctk.CTkFrame(map_frame, fg_color="transparent")
        map_inner.pack(fill="both", padx=10, pady=5)
        
        ctk.CTkCheckBox(map_inner, text="Depth", variable=self.var_depth).pack(anchor="w", pady=1)
        ctk.CTkCheckBox(map_inner, text="Normal", variable=self.var_normal).pack(anchor="w", pady=1)
        
        ctk.CTkFrame(map_inner, height=1, fg_color="gray30").pack(fill="x", pady=4)
        
        ctk.CTkCheckBox(map_inner, text="Albedo", variable=self.var_albedo).pack(anchor="w", pady=1)
        ctk.CTkCheckBox(map_inner, text="Roughness", variable=self.var_roughness).pack(anchor="w", pady=1)
        ctk.CTkCheckBox(map_inner, text="Metallicity", variable=self.var_metallicity).pack(anchor="w", pady=1)

        # 1B. Export Format (Right)
        fmt_frame = ctk.CTkFrame(top_frame)
        fmt_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=0)
        
        ctk.CTkLabel(fmt_frame, text="Export Format", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(8, 2))
        
        fmt_inner = ctk.CTkFrame(fmt_frame, fg_color="transparent")
        fmt_inner.pack(fill="both", padx=10, pady=5)
        
        # Shortened text slightly to prevent clipping
        cb_flip = ctk.CTkCheckBox(fmt_inner, text="DX Normal", variable=self.var_flip_y)
        cb_flip.pack(anchor="w", pady=1)
        CTkToolTip(cb_flip, "Flip Y (Green Channel) for DirectX/Unreal.")
        
        ctk.CTkFrame(fmt_inner, height=1, fg_color="gray30").pack(fill="x", pady=4)
        
        cb_orm = ctk.CTkCheckBox(fmt_inner, text="Unreal ORM", variable=self.var_orm)
        cb_orm.pack(anchor="w", pady=1)
        CTkToolTip(cb_orm, "Packed: R=Occlusion, G=Roughness, B=Metallicity")
        
        # --- BOTTOM SECTION: QUALITY ---
        
        qual_frame = ctk.CTkFrame(content)
        qual_frame.pack(fill="x", pady=5)
        
        # Quality Header & Presets (Centered)
        h_frame = ctk.CTkFrame(qual_frame, fg_color="transparent")
        h_frame.pack(anchor="center", pady=(10, 5)) 
        
        ctk.CTkLabel(h_frame, text="Quality:", font=("Arial", 12, "bold")).pack(side="left", padx=5)
        
        # Presets inline
        def create_preset_btn(name, mode, tip):
            btn = ctk.CTkButton(h_frame, text=name, width=60, height=24, fg_color="#4a4a4a", command=lambda: self.set_preset(mode))
            btn.pack(side="left", padx=3)
            CTkToolTip(btn, tip)
            
        create_preset_btn("Speed", "speed", "Fast preview.\n10 Steps, 512px.")
        create_preset_btn("Balanced", "balanced", "Good balance.\n20 Steps, 768px.")
        create_preset_btn("Quality", "quality", "Best details.\n50 Steps, Native Res.")

        # Sliders Area
        slider_frame = ctk.CTkFrame(qual_frame, fg_color=("gray90", "gray16"))
        slider_frame.pack(fill="x", padx=10, pady=5)
        
        # Steps
        s_row = ctk.CTkFrame(slider_frame, fg_color="transparent")
        s_row.pack(fill="x", padx=5, pady=2)
        lbl_s = ctk.CTkLabel(s_row, text="Steps:", width=50, anchor="w")
        lbl_s.pack(side="left")
        CTkToolTip(lbl_s, "More steps = Less noise, better structure.")
        
        ctk.CTkSlider(s_row, from_=1, to=50, number_of_steps=49, variable=self.var_steps, height=16).pack(side="left", fill="x", expand=True, padx=5)
        lbl_s_val = ctk.CTkLabel(s_row, text="10", width=30)
        lbl_s_val.pack(side="right")
        self.var_steps.trace("w", lambda *a: lbl_s_val.configure(text=str(int(self.var_steps.get()))))

        # Passes
        e_row = ctk.CTkFrame(slider_frame, fg_color="transparent")
        e_row.pack(fill="x", padx=5, pady=5)
        lbl_e = ctk.CTkLabel(e_row, text="Passes:", width=50, anchor="w")
        lbl_e.pack(side="left")
        CTkToolTip(lbl_e, "Ensemble Size (Detail Quality).\nRuns multiple times to reduce noise.")
        
        ctk.CTkSlider(e_row, from_=1, to=10, number_of_steps=9, variable=self.var_ensemble, height=16).pack(side="left", fill="x", expand=True, padx=5)
        lbl_e_val = ctk.CTkLabel(e_row, text="1", width=30)
        lbl_e_val.pack(side="right")
        self.var_ensemble.trace("w", lambda *a: lbl_e_val.configure(text=str(int(self.var_ensemble.get()))))

        # Tech Specs Bar
        tech_frame = ctk.CTkFrame(qual_frame, fg_color="transparent")
        tech_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        # Model
        ctk.CTkLabel(tech_frame, text="Ver:").pack(side="left")
        cm_ver = ctk.CTkComboBox(tech_frame, variable=self.var_model_ver, values=["v1-0", "v1-1"], width=70, height=24)
        cm_ver.pack(side="left", padx=2)
        CTkToolTip(cm_ver, "v1-1: Newer.\nv1-0: Legacy.")
        
        # Res
        ctk.CTkLabel(tech_frame, text="Res:").pack(side="left", padx=(10, 0))
        cm_res = ctk.CTkComboBox(tech_frame, variable=self.var_processing_res, values=["0", "512", "768", "1024"], width=70, height=24)
        cm_res.pack(side="left", padx=2)
        CTkToolTip(cm_res, "Processing Res.\n0 = Native.")
        
        # FP16
        cb_fp = ctk.CTkCheckBox(tech_frame, text="FP16", variable=self.var_fp16, checkbox_width=20, checkbox_height=20)
        cb_fp.pack(side="right")
        CTkToolTip(cb_fp, "Use Half Precision (Recommended).")

        # Run
        self.btn_run = ctk.CTkButton(self.main_frame, text="Generate PBR Maps", height=40, font=("Arial", 13, "bold"), command=self.start_generation)
        self.btn_run.pack(fill="x", side="bottom", padx=15, pady=15)
        
        self.lbl_status = ctk.CTkLabel(self.main_frame, text="Ready", text_color="gray", height=20)
        self.lbl_status.pack(side="bottom", pady=0)
        
        self.progress = ctk.CTkProgressBar(self.main_frame, height=10)
        self.progress.pack(side="bottom", fill="x", padx=15, pady=(0, 5))
        self.progress.set(0)

    def set_preset(self, mode):
        if mode == "speed":
            self.var_steps.set(10)
            self.var_ensemble.set(1)
            self.var_processing_res.set(512)
        elif mode == "balanced":
            self.var_steps.set(20)
            self.var_ensemble.set(3)
            self.var_processing_res.set(768)
        elif mode == "quality":
            self.var_steps.set(50)
            self.var_ensemble.set(5)
            self.var_processing_res.set(0) # Native res for max quality
            
    def start_generation(self):
        if not any([self.var_depth.get(), self.var_normal.get(), self.var_albedo.get(), self.var_roughness.get(), self.var_metallicity.get(), self.var_orm.get()]):
            messagebox.showwarning("Warning", "Select at least one map type.")
            return
            
        self.btn_run.configure(state="disabled", text="Processing...")
        self.progress.configure(mode="indeterminate")
        self.progress.start()
        
        threading.Thread(target=self.run_process, daemon=True).start()
        
    def run_process(self):
        try:
            self.update_status("Starting Diffusers...")
            
            args = []
            args.append(str(self.target_path))
            
            if self.var_depth.get(): args.append("--depth")
            if self.var_normal.get(): args.append("--normal")
            if self.var_albedo.get(): args.append("--albedo")
            if self.var_roughness.get(): args.append("--roughness")
            if self.var_metallicity.get(): args.append("--metallicity")
            if self.var_orm.get(): args.append("--orm")
            
            if self.var_flip_y.get(): args.append("--flip_y")
            
            args.append("--res")
            args.append(str(self.var_processing_res.get()))
            
            args.append("--ensemble")
            args.append(str(int(self.var_ensemble.get())))
            
            args.append("--steps")
            args.append(str(int(self.var_steps.get())))
            
            args.append("--model_version")
            args.append(self.var_model_ver.get())
            
            if self.var_fp16.get():
                args.append("--fp16")
                
            success, output = run_ai_script("marigold_inference.py", *args)
            
            if success:
                self.main_frame.after(0, lambda: self.finish_success(output))
            else:
                self.main_frame.after(0, lambda: self.finish_error(output))
                
        except Exception as e:
            self.main_frame.after(0, lambda: self.finish_error(str(e)))

    def update_status(self, text):
        self.lbl_status.configure(text=text)

    def finish_success(self, output):
        self.progress.stop()
        self.progress.set(1)
        self.lbl_status.configure(text="Complete")
        self.btn_run.configure(state="normal", text="Generate PBR Maps")
        
        # Ask to open folder
        parent_dir = self.target_path.parent
        if messagebox.askyesno("Success", f"Maps generated successfully!\n\nOpen output folder?\n{parent_dir}"):
            try:
                os.startfile(parent_dir)
            except Exception as e:
                messagebox.showerror("Error", f"Could not open folder:\n{e}")
        # self.destroy() # Optional: Keep open to verify? Let's close for now or keep open. User might want to tweak.
        
    def finish_error(self, error_msg):
        self.progress.stop()
        self.progress.set(0)
        self.lbl_status.configure(text="Error")
        self.btn_run.configure(state="normal", text="Generate PBR Maps")
        messagebox.showerror("Error", f"Generation Failed:\n{error_msg}")

def run_marigold_gui(target_path):
    app = MarigoldGUI(target_path)
    app.mainloop()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_marigold_gui(sys.argv[1])
    else:
        # Test Stub
        pass
