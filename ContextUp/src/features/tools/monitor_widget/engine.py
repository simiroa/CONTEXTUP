import warnings
# Suppress pynvml deprecation warning
warnings.filterwarnings("ignore", category=FutureWarning)

import sys
import time
import threading
import logging
import math
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable, Any
from collections import deque

# Add src to path if running directly
ROOT = Path(__file__).resolve().parent
while not (ROOT / 'src').exists() and ROOT.parent != ROOT:
    ROOT = ROOT.parent
if (ROOT / 'src').exists() and str(ROOT / 'src') not in sys.path:
    sys.path.insert(0, str(ROOT / 'src'))

import psutil

# Try to import pynvml for NVIDIA GPU support
try:
    import pynvml
    NVML_AVAILABLE = True
except ImportError:
    NVML_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class SystemStats:
    """System resource statistics snapshot."""
    cpu_percent: float = 0.0
    cpu_temp: float = 0.0
    ram_percent: float = 0.0
    ram_used_gb: float = 0.0
    ram_total_gb: float = 0.0
    gpu_load: float = 0.0
    gpu_temp: float = 0.0
    vram_percent: float = 0.0
    vram_used_gb: float = 0.0
    vram_total_gb: float = 0.0
    disk_read_speed: float = 0.0  # MB/s
    disk_write_speed: float = 0.0  # MB/s
    drives: List['DriveInfo'] = field(default_factory=list)
    net_recv_speed: float = 0.0  # MB/s
    net_sent_speed: float = 0.0  # MB/s
    server_points: List['ServerPoint'] = field(default_factory=list)
    gpu_name: str = ""
    nvidia_available: bool = False


@dataclass
class ProcessInfo:
    """Process resource information."""
    pid: int
    name: str
    cpu_percent: float = 0.0
    ram_mb: float = 0.0
    vram_mb: float = 0.0
    gpu_percent: float = 0.0
    disk_io_mb: float = 0.0  # Read + Write MB/s (snapshot, approximate)
    is_server: bool = False
    server_ports: List[int] = field(default_factory=list)
    is_leak_suspect: bool = False
    is_whitelisted: bool = False
    icon_path: Optional[str] = None


@dataclass
class DriveInfo:
    """Drive usage information."""
    mountpoint: str
    total_gb: float
    used_gb: float
    free_gb: float
    percent: float
    fstype: str
    read_speed: float = 0.0  # MB/s
    write_speed: float = 0.0  # MB/s
    io_valid: bool = False


@dataclass
class ServerPoint:
    """Server port metadata for UI display."""
    port: int
    name: str
    pid: int
    server_type: str = ""  # comfyui, docker, vite, webpack, flask, django, nodejs, etc.
    exe_path: str = ""     # Full executable path


class SystemMonitor:
    """Monitors CPU and RAM usage."""
    
    def __init__(self):
        self._cpu_percent = 0.0
        self._cpu_temp = 0.0
        # Initialize cpu_percent so first update() returns non-zero if busy
        psutil.cpu_percent(interval=None)
        
    def update(self) -> tuple:
        """Update and return (cpu_percent, cpu_temp, ram_percent, ram_used_gb, ram_total_gb)."""
        self._cpu_percent = psutil.cpu_percent(interval=None)
        
        # Try to get CPU temperature
        self._cpu_temp = 0.0
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    if entries:
                        self._cpu_temp = entries[0].current
                        break
        except (AttributeError, KeyError):
            pass
        
        mem = psutil.virtual_memory()
        ram_percent = mem.percent
        ram_used_gb = mem.used / (1024 ** 3)
        ram_total_gb = mem.total / (1024 ** 3)
        
        return self._cpu_percent, self._cpu_temp, ram_percent, ram_used_gb, ram_total_gb


