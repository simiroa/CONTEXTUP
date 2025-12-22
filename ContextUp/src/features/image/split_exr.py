import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import sys
import threading
import numpy as np
from PIL import Image, ImageTk

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent  # features/image -> src
sys.path.append(str(src_dir))

from utils.gui_lib import BaseWindow
from utils.files import get_safe_path
from utils.image_utils import scan_for_images
from core.config import MenuConfig

import OpenEXR
import Imath

class ExrSplitGUI(BaseWindow):
    def __init__(self, files_list, demo=False):
        # Sync Name
        self.tool_name = "ContextUp EXR Splitter"
        try:
             config = MenuConfig()
             item = config.get_item_by_id("split_exr")
             if item: self.tool_name = item.get("name", self.tool_name)
        except: pass

        super().__init__(title=self.tool_name, width=1000, height=700, icon_name="image_exr_split")
        
        self.demo_mode = demo
        self.files = []
        self.exr_files = []
        self.current_file = None
        self.exr_header = None
        self.layer_map = {} # { "LayerName": ["R", "G", "B"] }
        self.preview_cache = None

        if demo:
             pass 
        else:
            if isinstance(files_list, (list, tuple)) and len(files_list) > 0:
                self.files, self.scan_count = scan_for_images(files_list)
            else:
                self.files, self.scan_count = scan_for_images(files_list)
            
            self.exr_files = [f for f in self.files if f.suffix.lower() == ".exr"]
            
            if not self.exr_files:
                msg = f"No EXR files found.\nScanned: {self.scan_count}"
                messagebox.showerror("Error", msg)
                self.destroy()
                return

            self.current_file = self.exr_files[0]
        
        self.create_widgets()
        
        if not demo and self.current_file:
            self.load_file_info(self.current_file)
            
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        # Layout: 3 Columns
        self.main_frame.grid_columnconfigure(0, weight=0) # File List
        self.main_frame.grid_columnconfigure(1, weight=1) # Preview
        self.main_frame.grid_columnconfigure(2, weight=0) # Controls
        self.main_frame.grid_rowconfigure(0, weight=1)
        
        # === 1. Left Panel: File List ===
        self.left_panel = ctk.CTkFrame(self.main_frame, width=220, corner_radius=0)
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self.left_panel.grid_propagate(False)
        
        ctk.CTkLabel(self.left_panel, text="EXR Files", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(15, 10))
        self.scroll_files = ctk.CTkScrollableFrame(self.left_panel, fg_color="transparent")
        self.scroll_files.pack(fill="both", expand=True, padx=5, pady=5)
        
        # === 2. Center Panel: Preview ===
        self.center_panel = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.center_panel.grid(row=0, column=1, sticky="nsew", padx=5)
        
        self.lbl_preview_title = ctk.CTkLabel(self.center_panel, text="Preview", font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_preview_title.pack(pady=(0, 10))
        
        self.preview_area = ctk.CTkLabel(self.center_panel, text="[No Preview]", corner_radius=5)
        self.preview_area.pack(fill="both", expand=True)

        # === 3. Right Panel: Info & Actions ===
        self.right_panel = ctk.CTkFrame(self.main_frame, width=280, corner_radius=0)
        self.right_panel.grid(row=0, column=2, sticky="nsew", padx=(5, 0))
        self.right_panel.grid_propagate(False)
        
        self.create_controls()

    def create_controls(self):
        # Info
        ctk.CTkLabel(self.right_panel, text="EXR Info", font=("", 14, "bold")).pack(pady=10)
        self.info_box = ctk.CTkTextbox(self.right_panel, height=80, font=("Consolas", 11))
        self.info_box.pack(fill="x", padx=10, pady=5)
        self.info_box.configure(state="disabled")
        
        # Layers
        ctk.CTkLabel(self.right_panel, text="Detected Layers (Passes):", font=("", 12, "bold")).pack(anchor="w", padx=10, pady=(15, 5))
        
        # Select All/None
        btn_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10)
        ctk.CTkButton(btn_frame, text="All", width=60, height=20, command=lambda: self.toggle_layers(True)).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="None", width=60, height=20, command=lambda: self.toggle_layers(False)).pack(side="left", padx=2)
        
        self.scroll_layers = ctk.CTkScrollableFrame(self.right_panel, height=200)
        self.scroll_layers.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.layer_vars = {} # layer_name -> BooleanVar

        # Output
        out_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        out_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(out_frame, text="Format:").pack(side="left")
        self.format_var = ctk.StringVar(value="EXR")
        ctk.CTkComboBox(out_frame, variable=self.format_var, values=["EXR", "PNG", "JPG", "TGA"], width=80).pack(side="right")

        # Action
        self.progress = ctk.CTkProgressBar(self.right_panel)
        self.progress.pack(fill="x", padx=15, pady=(0, 5))
        self.progress.set(0)
        
        self.lbl_status = ctk.CTkLabel(self.right_panel, text="Ready", text_color="gray", font=("", 11))
        self.lbl_status.pack(pady=(0, 5))

        self.btn_split = ctk.CTkButton(self.right_panel, text="Split Selected Layers", command=self.split_layers, fg_color="#1f6aa5")
        self.btn_split.pack(fill="x", padx=10, pady=10)

    def toggle_layers(self, state):
        for var in self.layer_vars.values():
            var.set(state)

    def refresh_file_list(self):
        for w in self.scroll_files.winfo_children(): w.destroy()
        for f in self.exr_files:
            is_current = (f == self.current_file)
            fg = "#1f6aa5" if is_current else "transparent"
            btn = ctk.CTkButton(self.scroll_files, text=f.name, anchor="w", fg_color=fg, 
                                command=lambda p=f: self.load_file_info(p))
            btn.pack(fill="x", pady=2)

    def load_file_info(self, path):
        self.current_file = path
        self.refresh_file_list()
        self.lbl_preview_title.configure(text=path.name)
        self.lbl_status.configure(text="Reading Header...")
        
        # Clear UI
        self.info_box.configure(state="normal")
        self.info_box.delete("1.0", "end")
        self.info_box.configure(state="disabled")
        for w in self.scroll_layers.winfo_children(): w.destroy()
        
        threading.Thread(target=self._parse_exr_header, args=(path,), daemon=True).start()

    def _parse_exr_header(self, path):
        try:
            if not OpenEXR.isOpenExrFile(str(path)):
                self.update_status("Invalid EXR File")
                return

            exr_file = OpenEXR.InputFile(str(path))
            header = exr_file.header()
            self.exr_header = header
            
            # extract channels
            channels = header['channels'].keys()
            
            # Group into layers
            self.layer_map = self._group_channels_to_layers(channels)
            
            # Update Info
            dw = header['dataWindow']
            w = dw.max.x - dw.min.x + 1
            h = dw.max.y - dw.min.y + 1
            comp = header.get('compression', 'unknown')
            
            info_text = f"Size: {w}x{h}\nCompression: {comp}\nTotal Channels: {len(channels)}\nLayers: {len(self.layer_map)}"
            self.update_info_box(info_text)
            
            # Update Layer List
            self.update_layer_list(sorted(self.layer_map.keys()))
            
            # Generate Preview (Try to find RGB or Beauty pass)
            self._generate_preview(exr_file, w, h)
            
            self.update_status("Ready")
            
        except Exception as e:
            print(f"EXR Parse Error: {e}")
            self.update_status("Error reading EXR")

    def _group_channels_to_layers(self, channels):
        """
        Heuristic to group channels:
        Layer.R, Layer.G -> Layer
        R, G, B -> Beauty (or Main)
        """
        layers = {}
        
        for chan in channels:
            parts = chan.split('.')
            if len(parts) > 1:
                # Has layer prefix
                layer_name = ".".join(parts[:-1]) # Join all except last (R/G/B)
                comp = parts[-1]
            else:
                # Root channel
                layer_name = "Beauty/Main"
                comp = chan
                
            if layer_name not in layers:
                layers[layer_name] = []
            layers[layer_name].append(chan)
            
        return layers

    def update_info_box(self, text):
        self.info_box.configure(state="normal")
        self.info_box.delete("1.0", "end")
        self.info_box.insert("1.0", text)
        self.info_box.configure(state="disabled")

    def update_layer_list(self, layer_names):
        for w in self.scroll_layers.winfo_children(): w.destroy()
        self.layer_vars = {}
        
        for layer in layer_names:
            var = ctk.BooleanVar(value=True)
            self.layer_vars[layer] = var
            
            # Count channels
            ch_count = len(self.layer_map[layer])
            text = f"{layer} ({ch_count} ch)"
            
            chk = ctk.CTkCheckBox(self.scroll_layers, text=text, variable=var)
            chk.pack(anchor="w", pady=2)

    def _generate_preview(self, exr_file, w, h):
        # Try to find R, G, B channels in root or first layer
        dw = self.exr_header['dataWindow']
        
        # Determine channels to read for preview
        # Prefer root R, G, B
        channels_to_read = []
        labels = []
        
        all_chans = self.exr_header['channels'].keys()
        
        # Simple logic: precise match for R, G, B
        if 'R' in all_chans and 'G' in all_chans and 'B' in all_chans:
            channels_to_read = ['R', 'G', 'B']
        else:
            # Pick first available 3 channels or first layer
            first_layer = list(self.layer_map.keys())[0]
            channels_to_read = self.layer_map[first_layer][:3]
        
        # Read
        pt = Imath.PixelType(Imath.PixelType.FLOAT)
        # Read as strings
        bytes_str = exr_file.channels(channels_to_read, pt)
        
        rgb = []
        for b in bytes_str:
            # convert string of bytes to numpy array
            arr = np.frombuffer(b, dtype=np.float32)
            arr = arr.reshape(h, w)
            rgb.append(arr)
            
        # Pad if less than 3 channels (e.g. Z-depth)
        while len(rgb) < 3:
            rgb.append(rgb[0])
            
        # Merge
        img = np.dstack(rgb)
        
        # Process preview (Tone map)
        preview = np.nan_to_num(img)
        preview = np.clip(preview, 0, None)
        max_val = np.max(preview)
        if max_val > 1.0: preview /= max_val
        
        # Gamma
        preview = np.power(preview, 1/2.2)
        preview = (preview * 255).astype(np.uint8)
        
        pil_img = Image.fromarray(preview)
        pil_img.thumbnail((800, 600))
        
        self.tk_img = ImageTk.PhotoImage(pil_img)
        self.preview_area.configure(image=self.tk_img, text="")

    def update_status(self, text):
        self.lbl_status.configure(text=text)

    def split_layers(self):
        if not self.current_file: return
        threading.Thread(target=self.run_split, daemon=True).start()

    def run_split(self):
        try:
            self.update_status("Preparing...")
            
            # Gather selected layers
            selected_layers = [l for l, v in self.layer_vars.items() if v.get()]
            if not selected_layers:
                self.update_status("No layers selected")
                return
            
            out_format = self.format_var.get().lower()
            out_dir = self.current_file.parent / "Split"
            out_dir.mkdir(exist_ok=True)
            
            exr_file = OpenEXR.InputFile(str(self.current_file))
            header = self.exr_header
            dw = header['dataWindow']
            w = dw.max.x - dw.min.x + 1
            h = dw.max.y - dw.min.y + 1
            
            total = len(selected_layers)
            
            for idx, layer_name in enumerate(selected_layers):
                self.progress.set((idx) / total)
                self.update_status(f"Saving {layer_name}...")
                
                # Get channels for this layer
                channels = self.layer_map[layer_name]
                
                # Read Data
                # Map channel names to requested R,G,B order if possible?
                # Usually we want to save them as R, G, B in the new file if they have suffixes .R .G .B
                
                # Sort channels to try R, G, B order
                # Sort by last character usually works: B, G, R ... wait alphabetical is B, G, R
                # Custom sort: R, G, B, A, others
                
                def chan_sort_key(name):
                    suffix = name.split('.')[-1]
                    order = {'R':0, 'G':1, 'B':2, 'A':3, 'X':0, 'Y':1, 'Z':2}
                    return order.get(suffix, 99)
                    
                sorted_chans = sorted(channels, key=chan_sort_key)
                
                pt = Imath.PixelType(Imath.PixelType.FLOAT)
                bytes_list = exr_file.channels(sorted_chans, pt)
                
                # Save Logic
                if out_format == "exr":
                    # Create new EXR
                    new_header = OpenEXR.Header(w, h)
                    
                    # Create channel definitions for new file
                    # We map SourceName -> TargetName (e.g., Layer.R -> R)
                    out_channels = {}
                    
                    chan_data = {}
                    
                    for i, old_name in enumerate(sorted_chans):
                        # Determine new simple name
                        parts = old_name.split('.')
                        simple_name = parts[-1] if len(parts) > 1 else old_name
                        
                        new_header['channels'][simple_name] = Imath.Channel(Imath.PixelType(Imath.PixelType.FLOAT))
                        chan_data[simple_name] = bytes_list[i]
                        
                    out = OpenEXR.OutputFile(str(out_dir / f"{self.current_file.stem}_{layer_name.replace('/', '_')}.exr"), new_header)
                    out.writePixels(chan_data)
                    out.close()
                    
                else:
                    # LDR Formats (PNG, JPG)
                    # Convert to numpy
                    arrays = []
                    for b in bytes_list:
                        arr = np.frombuffer(b, dtype=np.float32)
                        arr = arr.reshape(h, w)
                        arrays.append(arr)
                    
                    # Handle grayscale vs RGB
                    if len(arrays) == 1:
                        img = arrays[0]
                    elif len(arrays) >= 3:
                        # Take first 3 for RGB
                        img = np.dstack(arrays[:3])
                    else:
                        # 2 channels? Pad with 0
                        img = np.dstack([arrays[0], arrays[1], np.zeros_like(arrays[0])])
                        
                    # Normalize & Gamma
                    img = np.nan_to_num(img)
                    max_val = np.max(img)
                    if max_val > 1.0: img /= max_val
                    img = np.power(np.clip(img, 0, 1), 1/2.2) * 255
                    img = img.astype(np.uint8)
                    
                    pil_img = Image.fromarray(img)
                    save_path = out_dir / f"{self.current_file.stem}_{layer_name.replace('/', '_')}.{out_format}"
                    pil_img.save(save_path)

            self.progress.set(1.0)
            self.update_status("Done")
            messagebox.showinfo("Success", f"Split completed to:\n{out_dir}")
            
        except Exception as e:
            print(f"Split Error: {e}")
            self.update_status("Error splitting")
            messagebox.showerror("Error", str(e))

    def on_closing(self):
        self.destroy()

if __name__ == "__main__":
    if "--demo" in sys.argv:
        app = ExrSplitGUI([], demo=True)
        app.mainloop()
    elif len(sys.argv) > 1:
        anchor = sys.argv[1]
        from utils.explorer import get_selection_from_explorer
        all_files = []
        try:
            selected = get_selection_from_explorer(anchor)
            if selected: all_files = selected
        except: pass
        if not all_files: all_files = [Path(anchor)]
        
        from utils.batch_runner import collect_batch_context
        if collect_batch_context("split_exr", anchor, timeout=0.2) is None: sys.exit(0)
        
        app = ExrSplitGUI(all_files)
        app.mainloop()
