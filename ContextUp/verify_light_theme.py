import customtkinter as ctk
import sys
from pathlib import Path
import json
import time

# Add src to path
src_dir = Path(__file__).parent / "src"
sys.path.append(str(src_dir))

from utils.gui_lib import setup_theme, BaseWindow

class ThemeTestWindow(BaseWindow):
    def __init__(self):
        super().__init__(title="Theme Test", width=400, height=400)
        
        self.add_header("Theme Switching Test")
        
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkButton(frame, text="Primary Button (Themed)").pack(pady=10)
        ctk.CTkCheckBox(frame, text="Checkbox (Themed)").pack(pady=10)
        ctk.CTkOptionMenu(frame, values=["Option 1", "Option 2"]).pack(pady=10)
        ctk.CTkSlider(frame).pack(pady=10)
        
        self.btn_toggle = ctk.CTkButton(self.main_frame, text="Toggle Theme (Mode)", command=self.toggle_mode)
        self.btn_toggle.pack(pady=20)
        
        self.mode = "dark"
        
    def toggle_mode(self):
        if self.mode == "dark":
            self.mode = "light"
            ctk.set_appearance_mode("Light")
        else:
            self.mode = "dark"
            ctk.set_appearance_mode("Dark")
        print(f"Switched to {self.mode} mode")

if __name__ == "__main__":
    app = ThemeTestWindow()
    # No mainloop here, we just want to see if it works in a test script or provide it for the user.
    # Actually, I'll run it with a timeout to verify no crash and maybe a screenshot.
    app.after(1000, lambda: app.toggle_mode())
    app.after(2000, lambda: app.destroy())
    app.mainloop()