class DiskMonitor:
    """Monitors Disk I/O."""
    def __init__(self):
        self._last_io = psutil.disk_io_counters()
        self._last_time = time.time()
        
    def update(self) -> tuple:
        """Return (read_mb_s, write_mb_s)."""
        now = time.time()
        current_io = psutil.disk_io_counters()
        
        if not current_io or not self._last_io:
            self._last_io = current_io
            self._last_time = now
            return 0.0, 0.0
            
        dt = now - self._last_time
        if dt < 0.1:  # Prevent division by zero or tiny intervals
            return 0.0, 0.0
            
        read_bytes = current_io.read_bytes - self._last_io.read_bytes
        write_bytes = current_io.write_bytes - self._last_io.write_bytes
        
        self._last_io = current_io
        self._last_time = now
        
        return read_bytes / (1024**2) / dt, write_bytes / (1024**2) / dt


class NetworkMonitor:
    """Monitors Network I/O."""
    def __init__(self):
        self._last_io = psutil.net_io_counters()
        self._last_time = time.time()
        
    def update(self) -> tuple:
        """Return (recv_mb_s, sent_mb_s)."""
        now = time.time()
        current_io = psutil.net_io_counters()
        
        if not current_io or not self._last_io:
            self._last_io = current_io
            self._last_time = now
            return 0.0, 0.0
            
        dt = now - self._last_time
        if dt < 0.1:
            return 0.0, 0.0
            
        recv_bytes = current_io.bytes_recv - self._last_io.bytes_recv
        sent_bytes = current_io.bytes_sent - self._last_io.bytes_sent
        
        self._last_io = current_io
        self._last_time = now
        
        return recv_bytes / (1024**2) / dt, sent_bytes / (1024**2) / dt


class DriveMonitor:
    """Monitors disk space usage and per-drive I/O."""
    def __init__(self):
        self._last_check = 0
        self._cache = []
        self._check_interval = 2.0 # Faster updates for I/O
        self._last_io = {}
        self._last_io_time = time.time()
        
    def update(self) -> List[DriveInfo]:
        """Update and return drive info list with I/O speeds."""
        now = time.time()
        if now - self._last_check < self._check_interval and self._cache:
            return self._cache
            
        self._last_check = now
        dt = now - self._last_io_time
        self._last_io_time = now
        
        # Get per-disk I/O counters
        current_io = {}
        try:
            io_counters = psutil.disk_io_counters(perdisk=True)
            if io_counters:
                current_io = io_counters
        except Exception:
            pass
            
        drives = []
        try:
            partitions = psutil.disk_partitions(all=False)
            for part in partitions:
                if 'cdrom' in part.opts or part.fstype == '':
                    continue
                    
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    
                    # Calculate I/O speed for this drive
                    read_speed = 0.0
                    write_speed = 0.0
                    io_valid = False
                    
                    # Find matching disk name (e.g., C: -> PhysicalDrive0 on Windows is tricky)
                    # On Windows, mountpoint is like 'C:\\', disk names in io_counters are like 'PhysicalDrive0'
                    # We'll try to match by drive token first, then by device name, then by single-disk fallback.
                    drive_letter = part.mountpoint[0].upper() if part.mountpoint else ''
                    
                    matched_disk = None
                    if current_io:
                        if drive_letter:
                            drive_token = f"{drive_letter}:"
                            for disk_name in current_io.keys():
                                disk_upper = disk_name.upper()
                                if disk_upper == drive_token or disk_upper.startswith(drive_token):
                                    matched_disk = disk_name
                                    break
                        if not matched_disk and part.device:
                            device_lower = part.device.lower()
                            for disk_name in current_io.keys():
                                if disk_name.lower() in device_lower:
                                    matched_disk = disk_name
                                    break
                        if not matched_disk and len(current_io) == 1:
                            matched_disk = next(iter(current_io))

                    if matched_disk:
                        io_valid = True
                        if matched_disk in self._last_io and dt > 0.1:
                            counters = current_io[matched_disk]
                            prev = self._last_io[matched_disk]
                            read_speed = (counters.read_bytes - prev.read_bytes) / (1024**2) / dt
                            write_speed = (counters.write_bytes - prev.write_bytes) / (1024**2) / dt
                    
                    drives.append(DriveInfo(
                        mountpoint=part.mountpoint,
                        total_gb=usage.total / (1024**3),
                        used_gb=usage.used / (1024**3),
                        free_gb=usage.free / (1024**3),
                        percent=usage.percent,
                        fstype=part.fstype,
                        read_speed=max(0, read_speed),
                        write_speed=max(0, write_speed),
                        io_valid=io_valid
                    ))
                except Exception:
                    pass
        except Exception:
            pass
            
        self._last_io = current_io
        if drives:  # Only update cache if we got valid data
            self._cache = drives
        return self._cache if self._cache else drives


