"""
Document Converter GUI (PyMuPDF Enhanced Version)
Uses PyMuPDF for all PDF operations with advanced features:
- High-quality image export with DPI control
- Table extraction to CSV/Excel
- Image extraction from PDFs
- Annotation extraction
- Metadata extraction
- No external Poppler dependency
"""
import sys
import os
import threading
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

# Setup file-only logger (no console output for GUI)
import logging
def setup_simple_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        # File log only (no console to avoid CMD window)
        try:
            log_dir = Path(__file__).parent.parent.parent.parent / "logs"
            log_dir.mkdir(exist_ok=True)
            f_handler = logging.FileHandler(log_dir / f"{name}.log", encoding='utf-8')
            f_handler.setFormatter(formatter)
            logger.addHandler(f_handler)
        except Exception:
            pass
    return logger

logger = setup_simple_logger("doc_converter")
logger.info(f"Startup Executable: {sys.executable}")

# Add src to path for utils
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent
sys.path.append(str(src_dir))

# Try to import GUI utils
try:
    from utils.gui_lib import FileListFrame, setup_theme
    # Use custom BaseWindow with less padding but theme-aware
    class BaseWindow(ctk.CTk):
        def __init__(self, title, width, height, icon_name=None):
            super().__init__()
            setup_theme()  # Apply theme from settings.json
            self.title(title)
            self.geometry(f"{width}x{height}")
            # Minimal padding for compact UI
            self.main_frame = ctk.CTkFrame(self)
            self.main_frame.pack(fill="both", expand=True, padx=5, pady=5)
except ImportError:
    class BaseWindow(ctk.CTk):
        def __init__(self, title, width, height, icon_name=None):
            super().__init__()
            self.title(title)
            self.geometry(f"{width}x{height}")
            self.main_frame = ctk.CTkFrame(self)
            self.main_frame.pack(fill="both", expand=True, padx=5, pady=5)
            
    class FileListFrame(ctk.CTkFrame):
        def __init__(self, master, files, height=200):
            super().__init__(master, height=height)
            self.lbl = ctk.CTkLabel(self, text="\n".join([str(f) for f in files[:5]]))
            self.lbl.pack()


# Output format configurations
OUTPUT_FORMATS = {
    "PNG (High Quality)": {"ext": "png", "type": "image", "dpi": 300, "supports_ocr": False, "supports_dpi": True},
    "JPG (Compressed)": {"ext": "jpg", "type": "image", "dpi": 200, "supports_ocr": False, "supports_dpi": True},
    "PNG (Web/Fast)": {"ext": "png", "type": "image", "dpi": 150, "supports_ocr": False, "supports_dpi": True},
    "DOCX": {"ext": "docx", "type": "docx", "supports_ocr": False, "supports_dpi": False}, # pdf2docx handles text naturally
    "TXT (Text Only)": {"ext": "txt", "type": "text", "supports_ocr": True, "supports_dpi": False},
    "HTML (Styled)": {"ext": "html", "type": "html", "supports_ocr": False, "supports_dpi": False},
    "Markdown (LLM)": {"ext": "md", "type": "markdown", "supports_ocr": True, "supports_dpi": False},
    "CSV (Tables Only)": {"ext": "csv", "type": "tables", "supports_ocr": True, "supports_dpi": False}, # OCR used for text in tables? Maybe.
    "Extract Images": {"ext": "various", "type": "extract_images", "supports_ocr": False, "supports_dpi": False},
}


