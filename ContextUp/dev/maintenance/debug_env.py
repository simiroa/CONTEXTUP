try:
    import sys
    print(f"Python: {sys.executable}")
    import psutil
    print(f"psutil: {psutil.__version__}")
    import customtkinter
    print(f"customtkinter: {customtkinter.__version__}")
    import PIL
    print(f"PIL: {PIL.__version__}")
    print("SUCCESS")
except Exception as e:
    print(f"FAIL: {e}")
    sys.exit(1)
