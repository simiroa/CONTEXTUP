import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from pathlib import Path
from PIL import Image
import sys
import torch # Fix for [WinError 127] shm.dll load order conflict with Paddle/OpenCV
import os
import threading

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent.parent # src/features/ai/standalone -> src
if str(src_dir) not in sys.path:
    sys.path.append(str(src_dir))

from utils.config_persistence import load_gui_state, save_gui_state

# Third-party libraries (lazy imported in run function where possible, but top level for GUI if needed)
# We'll lazy load PaddleOCR to keep startup fast

class PdfOcrToolGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Load State
        self.gui_state = load_gui_state("pdf_ocr", {
            "lang": "korean",
            "use_gpu": True,
            "angle_cls": True, 
            "threshold": 0.5,
            "page_range": ""
        })

        self.title("PDF/Image OCR (PaddleOCR)")
        self.geometry("700x600") # Increased size
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Center window
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - 700) // 2
        y = (screen_height - 600) // 2
        self.geometry(f"700x600+{x}+{y}")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1) # Log area takes space

        # 1. File Selection
        self.frame_file = ctk.CTkFrame(self)
        self.frame_file.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        self.frame_file.grid_columnconfigure(1, weight=1)

        self.lbl_file = ctk.CTkLabel(self.frame_file, text="Input File:", width=80)
        self.lbl_file.grid(row=0, column=0, padx=10, pady=10)

        self.entry_file = ctk.CTkEntry(self.frame_file, placeholder_text="Select a PDF or Image file...")
        self.entry_file.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        self.btn_browse = ctk.CTkButton(self.frame_file, text="Browse", width=80, command=self.browse_file)
        self.btn_browse.grid(row=0, column=2, padx=10, pady=10)

        # 2. Basic Options
        self.frame_basic = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_basic.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
        
        # Language
        self.lbl_lang = ctk.CTkLabel(self.frame_basic, text="Language:")
        self.lbl_lang.pack(side="left", padx=(0,10))
        
        self.combo_lang = ctk.CTkOptionMenu(self.frame_basic, values=["korean", "en", "japan", "chinese_cht", "french", "german"], width=120)
        self.combo_lang.set(self.gui_state.get("lang", "korean"))
        self.combo_lang.pack(side="left", padx=10)

        # Page Range
        self.lbl_pages = ctk.CTkLabel(self.frame_basic, text="Page Range (e.g. 1-5, 8):")
        self.lbl_pages.pack(side="left", padx=(20,10))
        
        self.entry_pages = ctk.CTkEntry(self.frame_basic, placeholder_text="All", width=120)
        self.entry_pages.insert(0, self.gui_state.get("page_range", ""))
        self.entry_pages.pack(side="left", padx=10)

        # 3. Advanced Options
        self.lbl_adv = ctk.CTkLabel(self, text="Advanced Options", anchor="w", font=("Arial", 12, "bold"))
        self.lbl_adv.grid(row=2, column=0, padx=20, pady=(10, 0), sticky="ew")

        self.frame_adv = ctk.CTkFrame(self)
        self.frame_adv.grid(row=3, column=0, padx=20, pady=5, sticky="ew")
        
        # Row 1: Checkboxes
        self.frame_checks = ctk.CTkFrame(self.frame_adv, fg_color="transparent")
        self.frame_checks.pack(fill="x", padx=10, pady=5)

        self.check_gpu = ctk.CTkCheckBox(self.frame_checks, text="Use GPU")
        self.check_gpu.pack(side="left", padx=20)
        
        # Check CUDA availability and update UI
        # Priority: State > Auto-check
        # If state has use_gpu=True, check it. (User preference dominant)
        # But we should still warn if CUDA not available.
        cuda_available = self._check_cuda_available()
        
        should_check_gpu = self.gui_state.get("use_gpu", True)
        if should_check_gpu:
            self.check_gpu.select()
        else:
            self.check_gpu.deselect()

        if cuda_available:
            self.lbl_cuda_status = ctk.CTkLabel(self.frame_checks, text="✅ CUDA Available", text_color="green")
        else:
            self.lbl_cuda_status = ctk.CTkLabel(self.frame_checks, text="⚠️ CPU Only (CUDA not found)", text_color="orange")
            if should_check_gpu:
                 # User wants GPU but not available - maybe deselect or keep? 
                 # Keep it checked but status warning is enough.
                 pass
        self.lbl_cuda_status.pack(side="left", padx=5)

        self.check_angle = ctk.CTkCheckBox(self.frame_checks, text="Auto-Rotate (Angle Correction)")
        if self.gui_state.get("angle_cls", True):
            self.check_angle.select()
        else:
            self.check_angle.deselect()
        self.check_angle.pack(side="left", padx=20)

        # Row 2: Threshold Slider
        self.frame_thresh = ctk.CTkFrame(self.frame_adv, fg_color="transparent")
        self.frame_thresh.pack(fill="x", padx=10, pady=10)

        self.lbl_thresh = ctk.CTkLabel(self.frame_thresh, text="Min Confidence (0.50):")
        self.lbl_thresh.pack(side="left", padx=10)
        
        self.slider_thresh = ctk.CTkSlider(self.frame_thresh, from_=0.0, to=1.0, number_of_steps=20, command=self.update_thresh_label)
        self.slider_thresh.set(self.gui_state.get("threshold", 0.5))
        self.update_thresh_label(self.gui_state.get("threshold", 0.5))
        self.slider_thresh.pack(side="left", fill="x", expand=True, padx=20)

        # 4. Action & Progress
        self.frame_action = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_action.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        
        self.btn_run = ctk.CTkButton(self.frame_action, text="Start OCR", height=40, font=("Arial", 14, "bold"), command=self.start_ocr_thread)
        self.btn_run.pack(fill="x")

        self.progress_bar = ctk.CTkProgressBar(self.frame_action)
        self.progress_bar.pack(fill="x", pady=(10, 0))
        self.progress_bar.set(0)

        # 5. Log
        self.textbox_log = ctk.CTkTextbox(self, state="disabled")
        self.textbox_log.grid(row=5, column=0, padx=20, pady=(10, 20), sticky="nsew")

    def _check_cuda_available(self):
        """Check if CUDA is available for PaddlePaddle."""
        try:
            import paddle
            return paddle.device.is_compiled_with_cuda() and paddle.device.cuda.device_count() > 0
        except ImportError:
            # Paddle not installed yet, assume CPU
            return False
        except Exception:
            return False

    def check_cuda(self):
        return self._check_cuda_available()

    def update_thresh_label(self, value):
        self.lbl_thresh.configure(text=f"Min Confidence ({value:.2f}):")

    def on_closing(self):
        # Save State
        try:
            state = {
                "lang": self.combo_lang.get(),
                "use_gpu": bool(self.check_gpu.get()),
                "angle_cls": bool(self.check_angle.get()),
                "threshold": self.slider_thresh.get(),
                "page_range": self.entry_file.get() # Persist input? Maybe not file path but range
            }
            # Actually range is entry_pages
            state["page_range"] = self.entry_pages.get()
            
            save_gui_state("pdf_ocr", state)
        except Exception as e:
            print(f"Error saving state: {e}")
            
        self.quit()

    def browse_file(self):
        path = filedialog.askopenfilename(filetypes=[("PDF & Images", "*.pdf;*.png;*.jpg;*.jpeg;*.bmp;*.tiff;*.webp"), ("PDF Files", "*.pdf"), ("Images", "*.png;*.jpg;*.jpeg;*.bmp;*.tiff;*.webp")])
        if path:
            self.entry_file.delete(0, "end")
            self.entry_file.insert(0, path)

    def log(self, text):
        self.textbox_log.configure(state="normal")
        self.textbox_log.insert("end", text + "\n")
        self.textbox_log.see("end")
        self.textbox_log.configure(state="disabled")

    def parse_page_range(self, range_str, total_pages):
        if not range_str.strip():
            return range(total_pages)
        
        pages = set()
        parts = range_str.split(',')
        for part in parts:
            part = part.strip()
            if '-' in part:
                try:
                    start, end = map(int, part.split('-'))
                    # 1-based to 0-based
                    start = max(1, start)
                    end = min(total_pages, end)
                    if start <= end:
                        pages.update(range(start-1, end))
                except ValueError:
                    continue
            else:
                try:
                    p = int(part)
                    if 1 <= p <= total_pages:
                        pages.add(p-1)
                except ValueError:
                    continue
        return sorted(list(pages))

    def start_ocr_thread(self):
        pdf_path = self.entry_file.get()
        if not pdf_path or not os.path.exists(pdf_path):
            messagebox.showerror("Error", "Please select a valid PDF file.")
            return

        self.is_running = True
        self.btn_run.configure(state="disabled", text="Running...")
        self.btn_cancel = ctk.CTkButton(self.frame_action, text="Cancel", fg_color="red", command=self.cancel_ocr)
        self.btn_cancel.pack(side="right", padx=10)
        
        self.textbox_log.configure(state="normal")
        self.textbox_log.delete("1.0", "end")
        self.textbox_log.configure(state="disabled")
        self.progress_bar.set(0)

        threading.Thread(target=self.run_ocr, args=(pdf_path,), daemon=True).start()

    def cancel_ocr(self):
        self.is_running = False
        self.log("Stopping...")

    def run_ocr(self, pdf_path):
        import time
        from pdf2image import convert_from_path
        
        lang = self.combo_lang.get()
        use_gpu = bool(self.check_gpu.get())
        use_angle_cls = bool(self.check_angle.get())
        drop_score = self.slider_thresh.get()
        
        self.log(f"Initializing PaddleOCR ({lang})...")
        self.log(f"Options: GPU={use_gpu}, Angle={use_angle_cls}, Score={drop_score:.2f}")

        try:
            from paddleocr import PaddleOCR
            
            # Initialize OCR engine
            device_val = "gpu" if use_gpu else "cpu"
            ocr = PaddleOCR(use_textline_orientation=use_angle_cls, lang=lang, device=device_val)
            
            self.log("Loading file...")
            ext = Path(pdf_path).suffix.lower()
            
            if ext == '.pdf':
                self.log("Converting PDF to images...")
                all_images = convert_from_path(pdf_path)
                total_pages = len(all_images)
                
                # Filter pages for PDF
                target_indices = self.parse_page_range(self.entry_pages.get(), total_pages)
                self.log(f"PDF has {total_pages} pages. Processing {len(target_indices)} pages.")
            else:
                # Assume Image
                self.log(f"Detected Image ({ext}). Processing single image.")
                try:
                    img = Image.open(pdf_path).convert('RGB')
                    all_images = [img]
                    target_indices = [0] # Single page
                except Exception as e:
                    self.log(f"Failed to load image: {e}")
                    raise
            
            total_target = len(target_indices)
            full_text = ""
            
            for i, page_idx in enumerate(target_indices):
                if not self.is_running:
                    self.log("Confirmed Cancel.")
                    break

                page_num_user = page_idx + 1
                img = all_images[page_idx]
                
                self.log(f"Processing Page {page_num_user} ({i+1}/{total_target})...")
                
                import numpy as np
                img_np = np.array(img)
                
                result = ocr.ocr(img_np, use_textline_orientation=use_angle_cls)
                
                page_text_block = f"\n--- Page {page_num_user} ---\n"
                
                if result and result[0]:
                    for line in result:
                        if not line: continue
                        for box in line:
                            text_content = box[1][0]
                            confidence = box[1][1]
                            
                            if confidence >= drop_score:
                                page_text_block += text_content + "\n"
                
                full_text += page_text_block
                
                # Update progress
                progress = (i + 1) / total_target
                self.progress_bar.set(progress)

            # Save result if we have something
            output_path = str(Path(pdf_path).with_suffix(".txt"))
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(full_text)
            
            if self.is_running:
                self.log(f"Done! Saved to:\n{output_path}")
                self.progress_bar.set(1.0)
                
                # Open Button
                self.btn_open = ctk.CTkButton(self.frame_action, text="Open Result", fg_color="green", command=lambda: os.startfile(output_path))
                self.btn_open.pack(side="right", padx=10)
                
                messagebox.showinfo("Success", f"OCR Complete!\nSaved to {output_path}")
            else:
                self.log("Cancelled. Partial result saved.")
            
        except ImportError as e:
            self.log(f"Error: Missing libraries. {e}")
            messagebox.showerror("Error", f"Missing libraries: {e}")
        except Exception as e:
            self.log(f"Error: {e}")
            import traceback
            traceback.print_exc()
            self.log(traceback.format_exc())
            messagebox.showerror("Error", f"OCR Failed: {e}")
        finally:
            self.is_running = False
            self.btn_run.configure(state="normal", text="Start OCR")
            if hasattr(self, 'btn_cancel'): self.btn_cancel.destroy()