class NvidiaMonitor:
    """Monitors NVIDIA GPU using NVML."""
    
    def __init__(self):
        self.available = False
        self.handle = None
        self.device_count = 0
        
        if NVML_AVAILABLE:
            try:
                pynvml.nvmlInit()
                self.device_count = pynvml.nvmlDeviceGetCount()
                if self.device_count > 0:
                    self.handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                    self.available = True
                    try:
                        self.name = pynvml.nvmlDeviceGetName(self.handle)
                        if isinstance(self.name, bytes):
                           self.name = self.name.decode("utf-8")
                    except:
                        self.name = "NVIDIA GPU"
            except Exception:
                self.available = False
                self.name = ""
    
    def update(self) -> tuple:
        """Update and return (gpu_load, gpu_temp, vram_percent, vram_used_gb, vram_total_gb)."""
        if not self.available or not self.handle:
            return 0.0, 0.0, 0.0, 0.0, 0.0
        
        try:
            # GPU utilization
            util = pynvml.nvmlDeviceGetUtilizationRates(self.handle)
            gpu_load = util.gpu
            
            # GPU temperature
            gpu_temp = pynvml.nvmlDeviceGetTemperature(self.handle, pynvml.NVML_TEMPERATURE_GPU)
            
            # VRAM usage
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(self.handle)
            vram_used_gb = mem_info.used / (1024 ** 3)
            vram_total_gb = mem_info.total / (1024 ** 3)
            vram_percent = (mem_info.used / mem_info.total) * 100 if mem_info.total > 0 else 0
            
            return gpu_load, gpu_temp, vram_percent, vram_used_gb, vram_total_gb
        except Exception:
            return 0.0, 0.0, 0.0, 0.0, 0.0
    
    def get_process_vram(self) -> Dict[int, float]:
        """Get VRAM usage per process (pid -> MB)."""
        result = {}
        if not self.available or not self.handle:
            return result
        
        try:
            # Compute processes (CUDA)
            compute_procs = pynvml.nvmlDeviceGetComputeRunningProcesses(self.handle)
            for proc in compute_procs:
                try:
                    mem = proc.usedGpuMemory
                    if mem is not None and mem > 0:
                        result[proc.pid] = mem / (1024 ** 2)
                except: pass
            
            # Graphics processes (Graphics API, Games, Video)
            try:
                gfx_procs = pynvml.nvmlDeviceGetGraphicsRunningProcesses(self.handle)
                for proc in gfx_procs:
                    mem = proc.usedGpuMemory
                    if mem is not None and mem > 0:
                        mem_mb = mem / (1024 ** 2)
                        if proc.pid in result:
                            result[proc.pid] += mem_mb
                        else:
                            result[proc.pid] = mem_mb
            except pynvml.NVMLError:
                pass
            except Exception:
                pass
                
        except pynvml.NVMLError:
            pass
        except Exception:
            pass

        return result

    def get_process_gpu_util(self) -> Dict[int, float]:
        """Get GPU utilization per process (pid -> %). Windows PDH method."""
        # Always use PDH on Windows - NVML doesn't provide per-process utilization
        if not sys.platform.startswith("win"):
            return {}
        return self._get_gpu_processes_from_pdh()
    
    def _get_gpu_processes_from_pdh(self) -> Dict[int, float]:
        """Get GPU utilization per process via Windows Performance Counters."""
        import subprocess
        import re
        
        result = {}
        try:
            # Query Windows PDH for GPU utilization per process
            # Simpler format: just output raw CSV
            cmd = '''powershell -Command "$c = Get-Counter '\\GPU Engine(*)\\Utilization Percentage' -ErrorAction SilentlyContinue; $c.CounterSamples | ForEach-Object { $_.InstanceName + ',' + $_.CookedValue }"'''
            output = subprocess.check_output(cmd, shell=True, timeout=8, stderr=subprocess.DEVNULL)
            lines = output.decode('utf-8', errors='ignore').strip().split('\n')
            
            # Parse output: pid_XXXXX_luid_...,0.123456
            for line in lines:
                line = line.strip()
                if not line or ',' not in line:
                    continue
                    
                match = re.search(r'pid_(\d+)_', line)
                if match:
                    pid = int(match.group(1))
                    try:
                        # Value is after the last comma
                        value = float(line.rsplit(',', 1)[-1])
                        if value > 0:  # Only include non-zero usage
                            if pid in result:
                                result[pid] = max(result[pid], value)
                            else:
                                result[pid] = value
                    except:
                        pass
        except Exception as e:
            pass
        
        return result
    
    def shutdown(self):
        """Clean up NVML."""
        if self.available:
            try:
                pynvml.nvmlShutdown()
            except Exception:
                pass


