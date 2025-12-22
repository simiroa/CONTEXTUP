import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import threading
import sys
import os
import json
import time
import shutil
import random
from pathlib import Path
from PIL import Image, ImageTk
import io
import subprocess

# Add src to path
current_dir = Path(__file__).resolve().parent
src_dir = current_dir.parent.parent
if str(src_dir) not in sys.path:
    sys.path.append(str(src_dir))

from utils.gui_lib import BaseWindow
from features.comfyui.base_gui import ComfyUIFeatureBase
from manager.helpers.comfyui_client import ComfyUIManager
from features.comfyui import workflow_utils
# from features.ai.standalone.ollama_text_refine import refine_text # Moved to runtime import


class ZImageTurboGUI(ComfyUIFeatureBase):
    def __init__(self):
        super().__init__(title="Z Image Turbo", width=1100, height=850)
        
        # Internal State
        self.prompts = []  # List of CTkTextbox widgets
        self.prompt_frames = [] # List of frames holding textboxes and buttons
        self.generated_images = [] # List of paths
        self.is_processing = False
        
        # Client initialized by Base Class self.client
        
        # UI Setup
        self._setup_ui()
        
        # Add initial prompt box
        self.add_prompt_box()

    def _setup_ui(self):
        # Configure Grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # --- Left Panel: Controls ---
        self.control_panel = ctk.CTkFrame(self, width=400, corner_radius=0)
        self.control_panel.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.control_panel.grid_propagate(False) 
        
        # Header
        ctk.CTkLabel(self.control_panel, text="Z Image Turbo", 
                    font=("Segoe UI Display", 24, "bold")).pack(pady=(20, 10), padx=20, anchor="w")
        
        # Prompt Area (Scrollable)
        self.prompt_scroll = ctk.CTkScrollableFrame(self.control_panel, fg_color="transparent")
        self.prompt_scroll.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Add Prompt Button
        self.btn_add_prompt = ctk.CTkButton(self.control_panel, text="+ Add Prompt Layer", 
                                          command=self.add_prompt_box, fg_color="#333", hover_color="#444")
        self.btn_add_prompt.pack(fill="x", padx=20, pady=5)
        
        # Advanced Settings Toggle
        self.adv_var = ctk.BooleanVar(value=False)
        self.chk_adv = ctk.CTkCheckBox(self.control_panel, text="Show Advanced Settings", 
                                      variable=self.adv_var, command=self._toggle_advanced)
        self.chk_adv.pack(pady=10, padx=20, anchor="w")
        
        # Advanced Settings Frame (Hidden by default)
        self.adv_frame = ctk.CTkFrame(self.control_panel, fg_color="transparent")
        
        # -- Batch Size
        self.lbl_batch = ctk.CTkLabel(self.adv_frame, text="Batch Size: 1")
        self.lbl_batch.pack(anchor="w", padx=10)
        self.slider_batch = ctk.CTkSlider(self.adv_frame, from_=1, to=4, number_of_steps=3, command=self._update_batch_label)
        self.slider_batch.set(1)
        self.slider_batch.pack(fill="x", padx=10, pady=5)
        
        # -- Resolution
        ctk.CTkLabel(self.adv_frame, text="Resolution").pack(anchor="w", padx=10, pady=(10, 0))
        self.combo_res = ctk.CTkComboBox(self.adv_frame, values=["1024x1024 (Square)", "896x1152 (Portrait)", "1152x896 (Landscape)"])
        self.combo_res.set("1024x1024 (Square)")
        self.combo_res.pack(fill="x", padx=10, pady=5)
        
        # -- Steps
        self.lbl_steps = ctk.CTkLabel(self.adv_frame, text="Steps: 4") # Turbo needs few steps
        self.lbl_steps.pack(anchor="w", padx=10)
        self.slider_steps = ctk.CTkSlider(self.adv_frame, from_=1, to=10, number_of_steps=9, command=self._update_steps_label)
        self.slider_steps.set(4)
        self.slider_steps.pack(fill="x", padx=10, pady=5)

        # -- CFG
        self.lbl_cfg = ctk.CTkLabel(self.adv_frame, text="CFG: 1.0") # Flux/Turbo often uses 1.0
        self.lbl_cfg.pack(anchor="w", padx=10)
        self.slider_cfg = ctk.CTkSlider(self.adv_frame, from_=1.0, to=5.0, number_of_steps=40, command=self._update_cfg_label)
        self.slider_cfg.set(1.0)
        self.slider_cfg.pack(fill="x", padx=10, pady=5)
        
        # -- Seed
        ctk.CTkLabel(self.adv_frame, text="Seed").pack(anchor="w", padx=10, pady=(10, 0))
        self.entry_seed = ctk.CTkEntry(self.adv_frame, placeholder_text="Random")
        self.entry_seed.pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(self.adv_frame, text="Randomize Sc", command=lambda: self.entry_seed.delete(0, 'end'), 
                      width=100, fg_color="#444").pack(anchor="e", padx=10)

        # Generate Button
        self.btn_generate = ctk.CTkButton(self.control_panel, text="Generate (Turbo)", 
                                        height=50, font=("Segoe UI", 16, "bold"),
                                        command=self.start_generation)
        self.btn_generate.pack(fill="x", padx=20, pady=20, side="bottom")

        # --- Right Panel: Gallery ---
        self.gallery_panel = ctk.CTkFrame(self, fg_color="#181818")
        self.gallery_panel.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        
        # Preview Image (Main Viewer)
        self.preview_label = ctk.CTkLabel(self.gallery_panel, text="No Image Generated", text_color="gray")
        self.preview_label.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Bottom Gallery Strip
        self.strip_frame = ctk.CTkScrollableFrame(self.gallery_panel, height=120, orientation="horizontal", fg_color="#222")
        self.strip_frame.pack(fill="x", side="bottom", padx=10, pady=10)
        
        # Gallery Actions
        self.action_frame = ctk.CTkFrame(self.gallery_panel, height=40, fg_color="transparent")
        self.action_frame.pack(fill="x", side="bottom", padx=10, pady=(0, 5))
        
        ctk.CTkButton(self.action_frame, text="Open Folder", width=100, command=self.open_output_folder).pack(side="left", padx=5)
        ctk.CTkButton(self.action_frame, text="Copy", width=80, command=self.copy_current_image).pack(side="right", padx=5)
        ctk.CTkButton(self.action_frame, text="Save As...", width=80, command=self.save_current_image).pack(side="right", padx=5)

        self.current_image_path = None

    def add_prompt_box(self):
        # Create a frame for the prompt row
        frame = ctk.CTkFrame(self.prompt_scroll, fg_color="transparent")
        frame.pack(fill="x", pady=5)
        
        # Textbox
        txt = ctk.CTkTextbox(frame, height=80, font=("Segoe UI", 12))
        txt.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        # Right Setup (Refine & Delete)
        right_sub = ctk.CTkFrame(frame, fg_color="transparent")
        right_sub.pack(side="right", fill="y")
        
        # Refine Button
        btn_refine = ctk.CTkButton(right_sub, text="✨", width=30, height=30, 
                                 command=lambda t=txt: self.refine_prompt(t))
        btn_refine.pack(pady=(0, 5))
        
        # Delete Button (Only if not the first one, or allow clearing first)
        if len(self.prompts) > 0:
            btn_del = ctk.CTkButton(right_sub, text="🗑️", width=30, height=30, fg_color="#C62828", hover_color="#B71C1C",
                                  command=lambda f=frame, t=txt: self.remove_prompt_box(f, t))
            btn_del.pack()
            
        self.prompts.append(txt)
        self.prompt_frames.append(frame)

    def remove_prompt_box(self, frame, txt_widget):
        if txt_widget in self.prompts:
            self.prompts.remove(txt_widget)
        if frame in self.prompt_frames:
            self.prompt_frames.remove(frame)
        frame.destroy()

    def refine_prompt(self, text_widget):
        """Use Ollama to refine text in specific widget"""
        current_text = text_widget.get("1.0", "end").strip()
        if not current_text:
            return
            
        def _run():
            try:
                import pyperclip
                from features.ai.standalone.ollama_text_refine import refine_text
            except ImportError:
                self.after(0, lambda: messagebox.showwarning("Library Missing", "Ollama extension or pyperclip library not found."))
                return

            try:
                success = refine_text(current_text, task_type='refine')
                
                if success:
                    refined = pyperclip.paste()
                    self.after(0, lambda: self._update_text(text_widget, refined))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Refine Error", f"Ollama refine failed: {e}"))
        
        threading.Thread(target=_run, daemon=True).start()

    def _update_text(self, widget, text):
        widget.delete("1.0", "end")
        widget.insert("end", text)

    def _toggle_advanced(self):
        if self.adv_var.get():
            self.adv_frame.pack(fill="x", padx=10, pady=5, after=self.chk_adv)
        else:
            self.adv_frame.pack_forget()

    def _update_batch_label(self, value):
        self.lbl_batch.configure(text=f"Batch Size: {int(value)}")

    def _update_steps_label(self, value):
        self.lbl_steps.configure(text=f"Steps: {int(value)}")
        
    def _update_cfg_label(self, value):
        self.lbl_cfg.configure(text=f"CFG: {round(value, 1)}")

    def start_generation(self):
        if self.is_processing:
            return
            
        # Collect Prompts
        texts = [p.get("1.0", "end").strip() for p in self.prompts if p.get("1.0", "end").strip()]
        if not texts:
            messagebox.showwarning("Empty Prompt", "Please enter at least one prompt.")
            return
            
        full_prompt = ", ".join(texts)
        
        # Settings
        batch_size = int(self.slider_batch.get())
        steps = int(self.slider_steps.get())
        cfg = self.slider_cfg.get()
        res_str = self.combo_res.get().split()[0]
        width, height = map(int, res_str.split("x"))
        
        seed_val = self.entry_seed.get().strip()
        if not seed_val:
            seed_val = random.randint(0, 2**32 - 1)
        else:
            try:
                seed_val = int(seed_val)
            except:
                seed_val = random.randint(0, 2**32 - 1)
                
        self.is_processing = True
        self.btn_generate.configure(state="disabled", text="Generating...")
        self.preview_label.configure(text="Processing...", image=None)
        
        threading.Thread(target=self._run_workflow, args=(full_prompt, width, height, batch_size, steps, cfg, seed_val), daemon=True).start()

    def _run_workflow(self, prompt, width, height, batch_size, steps, cfg, seed):
        try:
            # Load Workflow
            wf_path = workflow_utils.get_workflow_path("z_image_turbo")
            workflow = workflow_utils.load_workflow(wf_path)
            if not workflow:
                raise Exception("Workflow file not found.")
            
            # Check execution format and convert if necessary
            if "nodes" in workflow:
                workflow = self.convert_to_api_format(workflow)

            # Node IDs from verified turbo.json
            # 45: CLIPTextEncode (Positive Prompt)
            # 41: EmptySD3LatentImage (Resolution/Batch)
            # 44: KSampler (Seed/Steps/CFG)
            
            # Update Prompt (Node 45)
            # Ensure 'inputs' dict exists (conversion creates it, but safe to use util)
            workflow["45"]["inputs"]["text"] = prompt
            
            # Update Resolution & Batch (Node 41)
            workflow["41"]["inputs"]["width"] = width
            workflow["41"]["inputs"]["height"] = height
            workflow["41"]["inputs"]["batch_size"] = batch_size
            
            # Update KSampler (Node 44)
            workflow["44"]["inputs"]["seed"] = seed
            workflow["44"]["inputs"]["steps"] = steps
            workflow["44"]["inputs"]["cfg"] = cfg
            
            # Execute
            outputs = self.client.generate_image(workflow)
            
            if outputs:
                # Handle multiple outputs (batch)
                image_paths = []
                for _, images in outputs.items():
                    # images is list of dicts with 'filename', 'subfolder', etc or direct bytes sometimes?
                    # Client returns mapped images dict {node_id: [Image objects or paths]}
                    # Actually client.generate_image returns {node_id: [PIL.Images]} usually if save_image=False?
                    # Wait, client.generate_image implementation saves to output and returns paths?
                    # Let's check client implementation. usually it returns bytes or PIL images.
                    pass
                
                # Assuming client returns {node_id: [PIL.Image, ...]}
                all_images = []
                for node_id, imgs in outputs.items():
                     all_images.extend(imgs)
                     
                self.after(0, lambda: self._on_success(all_images))
            else:
                 raise Exception("No images returned.")

        except Exception as e:
            self.after(0, lambda: self._on_error(str(e)))

    def _on_success(self, images):
        self.is_processing = False
        self.btn_generate.configure(state="normal", text="Generate (Turbo)")
        
        timestamp = int(time.time())
        saved_paths = []
        
        # Save images to local output dir for persistence
        out_dir = Path("outputs/z_turbo")
        out_dir.mkdir(parents=True, exist_ok=True)
        
        for idx, img in enumerate(images):
            path = out_dir / f"z_turbo_{timestamp}_{idx}.png"
            img.save(path)
            saved_paths.append(str(path))
            
        self.generated_images.extend(saved_paths)
        
        # Show last image
        self.show_image(saved_paths[-1])
        
        # Refresh Gallery
        self._refresh_gallery()

    def _on_error(self, err_msg):
        self.is_processing = False
        self.btn_generate.configure(state="normal", text="Generate (Turbo)")
        self.preview_label.configure(text=f"Error: {err_msg}")
        messagebox.showerror("Error", err_msg)

    def show_image(self, path):
        self.current_image_path = path
        pil_img = Image.open(path)
        
        # Resize for preview
        w, h = pil_img.size
        aspect = w / h
        
        # Fit to panel
        display_w = self.gallery_panel.winfo_width() - 40
        display_h = self.gallery_panel.winfo_height() - 200
        
        if display_w < 100: display_w = 400
        if display_h < 100: display_h = 400
        
        if display_w / display_h > aspect:
             new_h = display_h
             new_w = int(new_h * aspect)
        else:
             new_w = display_w
             new_h = int(new_w / aspect)
             
        ctk_img = ctk.CTkImage(pil_img, size=(new_w, new_h))
        self.preview_label.configure(image=ctk_img, text="")

    def _refresh_gallery(self):
        # Clear old widgets
        for widget in self.strip_frame.winfo_children():
            widget.destroy()
            
        # Add thumbnails (reverse order)
        for path in reversed(self.generated_images):
            try:
                img = Image.open(path)
                ctk_thumb = ctk.CTkImage(img, size=(100, 100))
                btn = ctk.CTkButton(self.strip_frame, image=ctk_thumb, text="", width=110, height=110,
                                  command=lambda p=path: self.show_image(p), fg_color="transparent", border_width=1)
                btn.pack(side="left", padx=5)
            except:
                pass

    def open_output_folder(self):
        if self.current_image_path:
            path = Path(self.current_image_path).parent
            os.startfile(path)
        else:
            Path("outputs/z_turbo").mkdir(parents=True, exist_ok=True)
            os.startfile(Path("outputs/z_turbo").resolve())

    def copy_current_image(self):
        if not self.current_image_path:
            return
            
        try:
             # Use powershell to copy image to clipboard
             cmd = f"Get-Item '{self.current_image_path}' | Set-Clipboard" # File copy
             # To copy IMAGE CONTENT to clipboard in Windows is tricky with just powershell one-liner for bitmaps without extra libs.
             # Easier to use recent 'pyperclip' if it supported images, but it doesn't fully.
             # Using a dedicated python method using ctypes or win32clipboard is better.
             # Or simply use the dedicated tool:
             self.copy_image_to_clipboard(self.current_image_path)
             messagebox.showinfo("Copied", "Image copied to clipboard!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy: {e}")

    def copy_image_to_clipboard(self, path):
        # Concise windows clipboard implementation
        try:
            import win32clipboard
            from io import BytesIO
            
            image = Image.open(path)
            output = BytesIO()
            image.convert("RGB").save(output, "BMP")
            data = output.getvalue()[14:]
            output.close()
            
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            win32clipboard.CloseClipboard()
        except ImportError:
            messagebox.showwarning("Library Missing", "pywin32 library is required for clipboard operations.")
        except Exception as e:
            messagebox.showerror("Clipboard Error", f"Failed to copy image: {e}")

    def save_current_image(self):
        if not self.current_image_path:
            return
        
        dest = filedialog.asksaveasfilename(defaultextension=".png", 
                                          filetypes=[("PNG", "*.png"), ("JPG", "*.jpg")])
        if dest:
            shutil.copy(self.current_image_path, dest)
            messagebox.showinfo("Saved", f"Image saved to {dest}")

    def convert_to_api_format(self, data):
        api = {}
        links = {}
        for l in data.get("links", []):
             links[l[0]] = (str(l[1]), l[2])
             
        for node in data.get("nodes", []):
            node_id = str(node["id"])
            inputs = {}
            if "inputs" in node:
                for inp in node["inputs"]:
                    if inp.get("link") and inp["link"] in links:
                        inputs[inp["name"]] = list(links[inp["link"]])
            vals = node.get("widgets_values", [])
            if vals:
                ct = node["type"]
                if ct == "CLIPTextEncode": inputs["text"] = vals[0]
                elif ct == "EmptySD3LatentImage":
                    inputs["width"], inputs["height"], inputs["batch_size"] = vals[0], vals[1], vals[2]
                elif ct == "KSampler":
                    inputs["seed"] = vals[0]
                    inputs["control_after_generate"] = vals[1]
                    inputs["steps"] = vals[2]
                    inputs["cfg"] = vals[3]
                    inputs["sampler_name"] = vals[4]
                    inputs["scheduler"] = vals[5]
                    inputs["denoise"] = vals[6]
                elif ct == "SaveImage": inputs["filename_prefix"] = vals[0]
                elif ct == "CLIPLoader":
                     inputs["clip_name"] = vals[0]
                     if len(vals) > 1: inputs["type"] = vals[1]
                elif ct == "VAELoader": inputs["vae_name"] = vals[0]
                elif ct == "UNETLoader":
                     inputs["unet_name"] = vals[0]
                     if len(vals) > 1: inputs["weight_dtype"] = vals[1]
                elif ct == "LoraLoaderModelOnly":
                     inputs["lora_name"] = vals[0]
                     inputs["strength_model"] = vals[1]
            api[node_id] = {"class_type": node["type"], "inputs": inputs}
        return api

    def on_closing(self):
        self.destroy()

if __name__ == "__main__":
    app = ZImageTurboGUI()
    app.mainloop()
