"""
Monitor Widget Process Manager - Process Control Module
Provides Kill, Suspend, Resume, and Boost functionality for processes.
"""

import sys
import ctypes
from pathlib import Path
from typing import List, Set

# Add src to path if running directly
ROOT = Path(__file__).resolve().parent
while not (ROOT / 'src').exists() and ROOT.parent != ROOT:
    ROOT = ROOT.parent
if (ROOT / 'src').exists() and str(ROOT / 'src') not in sys.path:
    sys.path.insert(0, str(ROOT / 'src'))

import psutil


# Windows API constants for process suspension
PROCESS_SUSPEND_RESUME = 0x0800
PROCESS_TERMINATE = 0x0001


class ProcessManager:
    """Manages process control operations: Kill, Suspend, Resume, Boost."""
    
    # Whitelist of system processes that should never be killed/suspended
    PROTECTED_PROCESSES = {
        'System', 'Registry', 'smss.exe', 'csrss.exe', 'wininit.exe',
        'services.exe', 'lsass.exe', 'svchost.exe', 'dwm.exe',
        'explorer.exe', 'SearchIndexer.exe', 'SecurityHealthService.exe',
        'MsMpEng.exe', 'winlogon.exe', 'fontdrvhost.exe', 'sihost.exe',
        'taskhostw.exe', 'ctfmon.exe', 'RuntimeBroker.exe',
        'python.exe', 'pythonw.exe',  # Don't kill ourselves
    }
    
    def __init__(self):
        self._suspended_pids: Set[int] = set()
        
        # Load ntdll for process suspension
        try:
            self._ntdll = ctypes.WinDLL('ntdll.dll')
            self._NtSuspendProcess = self._ntdll.NtSuspendProcess
            self._NtResumeProcess = self._ntdll.NtResumeProcess
        except Exception:
            self._ntdll = None
    
    def is_protected(self, name: str) -> bool:
        """Check if a process is protected from control operations."""
        return name in self.PROTECTED_PROCESSES
    
    def kill_process(self, pid: int) -> bool:
        """
        Kill a process by PID.
        Returns True if successful, False otherwise.
        """
        try:
            proc = psutil.Process(pid)
            
            # Check if protected
            if self.is_protected(proc.name()):
                return False
            
            proc.kill()
            
            # Remove from suspended list if it was there
            self._suspended_pids.discard(pid)
            
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return False
    
    def suspend_process(self, pid: int) -> bool:
        """
        Suspend a process by PID using NtSuspendProcess.
        Returns True if successful, False otherwise.
        """
        if not self._ntdll:
            return False
        
        try:
            proc = psutil.Process(pid)
            
            # Check if protected
            if self.is_protected(proc.name()):
                return False
            
            # Get process handle
            kernel32 = ctypes.WinDLL('kernel32.dll')
            handle = kernel32.OpenProcess(PROCESS_SUSPEND_RESUME, False, pid)
            
            if handle:
                result = self._NtSuspendProcess(handle)
                kernel32.CloseHandle(handle)
                
                if result == 0:  # STATUS_SUCCESS
                    self._suspended_pids.add(pid)
                    return True
            
            return False
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
    
    def resume_process(self, pid: int) -> bool:
        """
        Resume a suspended process by PID using NtResumeProcess.
        Returns True if successful, False otherwise.
        """
        if not self._ntdll:
            return False
        
        try:
            kernel32 = ctypes.WinDLL('kernel32.dll')
            handle = kernel32.OpenProcess(PROCESS_SUSPEND_RESUME, False, pid)
            
            if handle:
                result = self._NtResumeProcess(handle)
                kernel32.CloseHandle(handle)
                
                if result == 0:  # STATUS_SUCCESS
                    self._suspended_pids.discard(pid)
                    return True
            
            return False
        except Exception:
            return False
    
    def is_suspended(self, pid: int) -> bool:
        """Check if a process is currently suspended by us."""
        return pid in self._suspended_pids
    
    def boost_process(self, target_pid: int, exclude_pids: List[int] = None) -> List[int]:
        """
        Boost a target process by suspending background processes.
        Returns list of PIDs that were suspended.
        
        Args:
            target_pid: The PID of the process to boost (will not be suspended)
            exclude_pids: Additional PIDs to exclude from suspension
        """
        excluded = set([target_pid])
        if exclude_pids:
            excluded.update(exclude_pids)
        
        # Add current process
        excluded.add(psutil.Process().pid)
        
        suspended = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
            try:
                pid = proc.info['pid']
                name = proc.info['name']
                
                # Skip excluded and protected processes
                if pid in excluded or self.is_protected(name):
                    continue
                
                # Skip processes with low CPU usage (they're not competing for resources)
                if proc.info['cpu_percent'] is not None and proc.info['cpu_percent'] < 1.0:
                    continue
                
                # Suspend the process
                if self.suspend_process(pid):
                    suspended.append(pid)
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        return suspended
    
    def resume_all(self) -> int:
        """
        Resume all processes that were suspended by us.
        Returns count of processes resumed.
        """
        count = 0
        for pid in list(self._suspended_pids):
            if self.resume_process(pid):
                count += 1
        return count
    
    def get_suspended_count(self) -> int:
        """Get count of currently suspended processes."""
        return len(self._suspended_pids)


# Quick test
if __name__ == "__main__":
    print("Testing ProcessManager...")
    
    pm = ProcessManager()
    
    print(f"\nProtected process check:")
    print(f"  explorer.exe: {pm.is_protected('explorer.exe')}")
    print(f"  notepad.exe: {pm.is_protected('notepad.exe')}")
    
    print(f"\nCurrently suspended: {pm.get_suspended_count()}")
    
    print("\nProcessManager test complete.")
