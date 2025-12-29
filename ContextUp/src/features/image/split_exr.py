import customtkinter as ctk
from tkinter import messagebox, filedialog
from pathlib import Path
import sys
import threading
import numpy as np
from PIL import Image

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent  # features/image -> src
sys.path.append(str(src_dir))

from utils.gui_lib import BaseWindow
from utils.files import get_safe_path

import OpenEXR
import Imath

class ExrSplitGUI(BaseWindow):
    def __init__(self, target_file=None):
        super().__init__(title="EXR Channel Splitter", width=500, height=500, icon_name="image_exr_split")
        
        self.current_file = None
        self.exr_header = None
        self.layer_map = {} # { "LayerName": [channels] }
        self.layer_vars = {} # layer_name -> BooleanVar
        
        self.create_widgets()
        
        if target_file and Path(target_file).exists():
            self.load_exr_file(Path(target_file))
            
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        # Title
        title_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        title_frame.pack(fill="x", padx=15, pady=(10, 5))
        ctk.CTkLabel(title_frame, text="EXR Channel Splitter", font=("Arial", 16, "bold")).pack(side="left")
        
        # File Selector
        file_frame = ctk.CTkFrame(self.main_frame)
        file_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(file_frame, text="EXR File:", font=("Arial", 11)).pack(side="left", padx=(10, 5), pady=8)
        self.lbl_file = ctk.CTkLabel(file_frame, text="No file selected", text_color="gray", font=("Arial", 11))
        self.lbl_file.pack(side="left", fill="x", expand=True, padx=5, pady=8)
        
        ctk.CTkButton(file_frame, text="Browse...", width=80, command=self.browse_file).pack(side="right", padx=10, pady=8)
        
        # Info
        info_frame = ctk.CTkFrame(self.main_frame)
        info_frame.pack(fill="x", padx=15, pady=5)
        
        self.lbl_info = ctk.CTkLabel(info_frame, text="", text_color="gray", font=("Arial", 10), justify="left")
        self.lbl_info.pack(padx=10, pady=8, anchor="w")
        
        # Layers Section
        layer_header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        layer_header.pack(fill="x", padx=15, pady=(10, 5))
        
        ctk.CTkLabel(layer_header, text="Channels/Layers:", font=("Arial", 12, "bold")).pack(side="left")
        
        btn_all = ctk.CTkButton(layer_header, text="All", width=50, height=24, command=lambda: self.toggle_all_layers(True))
        btn_all.pack(side="right", padx=2)
        btn_none = ctk.CTkButton(layer_header, text="None", width=50, height=24, command=lambda: self.toggle_all_layers(False))
        btn_none.pack(side="right", padx=2)
        
        # Scrollable Layer List
        self.scroll_layers = ctk.CTkScrollableFrame(self.main_frame, height=200)
        self.scroll_layers.pack(fill="both", expand=True, padx=15, pady=5)
        
        # Output Format
        format_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        format_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(format_frame, text="Output Format:", font=("Arial", 11)).pack(side="left", padx=5)
        self.format_var = ctk.StringVar(value="EXR")
        ctk.CTkComboBox(format_frame, variable=self.format_var, values=["EXR", "PNG", "JPG", "TGA"], width=100).pack(side="left", padx=5)
        
        # Bottom Controls
        footer = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        footer.pack(fill="x", side="bottom", padx=15, pady=10)
        
        self.progress = ctk.CTkProgressBar(footer, height=8)
        self.progress.pack(fill="x", pady=(0, 5))
        self.progress.set(0)
        
        self.lbl_status = ctk.CTkLabel(footer, text="Ready", text_color="gray", font=("Arial", 11))
        self.lbl_status.pack(pady=(0, 5))
        
        self.btn_extract = ctk.CTkButton(footer, text="Extract Selected Channels", height=40, 
                                         fg_color="#00b894", hover_color="#00cec9",
                                         font=("Arial", 13, "bold"), command=self.extract_channels, state="disabled")
        self.btn_extract.pack(fill="x")

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Select EXR File",
            filetypes=[("OpenEXR files", "*.exr"), ("All files", "*.*")]
        )
        if file_path:
            self.load_exr_file(Path(file_path))

    def load_exr_file(self, path):
        if not path.exists():
            messagebox.showerror("Error", f"File not found:\\n{path}")
            return
            
        self.current_file = path
        self.lbl_file.configure(text=path.name)
        self.lbl_status.configure(text="Reading EXR header...")
        self.btn_extract.configure(state="disabled")
        
        threading.Thread(target=self._parse_exr_header, args=(path,), daemon=True).start()

    def _parse_exr_header(self, path):
        try:
            if not OpenEXR.isOpenExrFile(str(path)):
                self.update_status("Invalid EXR file")
                return

            exr_file = OpenEXR.InputFile(str(path))
            header = exr_file.header()
            self.exr_header = header
            
            # Extract channels
            channels = list(header['channels'].keys())
            
            # Group into layers
            self.layer_map = self._group_channels_to_layers(channels)
            
            # Update Info
            dw = header['dataWindow']
            w = dw.max.x - dw.min.x + 1
            h = dw.max.y - dw.min.y + 1
            comp = header.get('compression', 'unknown')
            
            info_text = f"Size: {w}x{h}  |  Channels: {len(channels)}  |  Layers: {len(self.layer_map)}"
            self.lbl_info.configure(text=info_text)
            
            # Update Layer List
            self.update_layer_list(sorted(self.layer_map.keys()))
            
            self.update_status("Ready to extract")
            self.btn_extract.configure(state="normal")
            
        except Exception as e:
            print(f"EXR Parse Error: {e}")
            self.update_status(f"Error: {str(e)}")

    def _group_channels_to_layers(self, channels):
        """
        Group channels by layer prefix (e.g., 'Diffuse.R' -> 'Diffuse')
        """
        layers = {}
        
        for chan in channels:
            parts = chan.split('.')
            if len(parts) > 1:
                # Has layer prefix
                layer_name = ".".join(parts[:-1])
                comp = parts[-1]
            else:
                # Root channel (R, G, B, etc)
                layer_name = "Main"
                comp = chan
                
            if layer_name not in layers:
                layers[layer_name] = []
            layers[layer_name].append(chan)
            
        return layers

    def update_layer_list(self, layer_names):
        for w in self.scroll_layers.winfo_children():
            w.destroy()
        self.layer_vars = {}
        
        for layer in layer_names:
            var = ctk.BooleanVar(value=True)
            self.layer_vars[layer] = var
            
            ch_count = len(self.layer_map[layer])
            ch_names = ", ".join([c.split('.')[-1] for c in self.layer_map[layer][:4]])
            if ch_count > 4:
                ch_names += "..."
            text = f"{layer} ({ch_count} ch: {ch_names})"
            
            chk = ctk.CTkCheckBox(self.scroll_layers, text=text, variable=var, font=("Arial", 11))
            chk.pack(anchor="w", pady=3, padx=5)

    def toggle_all_layers(self, state):
        for var in self.layer_vars.values():
            var.set(state)

    def extract_channels(self):
        if not self.current_file:
            return
        threading.Thread(target=self.run_extraction, daemon=True).start()

    def run_extraction(self):
        try:
            self.update_status("Preparing...")
            self.btn_extract.configure(state="disabled")
            
            selected_layers = [l for l, v in self.layer_vars.items() if v.get()]
            if not selected_layers:
                self.update_status("No layers selected")
                self.btn_extract.configure(state="normal")
                return
            
            out_format = self.format_var.get().lower()
            out_dir = self.current_file.parent / f"{self.current_file.stem}_channels"
            out_dir.mkdir(exist_ok=True)
            
            exr_file = OpenEXR.InputFile(str(self.current_file))
            header = self.exr_header
            dw = header['dataWindow']
            w = dw.max.x - dw.min.x + 1
            h = dw.max.y - dw.min.y + 1
            
            total = len(selected_layers)
            
            for idx, layer_name in enumerate(selected_layers):
                self.progress.set((idx) / total)
                self.update_status(f"Extracting {layer_name}... ({idx+1}/{total})")
                
                channels = self.layer_map[layer_name]
                
                # Sort channels (R, G, B, A order)
                def chan_sort_key(name):
                    suffix = name.split('.')[-1]
                    order = {'R':0, 'G':1, 'B':2, 'A':3, 'X':0, 'Y':1, 'Z':2}
                    return order.get(suffix, 99)
                    
                sorted_chans = sorted(channels, key=chan_sort_key)
                
                pt = Imath.PixelType(Imath.PixelType.FLOAT)
                bytes_list = exr_file.channels(sorted_chans, pt)
                
                # Save Logic
                if out_format == "exr":
                    new_header = OpenEXR.Header(w, h)
                    chan_data = {}
                    
                    for i, old_name in enumerate(sorted_chans):
                        parts = old_name.split('.')
                        simple_name = parts[-1] if len(parts) > 1 else old_name
                        
                        new_header['channels'][simple_name] = Imath.Channel(Imath.PixelType(Imath.PixelType.FLOAT))
                        chan_data[simple_name] = bytes_list[i]
                        
                    out = OpenEXR.OutputFile(str(out_dir / f"{layer_name.replace('/', '_')}.exr"), new_header)
                    out.writePixels(chan_data)
                    out.close()
                    
                else:
                    # LDR Formats
                    arrays = []
                    for b in bytes_list:
                        arr = np.frombuffer(b, dtype=np.float32)
                        arr = arr.reshape(h, w)
                        arrays.append(arr)
                    
                    if len(arrays) == 1:
                        img = arrays[0]
                    elif len(arrays) >= 3:
                        img = np.dstack(arrays[:3])
                    else:
                        img = np.dstack([arrays[0], arrays[1], np.zeros_like(arrays[0])])
                        
                    # Normalize & Gamma
                    img = np.nan_to_num(img)
                    max_val = np.max(img)
                    if max_val > 1.0:
                        img /= max_val
                    img = np.power(np.clip(img, 0, 1), 1/2.2) * 255
                    img = img.astype(np.uint8)
                    
                    pil_img = Image.fromarray(img)
                    save_path = out_dir / f"{layer_name.replace('/', '_')}.{out_format}"
                    pil_img.save(save_path)

            self.progress.set(1.0)
            self.update_status("Complete!")
            self.btn_extract.configure(state="normal")
            messagebox.showinfo("Success", f"Extracted {total} layers to:\\n{out_dir}")
            
        except Exception as e:
            print(f"Extraction Error: {e}")
            self.update_status(f"Error: {str(e)}")
            self.btn_extract.configure(state="normal")
            messagebox.showerror("Error", str(e))

    def update_status(self, text):
        self.lbl_status.configure(text=text)

    def on_closing(self):
        self.destroy()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        app = ExrSplitGUI(sys.argv[1])
    else:
        app = ExrSplitGUI()
    app.mainloop()
