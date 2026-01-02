"""
Noise Master - GUI

Clean, minimal UI with clear separation of concerns.
All rendering logic is delegated to engine.py.
"""

import sys
from pathlib import Path
import customtkinter as ctk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
import numpy as np
import time
import copy
from concurrent.futures import ThreadPoolExecutor
import uuid

# Add src to path
current_dir = Path(__file__).resolve().parent
src_dir = current_dir.parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from utils.gui_lib import BaseWindow
from features.image.noise_master.engine import NoiseEngine


class LayerItem(ctk.CTkFrame):
    """Single layer item in the layer list."""
    
    def __init__(self, master, layer: dict, index: int, callbacks: dict):
        super().__init__(master, fg_color="#2b2b2b", corner_radius=6, height=40)
        self.layer = layer
        self.index = index
        self.callbacks = callbacks
        
        self.grid_columnconfigure(1, weight=1)
        
        # Visibility checkbox
        self.var_visible = ctk.BooleanVar(value=layer.get('visible', True))
        ctk.CTkCheckBox(
            self, text="", width=20, variable=self.var_visible,
            command=self._on_visible_change
        ).grid(row=0, column=0, padx=5, pady=8)
        
        # Name label
        self.lbl_name = ctk.CTkLabel(
            self, text=layer.get('name', 'Layer'), 
            anchor="w", font=("", 12, "bold")
        )
        self.lbl_name.grid(row=0, column=1, padx=5, sticky="ew")
        
        # Blend mode
        self.var_blend = ctk.StringVar(value=layer.get('blend_mode', 'normal'))
        ctk.CTkOptionMenu(
            self, values=["normal", "add", "multiply", "subtract", "overlay"],
            variable=self.var_blend, width=70, height=24,
            command=self._on_blend_change
        ).grid(row=0, column=2, padx=5)
        
        # Delete button
        ctk.CTkButton(
            self, text="✕", width=24, height=24,
            fg_color="transparent", hover_color="#c0392b",
            command=lambda: callbacks['delete'](index)
        ).grid(row=0, column=3, padx=5)
        
        # Click to select
        self.bind("<Button-1>", lambda e: callbacks['select'](index))
        self.lbl_name.bind("<Button-1>", lambda e: callbacks['select'](index))
    
    def _on_visible_change(self):
        self.layer['visible'] = self.var_visible.get()
        self.callbacks['render']()
    
    def _on_blend_change(self, value):
        self.layer['blend_mode'] = value
        self.callbacks['render']()
    
    def set_selected(self, selected: bool):
        self.configure(fg_color="#404040" if selected else "#2b2b2b")