if __name__ == "__main__":
    # Setup Debug Logging
    try:
        log_dir = Path(__file__).resolve().parent.parent.parent.parent / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "pdf_ocr_debug.log"
        
        # Simple file logger
        def debug_log(msg):
            with open(log_file, "a", encoding="utf-8") as f:
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{timestamp}] {msg}\n")
        
        debug_log(f"Starting PDF OCR Tool. Args: {sys.argv}")
    except Exception as e:
        print(f"Failed to setup logging: {e}")
        def debug_log(msg): pass

    try:
        # Appearance mode is inherited from settings.json
        app = PdfOcrToolGUI()
        if len(os.sys.argv) > 1:
            # If file path passed as argument (from context menu)
            fpath = os.sys.argv[1]
            debug_log(f"Received file argument: {fpath}")
            if os.path.exists(fpath):
                app.entry_file.delete(0, "end")
                app.entry_file.insert(0, fpath)
            else:
                 debug_log(f"File does not exist: {fpath}")
        
        debug_log("Starting mainloop...")
        app.mainloop()
        debug_log("Exited mainloop.")
        
    except Exception as e:
        import traceback
        err = traceback.format_exc()
        debug_log(f"CRITICAL ERROR: {err}")
        try:
            messagebox.showerror("Critical Error", f"Failed to start PDF OCR:\n{e}")
        except: pass
