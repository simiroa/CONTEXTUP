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
        super().__init__(title="Marigold PBR Generator", width=440, height=580)
        
        self.target_path = Path(target_path)
        if not self.target_path.exists():
            messagebox.showerror("Error", "File not found.")
            self.destroy()
            return
            
        self.files = [self.target_path]
        
        # Get input image size
        try:
            with Image.open(self.target_path) as img:
                self.input_width, self.input_height = img.size
        except:
            self.input_width, self.input_height = 0, 0
        
        # UI State - Material Maps (require Albedo)
        self.var_albedo = ctk.BooleanVar(value=False)
        self.var_roughness = ctk.BooleanVar(value=False)
        self.var_metallicity = ctk.BooleanVar(value=False)
        
        # UI State - Geometry Maps (use input directly)
        self.var_depth = ctk.BooleanVar(value=False)
        self.var_normal = ctk.BooleanVar(value=True)
        
        # Export Options
        self.var_flip_y = ctk.BooleanVar(value=False)
        self.var_orm = ctk.BooleanVar(value=False)
        self.var_invert_roughness = ctk.BooleanVar(value=False)
        self.var_output_res = ctk.StringVar(value="768")  # Output resolution
        
        # Technical Settings
        self.var_processing_res = ctk.IntVar(value=768)
        self.var_steps = ctk.IntVar(value=10)
        self.var_ensemble = ctk.IntVar(value=1)
        self.var_fp16 = ctk.BooleanVar(value=True)
        
        self.create_widgets()
        

    def create_widgets(self):
        # 1. File Info (Compact Header)
        target_name = self.files[0].name if self.files else "Unknown"
        size_info = f"  ({self.input_width}×{self.input_height})" if self.input_width > 0 else ""
        
        info_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        info_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        icon_lbl = ctk.CTkLabel(info_frame, text="📄", font=("Arial", 14))
        icon_lbl.pack(side="left", padx=(5, 8))
        
        self.ent_file = ctk.CTkEntry(info_frame, height=26)
        self.ent_file.pack(side="left", fill="x", expand=True)
        self.ent_file.insert(0, f"{target_name}{size_info}")
        self.ent_file.configure(state="readonly")
        
        # Main Content
        content = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=10, pady=0)
        
        # === SECTION 1: Material Maps (Top - Most Important) ===
        mat_frame = ctk.CTkFrame(content)
        mat_frame.pack(fill="x", pady=(5, 3))
        
        mat_header = ctk.CTkFrame(mat_frame, fg_color="transparent")
        mat_header.pack(fill="x", padx=10, pady=(6, 2))
        ctk.CTkLabel(mat_header, text="Material Maps", font=("Arial", 11, "bold")).pack(side="left")
        ctk.CTkLabel(mat_header, text="(Auto-Albedo)", font=("Arial", 9), text_color="gray").pack(side="left", padx=5)
        
        mat_inner = ctk.CTkFrame(mat_frame, fg_color="transparent")
        mat_inner.pack(fill="x", padx=10, pady=(0, 6))
        
        ctk.CTkCheckBox(mat_inner, text="Albedo", variable=self.var_albedo, width=80).pack(side="left", padx=(0, 8))
        ctk.CTkCheckBox(mat_inner, text="Roughness", variable=self.var_roughness, width=95).pack(side="left", padx=8)
        ctk.CTkCheckBox(mat_inner, text="Metallic", variable=self.var_metallicity, width=80).pack(side="left", padx=8)
        
        # === SECTION 2: Geometry Maps ===
        geo_frame = ctk.CTkFrame(content)
        geo_frame.pack(fill="x", pady=3)
        
        geo_header = ctk.CTkFrame(geo_frame, fg_color="transparent")
        geo_header.pack(fill="x", padx=10, pady=(6, 2))
        ctk.CTkLabel(geo_header, text="Geometry Maps", font=("Arial", 11, "bold")).pack(side="left")
        ctk.CTkLabel(geo_header, text="(Direct)", font=("Arial", 9), text_color="gray").pack(side="left", padx=5)
        
        geo_inner = ctk.CTkFrame(geo_frame, fg_color="transparent")
        geo_inner.pack(fill="x", padx=10, pady=(0, 6))
        
        ctk.CTkCheckBox(geo_inner, text="Depth", variable=self.var_depth, width=70).pack(side="left", padx=(0, 8))
        ctk.CTkCheckBox(geo_inner, text="Normal", variable=self.var_normal, width=80).pack(side="left", padx=8)
        
        # === SECTION 3: Quality Settings ===
        qual_frame = ctk.CTkFrame(content)
        qual_frame.pack(fill="x", pady=3)
        
        # Presets
        h_frame = ctk.CTkFrame(qual_frame, fg_color="transparent")
        h_frame.pack(anchor="center", pady=(6, 4))
        
        ctk.CTkLabel(h_frame, text="Quality:", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        
        def create_preset_btn(name, mode, tip):
            btn = ctk.CTkButton(h_frame, text=name, width=55, height=20, fg_color="#4a4a4a", font=("Arial", 10), command=lambda: self.set_preset(mode))
            btn.pack(side="left", padx=2)
            CTkToolTip(btn, tip)
            
        create_preset_btn("Speed", "speed", "10 Steps, 512px")
        create_preset_btn("Balanced", "balanced", "20 Steps, 768px")
        create_preset_btn("Quality", "quality", "50 Steps, Native")

        # Sliders
        slider_frame = ctk.CTkFrame(qual_frame, fg_color=("gray90", "gray16"))
        slider_frame.pack(fill="x", padx=10, pady=4)
        
        # Steps
        s_row = ctk.CTkFrame(slider_frame, fg_color="transparent")
        s_row.pack(fill="x", padx=5, pady=2)
        ctk.CTkLabel(s_row, text="Steps:", width=45, anchor="w", font=("Arial", 10)).pack(side="left")
        ctk.CTkSlider(s_row, from_=1, to=50, number_of_steps=49, variable=self.var_steps, height=12).pack(side="left", fill="x", expand=True, padx=5)
        lbl_s_val = ctk.CTkLabel(s_row, text="10", width=25, font=("Arial", 10))
        lbl_s_val.pack(side="right")
        self.var_steps.trace("w", lambda *a: lbl_s_val.configure(text=str(int(self.var_steps.get()))))

        # Passes
        e_row = ctk.CTkFrame(slider_frame, fg_color="transparent")
        e_row.pack(fill="x", padx=5, pady=2)
        ctk.CTkLabel(e_row, text="Passes:", width=45, anchor="w", font=("Arial", 10)).pack(side="left")
        ctk.CTkSlider(e_row, from_=1, to=10, number_of_steps=9, variable=self.var_ensemble, height=12).pack(side="left", fill="x", expand=True, padx=5)
        lbl_e_val = ctk.CTkLabel(e_row, text="1", width=25, font=("Arial", 10))
        lbl_e_val.pack(side="right")
        self.var_ensemble.trace("w", lambda *a: lbl_e_val.configure(text=str(int(self.var_ensemble.get()))))

        # === SECTION 4: Export Options ===
        export_frame = ctk.CTkFrame(content)
        export_frame.pack(fill="x", pady=(3, 5))
        
        ctk.CTkLabel(export_frame, text="Export Options", font=("Arial", 11, "bold")).pack(anchor="w", padx=10, pady=(6, 4))
        
        export_inner = ctk.CTkFrame(export_frame, fg_color="transparent")
        export_inner.pack(fill="x", padx=10, pady=(0, 6))
        
        # Row 1: Output Size + FP16
        row1 = ctk.CTkFrame(export_inner, fg_color="transparent")
        row1.pack(fill="x", pady=2)
        
        ctk.CTkLabel(row1, text="Output Size:", font=("Arial", 10)).pack(side="left")
        cm_res = ctk.CTkComboBox(row1, variable=self.var_output_res, values=["512", "768", "1024", "2048", "Native"], width=75, height=22)
        cm_res.pack(side="left", padx=5)
        CTkToolTip(cm_res, "Final output resolution")
        
        # Sync with processing res
        def on_res_change(*args):
            val = self.var_output_res.get()
            if val == "Native":
                self.var_processing_res.set(0)
            else:
                try:
                    self.var_processing_res.set(int(val))
                except:
                    self.var_processing_res.set(768)
        self.var_output_res.trace("w", on_res_change)
        
        ctk.CTkCheckBox(row1, text="FP16", variable=self.var_fp16, checkbox_width=16, checkbox_height=16, font=("Arial", 10)).pack(side="right")
        
        # Row 2: Normal options
        row2 = ctk.CTkFrame(export_inner, fg_color="transparent")
        row2.pack(fill="x", pady=2)
        
        cb_flip = ctk.CTkCheckBox(row2, text="DX Normal", variable=self.var_flip_y, width=95, font=("Arial", 10))
        cb_flip.pack(side="left")
        CTkToolTip(cb_flip, "Flip Y for DirectX/Unreal")
        
        cb_orm = ctk.CTkCheckBox(row2, text="ORM Pack", variable=self.var_orm, width=90, font=("Arial", 10))
        cb_orm.pack(side="left", padx=10)
        CTkToolTip(cb_orm, "R=AO, G=Roughness, B=Metallic")
        
        cb_smooth = ctk.CTkCheckBox(row2, text="Invert Rough.", variable=self.var_invert_roughness, width=105, font=("Arial", 10))
        cb_smooth.pack(side="left", padx=10)
        CTkToolTip(cb_smooth, "Roughness → Smoothness")

        # === Bottom: Status & Button ===
        self.progress = ctk.CTkProgressBar(self.main_frame, height=6)
        self.progress.pack(side="bottom", fill="x", padx=15, pady=(0, 5))
        self.progress.set(0)
        
        self.lbl_status = ctk.CTkLabel(self.main_frame, text="Ready", text_color="gray", height=16, font=("Arial", 10))
        self.lbl_status.pack(side="bottom", pady=0)
        
        self.btn_run = ctk.CTkButton(self.main_frame, text="Generate PBR Maps", height=36, font=("Arial", 12, "bold"), command=self.start_generation)
        self.btn_run.pack(fill="x", side="bottom", padx=15, pady=(5, 6))

    def set_preset(self, mode):
        if mode == "speed":
            self.var_steps.set(10)
            self.var_ensemble.set(1)
            self.var_output_res.set("512")
        elif mode == "balanced":
            self.var_steps.set(20)
            self.var_ensemble.set(3)
            self.var_output_res.set("768")
        elif mode == "quality":
            self.var_steps.set(50)
            self.var_ensemble.set(5)
            self.var_output_res.set("Native")
            
    def start_generation(self):
        has_geometry = self.var_depth.get() or self.var_normal.get()
        has_material = self.var_albedo.get() or self.var_roughness.get() or self.var_metallicity.get() or self.var_orm.get()
        
        if not has_geometry and not has_material:
            messagebox.showwarning("Warning", "Select at least one map type.")
            return
        
        # Auto-enable Albedo if material maps are selected
        if has_material and not self.var_albedo.get():
            self.var_albedo.set(True)
            
        self.btn_run.configure(state="disabled", text="Processing...")
        self.progress.configure(mode="indeterminate")
        self.progress.start()
        
        threading.Thread(target=self.run_process, daemon=True).start()
        
    def run_process(self):
        try:
            self.update_status("Starting Marigold...")
            
            args = [str(self.target_path)]
            
            if self.var_depth.get(): args.append("--depth")
            if self.var_normal.get(): args.append("--normal")
            if self.var_albedo.get(): args.append("--albedo")
            if self.var_roughness.get(): args.append("--roughness")
            if self.var_metallicity.get(): args.append("--metallicity")
            if self.var_orm.get(): args.append("--orm")
            
            if self.var_flip_y.get(): args.append("--flip_y")
            if self.var_invert_roughness.get(): args.append("--invert_roughness")
            
            args.extend(["--res", str(self.var_processing_res.get())])
            args.extend(["--ensemble", str(int(self.var_ensemble.get()))])
            args.extend(["--steps", str(int(self.var_steps.get()))])
            args.extend(["--model_version", "v1-1"])  # Hardcoded to latest
            
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
        
        parent_dir = self.target_path.parent
        if messagebox.askyesno("Success", f"Maps generated!\n\nOpen folder?"):
            try:
                os.startfile(parent_dir)
            except Exception as e:
                messagebox.showerror("Error", f"Could not open folder:\n{e}")
        
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
        from utils.batch_runner import collect_batch_context
        
        batch_files = collect_batch_context("marigold_pbr", sys.argv[1], timeout=0.3)
        
        if batch_files is None:
            sys.exit(0)
        
        run_marigold_gui(str(batch_files[0]))
    else:
        pass
