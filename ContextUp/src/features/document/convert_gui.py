import sys
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

# Add src to path for utils
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent
if str(src_dir) not in sys.path:
    sys.path.append(str(src_dir))

from utils.gui_lib import (BaseWindow, FileListFrame, setup_theme, THEME_BG, THEME_CARD, THEME_BORDER, THEME_TEXT_DIM,
                                THEME_BTN_PRIMARY, THEME_BTN_HOVER, THEME_DROPDOWN_FG, THEME_DROPDOWN_BTN, THEME_DROPDOWN_HOVER,
                                THEME_ACCENT, THEME_TEXT_MAIN)
from features.document.core.converter import DocumentConverter

# Supported Conversions Matrix
# Key: (Source Ext, Target Format Label) -> (Target Ext, Type)
CONVERSIONS = {
    '.pdf': {
        "Word (DOCX)": ".docx",
        "Excel (XLSX)": ".xlsx",
        "PowerPoint (PPTX)": ".pptx",
        "Image (PNG)": ".png",
        "Image (JPG)": ".jpg",
        "EPUB (E-Book)": ".epub",
        "HTML (Styled)": ".html",
        "Markdown (MD)": ".md",
        "Extract Embedded Images": ".images",
    },
    '.docx': {
        "PDF Document": ".pdf",
        "Extract Embedded Images": ".images"
    },
    '.doc': {"PDF Document": ".pdf"},
    '.xlsx': {
        "PDF Document": ".pdf",
        "Extract Embedded Images": ".images"
    },
    '.xls': {"PDF Document": ".pdf"},
    '.pptx': {
        "PDF Document": ".pdf",
        "Extract Embedded Images": ".images"
    },
    '.ppt': {"PDF Document": ".pdf"},
    '.png': {"PDF Document": ".pdf"},
    '.jpg': {"PDF Document": ".pdf"},
    '.jpeg': {"PDF Document": ".pdf"},
    '.md': {
        "PDF Document": ".pdf",
        "HTML Webpage": ".html"
    }
}