class DocConverterGUI(BaseWindow):
    def __init__(self, files_list=None):
        try:
            super().__init__(title="Document Converter", width=380, height=520, icon_name="document_convert")
            
            raw_files = [Path(f) for f in files_list] if files_list else []
            self.files = [f for f in raw_files if f.exists() and f.suffix.lower() == '.pdf']
            self.files = list(dict.fromkeys(self.files))

            if not self.files:
                messagebox.showerror("Error", "No PDF files selected.")
                self.destroy()
                return

            self._is_running = False
            self.create_ui()
            
        except Exception as e:
            messagebox.showerror("Critical Error", f"Failed to initialize GUI: {e}")
            logger.exception("Init failed")
            self.destroy()

    def create_ui(self):
        # Use grid for precise layout control
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        row = 0
        
        # === Header ===
        header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header.grid(row=row, column=0, sticky="ew", padx=10, pady=(5, 2))
        header.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(header, text="📄 Document Converter", 
                     font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(header, text=f"{len(self.files)} file(s)", 
                     font=ctk.CTkFont(size=11), text_color="gray").grid(row=0, column=1, sticky="e")
        row += 1
        
        # === File List (scrollable) ===
        self.file_list = FileListFrame(self.main_frame, self.files, height=80)
        self.file_list.grid(row=row, column=0, sticky="ew", padx=10, pady=2)
        row += 1
        
        # === Format & DPI Row ===
        format_row = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        format_row.grid(row=row, column=0, sticky="ew", padx=10, pady=5)
        format_row.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(format_row, text="Format:", width=50, anchor="w").grid(row=0, column=0, sticky="w")
        self.fmt_var = ctk.StringVar(value="PNG (High Quality)")
        ctk.CTkOptionMenu(format_row, variable=self.fmt_var, values=list(OUTPUT_FORMATS.keys()),
                          command=self._on_format_change, height=28, width=180).grid(row=0, column=1, sticky="w", padx=(5,10))
        
        ctk.CTkLabel(format_row, text="DPI:", width=30, anchor="e").grid(row=0, column=2, sticky="e")
        self.dpi_var = ctk.StringVar(value="300")
        self.dpi_menu = ctk.CTkOptionMenu(format_row, variable=self.dpi_var,
                                           values=["72", "150", "200", "300", "400", "600"], height=28, width=70)
        self.dpi_menu.grid(row=0, column=3, sticky="e", padx=(5,0))
        row += 1
        
        # === Options Container ===
        self.var_extract_tables = ctk.BooleanVar(value=False)
        self.var_extract_images = ctk.BooleanVar(value=False)
        self.var_include_metadata = ctk.BooleanVar(value=False)
        self.var_markdown = ctk.BooleanVar(value=False)
        self.var_separate_pages = ctk.BooleanVar(value=True)
        self.var_folder = ctk.BooleanVar(value=True)
        
        cb_font = ctk.CTkFont(size=11)
        
        # --- Conversion Options Group ---
        conv_frame = ctk.CTkFrame(self.main_frame)
        conv_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=2)
        conv_frame.grid_columnconfigure((0,1,2), weight=1)
        ctk.CTkLabel(conv_frame, text="Conversion Options", font=ctk.CTkFont(size=10, weight="bold")).grid(row=0, column=0, columnspan=3, sticky="w", padx=5, pady=2)
        
        self.cb_markdown = ctk.CTkCheckBox(conv_frame, text="+ Markdown", variable=self.var_markdown, font=cb_font, checkbox_width=16, checkbox_height=16)
        self.cb_markdown.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        
        self.cb_separate_pages = ctk.CTkCheckBox(conv_frame, text="Sep. Pages", variable=self.var_separate_pages, font=cb_font, checkbox_width=16, checkbox_height=16)
        self.cb_separate_pages.grid(row=1, column=2, sticky="w", padx=5, pady=2)
        row += 1

        # --- Extraction & General Group ---
        extra_frame = ctk.CTkFrame(self.main_frame)
        extra_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=2)
        extra_frame.grid_columnconfigure((0,1,2), weight=1)
        ctk.CTkLabel(extra_frame, text="Extraction & Output", font=ctk.CTkFont(size=10, weight="bold")).grid(row=0, column=0, columnspan=3, sticky="w", padx=5, pady=2)
        
        ctk.CTkCheckBox(extra_frame, text="Extract Tables", variable=self.var_extract_tables, font=cb_font, checkbox_width=16, checkbox_height=16).grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ctk.CTkCheckBox(extra_frame, text="Extract Images", variable=self.var_extract_images, font=cb_font, checkbox_width=16, checkbox_height=16).grid(row=1, column=1, sticky="w", padx=5, pady=2)
        ctk.CTkCheckBox(extra_frame, text="Metadata", variable=self.var_include_metadata, font=cb_font, checkbox_width=16, checkbox_height=16).grid(row=1, column=2, sticky="w", padx=5, pady=2)
        
        ctk.CTkCheckBox(extra_frame, text="Create Subfolder", variable=self.var_folder, font=cb_font, checkbox_width=16, checkbox_height=16).grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=2)
        row += 1
        
        # === Progress ===
        prog_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        prog_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=3)
        
        self.status_label = ctk.CTkLabel(prog_frame, text="Ready", text_color="gray", font=ctk.CTkFont(size=10))
        self.status_label.pack(anchor="w")
        self.progress = ctk.CTkProgressBar(prog_frame, height=6)
        self.progress.pack(fill="x", pady=2)
        self.progress.set(0)
        self.detail_label = ctk.CTkLabel(prog_frame, text="", text_color="gray", font=ctk.CTkFont(size=9))
        self.detail_label.pack(anchor="w")
        row += 1
        
        # === Buttons ===
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=(5, 10))
        btn_frame.grid_columnconfigure((0, 1), weight=1)
        
        self.btn_cancel = ctk.CTkButton(btn_frame, text="Cancel", fg_color="transparent", 
                                         border_width=1, text_color="gray", command=self._on_cancel, height=30)
        self.btn_cancel.grid(row=0, column=0, sticky="ew", padx=(0, 3))
        
        self.btn_run = ctk.CTkButton(btn_frame, text="Convert All", command=self.start_conversion, height=30)
        self.btn_run.grid(row=0, column=1, sticky="ew", padx=(3, 0))

        # Initial State Update
        self._update_ui_state()

    def _on_format_change(self, choice):
        """Handle format change event"""
        self._update_ui_state()

    def _update_ui_state(self):
        """Enable/Disable widgets based on current format selection"""
        choice = self.fmt_var.get()
        fmt_config = OUTPUT_FORMATS.get(choice, {})
        
        supports_dpi = fmt_config.get("supports_dpi", False)
        fmt_type = fmt_config.get("type", "")

        # DPI
        self.dpi_menu.configure(state="normal" if supports_dpi else "disabled")
        
        # Separate Pages (Only for Image)
        if fmt_type == "image":
            self.cb_separate_pages.configure(state="normal", text_color=("black", "white"))
        else:
            self.cb_separate_pages.configure(state="disabled", text_color="gray")

        # Markdown Checkbox (Avoid redundancy)
        if fmt_type == "markdown":
            self.cb_markdown.configure(state="disabled", text_color="gray")
            self.var_markdown.set(False)
        else:
            self.cb_markdown.configure(state="normal", text_color=("black", "white"))

    def _on_cancel(self):
        if self._is_running:
            self._is_running = False
            self.status_label.configure(text="Cancelling...", text_color="orange")
        else:
            self.destroy()

    def start_conversion(self):
        self._is_running = True
        self.btn_run.configure(state="disabled", text="Processing...")
        self.btn_cancel.configure(text="Stop")
        self.progress.set(0)
        self.status_label.configure(text="Starting conversion...", text_color="white")
        
        threading.Thread(target=self._run_thread, daemon=True).start()

    def _update_status(self, text, detail="", progress=None):
        """Thread-safe status update"""
        def update():
            self.status_label.configure(text=text)
            self.detail_label.configure(text=detail)
            if progress is not None:
                self.progress.set(progress)
        self.after(0, update)

    def _run_thread(self):
        success = 0
        errors = []
        
        fmt_choice = self.fmt_var.get()
        fmt_config = OUTPUT_FORMATS.get(fmt_choice, {})
        fmt_type = fmt_config.get("type", "image")
        fmt_ext = fmt_config.get("ext", "png")
        
        try:
            dpi = int(self.dpi_var.get())
        except:
            dpi = 300
            
        extract_tables = self.var_extract_tables.get()
        extract_images = self.var_extract_images.get()
        include_metadata = self.var_include_metadata.get()
        also_markdown = self.var_markdown.get()
        separate_pages = self.var_separate_pages.get()
        use_folder = self.var_folder.get()

        total = len(self.files)
        
        for idx, fpath in enumerate(self.files):
            if not self._is_running:
                break
                
            try:
                self._update_status(f"Processing {idx+1}/{total}", fpath.name, idx / total)
                
                out_dir = fpath.parent
                if use_folder:
                    out_dir = out_dir / "Converted_Docs"
                    out_dir.mkdir(exist_ok=True)

                base = fpath.stem
                
                # Main conversion based on type
                if fmt_type == "image":
                    self._do_images(fpath, out_dir, fmt_ext, dpi, separate_pages)
                elif fmt_type == "docx":
                    self._do_docx(fpath, out_dir / f"{base}.docx")
                elif fmt_type == "html":
                    self._do_html(fpath, out_dir / f"{base}.html")
                elif fmt_type == "text":
                    self._do_txt(fpath, out_dir / f"{base}.txt")
                elif fmt_type == "markdown":
                    self._do_md(fpath, out_dir / f"{base}.md")
                elif fmt_type == "tables":
                    self._do_extract_tables(fpath, out_dir)
                elif fmt_type == "extract_images":
                    self._do_extract_embedded_images(fpath, out_dir)
                
                # Additional extractions if enabled
                if extract_tables and fmt_type != "tables":
                    self._do_extract_tables(fpath, out_dir)
                    
                if extract_images and fmt_type != "extract_images":
                    self._do_extract_embedded_images(fpath, out_dir)
                    
                if also_markdown and fmt_type != "markdown":
                    self._do_md(fpath, out_dir / f"{base}.md")
                    
                if include_metadata:
                    self._do_extract_metadata(fpath, out_dir / f"{base}_metadata.json")

                success += 1

            except Exception as e:
                import traceback
                trace = traceback.format_exc()
                logger.error(f"Failed {fpath}: {e}\n{trace}")
                errors.append(f"{fpath.name}: {str(e)}")
            
            self._update_status(f"Processing {idx+1}/{total}", fpath.name, (idx + 1) / total)
        
        self.after(0, lambda: self._finish(success, errors))

    def _finish(self, count, errors):
        self._is_running = False
        self.btn_run.configure(state="normal", text="Convert All")
        self.btn_cancel.configure(text="Cancel")
        
        if errors:
            msg = "Errors occurred:\n" + "\n".join(errors[:3])
            if len(errors) > 3: 
                msg += f"\n... and {len(errors) - 3} more"
            self._update_status("Completed with errors", f"{count} succeeded, {len(errors)} failed", 1.0)
            messagebox.showwarning("Incomplete", msg)
        else:
            self._update_status("Completed successfully!", f"Converted {count} files", 1.0)
            messagebox.showinfo("Success", f"Converted {count} files successfully.")
            self.destroy()

    # ==========================================================================
    # CONVERSION WORKERS (Using PyMuPDF)
    # ==========================================================================

    def _do_images(self, pdf, out_dir, fmt, dpi, separate_pages):
        """Convert PDF pages to images using PyMuPDF"""
        try:
            import pymupdf
        except ImportError:
            raise ImportError("PyMuPDF not installed. Run: pip install pymupdf")
        
        doc = pymupdf.open(str(pdf))
        
        # Calculate zoom from DPI (72 DPI is base)
        zoom = dpi / 72.0
        mat = pymupdf.Matrix(zoom, zoom)
        
        for i, page in enumerate(doc):
            if not self._is_running:
                break
                
            pix = page.get_pixmap(matrix=mat, alpha=False)
            output_path = out_dir / f"{pdf.stem}_p{i+1:03d}.{fmt}"
            
            if fmt.lower() == 'jpg':
                try:
                    from PIL import Image
                    import io
                    img_data = pix.tobytes("ppm")
                    img = Image.open(io.BytesIO(img_data))
                    img.save(str(output_path), "JPEG", quality=95, optimize=True)
                except ImportError:
                    pix.save(str(output_path))
            else:
                pix.save(str(output_path))
        
        doc.close()

    def _do_docx(self, pdf, out_path):
        """Convert PDF to DOCX"""
        try:
            from pdf2docx import Converter
        except ImportError:
            raise ImportError("pdf2docx not installed. Run: pip install pdf2docx")
            
        cv = Converter(str(pdf))
        try:
            cv.convert(str(out_path), start=0, end=None)
        finally:
            cv.close()

    def _do_html(self, pdf, out_path):
        """Convert PDF to HTML with styling"""
        try:
            import pymupdf
        except ImportError:
            raise ImportError("PyMuPDF not installed.")
                
        doc = pymupdf.open(str(pdf))
        
        html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{pdf.stem}</title>
    <style>
        :root {{ --bg: #1a1a2e; --text: #eaeaea; --accent: #4a9eff; --border: #333; }}
        body {{ 
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg); color: var(--text);
            max-width: 900px; margin: 0 auto; padding: 40px 20px; line-height: 1.8;
        }}
        h1 {{ color: var(--accent); border-bottom: 2px solid var(--accent); padding-bottom: 10px; }}
        .page {{ 
            background: #252542; border-radius: 8px; padding: 30px; margin: 20px 0;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }}
        .page-header {{ 
            color: var(--accent); font-size: 0.85em; margin-bottom: 15px;
            padding-bottom: 10px; border-bottom: 1px solid var(--border);
        }}
        table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
        th, td {{ border: 1px solid var(--border); padding: 10px; text-align: left; }}
        th {{ background: #333355; }}
        img {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
<h1>{pdf.stem}</h1>
"""
        
        for i, page in enumerate(doc):
            page_html = page.get_text("html")
            html_content += f'<div class="page">\n<div class="page-header">📄 Page {i+1}</div>\n{page_html}\n</div>\n'
        
        html_content += "</body>\n</html>"
        
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        doc.close()

    def _do_txt(self, pdf, out_path):
        """Extract text from PDF"""
        try:
            import pymupdf
        except ImportError:
            raise ImportError("PyMuPDF not installed.")
        
        text = ""
        doc = pymupdf.open(str(pdf))
        for page in doc:
            text += page.get_text() + "\n"
        
        doc.close()
        
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)

    def _do_md(self, pdf, out_path):
        """Convert PDF to Markdown (LLM optimized)"""
        try:
            import pymupdf4llm
            md = pymupdf4llm.to_markdown(str(pdf))
        except ImportError:
            # Fallback to basic extraction
            try:
                import pymupdf
                doc = pymupdf.open(str(pdf))
                md = f"# {pdf.stem}\n\n"
                
                for i, page in enumerate(doc):
                    md += f"## Page {i+1}\n\n"
                    md += page.get_text() + "\n\n"
                    
                    # Try to extract tables
                    try:
                        tables = page.find_tables()
                        for table in tables:
                            md += table.to_markdown() + "\n\n"
                    except:
                        pass
                
                doc.close()
            except ImportError:
                raise ImportError("PyMuPDF not installed.")
            
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(md)

    def _do_extract_tables(self, pdf, out_dir):
        """Extract tables from PDF to CSV files"""
        try:
            import pymupdf
        except ImportError:
            raise ImportError("PyMuPDF not installed.")
        
        doc = pymupdf.open(str(pdf))
        table_count = 0
        
        for page_num, page in enumerate(doc):
            try:
                tables = page.find_tables()
                for idx, table in enumerate(tables):
                    table_count += 1
                    csv_path = out_dir / f"{pdf.stem}_table_p{page_num+1}_{idx+1}.csv"
                    
                    # Extract table data
                    import csv
                    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
                        writer = csv.writer(f)
                        for row in table.extract():
                            writer.writerow([cell if cell else "" for cell in row])
            except Exception as e:
                logger.warning(f"Table extraction failed on page {page_num+1}: {e}")
        
        doc.close()
        logger.info(f"Extracted {table_count} tables from {pdf.name}")

    def _do_extract_embedded_images(self, pdf, out_dir):
        """Extract embedded images from PDF"""
        try:
            import pymupdf
        except ImportError:
            raise ImportError("PyMuPDF not installed.")
        
        doc = pymupdf.open(str(pdf))
        img_count = 0
        
        img_folder = out_dir / f"{pdf.stem}_images"
        img_folder.mkdir(exist_ok=True)
        
        for page_num, page in enumerate(doc):
            images = page.get_images()
            
            for img_idx, img_info in enumerate(images):
                try:
                    xref = img_info[0]
                    base_image = doc.extract_image(xref)
                    
                    if base_image:
                        img_count += 1
                        image_bytes = base_image["image"]
                        image_ext = base_image["ext"]
                        
                        img_path = img_folder / f"img_p{page_num+1}_{img_idx+1}.{image_ext}"
                        with open(img_path, "wb") as f:
                            f.write(image_bytes)
                except Exception as e:
                    logger.warning(f"Image extraction failed: {e}")
        
        doc.close()
        logger.info(f"Extracted {img_count} images from {pdf.name}")

    def _do_extract_metadata(self, pdf, out_path):
        """Extract PDF metadata to JSON"""
        try:
            import pymupdf
            import json
        except ImportError:
            raise ImportError("PyMuPDF not installed.")
        
        doc = pymupdf.open(str(pdf))
        
        metadata = {
            "file": pdf.name,
            "page_count": doc.page_count,
            "metadata": doc.metadata,
            "toc": doc.get_toc(),  # Table of contents
            "pages": []
        }
        
        for i, page in enumerate(doc):
            page_info = {
                "page": i + 1,
                "width": page.rect.width,
                "height": page.rect.height,
                "rotation": page.rotation,
                "image_count": len(page.get_images()),
                "link_count": len(page.get_links()),
            }
            
            # Count annotations
            try:
                annots = list(page.annots())
                page_info["annotation_count"] = len(annots) if annots else 0
            except:
                page_info["annotation_count"] = 0
                
            metadata["pages"].append(page_info)
        
        doc.close()
        
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2, default=str)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        files = sys.argv[1:]
        app = DocConverterGUI(files)
        app.mainloop()