class LeakDetector:
    """Detects memory leak patterns in processes."""
    
    def __init__(self, history_minutes: int = 5, sample_interval_sec: int = 60):
        self.history_minutes = history_minutes
        self.sample_interval_sec = sample_interval_sec
        samples = (history_minutes * 60) / sample_interval_sec
        self.max_samples = max(1, math.ceil(samples))
        
        # pid -> deque of (timestamp, memory_mb)
        self._history: Dict[int, deque] = {}
        self._last_sample_time = 0
    
    def update(self, processes: List[ProcessInfo]) -> None:
        """Record memory samples for all processes."""
        now = time.time()
        
        # Only sample once per interval
        if now - self._last_sample_time < self.sample_interval_sec:
            return
        
        self._last_sample_time = now
        
        current_pids = set()
        for proc in processes:
            current_pids.add(proc.pid)
            
            if proc.pid not in self._history:
                self._history[proc.pid] = deque(maxlen=self.max_samples)
            
            self._history[proc.pid].append((now, proc.ram_mb))
        
        # Clean up dead processes
        dead_pids = set(self._history.keys()) - current_pids
        for pid in dead_pids:
            del self._history[pid]
    
    def is_leaking(self, pid: int) -> bool:
        """Check if a process shows memory leak pattern (linear growth for 5+ minutes)."""
        if pid not in self._history:
            return False
        
        history = self._history[pid]
        if len(history) < self.max_samples:
            return False
        
        # Check if memory is monotonically increasing
        samples = list(history)
        for i in range(1, len(samples)):
            if samples[i][1] <= samples[i-1][1]:
                return False
        
        # Additional check: significant growth (at least 10% increase over the period)
        if samples[0][1] > 0:
            growth_ratio = samples[-1][1] / samples[0][1]
            if growth_ratio < 1.1:  # Less than 10% growth
                return False
        
        return True


