import sys
import subprocess
import os

def check_torch():
    code = """
import torch
print(f"CUDA Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"Device: {torch.cuda.get_device_name(0)}")
    print(f"Version: {torch.__version__}")
"""
    return run_check("PyTorch", code)

def check_paddle():
    code = """
import paddle
print(f"Compiled with CUDA: {paddle.device.is_compiled_with_cuda()}")
print(f"Device: {paddle.device.get_device()}")
"""
    return run_check("PaddlePaddle (OCR)", code)

def check_onnx():
    code = """
import onnxruntime as ort
providers = ort.get_available_providers()
print(f"Providers: {providers}")
if 'CUDAExecutionProvider' in providers:
    print("CUDA Provider: YES")
else:
    print("CUDA Provider: NO")
"""
    return run_check("ONNX Runtime (RemBG)", code)

def run_check(name, code):
    print(f"[{name}] Checking...")
    try:
        # Use the current python executable
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            check=False
        )
        
        output = result.stdout.strip()
        error = result.stderr.strip()
        
        if result.returncode == 0:
            print("   PASS")
            # Indent output
            for line in output.split('\n'):
                if line: print(f"   {line}")
        else:
            print("   FAIL")
            print(f"   Error: {error}")
            for line in output.split('\n'):
                 if line: print(f"   {line}")
                 
    except Exception as e:
        print(f"   Execution Error: {e}")
    print("-" * 30)

def main():
    print("=== ContextUp GPU Health Check (Isolated) ===\n")
    check_torch()
    check_paddle()
    check_onnx()
    print("\n=== Check Complete ===")
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()
