import pyautogui
import pygetwindow as gw
import time
import sys

def main():
    try:
        wins = gw.getWindowsWithTitle('SeedVR2 Upscaler')
        if not wins:
            print("Window not found")
            return
        
        win = wins[0]
        win.activate()
        time.sleep(1)
        
        # Take screenshot of the window area
        pyautogui.screenshot('docs/gui_screenshots/default/seedvr2_final.png', region=(win.left, win.top, win.width, win.height))
        print("Screenshot saved to docs/gui_screenshots/default/seedvr2_final.png")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