class ServerDetector:
    """Detects processes with listening network ports."""
    
    # Common server ports to highlight
    COMMON_SERVER_PORTS = {
        80, 443, 3000, 3001, 5000, 5001, 8000, 8080, 8081, 8188, 8888,
        11434,  # Ollama
        7860,   # Gradio
    }
    
    def __init__(self):
        self._port_cache: Dict[int, List[int]] = {}
        self._last_update = 0
        self._update_interval = 5  # seconds
    
    def update(self) -> None:
        """Update the port cache."""
        now = time.time()
        if now - self._last_update < self._update_interval:
            return
        
        self._last_update = now
        self._port_cache.clear()
        
        try:
            # kind='inet' is much faster than kindness='all'
            connections = psutil.net_connections(kind='inet4')
            for conn in connections:
                if conn.status == 'LISTEN' and conn.pid:
                    if conn.pid not in self._port_cache:
                        self._port_cache[conn.pid] = []
                    # Avoid duplicates
                    if conn.laddr.port not in self._port_cache[conn.pid]:
                        self._port_cache[conn.pid].append(conn.laddr.port)
            for ports in self._port_cache.values():
                ports.sort()
        except Exception as e:
            logger.error(f"Server detection error: {e}")
    
    def get_listening_ports(self, pid: int) -> List[int]:
        """Get listening ports for a process."""
        return self._port_cache.get(pid, [])
    
    def is_server(self, pid: int) -> bool:
        """Check if a process has listening ports."""
        return pid in self._port_cache and len(self._port_cache[pid]) > 0

    def get_server_points(self) -> List[ServerPoint]:
        """Returns list of server points with detected server types."""
        results = []
        for pid, ports in self._port_cache.items():
            try:
                proc = psutil.Process(pid)
                name = proc.name()
                
                # Filter out common Windows services and background apps
                blacklist = {
                    'svchost.exe', 'System', 'wininit.exe', 'services.exe', 'lsass.exe',
                    'spoolsv.exe', 'Memory Compression', 'Registry', 'smss.exe', 'csrss.exe',
                    'SearchIndexer.exe', 'SecurityHealthService.exe', 'fontdrvhost.exe',
                    'dasHost.exe', 'WmiPrvSE.exe', 'taskhostw.exe', 'explorer.exe',
                    'ApplicationFrameHost.exe', 'StartMenuExperienceHost.exe',
                    'ShellExperienceHost.exe', 'RuntimeBroker.exe', 'LockApp.exe',
                    'smartscreen.exe', 'MsMpEng.exe', 'NisSrv.exe', 'MpCmdRun.exe',
                    'discord.exe', 'steam.exe', 'steamwebhelper.exe', 'EpicGamesLauncher.exe',
                    'Spotify.exe', 'chrome.exe', 'msedge.exe', 'nvcontainer.exe',
                    'NVIDIA Web Helper.exe', 'nvsphelper64.exe', 'googledrivesync.exe',
                    'OneDrive.exe', 'Dropbox.exe', 'TextInputHost.exe', 'ctfmon.exe',
                    'PhoneExperienceHost.exe', 'Widgets.exe', 'logioptionsplus_agent.exe',
                    'gamingservices.exe', 'gamingservicesnet.exe', 'jhi_service.exe',
                    'ipoint.exe', 'itype.exe'
                }
                
                if name in blacklist or name.lower() in {x.lower() for x in blacklist}:
                    continue

                # Get executable path and cmdline for type detection
                try:
                    exe_path = proc.exe()
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    exe_path = ""
                
                try:
                    cmdline = ' '.join(proc.cmdline()).lower()
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    cmdline = ""
                
                # Detect server type
                server_type = self._detect_server_type(name, exe_path, cmdline, ports)
                
                # Filter internal/background ports for game engines
                if server_type == 'unity' and not (8080 <= port <= 8090):
                    # Unity Editor often opens many random high ports for internal comms
                    # Only keep standard web server ports if present, or just the first one found
                    pass
                
                for port in ports:
                    # Specific port filtering
                    if server_type == 'unity':
                         # Filter common internal Unity ports range
                        if 50000 <= port <= 60000:
                            continue
                            
                    results.append(ServerPoint(
                        port=port,
                        name=name,
                        pid=pid,
                        server_type=server_type,
                        exe_path=exe_path
                    ))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Sort by server type priority, then port
        type_priority = {
            'comfyui': 0, 'docker': 1, 'jupyter': 2, 'vite': 3, 'webpack': 4,
            'react': 5, 'vue': 6, 'angular': 7, 'flask': 8, 'django': 9,
            'nodejs': 10, 'unity': 11, 'unreal': 12, 'blender': 13, '': 99
        }
        results.sort(key=lambda sp: (type_priority.get(sp.server_type, 50), sp.port))
        
        # Deduplicate: For game engines/heavy apps, show only the first detected port 
        # to avoid cluttering the UI with multiple internal ports
        unique_results = []
        seen_types = set()
        
        for sp in results:
            if sp.server_type in ('unity', 'unreal', 'blender', 'comfyui'):
                # For these types, key by (type, pid) to allow multiple instances but single port per instance
                key = (sp.server_type, sp.pid)
                if key in seen_types:
                    continue
                seen_types.add(key)
            unique_results.append(sp)
            
        return unique_results
    
    def _detect_server_type(self, name: str, exe_path: str, cmdline: str, ports: List[int]) -> str:
        """Detect the type of server based on process info."""
        name_lower = name.lower()
        exe_lower = exe_path.lower()
        combined = f"{name_lower} {exe_lower} {cmdline}"
        
        # ComfyUI detection
        if 'comfyui' in combined or 'comfy' in combined:
            return 'comfyui'
        
        # Docker detection
        if 'docker' in name_lower or 'containerd' in name_lower:
            return 'docker'
        
        # Jupyter detection
        if 'jupyter' in combined:
            return 'jupyter'
        
        # Web dev servers
        if 'vite' in cmdline:
            return 'vite'
        if 'webpack' in cmdline or 'webpack-dev-server' in combined:
            return 'webpack'
        if 'react-scripts' in cmdline or 'create-react-app' in combined:
            return 'react'
        if 'vue-cli-service' in cmdline or '@vue' in cmdline:
            return 'vue'
        if 'ng serve' in cmdline or '@angular' in cmdline:
            return 'angular'
        
        # Python web frameworks
        if 'flask' in cmdline or 'werkzeug' in combined:
            return 'flask'
        if 'django' in cmdline or 'manage.py' in cmdline:
            return 'django'
        if 'uvicorn' in combined or 'fastapi' in combined:
            return 'fastapi'
        if 'streamlit' in combined:
            return 'streamlit'
        if 'gradio' in combined:
            return 'gradio'
        
        # Node.js detection
        if name_lower in ('node.exe', 'node') or 'nodejs' in exe_lower:
            return 'nodejs'
        
        # Game engines
        if 'unity' in name_lower or 'unity' in exe_lower:
            return 'unity'
        if 'unreal' in combined or 'ue4' in combined or 'ue5' in combined:
            return 'unreal'
        if 'blender' in name_lower:
            return 'blender'
        
        # Common ports heuristic
        if 3000 in ports:
            return 'nodejs'
        if 5000 in ports:
            return 'flask'
        if 8000 in ports:
            return 'django'
        if 8080 in ports:
            return 'webserver'
        if 8188 in ports:
            return 'comfyui'
        if 8888 in ports:
            return 'jupyter'
        
        return ""


