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
    print("\n=== Check Complete ===")
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()
