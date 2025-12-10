import subprocess
import sys
from pathlib import Path

# Test the fixed is_tray_agent_running logic
def test_tray_status():
    print("Testing tray agent status detection...")
    
    # Check PID file
    pid_file = Path("logs/tray_agent.pid")
    if pid_file.exists():
        pid_str = pid_file.read_text(encoding="utf-8").strip()
        print(f"PID file exists: {pid_str}")
        
        # Check if PID is alive
        try:
            out = subprocess.check_output(f"tasklist /FI \"PID eq {pid_str}\"", shell=True).decode()
            alive = str(pid_str) in out
            print(f"PID {pid_str} alive: {alive}")
        except Exception as e:
            print(f"Error checking PID: {e}")
    else:
        print("PID file does not exist")
    
    # Check using PowerShell (improved version)
    try:
        cmd = "powershell -Command \"Get-CimInstance Win32_Process | Where-Object {$_.CommandLine -like '*tray_agent.py*'} | Select-Object -ExpandProperty ProcessId\""
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode().strip()
        print(f"PowerShell output: '{output}'")
        print(f"Output length: {len(output)}")
        
        # New validation logic
        is_running = bool(output and output.replace('\n', '').replace('\r', '').isdigit())
        print(f"Is running (new logic): {is_running}")
        
        # Old validation logic (for comparison)
        try:
            old_logic = bool(output and output[0].isdigit())
            print(f"Is running (old logic): {old_logic}")
        except IndexError:
            print(f"Old logic would fail with IndexError")
    except Exception as e:
        print(f"PowerShell check failed: {e}")

if __name__ == "__main__":
    test_tray_status()