class NoiseMasterWindow(BaseWindow):
    """Main Noise Master window."""
    
    def __init__(self):
        super().__init__(title="Noise Master", width=1100, height=750, icon_name="noise_master")
        
        # State
        self.engine = NoiseEngine(256, 256)
        self.layers = [self._default_layer("Base Noise")]
        self.selected_index = 0
        self.preview_buffer = None
        
        # Rendering
        self.render_executor = ThreadPoolExecutor(max_workers=1)
        self.last_render_id = None
        self.debounce_job = None
        
        # Build UI
        self._create_ui()
        self._refresh_layers()
        self._update_properties()
        self._request_render()
    
    def _default_layer(self, name: str = "Layer") -> dict:
        """Create a default layer configuration."""
        return {
            'name': name,
            'type': 'perlin',
            'visible': True,
            'blend_mode': 'normal',
            'opacity': 1.0,
            'scale': 10.0,
            'rotation': 0.0,
            'seed': int(time.time()) % 9999,
            'octaves': 4,
            'persistence': 0.5,
            'lacunarity': 2.0,
            'invert': False,
            'ridged': False,
            'subtype': 'linear',
        }
    
    # ==================== UI CREATION ====================
    
    def _create_ui(self):
        """Build the main UI layout."""
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        
        self._create_layer_panel()
        self._create_preview_panel()
        self._create_properties_panel()
    
    def _create_layer_panel(self):
        """Left panel: Layer list."""
        frame = ctk.CTkFrame(self.main_frame, width=220)
        frame.grid(row=0, column=0, sticky="ns", padx=5, pady=5)
        frame.pack_propagate(False)
        
        # Header
        ctk.CTkLabel(frame, text="LAYERS", font=("", 12, "bold"), text_color="#666").pack(pady=10)
        
        # Layer list
        self.layer_list = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        self.layer_list.pack(fill="both", expand=True, padx=5)
        
        # Add button
        ctk.CTkButton(
            frame, text="+ Add Layer", height=32,
            command=self._add_layer
        ).pack(fill="x", padx=10, pady=10)
    
    def _create_preview_panel(self):
        """Center panel: Preview image."""
        frame = ctk.CTkFrame(self.main_frame, fg_color="#1a1a1a")
        frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        # Header
        header = ctk.CTkFrame(frame, fg_color="transparent", height=36)
        header.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(header, text="Preview", font=("", 12, "bold"), text_color="#666").pack(side="left")
        
        # Resolution
        self.var_res = ctk.StringVar(value="256")
        ctk.CTkOptionMenu(
            header, values=["256", "512", "1024"], 
            variable=self.var_res, width=70, height=24,
            command=self._on_resolution_change
        ).pack(side="right", padx=5)
        ctk.CTkLabel(header, text="Size:", font=("", 11)).pack(side="right")
        
        # Preview image
        self.lbl_preview = ctk.CTkLabel(frame, text="")
        self.lbl_preview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Toolbar
        toolbar = ctk.CTkFrame(frame, height=40, fg_color="#2b2b2b", corner_radius=8)
        toolbar.pack(fill="x", padx=10, pady=(0, 10))
        
        self.var_normal = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            toolbar, text="Normal Map", variable=self.var_normal,
            command=self._request_render, width=100
        ).pack(side="left", padx=10)
        
        # Save button
        ctk.CTkButton(
            toolbar, text="Save Image", width=100, height=28,
            command=self._save_image
        ).pack(side="right", padx=10)
    
    def _create_properties_panel(self):
        """Right panel: Layer properties."""
        frame = ctk.CTkFrame(self.main_frame, width=280)
        frame.grid(row=0, column=2, sticky="ns", padx=5, pady=5)
        frame.pack_propagate(False)
        
        ctk.CTkLabel(frame, text="PROPERTIES", font=("", 12, "bold"), text_color="#666").pack(pady=10)
        
        self.props_frame = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        self.props_frame.pack(fill="both", expand=True, padx=5)
    
    # ==================== LAYER MANAGEMENT ====================
    
    def _refresh_layers(self):
        """Rebuild the layer list."""
        for widget in self.layer_list.winfo_children():
            widget.destroy()
        
        callbacks = {
            'select': self._select_layer,
            'delete': self._delete_layer,
            'render': self._request_render,
        }
        
        for i, layer in enumerate(self.layers):
            item = LayerItem(self.layer_list, layer, i, callbacks)
            item.pack(fill="x", pady=2)
            item.set_selected(i == self.selected_index)
    
    def _add_layer(self):
        """Add a new layer."""
        self.layers.insert(0, self._default_layer(f"Layer {len(self.layers) + 1}"))
        self.selected_index = 0
        self._refresh_layers()
        self._update_properties()
        self._request_render()
    
    def _delete_layer(self, index: int):
        """Delete a layer."""
        if len(self.layers) <= 1:
            return
        del self.layers[index]
        self.selected_index = min(self.selected_index, len(self.layers) - 1)
        self._refresh_layers()
        self._update_properties()
        self._request_render()
    
    def _select_layer(self, index: int):
        """Select a layer."""
        self.selected_index = index
        self._refresh_layers()
        self._update_properties()
    
    # ==================== PROPERTIES PANEL ====================
    
    def _update_properties(self):
        """Rebuild properties panel for selected layer."""
        for widget in self.props_frame.winfo_children():
            widget.destroy()
        
        if not self.layers or self.selected_index >= len(self.layers):
            return
        
        layer = self.layers[self.selected_index]
        
        # -- GENERAL --
        self._add_section("GENERAL")
        self._add_entry("Name", layer, 'name')
        self._add_dropdown("Type", layer, 'type', 
            ['perlin', 'simplex', 'cellular', 'gradient', 'checker', 'grid', 'brick'])
        self._add_slider("Opacity", layer, 'opacity', 0.0, 1.0)
        
        # -- TRANSFORM --
        self._add_section("TRANSFORM")
        self._add_slider("Scale", layer, 'scale', 1.0, 50.0)
        self._add_slider("Rotation", layer, 'rotation', 0, 360)
        
        # -- NOISE PARAMS (for noise types) --
        if layer['type'] in ['perlin', 'simplex', 'cellular']:
            self._add_section("NOISE")
            self._add_slider("Octaves", layer, 'octaves', 1, 8, is_int=True)
            self._add_slider("Persistence", layer, 'persistence', 0.0, 1.0)
            self._add_slider("Lacunarity", layer, 'lacunarity', 1.0, 4.0)
            self._add_seed_row(layer)
        
        # -- GRADIENT PARAMS --
        if layer['type'] == 'gradient':
            self._add_section("GRADIENT")
            self._add_dropdown("Shape", layer, 'subtype', ['linear', 'radial'])
        
        # -- PATTERN PARAMS --
        if layer['type'] in ['grid', 'brick']:
            self._add_section("PATTERN")
            self._add_slider("Thickness", layer, 'persistence', 0.0, 1.0)
        
        # -- MODIFIERS --
        self._add_section("MODIFIERS")
        self._add_checkbox("Invert", layer, 'invert')
        self._add_checkbox("Ridged", layer, 'ridged')
    
    def _add_section(self, title: str):
        """Add a section header."""
        ctk.CTkLabel(
            self.props_frame, text=title, 
            font=("", 10, "bold"), text_color="#555"
        ).pack(fill="x", padx=5, pady=(15, 5), anchor="w")
    
    def _add_entry(self, label: str, layer: dict, key: str):
        """Add a text entry row."""
        row = ctk.CTkFrame(self.props_frame, fg_color="transparent")
        row.pack(fill="x", padx=5, pady=2)
        
        ctk.CTkLabel(row, text=label, width=80, anchor="w").pack(side="left")
        
        var = ctk.StringVar(value=layer.get(key, ''))
        entry = ctk.CTkEntry(row, textvariable=var, height=24)
        entry.pack(side="left", fill="x", expand=True)
        
        def on_change(*args):
            layer[key] = var.get()
            self._refresh_layers()
        var.trace_add("write", on_change)
    
    def _add_slider(self, label: str, layer: dict, key: str, 
                    min_val: float, max_val: float, is_int: bool = False):
        """Add a slider row."""
        row = ctk.CTkFrame(self.props_frame, fg_color="transparent")
        row.pack(fill="x", padx=5, pady=2)
        
        ctk.CTkLabel(row, text=label, width=80, anchor="w").pack(side="left")
        
        val = layer.get(key, min_val)
        var = ctk.DoubleVar(value=val)
        
        slider = ctk.CTkSlider(
            row, from_=min_val, to=max_val, variable=var,
            width=120, height=16
        )
        slider.pack(side="left", fill="x", expand=True, padx=5)
        
        # Value label
        lbl_val = ctk.CTkLabel(row, text=f"{val:.1f}" if not is_int else str(int(val)), width=35)
        lbl_val.pack(side="left")
        
        def on_change(*args):
            v = var.get()
            if is_int:
                v = int(round(v))
            layer[key] = v
            lbl_val.configure(text=f"{v:.1f}" if not is_int else str(v))
            self._request_render()
        
        slider.configure(command=lambda v: on_change())
    
    def _add_dropdown(self, label: str, layer: dict, key: str, options: list):
        """Add a dropdown row."""
        row = ctk.CTkFrame(self.props_frame, fg_color="transparent")
        row.pack(fill="x", padx=5, pady=2)
        
        ctk.CTkLabel(row, text=label, width=80, anchor="w").pack(side="left")
        
        var = ctk.StringVar(value=layer.get(key, options[0]))
        
        def on_change(value):
            layer[key] = value
            self._update_properties()  # Rebuild to show relevant options
            self._request_render()
        
        ctk.CTkOptionMenu(
            row, values=options, variable=var,
            command=on_change, width=120, height=24
        ).pack(side="left")
    
    def _add_checkbox(self, label: str, layer: dict, key: str):
        """Add a checkbox row."""
        var = ctk.BooleanVar(value=layer.get(key, False))
        
        def on_change():
            layer[key] = var.get()
            self._request_render()
        
        ctk.CTkCheckBox(
            self.props_frame, text=label, variable=var,
            command=on_change
        ).pack(fill="x", padx=5, pady=2, anchor="w")
    
    def _add_seed_row(self, layer: dict):
        """Add seed input with randomize button."""
        row = ctk.CTkFrame(self.props_frame, fg_color="transparent")
        row.pack(fill="x", padx=5, pady=2)
        
        ctk.CTkLabel(row, text="Seed", width=80, anchor="w").pack(side="left")
        
        var = ctk.StringVar(value=str(layer.get('seed', 0)))
        entry = ctk.CTkEntry(row, textvariable=var, width=80, height=24)
        entry.pack(side="left")
        
        def on_entry(*args):
            try:
                layer['seed'] = int(var.get())
                self._request_render()
            except ValueError:
                pass
        var.trace_add("write", on_entry)
        
        def randomize():
            layer['seed'] = int(time.time() * 1000) % 9999
            var.set(str(layer['seed']))
        
        ctk.CTkButton(
            row, text="🎲", width=28, height=24,
            fg_color="#444", command=randomize
        ).pack(side="left", padx=5)
    
    # ==================== RENDERING ====================
    
    def _request_render(self):
        """Request a render with debouncing."""
        if self.debounce_job:
            self.after_cancel(self.debounce_job)
        self.debounce_job = self.after(50, self._do_render)
    
    def _do_render(self):
        """Submit render job to thread pool."""
        render_id = str(uuid.uuid4())
        self.last_render_id = render_id
        
        layers_copy = copy.deepcopy(self.layers)
        show_normal = self.var_normal.get()
        
        future = self.render_executor.submit(
            self._render_task, layers_copy, show_normal, render_id
        )
        future.add_done_callback(self._on_render_complete)
    
    def _render_task(self, layers: list, show_normal: bool, render_id: str):
        """Background render task."""
        try:
            heightmap = self.engine.render(layers)
            
            if show_normal:
                normal = self.engine.generate_normal_map(heightmap)
                img_data = (normal * 255).astype(np.uint8)
                img = Image.fromarray(img_data, mode='RGB')
            else:
                img = self.engine.to_image(heightmap)
            
            return (render_id, img, heightmap, None)
        except Exception as e:
            return (render_id, None, None, str(e))
    
    def _on_render_complete(self, future):
        """Handle render completion."""
        try:
            render_id, img, heightmap, error = future.result()
            
            if render_id != self.last_render_id:
                return  # Discard stale render
            
            if error:
                print(f"Render error: {error}")
                return
            
            self.preview_buffer = heightmap
            self.after(0, lambda: self._update_preview(img))
            
        except Exception as e:
            print(f"Render callback error: {e}")
    
    def _update_preview(self, img: Image.Image):
        """Update preview image on main thread."""
        try:
            w = self.lbl_preview.winfo_width()
            h = self.lbl_preview.winfo_height()
            
            if w > 20 and h > 20:
                size = min(w, h) - 20
                img = img.resize((size, size), Image.NEAREST)
            
            tk_img = ImageTk.PhotoImage(img)
            self.lbl_preview.configure(image=tk_img, text="")
            self.lbl_preview.image = tk_img
        except Exception as e:
            print(f"Preview update error: {e}")
    
    def _on_resolution_change(self, value: str):
        """Handle resolution change."""
        res = int(value)
        self.engine.width = res
        self.engine.height = res
        self._request_render()
    
    def _save_image(self):
        """Save the current render."""
        if self.preview_buffer is None:
            return
        
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png")]
        )
        if path:
            img = self.engine.to_image(self.preview_buffer)
            img.save(path)
            messagebox.showinfo("Saved", f"Image saved to {path}")


if __name__ == "__main__":
    app = NoiseMasterWindow()
    app.mainloop()
