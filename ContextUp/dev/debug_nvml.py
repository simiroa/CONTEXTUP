import pynvml
import sys

try:
    pynvml.nvmlInit()
    print(f"Driver Version: {pynvml.nvmlSystemGetDriverVersion()}")
    device_count = pynvml.nvmlDeviceGetCount()
    print(f"Device Count: {device_count}")
    
    if device_count > 0:
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        name = pynvml.nvmlDeviceGetName(handle)
        print(f"Device 0: {name}")
        
        print("\n--- Compute Processes ---")
        try:
            procs = pynvml.nvmlDeviceGetComputeRunningProcesses(handle)
            print(f"Count: {len(procs)}")
            for p in procs:
                print(f"PID: {p.pid}, Mem: {p.usedGpuMemory}")
        except Exception as e:
            print(f"Error: {e}")
            
        print("\n--- Graphics Processes ---")
        try:
            procs = pynvml.nvmlDeviceGetGraphicsRunningProcesses(handle)
            print(f"Count: {len(procs)}")
            for p in procs:
                print(f"PID: {p.pid}, Mem: {p.usedGpuMemory}")
        except Exception as e:
            print(f"Error: {e}")

    pynvml.nvmlShutdown()
    
except Exception as e:
    print(f"NVML Init Failed: {e}")