class ProcessAnalyzer:
    """Analyzes process resource usage and categorizes them."""
    
    # Whitelist of system/important processes to protect
    WHITELIST = {
        'System', 'Registry', 'smss.exe', 'csrss.exe', 'wininit.exe',
        'services.exe', 'lsass.exe', 'svchost.exe', 'dwm.exe',
        'explorer.exe', 'SearchIndexer.exe', 'SecurityHealthService.exe',
    }
    
    def __init__(self, nvidia_monitor: NvidiaMonitor, leak_detector: LeakDetector, server_detector: ServerDetector):
        self.nvidia = nvidia_monitor
        self.leak_detector = leak_detector
        self.server_detector = server_detector
    
    def get_top_processes(self, mode: str = 'ram', top_n: int = 20) -> List[ProcessInfo]:
        """Fetch all processes in one pass."""
        all_processes = []
        vram_usage = self.nvidia.get_process_vram()
        gpu_util = self.nvidia.get_process_gpu_util()
        
        # Group psutil calls to be efficient
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
            try:
                info = proc.info
                pid = info['pid']
                if pid <= 4: continue # Skip System
                
                name = info['name']
                cpu_p = (info['cpu_percent'] or 0.0) / (psutil.cpu_count() or 1)
                ram_mb = (info['memory_info'].rss / (1024 ** 2)) if info['memory_info'] else 0.0
                vram_mb = vram_usage.get(pid, 0.0)
                gpu_percent = gpu_util.get(pid, 0.0)
                
                # Filter noise
                if cpu_p < 0.1 and ram_mb < 2.0 and vram_mb < 1.0 and gpu_percent < 0.5:
                    continue
                    
                all_processes.append(ProcessInfo(
                    pid=pid, name=name, cpu_percent=cpu_p, ram_mb=ram_mb, vram_mb=vram_mb,
                    gpu_percent=gpu_percent,
                    is_server=self.server_detector.is_server(pid),
                    server_ports=self.server_detector.get_listening_ports(pid),
                    is_leak_suspect=self.leak_detector.is_leaking(pid),
                    is_whitelisted=name in self.WHITELIST
                ))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return all_processes


