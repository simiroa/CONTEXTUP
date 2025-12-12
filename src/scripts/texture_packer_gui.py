"""
Texture Packer GUI - Pack ORM (Occlusion, Roughness, Metallic) textures.
Combines separate texture maps into a single RGB image.
"""
import sys
import re
from pathlib import Path
import customtkinter as ctk
from PIL import Image, ImageTk
from tkinter import messagebox, filedialog
import threading

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.append(str(src_dir))

from utils.gui_lib import BaseWindow
from utils.explorer import get_selection_from_explorer
from core.logger import setup_logger

logger = setup_logger("texture_packer")


class TexturePackerGUI(BaseWindow):
    """GUI for packing ORM textures into a single image."""
    
    def __init__(self, target_path=None):
        super().__init__(title="Texture Packer (ORM)", width=700, height=550)
        
        self.target_path = Path(target_path) if target_path else None
        self.slots = {
            "occlusion": None,
            "roughness": None,
            "metallic": None
        }
        self.previews = {}
        
        self.create_widgets()
        
        # Auto-parse if target provided
        if self.target_path:
            self.auto_parse_textures()
    
    def create_widgets(self):
        # Header
        header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 5))
        
        ctk.CTkLabel(header, text="Texture Packer (ORM)", font=("", 20, "bold")).pack(side="left")
        ctk.CTkLabel(header, text="R=Occlusion, G=Roughness, B=Metallic", 
                     font=("", 12), text_color="gray").pack(side="right")
        
        # Slots Frame
        slots_frame = ctk.CTkFrame(self.main_frame)
        slots_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Configure grid
        slots_frame.grid_columnconfigure((0, 1, 2), weight=1)
        slots_frame.grid_rowconfigure(1, weight=1)
        
        channels = [
            ("Occlusion (R)", "occlusion", "#FF6B6B"),
            ("Roughness (G)", "roughness", "#6BCB77"),
            ("Metallic (B)", "metallic", "#4D96FF")
        ]
        
        for col, (label, key, color) in enumerate(channels):
            # Label
            lbl = ctk.CTkLabel(slots_frame, text=label, font=("", 14, "bold"), text_color=color)
            lbl.grid(row=0, column=col, pady=(10, 5))
            
            # Preview Frame
            preview_frame = ctk.CTkFrame(slots_frame, width=180, height=180, fg_color="#2b2b2b")
            preview_frame.grid(row=1, column=col, padx=10, pady=5, sticky="nsew")
            preview_frame.grid_propagate(False)
            
            # Preview Label (for image)
            preview_label = ctk.CTkLabel(preview_frame, text="Drop or Load", 
                                         font=("", 11), text_color="gray")
            preview_label.place(relx=0.5, rely=0.5, anchor="center")
            self.previews[key] = preview_label
            
            # Enable drag and drop
            self._setup_drop_target(preview_frame, key)
            
            # Load Button
            btn = ctk.CTkButton(slots_frame, text="Load...", width=100,
                               command=lambda k=key: self.load_texture(k))
            btn.grid(row=2, column=col, pady=(5, 10))
        
        # Output Settings
        output_frame = ctk.CTkFrame(self.main_frame)
        output_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(output_frame, text="Output Name:").pack(side="left", padx=(15, 5))
        self.entry_output = ctk.CTkEntry(output_frame, width=200, placeholder_text="texture_ORM")
        self.entry_output.pack(side="left", padx=5)
        
        self.var_format = ctk.StringVar(value=".png")
        ctk.CTkOptionMenu(output_frame, values=[".png", ".tga", ".jpg"], 
                          variable=self.var_format, width=80).pack(side="left", padx=5)
        
        # Action Buttons
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(5, 20))
        
        ctk.CTkButton(btn_frame, text="Pack", command=self.pack_textures, 
                      fg_color="#28a745", hover_color="#218838", width=120).pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="Clear All", command=self.clear_all,
                      fg_color="transparent", border_width=1, text_color="gray", width=100).pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="Auto-Parse", command=self.auto_parse_textures,
                      fg_color="#6c757d", width=100).pack(side="right", padx=5)
    
    def _setup_drop_target(self, widget, slot_key):
        """Setup drag and drop for a widget."""
        try:
            # Bind drag and drop events
            widget.drop_target_register("DND_Files")
            widget.dnd_bind("<<Drop>>", lambda e, k=slot_key: self._on_drop(e, k))
        except Exception:
            # TkinterDnD not available, skip
            pass
    
    def _on_drop(self, event, slot_key):
        """Handle file drop."""
        try:
            # Parse dropped files
            files = self.tk.splitlist(event.data)
            if files:
                self.set_slot(slot_key, Path(files[0]))
        except Exception as e:
            logger.error(f"Drop error: {e}")
    
    def load_texture(self, slot_key):
        """Open file dialog to load texture."""
        filetypes = [
            ("Image files", "*.png *.jpg *.jpeg *.tga *.tif *.tiff *.exr"),
            ("All files", "*.*")
        ]
        
        initial_dir = self.target_path.parent if self.target_path else None
        
        path = filedialog.askopenfilename(
            title=f"Select {slot_key.capitalize()} Texture",
            filetypes=filetypes,
            initialdir=initial_dir
        )
        
        if path:
            self.set_slot(slot_key, Path(path))
    
    def set_slot(self, slot_key, path: Path):
        """Set a texture slot and update preview."""
        if not path.exists():
            messagebox.showerror("Error", f"File not found: {path}")
            return
        
        self.slots[slot_key] = path
        logger.info(f"Set {slot_key}: {path}")
        
        # Update preview
        try:
            img = Image.open(path)
            img.thumbnail((170, 170), Image.Resampling.LANCZOS)
            
            # Convert to CTkImage
            photo = ctk.CTkImage(light_image=img, dark_image=img, size=(170, 170))
            self.previews[slot_key].configure(image=photo, text="")
            self.previews[slot_key].image = photo  # Keep reference
        except Exception as e:
            logger.warning(f"Preview failed: {e}")
            self.previews[slot_key].configure(text=path.name[:20], image=None)
        
        # Auto-set output name if not set
        if not self.entry_output.get():
            base_name = re.sub(r'_(occlusion|roughness|metallic|ao|rough|metal|orm).*', '', 
                              path.stem, flags=re.IGNORECASE)
            self.entry_output.delete(0, "end")
            self.entry_output.insert(0, f"{base_name}_ORM")
    
    def auto_parse_textures(self):
        """Auto-detect textures based on naming conventions."""
        if not self.target_path:
            messagebox.showinfo("Info", "No target path provided. Use Load buttons.")
            return
        
        search_dir = self.target_path.parent if self.target_path.is_file() else self.target_path
        base_name = self.target_path.stem if self.target_path.is_file() else ""
        
        # Remove common suffixes to get base name
        base_name = re.sub(r'_(occlusion|roughness|metallic|ao|rough|metal|orm|basecolor|albedo|diffuse|normal).*', 
                          '', base_name, flags=re.IGNORECASE)
        
        logger.info(f"Auto-parsing in: {search_dir}, base: {base_name}")
        
        # Search patterns
        patterns = {
            "occlusion": ["*occlusion*", "*ao*", "*ambient*"],
            "roughness": ["*roughness*", "*rough*", "*gloss*"],
            "metallic": ["*metallic*", "*metal*", "*metalness*"]
        }
        
        found = 0
        for slot_key, slot_patterns in patterns.items():
            if self.slots[slot_key]:  # Already set
                continue
                
            for pattern in slot_patterns:
                # Try with base name first
                matches = list(search_dir.glob(f"{base_name}{pattern}"))
                if not matches:
                    matches = list(search_dir.glob(pattern))
                
                # Filter to images only
                img_exts = {'.png', '.jpg', '.jpeg', '.tga', '.tif', '.tiff', '.exr'}
                matches = [m for m in matches if m.suffix.lower() in img_exts]
                
                if matches:
                    self.set_slot(slot_key, matches[0])
                    found += 1
                    break
        
        if found == 0:
            messagebox.showinfo("Auto-Parse", "No matching textures found.\nUse Load buttons to select manually.")
        else:
            logger.info(f"Auto-parsed {found} textures")
    
    def clear_all(self):
        """Clear all slots."""
        for key in self.slots:
            self.slots[key] = None
            self.previews[key].configure(text="Drop or Load", image=None)
        self.entry_output.delete(0, "end")
    
    def pack_textures(self):
        """Pack textures into ORM image."""
        # Validate
        if not any(self.slots.values()):
            messagebox.showerror("Error", "Please load at least one texture.")
            return
        
        output_name = self.entry_output.get().strip() or "packed_ORM"
        output_ext = self.var_format.get()
        
        def _do_pack():
            try:
                # Determine output size from first available texture
                size = None
                for path in self.slots.values():
                    if path:
                        with Image.open(path) as img:
                            size = img.size
                        break
                
                if not size:
                    raise ValueError("No valid textures to pack")
                
                logger.info(f"Packing ORM at size: {size}")
                
                # Create channels
                channels = []
                for key in ["occlusion", "roughness", "metallic"]:
                    path = self.slots[key]
                    if path:
                        with Image.open(path) as img:
                            # Convert to grayscale, resize if needed
                            gray = img.convert('L')
                            if gray.size != size:
                                gray = gray.resize(size, Image.Resampling.LANCZOS)
                            channels.append(gray)
                    else:
                        # Default: white for occlusion/roughness, black for metallic
                        default_val = 255 if key != "metallic" else 0
                        channels.append(Image.new('L', size, default_val))
                
                # Merge to RGB
                result = Image.merge('RGB', channels)
                
                # Determine output path
                output_dir = self.target_path.parent if self.target_path else Path.cwd()
                output_path = output_dir / f"{output_name}{output_ext}"
                
                # Handle format-specific saving
                if output_ext == ".jpg":
                    result = result.convert('RGB')
                    result.save(output_path, quality=95)
                else:
                    result.save(output_path)
                
                logger.info(f"Packed ORM saved: {output_path}")
                
                self.after(0, lambda: messagebox.showinfo("Success", f"Saved: {output_path}"))
                self.after(0, self.destroy)
                
            except Exception as e:
                logger.error(f"Pack failed: {e}", exc_info=True)
                self.after(0, lambda: messagebox.showerror("Error", f"Failed to pack: {e}"))
        
        threading.Thread(target=_do_pack, daemon=True).start()


def run_texture_packer(target_path=None):
    """Entry point for texture packer."""
    app = TexturePackerGUI(target_path)
    app.mainloop()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        anchor = sys.argv[1]
        
        # Get all selected files via Explorer COM
        from utils.explorer import get_selection_from_explorer
        all_files = get_selection_from_explorer(anchor)
        if not all_files:
            all_files = [Path(anchor)]
        
        # Mutex - ensure only one GUI window opens
        from utils.batch_runner import collect_batch_context
        if collect_batch_context("texture_packer_orm", anchor, timeout=0.2) is None:
            sys.exit(0)
        
        # Texture packer uses folder, pass first file's parent
        run_texture_packer(str(all_files[0]))
    else:
        run_texture_packer()

