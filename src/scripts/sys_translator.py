"""
System Tool: Real-time Translator (Minimalist v3)
Features: Centered Layout, Opacity Slider, Icon UI, Auto-Clip, Middle Status, Click Feedback.
"""
import os
import sys
import time
import threading
import tkinter as tk
import customtkinter as ctk
from pathlib import Path

# Add src to path
try:
    current_dir = Path(__file__).parent
    src_dir = current_dir.parent
    sys.path.append(str(src_dir))
except: pass

from utils.gui_lib import BaseWindow
from core.logger import setup_logger

logger = setup_logger("sys_translator")

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.show)
        self.widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(self.tooltip, text=self.text, background="#2b2b2b", foreground="white", 
                        relief="solid", borderwidth=1, font=("Arial", 9))
        label.pack()

    def hide(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

class TranslatorApp(BaseWindow):
    def __init__(self):
        super().__init__(title="Translator", width=340, height=280)
        
        # State
        self.last_text = ""
        self.last_clip = ""
        self.debounce_timer = None
        self.is_pinned = False
        self.is_auto_clip = True
        self.opacity_slider_visible = False
        
        # GUI Setup
        self.create_widgets()
        
        # Async Init
        self.status_label.configure(text="Init...")
        threading.Thread(target=self.init_backend, daemon=True).start()
        
        # Clipboard Watcher
        self.start_clipboard_poll()
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        self.main_frame.pack_propagate(False)
        
        # --- Top Bar (3 Columns for Centering) ---
        top = ctk.CTkFrame(self.main_frame, fg_color="transparent", height=32)
        top.pack(fill="x", padx=5, pady=5)
        top.grid_columnconfigure(1, weight=1) # Center expands
        
        # Left: Auto + Paste
        left_frame = ctk.CTkFrame(top, fg_color="transparent")
        left_frame.grid(row=0, column=0, sticky="w")
        
        self.btn_auto = self.create_icon_btn(left_frame, "⚡", self.toggle_auto_clip, "Auto-Clip (On/Off)", fg_color="#F39C12")
        self.btn_auto.pack(side="left", padx=2)
        
        self.btn_paste = self.create_icon_btn(left_frame, "📋", self.paste_text, "Paste & Translate")
        self.btn_paste.pack(side="left", padx=2)

        # Center: Language
        center_frame = ctk.CTkFrame(top, fg_color="transparent")
        center_frame.grid(row=0, column=1) # Centered by weight
        
        self.lang_var = ctk.StringVar(value="Auto -> KO")
        self.opt_lang = ctk.CTkOptionMenu(center_frame, variable=self.lang_var, width=100, height=24,
                                        values=["Auto -> KO", "KO -> EN", "Auto -> FR", "FR -> KO"],
                                        command=self.on_lang_change, font=("", 11, "bold"),
                                        fg_color="#34495E", button_color="#2C3E50")
        self.opt_lang.pack()

        # Right: Opacity + Pin
        right_frame = ctk.CTkFrame(top, fg_color="transparent")
        right_frame.grid(row=0, column=2, sticky="e")
        
        self.btn_opacity = self.create_icon_btn(right_frame, "💧", self.toggle_opacity_slider, "Transparency")
        self.btn_opacity.pack(side="left", padx=2)
        
        self.btn_pin = self.create_icon_btn(right_frame, "📌", self.toggle_pin, "Always on Top")
        self.btn_pin.pack(side="left", padx=2)

        # --- Opacity Slider (Hidden by default) ---
        self.slider_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent", height=20)
        self.slider = ctk.CTkSlider(self.slider_frame, from_=0.3, to=1.0, number_of_steps=20, 
                                  command=self.change_opacity, width=200, height=16)
        self.slider.pack(pady=2)
        self.slider.set(1.0)

        # --- Content ---
        # Input (Distinct Style)
        self.input_text = ctk.CTkTextbox(self.main_frame, height=60, font=("", 12), 
                                       fg_color="#252525", border_width=1, border_color="#404040",
                                       text_color="white")
        self.input_text.pack(fill="x", padx=8, pady=(5, 2))
        self.input_text.bind("<KeyRelease>", self.on_key_release)
        
        # Status (Middle)
        self.status_label = ctk.CTkLabel(self.main_frame, text="Ready", text_color="gray", font=("", 10), height=14)
        self.status_label.pack(fill="x", padx=10, pady=0)

        # Output (Main)
        self.output_text = ctk.CTkTextbox(self.main_frame, height=100, fg_color="transparent", 
                                        font=("", 15, "bold"), text_color="#ECF0F1")
        self.output_text.pack(fill="both", expand=True, padx=8, pady=(0, 5))
        self.output_text.configure(state="disabled")
        # Bind click to copy
        self.output_text.bind("<Button-1>", self.on_output_click)

    def create_icon_btn(self, parent, text, command, tooltip_text, fg_color="transparent"):
        btn = ctk.CTkButton(parent, text=text, width=28, height=28, 
                          fg_color=fg_color, border_width=1 if fg_color=="transparent" else 0, 
                          border_color="gray", hover_color="#555555",
                          command=command)
        ToolTip(btn, tooltip_text)
        return btn

    def init_backend(self):
        try:
            from deep_translator import GoogleTranslator
            self.google = GoogleTranslator(source='auto', target='ko')
            self.update_status("Ready")
        except Exception as e:
            self.update_status(f"Init Error: {e}")

    def on_output_click(self, event):
        # 1. Disable Auto-Clip to prevent loop
        if self.is_auto_clip:
            self.toggle_auto_clip()
            
        # 2. Copy to Clipboard
        try:
            text = self.output_text.get("0.0", "end").strip()
            if text:
                self.clipboard_clear()
                self.clipboard_append(text)
                self.update() # Force clipboard update
                self.update_status("Copied! (Auto-Clip Paused)")
                
                # Visual Feedback (Flash)
                self.output_text.configure(fg_color="#2E4053")
                self.after(200, lambda: self.output_text.configure(fg_color="transparent"))
                
        except Exception as e:
            self.update_status(f"Copy Error: {e}")

    def toggle_opacity_slider(self):
        self.opacity_slider_visible = not self.opacity_slider_visible
        if self.opacity_slider_visible:
            # Show below top bar
            self.slider_frame.pack_forget()
            self.slider_frame.pack(before=self.input_text, fill="x", padx=10, pady=5)
            self.btn_opacity.configure(fg_color="#9B59B6", border_width=0)
        else:
            self.slider_frame.pack_forget()
            self.btn_opacity.configure(fg_color="transparent", border_width=1)

    def change_opacity(self, value):
        self.attributes('-alpha', value)

    def toggle_auto_clip(self):
        self.is_auto_clip = not self.is_auto_clip
        if self.is_auto_clip:
            self.btn_auto.configure(fg_color="#F39C12", border_width=0)
            self.update_status("Auto-Clip: ON")
        else:
            self.btn_auto.configure(fg_color="transparent", border_width=1)
            self.update_status("Auto-Clip: OFF")

    def toggle_pin(self):
        self.is_pinned = not self.is_pinned
        self.attributes('-topmost', self.is_pinned)
        if self.is_pinned:
            self.btn_pin.configure(fg_color="#3498DB", border_width=0)
        else:
            self.btn_pin.configure(fg_color="transparent", border_width=1)

    def start_clipboard_poll(self):
        self.check_clipboard()
        
    def check_clipboard(self):
        if self.is_auto_clip:
            try:
                text = self.clipboard_get()
                if text and text != self.last_clip:
                    self.last_clip = text
                    if len(text) < 5000: 
                        self.input_text.delete("0.0", "end")
                        self.input_text.insert("0.0", text)
                        self.trigger_translate()
            except: pass
        self.after(1000, self.check_clipboard)

    def on_key_release(self, event):
        if self.debounce_timer: self.debounce_timer.cancel()
        self.debounce_timer = threading.Timer(0.3, self.trigger_translate)
        self.debounce_timer.start()

    def trigger_translate(self):
        text = self.input_text.get("0.0", "end").strip()
        if not text or text == self.last_text: return
        
        self.last_text = text
        self.update_status("...")
        threading.Thread(target=self.run_translate, args=(text,), daemon=True).start()

    def run_translate(self, text):
        try:
            lang = self.lang_var.get()
            tgt = 'ko'
            if "-> EN" in lang: tgt = 'en'
            elif "-> FR" in lang: tgt = 'fr'
            
            self.google.target = tgt
            result = self.google.translate(text)
            self.after(0, lambda: self.show_result(result))
            
        except Exception as e:
            self.update_status(f"Error: {e}")

    def show_result(self, text):
        self.output_text.configure(state="normal")
        self.output_text.delete("0.0", "end")
        self.output_text.insert("0.0", text)
        self.output_text.configure(state="disabled")
        self.update_status("Done")

    def update_status(self, msg):
        self.after(0, lambda: self.status_label.configure(text=msg))

    def paste_text(self):
        try:
            text = self.clipboard_get()
            self.input_text.delete("0.0", "end")
            self.input_text.insert("0.0", text)
            self.trigger_translate()
        except: pass

    def on_lang_change(self, _):
        self.last_text = ""
        self.trigger_translate()

    def on_closing(self):
        self.destroy()

if __name__ == "__main__":
    app = TranslatorApp()
    app.mainloop()