class DocConverterGUI(BaseWindow):
    def __init__(self, files_list=None, dev_mode=False):
        super().__init__(title="Document Converter", width=380, height=620, icon_name="document_convert")
        self.dev_mode = dev_mode
        
        raw_files = [Path(f) for f in files_list] if files_list else []
        self.files = [f for f in raw_files if f.exists()]
        self.files = list(dict.fromkeys(self.files)) # Unique files

        if not self.files and not self.dev_mode:
            messagebox.showerror("Error", "선택된 파일이 없습니다.")
            self.destroy()
            return
        
        if self.dev_mode:
            # Add a dummy file for visual check if none provided
            if not self.files:
                self.files = [Path("sample_document.pdf")]
            # Auto-close after 5 seconds for automated tests
            self.after(5000, self.destroy)

        self.converter = DocumentConverter()
        self._is_running = False
        
        self.create_ui()
        self._detect_possible_conversions()

    def create_ui(self):
        # Header Section
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        ctk.CTkLabel(header_frame, text="📄 Document Converter", 
                     font=ctk.CTkFont(size=18, weight="bold"), text_color=THEME_TEXT_MAIN).pack(side="left")
        ctk.CTkLabel(header_frame, text=f"{len(self.files)} file(s)", 
                     font=ctk.CTkFont(size=12), text_color=THEME_TEXT_DIM).pack(side="right", pady=(5, 0))

        # File List Scrollable Area
        self.file_list_frame = FileListFrame(self.main_frame, self.files, height=100)
        self.file_list_frame.pack(fill="x", padx=10, pady=2)

        # Settings Card
        settings_card = self.create_card_frame(self.main_frame)
        settings_card.pack(fill="x", padx=10, pady=10)
        
        # Target Format Row
        fmt_row = ctk.CTkFrame(settings_card, fg_color="transparent")
        fmt_row.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(fmt_row, text="Target Format:", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
        self.fmt_var = ctk.StringVar(value="Select...")
        self.fmt_menu = ctk.CTkOptionMenu(fmt_row, variable=self.fmt_var, values=["Select..."],
                                          command=self._on_format_change, height=32, 
                                          fg_color=THEME_DROPDOWN_FG, button_color=THEME_DROPDOWN_BTN, 
                                          button_hover_color=THEME_DROPDOWN_HOVER)
        self.fmt_menu.pack(side="right", fill="x", expand=True, padx=(10, 0))

        # Options Container
        self.options_frame = ctk.CTkFrame(settings_card, fg_color="transparent", height=0)
        self.options_frame.pack(fill="x", padx=15, pady=0)
        
        # Separator
        ctk.CTkFrame(settings_card, height=1, fg_color=THEME_BORDER).pack(fill="x", padx=15, pady=5)
        
        # Global Options
        global_opts = ctk.CTkFrame(settings_card, fg_color="transparent")
        global_opts.pack(fill="x", padx=15, pady=(5, 10))
        
        self.var_subfolder = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(global_opts, text="Create 'Converted' Subfolder", variable=self.var_subfolder,
                        font=ctk.CTkFont(size=11), checkbox_width=18, checkbox_height=18,
                        fg_color=THEME_BTN_PRIMARY, hover_color=THEME_BTN_HOVER).pack(side="left", pady=0)

        # DPI Setting (Only for PDF -> Image)
        self.dpi_frame = ctk.CTkFrame(self.options_frame, fg_color="transparent")
        ctk.CTkLabel(self.dpi_frame, text="DPI:", font=ctk.CTkFont(size=11)).pack(side="left", padx=(0, 5))
        self.dpi_var = ctk.StringVar(value="300")
        self.dpi_menu = ctk.CTkOptionMenu(self.dpi_frame, variable=self.dpi_var,
                                           values=["72", "150", "200", "300", "400", "600"], 
                                           height=24, width=80, font=ctk.CTkFont(size=11))
        self.dpi_menu.pack(side="left")
        
        # Progress Section
        self.progress_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.progress_frame.pack(fill="x", padx=15, pady=10)
        
        self.status_label = ctk.CTkLabel(self.progress_frame, text="Ready", text_color=THEME_TEXT_DIM, font=ctk.CTkFont(size=11))
        self.status_label.pack(anchor="w")
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, height=8, corner_radius=4)
        self.progress_bar.pack(fill="x", pady=(5, 0))
        self.progress_bar.set(0)
        
        self.detail_label = ctk.CTkLabel(self.progress_frame, text="", text_color=THEME_TEXT_DIM, font=ctk.CTkFont(size=10))
        self.detail_label.pack(anchor="w")

        # Action Buttons
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=(5, 15))
        
        self.btn_cancel = ctk.CTkButton(btn_frame, text="Cancel", fg_color="transparent", 
                                         border_width=1, border_color=THEME_BORDER, 
                                         text_color=THEME_TEXT_DIM, command=self._on_cancel, height=36)
        self.btn_cancel.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.btn_run = ctk.CTkButton(btn_frame, text="Convert All", command=self.start_conversion, 
                                     height=36, font=ctk.CTkFont(weight="bold"),
                                     fg_color=THEME_BTN_PRIMARY, hover_color=THEME_BTN_HOVER)
        self.btn_run.pack(side="right", fill="x", expand=True, padx=(5, 0))

    def _detect_possible_conversions(self):
        """Analyze selected files and populate format dropdown"""
        possible = set()
        common_formats = None
        
        for f in self.files:
            ext = f.suffix.lower()
            formats_for_ext = CONVERSIONS.get(ext, {})
            if common_formats is None:
                common_formats = set(formats_for_ext.keys())
            else:
                common_formats = common_formats.intersection(set(formats_for_ext.keys()))
        
        if common_formats:
            sorted_formats = sorted(list(common_formats))
            self.fmt_menu.configure(values=sorted_formats)
            self.fmt_var.set(sorted_formats[0])
            self._on_format_change(sorted_formats[0])
        else:
            self.fmt_menu.configure(values=["Incompatible files"])
            self.fmt_var.set("Incompatible files")
            self.btn_run.configure(state="disabled")

    def _on_format_change(self, choice):
        # Show/Hide context specific options
        # Hide all first
        self.dpi_frame.pack_forget()
        
        if "Image" in choice:
            self.dpi_frame.pack(side="left", pady=5)

    def _on_cancel(self):
        if self._is_running:
            self._is_running = False
            self.status_label.configure(text="Cancelling...", text_color="orange")
            self.converter.cancel()
        else:
            self.destroy()

    def start_conversion(self):
        choice = self.fmt_var.get()
        if choice == "Select..." or choice == "Incompatible files":
            return
            
        self._is_running = True
        self.btn_run.configure(state="disabled", text="Processing...")
        self.btn_cancel.configure(text="Stop")
        self.progress_bar.set(0)
        self.status_label.configure(text="Initializing...", text_color=THEME_TEXT_MAIN)
        
        threading.Thread(target=self._run_thread, daemon=True).start()

    def _update_status(self, text, detail="", progress=None):
        def update():
            self.status_label.configure(text=text)
            self.detail_label.configure(text=detail)
            if progress is not None:
                self.progress_bar.set(progress)
        self.after(0, update)

    def _run_thread(self):
        success_count = 0
        errors = []
        
        target_label = self.fmt_var.get()
        use_subfolder = self.var_subfolder.get()
        
        options = {
            'dpi': int(self.dpi_var.get()),
            'separate_pages': True # Default for now
        }

        total = len(self.files)
        jobs = []

        # Prepare jobs
        for fpath in self.files:
            try:
                # Determine target extension from matrix
                ext = fpath.suffix.lower()
                target_ext = CONVERSIONS.get(ext, {}).get(target_label)
                if not target_ext:
                    raise ValueError(f"Unknown target extension for {ext} to {target_label}")
                
                out_dir = fpath.parent
                if use_subfolder:
                    out_dir = out_dir / "Converted_Docs"
                    out_dir.mkdir(exist_ok=True)
                
                jobs.append({
                    'fpath': fpath,
                    'target_ext': target_ext,
                    'out_dir': out_dir,
                    'options': options
                })
            except Exception as e:
                errors.append(f"{fpath.name}: {str(e)}")

        completed = 0
        total_jobs = len(jobs)
        
        if total_jobs > 0:
            with ThreadPoolExecutor(max_workers=3) as executor:
                # Map futures to jobs
                future_to_job = {executor.submit(self._convert_single, job): job for job in jobs}
                
                for future in as_completed(future_to_job):
                    if not self._is_running:
                        break
                        
                    job = future_to_job[future]
                    try:
                        future.result()
                        success_count += 1
                    except Exception as e:
                        errors.append(f"{job['fpath'].name}: {str(e)}")
                    
                    completed += 1
                    self._update_status(f"Converting {completed}/{total_jobs}", job['fpath'].name, completed / total_jobs)
        
        self.after(0, lambda: self._finish(success_count, errors))

    def _convert_single(self, job):
        if not self._is_running: return
        self.converter.convert(job['fpath'], job['target_ext'], job['out_dir'], job['options'])

    def _finish(self, count, errors):
        self._is_running = False
        self.btn_run.configure(state="normal", text="Convert All")
        self.btn_cancel.configure(text="Cancel")
        
        if errors:
            msg = "변환 중 문제가 발생했습니다:\n" + "\n".join(errors[:3])
            if len(errors) > 3: 
                msg += f"\n... 외 {len(errors) - 3}건"
            self._update_status("Completed with errors", f"{count} succeeded, {len(errors)} failed", 1.0)
            messagebox.showwarning("Warning", msg)
        else:
            self._update_status("성공적으로 완료되었습니다!", f"{count}개 파일 변환 완료", 1.0)
            messagebox.showinfo("Success", f"{count}개 파일이 성공적으로 변환되었습니다.")
            self.destroy()

if __name__ == "__main__":
    # Dev mode check
    dev_mode = "--dev" in sys.argv
    if dev_mode:
        sys.argv.remove("--dev")
    
    files = sys.argv[1:] if len(sys.argv) > 1 else []
    
    # If no files provided and not in dev mode, show a file dialog
    if not files and not dev_mode:
        import tkinter.filedialog as fd
        root = tk.Tk()
        root.withdraw()
        files = fd.askopenfilenames(title="변환할 파일 선택")
        root.destroy()
        if not files: sys.exit(0)

    setup_theme()
    app = DocConverterGUI(files, dev_mode=dev_mode)
    app.mainloop()
