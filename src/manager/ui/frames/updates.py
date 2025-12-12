import customtkinter as ctk
import tkinter.messagebox
import threading
import time

class UpdatesFrame(ctk.CTkFrame):
    def __init__(self, parent, package_manager, config_manager=None):
        super().__init__(parent)
        self.package_manager = package_manager
        self.config_manager = config_manager
        self.installed_packages = {}
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header
        header = ctk.CTkFrame(self, height=50, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
        ctk.CTkLabel(header, text="Common Dependencies", font=ctk.CTkFont(size=20, weight="bold")).pack(side="left")
        
        ctk.CTkButton(header, text="Check Updates", command=self.refresh_deps).pack(side="right", padx=10)
        ctk.CTkButton(header, text="Update Sys Libs", fg_color="#8E44AD", command=self.update_system_libs).pack(side="right", padx=10)
        
        # List
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        
        # Deferred loading flag - check on first view instead of init
        self._deps_loaded = False
        self._show_loading_placeholder()

    def _show_loading_placeholder(self):
        """Show a placeholder message until deps are loaded."""
        for w in self.scroll_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self.scroll_frame, 
            text="Click 'Check Updates' to scan dependencies...",
            text_color="gray"
        ).pack(pady=20)

    def on_visible(self):
        """Called when this frame becomes visible - trigger deferred loading."""
        if not self._deps_loaded:
            self._deps_loaded = True
            self.refresh_deps()

    def refresh_deps(self):
        # Run in thread to not freeze UI
        threading.Thread(target=self._scan_deps, daemon=True).start()

    def _scan_deps(self):
        self.installed_packages = self.package_manager.get_installed_packages()
        
        # Define common heavy libs to check explicitly (as per original tool)
        common_libs = [
            ("torch", "PyTorch (AI Core)"),
            ("rembg", "Rembg (Background Removal)"),
            ("customtkinter", "CustomTkinter (GUI)"),
            ("pystray", "Pystray (System Tray)"),
            ("Pillow", "Pillow (Image Processing)"),
            ("google-generativeai", "Gemini API"),
            ("numpy", "NumPy"),
            ("pyperclip", "Pyperclip (Clipboard)"),
        ]
        
        # Clear UI
        self.after(0, self._clear_list)
        
        for pkg, label in common_libs:
            ver = self.installed_packages.get(pkg.lower(), None)
            self.after(0, lambda p=pkg, l=label, v=ver: self._add_row(p, l, v))

    def _clear_list(self):
        for w in self.scroll_frame.winfo_children():
            w.destroy()

    def _add_row(self, pkg, label, version):
        row = ctk.CTkFrame(self.scroll_frame)
        row.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(row, text=label, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)
        
        status_color = "green" if version else "#C0392B"
        status_text = f"Installed ({version})" if version else "Missing"
        ctk.CTkLabel(row, text=status_text, text_color=status_color).pack(side="left", padx=10)
        
        if not version:
             ctk.CTkButton(row, text="Install", width=80, 
                         command=lambda: self.install_pkg(pkg)).pack(side="right", padx=10)

    def install_pkg(self, pkg, install_args=None):
        if tkinter.messagebox.askyesno("Confirm", f"Install {pkg}? This might take a while."):
            # Show progress dialog (simple version)
            top = ctk.CTkToplevel(self)
            top.title(f"Installing {pkg}...")
            top.geometry("300x100")
            lbl = ctk.CTkLabel(top, text="Installing... Please wait.")
            lbl.pack(pady=20)
            bar = ctk.CTkProgressBar(top)
            bar.pack(pady=10)
            bar.start()
            
            # Metadata assumption
            meta = {pkg: {'pip_name': pkg, 'install_args': install_args or []}}

            def on_progress(p, f):
                pass 
                
            def on_complete(success):
                top.destroy()
                if success:
                    tkinter.messagebox.showinfo("Success", f"{pkg} installed.")
                    self.refresh_deps()
                else:
                    tkinter.messagebox.showerror("Error", f"Failed to install {pkg}. Check console.")
            
            self.package_manager.install_packages([pkg], meta, on_progress, on_complete)

    def update_system_libs(self):
        if tkinter.messagebox.askyesno("System Update", "Install all requirements to system Python?"):
            top = ctk.CTkToplevel(self)
            top.title("System Update")
            top.geometry("300x100")
            ctk.CTkLabel(top, text="Running pip install...").pack(pady=20)
            bar = ctk.CTkProgressBar(top)
            bar.pack(pady=10)
            bar.start()
            
            def on_done(success, msg):
                top.destroy()
                if success:
                    tkinter.messagebox.showinfo("Success", msg)
                else:
                    tkinter.messagebox.showerror("Error", msg)
            
            self.package_manager.update_system_libs(on_done)
