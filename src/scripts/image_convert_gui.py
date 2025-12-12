"""
Image Converter GUI - High Performance Edition
Fast multi-file conversion with multi-threading and instant Explorer selection.
"""
import sys
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import multiprocessing

# === FAST IMPORTS - delay heavy modules ===
# Only import what's needed for startup
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.append(str(src_dir))


def get_all_selected_files(anchor_path: str) -> list[Path]:
    """Get all selected files from Explorer using COM - INSTANT."""
    try:
        from utils.explorer import get_selection_from_explorer
        selected = get_selection_from_explorer(anchor_path)
        if selected and len(selected) > 0:
            return selected
    except Exception as e:
        print(f"Explorer selection failed: {e}")
    return [Path(anchor_path)]


def main():
    """Main entry - imports heavy modules only when needed."""
    import customtkinter as ctk
    from PIL import Image, ImageOps
    from tkinter import messagebox, filedialog
    import threading
    
    from utils.gui_lib import BaseWindow
    from utils.image_utils import scan_for_images
    from core.logger import setup_logger
    
    logger = setup_logger("image_converter")
    
    class ImageConverterGUI(BaseWindow):
        def __init__(self, files_list=None):
            super().__init__(title="Convert Image Format", width=480, height=520)
            
            if files_list and len(files_list) > 0:
                self.selection, _ = scan_for_images(files_list)
            else:
                self.selection = []
            
            if not self.selection:
                messagebox.showerror("Error", "No valid images found.")
                self.destroy()
                return
            
            self.fmt_var = ctk.StringVar(value="PNG")
            self.resize_enabled = ctk.BooleanVar(value=False)
            self.resize_size = ctk.StringVar(value="1024")
            self.thread_count = ctk.StringVar(value="0")  # 0 = auto (max cores)
            
            self.create_widgets()
            self.update_preview()

        def create_widgets(self):
            header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
            header.pack(fill="x", padx=15, pady=(10, 5))
            
            ctk.CTkLabel(header, text="Convert Images", font=("", 18, "bold")).pack(side="left")
            ctk.CTkButton(header, text="+ Add", width=60, height=24, 
                          fg_color="gray30", command=self.add_files).pack(side="right")
            
            # File List
            list_frame = ctk.CTkFrame(self.main_frame)
            list_frame.pack(fill="both", expand=True, padx=15, pady=5)
            
            self.file_scroll = ctk.CTkScrollableFrame(list_frame, height=150)
            self.file_scroll.pack(fill="both", expand=True, padx=5, pady=5)
            
            # Options
            opts_frame = ctk.CTkFrame(self.main_frame)
            opts_frame.pack(fill="x", padx=15, pady=5)
            
            # Row 1: Format
            row1 = ctk.CTkFrame(opts_frame, fg_color="transparent")
            row1.pack(fill="x", padx=10, pady=6)
            
            ctk.CTkLabel(row1, text="Format:", font=("", 11), width=60).pack(side="left")
            formats = ["PNG", "JPG", "WEBP", "BMP", "TGA", "TIFF", "ICO"]
            ctk.CTkOptionMenu(row1, variable=self.fmt_var, values=formats, 
                              width=80, command=lambda _: self.update_preview()).pack(side="left", padx=5)
            
            # Threads option (right side)
            ctk.CTkLabel(row1, text="Threads:", font=("", 11)).pack(side="left", padx=(20, 5))
            ctk.CTkComboBox(row1, variable=self.thread_count, width=60,
                            values=["0", "1", "2", "4", "8", "16"]).pack(side="left")
            ctk.CTkLabel(row1, text="(0=auto)", font=("", 9), text_color="gray").pack(side="left", padx=3)
            
            # Row 2: Resize
            row2 = ctk.CTkFrame(opts_frame, fg_color="transparent")
            row2.pack(fill="x", padx=10, pady=6)
            
            self.chk_resize = ctk.CTkCheckBox(row2, text="Resize:", 
                                               variable=self.resize_enabled,
                                               command=self.on_resize_toggle, width=80)
            self.chk_resize.pack(side="left")
            
            self.opt_size = ctk.CTkComboBox(row2, variable=self.resize_size,
                                             values=["256", "512", "1024", "2048", "4096"],
                                             width=70, state="disabled")
            self.opt_size.pack(side="left", padx=5)
            ctk.CTkLabel(row2, text="px", font=("", 10), text_color="gray").pack(side="left")
            
            # Status
            self.lbl_status = ctk.CTkLabel(self.main_frame, text="Ready", text_color="gray", font=("", 10))
            self.lbl_status.pack(pady=2)
            
            self.progress = ctk.CTkProgressBar(self.main_frame, height=6)
            self.progress.pack(fill="x", padx=15, pady=(0, 5))
            self.progress.set(0)
            
            # Buttons
            btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
            btn_frame.pack(fill="x", padx=15, pady=(5, 15))
            
            self.btn_convert = ctk.CTkButton(btn_frame, text="Convert All", height=38,
                                              font=("", 13, "bold"), command=self.run_conversion)
            self.btn_convert.pack(side="right", padx=5)
            
            ctk.CTkButton(btn_frame, text="Cancel", fg_color="transparent", border_width=1,
                          text_color="gray", width=80, height=38, command=self.destroy).pack(side="right", padx=5)

        def add_files(self):
            filetypes = [("Image files", "*.png *.jpg *.jpeg *.bmp *.tga *.webp *.tiff *.ico *.exr")]
            files = filedialog.askopenfilenames(title="Add Images", filetypes=filetypes)
            if files:
                for f in files:
                    p = Path(f)
                    if p not in self.selection:
                        self.selection.append(p)
                self.update_preview()

        def on_resize_toggle(self):
            self.opt_size.configure(state="normal" if self.resize_enabled.get() else "disabled")

        def update_preview(self):
            for widget in self.file_scroll.winfo_children():
                widget.destroy()
            
            target_fmt = self.fmt_var.get().lower()
            target_ext = ".jpg" if target_fmt == "jpg" else f".{target_fmt}"
            
            max_display = 8
            for path in self.selection[:max_display]:
                row = ctk.CTkFrame(self.file_scroll, fg_color="transparent", height=22)
                row.pack(fill="x", pady=1)
                
                src = path.name[:28] + "…" if len(path.name) > 28 else path.name
                tgt = (path.stem + target_ext)[:28]
                
                ctk.CTkLabel(row, text=src, font=("", 10), text_color="gray", anchor="w", width=150).pack(side="left")
                ctk.CTkLabel(row, text="→", font=("", 10), text_color="gray", width=20).pack(side="left")
                ctk.CTkLabel(row, text=tgt, font=("", 10), text_color="#4da6ff", anchor="w").pack(side="left")
            
            remaining = len(self.selection) - max_display
            if remaining > 0:
                ctk.CTkLabel(self.file_scroll, text=f"... +{remaining} more", 
                            text_color="gray", font=("", 10)).pack(anchor="w", pady=3)
            
            self.btn_convert.configure(text=f"Convert {len(self.selection)} files")

        def run_conversion(self):
            if not self.selection:
                return
            
            target_fmt = self.fmt_var.get().lower()
            if target_fmt == "jpg":
                target_fmt = "jpeg"
            
            resize_size = None
            if self.resize_enabled.get():
                try:
                    resize_size = int(self.resize_size.get())
                except:
                    pass
            
            # Get thread count (0 = auto)
            try:
                threads = int(self.thread_count.get())
                if threads <= 0:
                    threads = multiprocessing.cpu_count()
            except:
                threads = multiprocessing.cpu_count()
            
            self.btn_convert.configure(state="disabled", text=f"Converting... ({threads} threads)")
            self.progress.set(0)
            
            def convert_single(args):
                """Convert a single image - designed for thread pool."""
                path, target_fmt, resize_size = args
                try:
                    with Image.open(path) as img:
                        # Handle alpha for formats that don't support it
                        if target_fmt in ['jpeg', 'bmp'] and img.mode in ('RGBA', 'LA', 'P'):
                            bg = Image.new("RGB", img.size, (255, 255, 255))
                            if img.mode == 'P':
                                img = img.convert('RGBA')
                            if 'A' in img.getbands():
                                bg.paste(img, mask=img.split()[-1])
                            else:
                                bg.paste(img)
                            img = bg
                        elif target_fmt in ['jpeg', 'bmp'] and img.mode not in ('RGB', 'L'):
                            img = img.convert('RGB')
                        
                        if target_fmt == "ico" and (img.size[0] > 256 or img.size[1] > 256):
                            img = ImageOps.contain(img, (256, 256), method=Image.Resampling.LANCZOS)
                        
                        if resize_size:
                            w, h = img.size
                            if w >= h:
                                new_w, new_h = resize_size, int(h * (resize_size / w))
                            else:
                                new_h, new_w = resize_size, int(w * (resize_size / h))
                            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                        
                        new_ext = ".jpg" if target_fmt == "jpeg" else f".{target_fmt}"
                        new_path = path.with_suffix(new_ext)
                        if new_path == path:
                            new_path = path.with_name(f"{path.stem}_converted{new_ext}")
                        
                        save_kwargs = {}
                        if target_fmt == "jpeg":
                            save_kwargs['quality'] = 95
                        elif target_fmt == "webp":
                            save_kwargs['quality'] = 90
                        
                        img.save(new_path, **save_kwargs)
                        return (True, None)
                except Exception as e:
                    return (False, f"{path.name}: {e}")
            
            def _process_all():
                """Process all files using thread pool."""
                args_list = [(p, target_fmt, resize_size) for p in self.selection]
                
                success = 0
                errors = []
                total = len(args_list)
                completed = 0
                
                with ThreadPoolExecutor(max_workers=threads) as executor:
                    futures = [executor.submit(convert_single, args) for args in args_list]
                    
                    for future in futures:
                        result = future.result()
                        completed += 1
                        
                        if result[0]:
                            success += 1
                        else:
                            errors.append(result[1])
                        
                        # Update progress
                        self.after(0, lambda v=completed/total: self.progress.set(v))
                
                self.after(0, lambda: self.finish_conversion(success, errors))
            
            threading.Thread(target=_process_all, daemon=True).start()

        def finish_conversion(self, count, errors):
            self.progress.set(1)
            self.lbl_status.configure(text="Complete")
            
            msg = f"Converted {count} image{'s' if count != 1 else ''}."
            if errors:
                msg += f"\n\nErrors ({len(errors)}):\n" + "\n".join(errors[:5])
                if len(errors) > 5:
                    msg += "\n..."
                messagebox.showwarning("Done with Errors", msg)
            else:
                messagebox.showinfo("Success", msg)
            
            self.destroy()
    
    return ImageConverterGUI


if __name__ == "__main__":
    if len(sys.argv) > 1:
        anchor = sys.argv[1]
        
        # INSTANT: Get all selected files via Explorer COM
        all_files = get_all_selected_files(anchor)
        
        # Quick mutex check (minimal delay)
        from utils.batch_runner import collect_batch_context
        if collect_batch_context("image_convert", anchor, timeout=0.2) is None:
            sys.exit(0)
        
        # Load GUI and run
        ImageConverterGUI = main()
        app = ImageConverterGUI(all_files)
        app.mainloop()
    else:
        ImageConverterGUI = main()
        app = ImageConverterGUI([])
        app.mainloop()
