import subprocess
import sys

def install():
    print("Installing rife-ncnn-vulkan-python...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "rife-ncnn-vulkan-python"])
        print("Success!")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install: {e}")

if __name__ == "__main__":
    install()