class MonitorEngine:
    """Main monitoring engine that coordinates all monitors."""
    
    def __init__(self, update_interval: float = 2.0):
        self.update_interval = update_interval
        self._process_update_interval = 5.0  # Update process list less frequently
        self._last_process_update = 0
        
        self.system_monitor = SystemMonitor()
        self.nvidia_monitor = NvidiaMonitor()
        self.disk_monitor = DiskMonitor()
        self.net_monitor = NetworkMonitor()
        self.drive_monitor = DriveMonitor()
        self.leak_detector = LeakDetector()
        self.server_detector = ServerDetector()
        self.process_analyzer = ProcessAnalyzer(
            self.nvidia_monitor, self.leak_detector, self.server_detector
        )
        
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._callbacks: List[Callable[[SystemStats], None]] = []
        self._current_stats = SystemStats()
        self._cached_processes: Dict[str, List[ProcessInfo]] = {}  # Cache for process lists
    
    def add_callback(self, callback: Callable[[SystemStats], None]) -> None:
        """Add a callback to be called on each update."""
        self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[SystemStats], None]) -> None:
        """Remove a callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def get_stats(self) -> SystemStats:
        """Get current system stats."""
        return self._current_stats
    
    def get_top_processes(self, resource_type: str = 'ram', top_n: int = 5) -> List[ProcessInfo]:
        """Get top processes by resource type (uses cache for performance)."""
        cache_key = f"{resource_type}"
        return self._cached_processes.get(cache_key, [])[:top_n]
    
    def _update_loop(self) -> None:
        """Main update loop running in background thread."""
        while self._running:
            try:
                self._update_logic()
                
                # Notify callbacks
                for callback in self._callbacks:
                    try:
                        callback(self._current_stats)
                    except Exception:
                        pass
                
                time.sleep(self.update_interval)
            except Exception as e:
                print(f"Monitor update error: {e}")
                time.sleep(1.0)
    
    def start(self) -> None:
        """Start the monitoring engine."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._update_loop, daemon=True)
        self._thread.start()

    def _update_logic(self):
        """Update system and process data once."""
        self.server_detector.update()
        # Update system stats
        cpu_percent, cpu_temp, ram_percent, ram_used_gb, ram_total_gb = self.system_monitor.update()
        gpu_load, gpu_temp, vram_percent, vram_used_gb, vram_total_gb = self.nvidia_monitor.update()
        disk_read, disk_write = self.disk_monitor.update()
        net_recv, net_sent = self.net_monitor.update()
        drives = self.drive_monitor.update()
        
        self._current_stats = SystemStats(
            cpu_percent=cpu_percent,
            cpu_temp=cpu_temp,
            ram_percent=ram_percent,
            ram_used_gb=ram_used_gb,
            ram_total_gb=ram_total_gb,
            gpu_load=gpu_load,
            gpu_temp=gpu_temp,
            gpu_name=self.nvidia_monitor.name if self.nvidia_monitor.available else "",
            vram_percent=vram_percent,
            vram_used_gb=vram_used_gb,
            vram_total_gb=vram_total_gb,
            disk_read_speed=disk_read,
            disk_write_speed=disk_write,
            drives=drives,
            net_recv_speed=net_recv,
            net_sent_speed=net_sent,
            server_points=self.server_detector.get_server_points(),
            nvidia_available=self.nvidia_monitor.available,
        )
        
        # Update detectors and cache at a slower rate
        now = time.time()
        if now - self._last_process_update >= self._process_update_interval:
            self._last_process_update = now
            
            # Update cached process lists (Single pass fetch)
            try:
                all_procs = self.process_analyzer.get_top_processes('all')
                if not all_procs:
                   # Sometimes psutil returns nothing on first run or error; don't clear cache immediately if it was populated
                   if not self._cached_processes.get('cpu'):
                       pass # Allow empty if it's truly empty (e.g. strict filters)
                   else:
                       # Keep old data for one more cycle to prevent flickering
                       return

                self._cached_processes['cpu'] = sorted(all_procs, key=lambda x: x.cpu_percent, reverse=True)
                self._cached_processes['ram'] = sorted(all_procs, key=lambda x: x.ram_mb, reverse=True)
                
                # Filter for VRAM/GPU (only processes using VRAM)
                vram_procs = [p for p in all_procs if p.vram_mb > 0]
                self._cached_processes['vram'] = sorted(vram_procs, key=lambda x: x.vram_mb, reverse=True)
                gpu_procs = [p for p in all_procs if p.gpu_percent > 0 or p.vram_mb > 0]
                if any(p.gpu_percent > 0 for p in gpu_procs):
                    self._cached_processes['gpu'] = sorted(gpu_procs, key=lambda x: x.gpu_percent, reverse=True)
                else:
                    self._cached_processes['gpu'] = sorted(gpu_procs, key=lambda x: x.vram_mb, reverse=True)
                
                # Update leak detector
                self.leak_detector.update(self._cached_processes['ram'][:20])
            except Exception as e:
                logger.error(f"Process update logic error: {e}")
    
    def stop(self) -> None:
        """Stop the monitoring engine."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        
        self.nvidia_monitor.shutdown()
    
    def is_running(self) -> bool:
        """Check if the engine is running."""
        return self._running


# Quick test
if __name__ == "__main__":
    print("Testing Monitor Widget Engine...")
    
    engine = MonitorEngine(update_interval=1.0)
    
    def print_stats(stats: SystemStats):
        print(f"\nCPU: {stats.cpu_percent:.1f}% ({stats.cpu_temp:.0f}°C)")
        print(f"RAM: {stats.ram_percent:.1f}% ({stats.ram_used_gb:.1f}/{stats.ram_total_gb:.1f} GB)")
        if stats.nvidia_available:
            print(f"GPU: {stats.gpu_load:.1f}% ({stats.gpu_temp:.0f}°C)")
            print(f"VRAM: {stats.vram_percent:.1f}% ({stats.vram_used_gb:.1f}/{stats.vram_total_gb:.1f} GB)")
        else:
            print("GPU: NVIDIA not available")
        print(f"Disk: R {stats.disk_read_speed:.1f} / W {stats.disk_write_speed:.1f} MB/s")
        print(f"Net: ↓ {stats.net_recv_speed:.1f} / ↑ {stats.net_sent_speed:.1f} MB/s")
    
    engine.add_callback(print_stats)
    engine.start()
    
    try:
        print("\nTop 5 RAM processes:")
        for proc in engine.get_top_processes('ram', 5):
            flags = []
            if proc.is_leak_suspect:
                flags.append("💧")
            if proc.is_server:
                flags.append(f"🌐{proc.server_ports}")
            if proc.is_whitelisted:
                flags.append("🛡️")
            flag_str = " ".join(flags)
            print(f"  {proc.name}: {proc.ram_mb:.0f} MB {flag_str}")
        
        time.sleep(3)
    finally:
        engine.stop()
    
    print("\nEngine test complete.")
