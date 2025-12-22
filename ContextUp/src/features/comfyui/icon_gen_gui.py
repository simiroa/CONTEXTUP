import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import threading
import sys
import io
import random
import time
from pathlib import Path
from PIL import Image

# Add src to path
current_dir = Path(__file__).resolve().parent
src_dir = current_dir.parent.parent
if str(src_dir) not in sys.path:
    sys.path.append(str(src_dir))

from utils.gui_lib import BaseWindow
from features.comfyui.base_gui import ComfyUIFeatureBase
from manager.helpers.comfyui_client import ComfyUIManager

try:
    from rembg import remove
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False

import json
from datetime import datetime

class IconGenGUI(ComfyUIFeatureBase):
    def __init__(self):
        super().__init__(title="AI Icon Generator", width=900, height=750)
        
        # Internal State
        self.is_processing = False
        self.generated_image = None
        self.history = [] # List of dicts: {path, prompt, seed, time}
        self.templates = self._load_templates()
        self.view_mode = "Single" # "Single" or "Grid"
        
        # Client initialized by Base Class self.client
        self._setup_ui()

    def _load_templates(self):
        try:
            path = Path(src_dir).parent / "userdata" / "icon_templates.json"
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Failed to load templates: {e}")
        return {}

    def _save_templates(self):
        try:
            path = Path(src_dir).parent / "userdata" / "icon_templates.json"
            path.parent.mkdir(exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.templates, f, indent=4)
        except Exception as e:
            print(f"Failed to save templates: {e}")

    def _setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # --- Left Panel: Controls ---
        self.left_panel = ctk.CTkFrame(self, width=400, corner_radius=0)
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.left_panel.grid_propagate(False)

        # Header
        ctk.CTkLabel(self.left_panel, text="AI Icon Generator", font=("Segoe UI Display", 20, "bold")).pack(pady=(20, 10), padx=20, anchor="w")

        # Mode Selection
        self.tab_mode = ctk.CTkTabview(self.left_panel, height=300)
        self.tab_mode.pack(fill="x", padx=10, pady=5)
        self.tab_mode.add("Single")
        self.tab_mode.add("Batch")
        
        # -- Single Mode --
        self.txt_prompt = ctk.CTkTextbox(self.tab_mode.tab("Single"), height=100)
        self.txt_prompt.pack(fill="x", pady=(0, 10))
        
        # Templates
        tmpl_frame = ctk.CTkFrame(self.tab_mode.tab("Single"), fg_color="transparent")
        tmpl_frame.pack(fill="x", pady=(0, 10))
        
        self.combo_tmpl = ctk.CTkComboBox(tmpl_frame, values=["Load Template..."] + list(self.templates.keys()), 
                                        command=self._on_template_select, width=150)
        self.combo_tmpl.pack(side="left", padx=(0, 5))
        
        ctk.CTkButton(tmpl_frame, text="Save", width=50, command=self._save_current_as_template).pack(side="left")

        # -- Batch Mode --
        ctk.CTkLabel(self.tab_mode.tab("Batch"), text="Enter one prompt per line:").pack(anchor="w")
        self.txt_batch = ctk.CTkTextbox(self.tab_mode.tab("Batch"), height=200)
        self.txt_batch.pack(fill="both", expand=True, pady=(0, 10))

        # Shared Options
        self.opt_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        self.opt_frame.pack(fill="x", padx=20)
        
        ctk.CTkLabel(self.opt_frame, text="Seed:").pack(side="left", padx=(0, 5))
        self.entry_seed = ctk.CTkEntry(self.opt_frame, width=100, placeholder_text="Random")
        self.entry_seed.pack(side="left")
        ctk.CTkButton(self.opt_frame, text="🎲", width=30, command=lambda: self.entry_seed.delete(0, 'end')).pack(side="left", padx=5)
        
        self.var_rembg = ctk.BooleanVar(value=REMBG_AVAILABLE)
        self.chk_rembg = ctk.CTkCheckBox(self.opt_frame, text="Remove BG", variable=self.var_rembg,
                                        state="normal" if REMBG_AVAILABLE else "disabled")
        self.chk_rembg.pack(side="right")

        # Generate Button
        self.btn_generate = ctk.CTkButton(self.left_panel, text="Generate", height=40, font=("Segoe UI", 14, "bold"),
                                        command=self.start_generation)
        self.btn_generate.pack(fill="x", padx=20, pady=20, side="bottom")

        # --- Right Panel: Preview & Gallery ---
        self.right_panel = ctk.CTkFrame(self, fg_color="#181818", corner_radius=0)
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.right_panel.grid_rowconfigure(0, weight=1)
        self.right_panel.grid_columnconfigure(0, weight=1)

        # Main Preview
        self.preview_label = ctk.CTkLabel(self.right_panel, text="No Image", text_color="gray")
        self.preview_label.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        # Gallery Strip
        self.gallery_frame = ctk.CTkScrollableFrame(self.right_panel, height=100, orientation="horizontal", fg_color="#222")
        self.gallery_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)

        # Grid View Frame (Hidden by default)
        self.grid_frame = ctk.CTkScrollableFrame(self.right_panel, fg_color="transparent")
        # Grid frame will be shown when toggled

        # Actions
        self.action_frame = ctk.CTkFrame(self.right_panel, height=50, fg_color="transparent")
        self.action_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        
        self.lbl_status = ctk.CTkLabel(self.action_frame, text="Ready", text_color="gray")
        self.lbl_status.pack(side="left", padx=10)
        
        self.btn_save_ico = ctk.CTkButton(self.action_frame, text="Save .ICO", state="disabled", command=lambda: self.save("ico"))
        self.btn_save_ico.pack(side="right", padx=5)
        
        self.btn_save_png = ctk.CTkButton(self.action_frame, text="Save .PNG", state="disabled", command=lambda: self.save("png"),
                                        fg_color="#444")
        self.btn_save_png.pack(side="right", padx=5)

        self.btn_view_mode = ctk.CTkButton(self.action_frame, text="Switch to Grid View", command=self.toggle_view_mode,
                                         fg_color="#555", width=120)
        self.btn_view_mode.pack(side="right", padx=20)

    def _on_template_select(self, value):
        if value in self.templates:
            self.txt_prompt.delete("1.0", "end")
            self.txt_prompt.insert("end", self.templates[value])

    def _save_current_as_template(self):
        prompt = self.txt_prompt.get("1.0", "end").strip()
        if not prompt: return
        
        dialog = ctk.CTkInputDialog(text="Enter Template Name:", title="Save Template")
        name = dialog.get_input()
        if name:
            self.templates[name] = prompt
            self._save_templates()
            self.combo_tmpl.configure(values=["Load Template..."] + list(self.templates.keys()))
            messagebox.showinfo("Saved", f"Template '{name}' saved.")

    def start_generation(self):
        if self.is_processing: return
        
        mode = self.tab_mode.get()
        prompts = []
        
        if mode == "Single":
            p = self.txt_prompt.get("1.0", "end").strip()
            if p: prompts.append(p)
        else:
            raw = self.txt_batch.get("1.0", "end").strip()
            if raw: prompts = [line.strip() for line in raw.split('\n') if line.strip()]
            
        if not prompts:
            messagebox.showwarning("Warning", "Please enter prompt(s).")
            return

        # Settings
        seed_raw = self.entry_seed.get().strip()
        try:
            base_seed = int(seed_raw) if seed_raw else None
        except:
            base_seed = None

        self.is_processing = True
        self.btn_generate.configure(state="disabled", text="Generating..." if len(prompts)==1 else f"Batch ({len(prompts)})...")
        self.btn_save_ico.configure(state="disabled")
        self.btn_save_png.configure(state="disabled")
        
        threading.Thread(target=self._run_batch, args=(prompts, base_seed), daemon=True).start()

    def _run_batch(self, prompts, base_seed):
        total = len(prompts)
        for i, prompt in enumerate(prompts):
            if not self.winfo_exists(): break # Stop if closed
            
            # Update Status
            self.after(0, lambda p=i+1, t=total: self.lbl_status.configure(text=f"Processing {p}/{t}..."))
            
            seed = base_seed if base_seed is not None else random.randint(1, 2**32-1)
            # If batching with random, generate new randoms. If fixed, use fixed (or increment? let's stick to fixed or random per item logic usually implies distinct seeds, but user might want consistent seed test. Let's increment seed if fixed to allow variation)
            if base_seed is not None and i > 0:
                 seed += 1
            
            try:
                self._run_single_generation_sync(prompt, seed)
            except Exception as e:
                print(f"Error on item {i}: {e}")
                
        self.after(0, self._on_batch_complete)

    def _run_single_generation_sync(self, prompt, seed):
        # Create Workflow
        workflow = self._create_workflow_json(prompt, seed)
        
        # Execute
        outputs = self.client.generate_image(workflow, output_node_id=9)
        
        if outputs:
            img_data = outputs[0]
            img = Image.open(io.BytesIO(img_data))
            
            # Rembg
            if self.var_rembg.get() and REMBG_AVAILABLE:
                try:
                    img = remove(img)
                    bbox = img.getbbox()
                    if bbox: img = img.crop(bbox)
                except Exception as e:
                    print(f"Rembg failed: {e}")
            
            # Resize
            new_img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
            img.thumbnail((256, 256), Image.Resampling.LANCZOS)
            x = (256 - img.width) // 2
            y = (256 - img.height) // 2
            new_img.paste(img, (x, y), img)
            
            # Add to History (thread-safe UI update)
            self.generated_image = new_img # Keep last as current
            self.history.append({
                "image": new_img,
                "prompt": prompt,
                "seed": seed,
                "time": datetime.now().strftime("%H:%M:%S")
            })
            
            self.after(0, lambda: self._add_to_gallery(new_img, prompt, seed))
            self.after(0, self._show_result) # Show latest
        else:
            raise Exception("No output from ComfyUI")

    def _add_to_gallery(self, img, prompt, seed):
        try:
            # Create thumbnail
            thumb = img.copy()
            thumb.thumbnail((80, 80))
            ctk_thumb = ctk.CTkImage(thumb, size=(80, 80))
            
            btn = ctk.CTkButton(self.gallery_frame, image=ctk_thumb, text="", width=90, height=90,
                              command=lambda i=img, p=prompt, s=seed: self._restore_from_history(i, p, s),
                              fg_color="transparent", border_width=1, border_color="#444")
            btn.pack(side="left", padx=5)
            
            # Scroll to end
            # self.gallery_frame._parent_canvas.yview_moveto(1.0) # Horizontal? xview
        except Exception as e:
            print(f"Gallery error: {e}")

    def _restore_from_history(self, img, prompt, seed):
        self.generated_image = img
        self.txt_prompt.delete("1.0", "end")
        self.txt_prompt.insert("end", prompt)
        self.entry_seed.delete(0, "end")
        self.entry_seed.insert(0, str(seed))
        self._show_result()

    def _on_batch_complete(self):
        self.is_processing = False
        self.lbl_status.configure(text="Ready")
        self.btn_generate.configure(state="normal", text="Generate")

    def _create_workflow_json(self, prompt, seed):
        # Hardcoded Z-Image Workflow from generate_icons_ai.py
        # Using Split Loade logic as per script
        return {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": seed, "steps": 4, "cfg": 1.0, "sampler_name": "euler_ancestral",
                    "scheduler": "simple", "denoise": 1, 
                    "model": ["10", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0]
                }
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": 512, "height": 512, "batch_size": 1}
            },
            "6": { # Positive Prompt
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": f"icon of {prompt}, 3d render, soft glassmorphism, neon glow, black background, minimal, 8k, best quality",
                    "clip": ["12", 0] 
                }
            },
            "7": { # Negative Prompt
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": "text, watermark, low quality, cropped, photo",
                    "clip": ["12", 0]
                }
            },
            "8": { "class_type": "VAEDecode", "inputs": { "samples": ["3", 0], "vae": ["11", 0] } },
            "9": { "class_type": "SaveImage", "inputs": { "filename_prefix": "icon_gen", "images": ["8", 0] } },
            "10": { "class_type": "UNETLoader", "inputs": { "unet_name": "z-image-turbo-fp8-e5m2.safetensors", "weight_dtype": "default" } },
            "11": { "class_type": "VAELoader", "inputs": { "vae_name": "ae.safetensors" } },
            "12": { "class_type": "CLIPLoader", "inputs": { "clip_name": "qwen_3_4b.safetensors", "type": "stable_diffusion" } }
        }

    def _on_error(self, msg):
        self.is_processing = False
        self.lbl_status.configure(text=f"Error: {msg}")
        self.preview_label.configure(text="Error")
        self.btn_generate.configure(state="normal", text="Generate")
        messagebox.showerror("Error", msg)

    def _show_result(self):
        if not self.generated_image: return
        self.btn_save_ico.configure(state="normal")
        self.btn_save_png.configure(state="normal")
        
        # Display
        display_img = self.generated_image.copy()
        
        # Resize to fit right panel
        panel_w = self.right_panel.winfo_width() - 40
        panel_h = self.right_panel.winfo_height() - 200 # Space for gallery
        if panel_w < 100: panel_w = 400
        if panel_h < 100: panel_h = 400
        
        display_img.thumbnail((panel_w, panel_h))
        ctk_img = ctk.CTkImage(display_img, size=display_img.size)
        self.preview_label.configure(image=ctk_img, text="")
        
        # Update Grid if in grid mode
        if self.view_mode == "Grid":
            self.refresh_grid_view()

    def save(self, fmt):
        if not self.generated_image: return
        
        filetypes = [("Icon", "*.ico")] if fmt == "ico" else [("PNG Image", "*.png")]
        def_ext = ".ico" if fmt == "ico" else ".png"
        
        path = filedialog.asksaveasfilename(defaultextension=def_ext, filetypes=filetypes)
        if path:
            try:
                if fmt == "ico":
                     self.generated_image.save(path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
                else:
                    self.generated_image.save(path)
                messagebox.showinfo("Saved", f"Saved to {path}")
            except Exception as e:
                messagebox.showerror("Error", f"Save failed: {e}")

    # --- Grid View Implementation ---
    
    def toggle_view_mode(self):
        if self.view_mode == "Single":
            self.view_mode = "Grid"
            self.btn_view_mode.configure(text="Switch to Single View")
            
            # Hide Single View elements
            self.preview_label.grid_forget()
            self.gallery_frame.grid_forget()
            
            # Show Grid View
            self.refresh_grid_view()
            self.grid_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=10, pady=10)
            
        else:
            self.view_mode = "Single"
            self.btn_view_mode.configure(text="Switch to Grid View")
            
            # Hide Grid View
            self.grid_frame.grid_forget()
            
            # Show Single View elements
            self.preview_label.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
            self.gallery_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
            
            # Restore selection
            self._show_result()

    def refresh_grid_view(self):
        # Clear existing
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
            
        # Populate
        if not self.history:
            ctk.CTkLabel(self.grid_frame, text="No images generated yet.", text_color="gray").pack(pady=20)
            return

        # Simple grid layout logic using pack/frames or grid
        # Let's use grid with dynamic column count based on width is hard in tkinter without recalculation
        # So we use a fixed column count for now (e.g. 4)
        columns = 4
        
        for i, item in enumerate(reversed(self.history)): # Show newest first
            row = i // columns
            col = i % columns
            
            # Thumbnail container
            frame = ctk.CTkFrame(self.grid_frame, fg_color="#333", width=120, height=140)
            frame.grid(row=row, column=col, padx=5, pady=5)
            frame.grid_propagate(False)
            
            # Image
            thumb = item["image"].copy()
            thumb.thumbnail((100, 100))
            ctk_thumb = ctk.CTkImage(thumb, size=(100, 100))
            
            btn = ctk.CTkButton(frame, text="", image=ctk_thumb, 
                              command=lambda it=item: self._select_from_grid(it),
                              fg_color="transparent", hover_color="#444", width=110, height=110)
            btn.pack(pady=(5, 0))
            
            # Index or Prompt hint
            lbl = ctk.CTkLabel(frame, text=f"#{len(self.history)-i}", font=("Arial", 10), text_color="gray")
            lbl.pack(pady=0)

    def _select_from_grid(self, item):
        self.generated_image = item["image"]
        self.txt_prompt.delete("1.0", "end")
        self.txt_prompt.insert("end", item["prompt"])
        self.entry_seed.delete(0, "end")
        self.entry_seed.insert(0, str(item["seed"]))
        
        # Switch back to Single View to edit/save
        self.toggle_view_mode()

    def on_closing(self):
        self.destroy()

if __name__ == "__main__":
    app = IconGenGUI()
    app.mainloop()
