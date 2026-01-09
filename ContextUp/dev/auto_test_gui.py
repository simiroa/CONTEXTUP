import sys
import os
import threading
import time
from pathlib import Path
import tkinter as tk
import customtkinter as ctk

# Setup Paths
BASE = Path("c:/Users/HG/Documents/HG_context_v2/ContextUp")
sys.path.append(str(BASE / "src"))

# Properly import target modules
# We need to use import 'features.image.convert_gui' but since 'src' is in path, it should be just 'features...'
# However, the structure of convert_gui.py has a 'main()' function returning the class.
# We need to adapt the import.

# For Image Converter, the class is returned by main().
import features.image.convert_gui as img_gui_mod

from features.video.convert_gui import VideoConvertGUI
from features.video.audio_gui import VideoAudioGUI

TEST_DATA = BASE / "dev/test_data"

class AutoTester:
    def __init__(self, target_type):
        self.target_type = target_type
        self.app = None
        self.start_time = time.time()
        
    def run(self):
        print(f"--- Starting Auto Test: {self.target_type} ---")
        
        if self.target_type == "image":
            files = list((TEST_DATA / "image").glob("*.jpg"))
            if not files:
                print("No test images found")
                sys.exit(1)
            
            # Setup GUI
            # Note: The GUI normally takes a list of files.
            print(f"Loading {len(files)} images...")
            ImageConverterGUI = img_gui_mod.main()
            self.app = ImageConverterGUI(files)
            
            # Auto-click Start
            self.app.after(1000, self._start_image_conversion)
            self.app.after(2000, self._monitor_image_progress)
            
        elif self.target_type == "video":
            files = list((TEST_DATA / "video").glob("*.mp4"))
            if not files:
                print("No test videos found") 
                sys.exit(1)
                
            print(f"Loading {len(files)} videos...")
            self.app = VideoConvertGUI(files[0].parent, selection=files)
            
            self.app.after(1000, self._start_video_conversion)
            self.app.after(2000, self._monitor_video_progress)

        elif self.target_type == "audio":
            files = list((TEST_DATA / "audio").glob("*.wav"))
            if not files:
                print("No test audio found")
                sys.exit(1)
            
            print(f"Loading {len(files)} audio files...")
            self.app = VideoAudioGUI(files[0].parent, selection=files)
            
            self.app.after(1000, self._start_audio_conversion)
            self.app.after(2000, self._monitor_audio_progress)

        self.app.mainloop()

    # --- IMAGE ---
    def _start_image_conversion(self):
        print("Clicking Start Conversion...")
        # Mock settings if needed
        self.app.run_conversion() 

    def _monitor_image_progress(self):
        status = self.app.lbl_status.cget("text")
        print(f"Status: {status}")
        
        if "Complete" in status:
            print("✅ Image Conversion Complete")
            self.app.destroy()
        else:
            self.app.after(500, self._monitor_image_progress)

    # --- VIDEO ---
    def _start_video_conversion(self):
        print("Clicking Start Video Conversion...")
        self.app.start_convert()

    def _monitor_video_progress(self):
        # Video GUI has a more complex status update
        # We also check the progress bar
        val = self.app.progress.get()
        status = self.app.lbl_status.cget("text")
        print(f"Progress: {val:.2f}, Status: {status}")
        
        if "Complete" in status or (val >= 0.99 and "Converted" in status):
            print("✅ Video Conversion Complete")
            self.app.destroy()
        else:
            self.app.after(1000, self._monitor_video_progress)

    # --- AUDIO ---
    def _start_audio_conversion(self):
        print("Clicking Audio Action...")
        # Defaults to Extract MP3.
        self.app.run_current_action()

    def _monitor_audio_progress(self):
        val = self.app.progress.get()
        status = self.app.lbl_status.cget("text")
        print(f"Progress: {val:.2f}, Status: {status}")
        
        if status == "Complete":
            print("✅ Audio Conversion Complete")
            self.app.destroy()
        else:
            self.app.after(500, self._monitor_audio_progress)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python auto_test_gui.py [image|video|audio]")
        sys.exit(1)
        
    tester = AutoTester(sys.argv[1])
    tester.run()
