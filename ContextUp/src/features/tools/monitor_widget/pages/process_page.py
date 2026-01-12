"""
ProcessListPage - Page showing top processes for CPU/RAM/GPU/VRAM.
"""
import platform
import psutil
import subprocess
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame

from ..theme import Theme
from ..engine import SystemStats
from ..components.base_page import BasePage
from ..components.rows import ProcessRow


def get_cpu_name():
    """Get CPU name using various methods."""
    # Try WMI on Windows
    if platform.system() == "Windows":
        try:
            result = subprocess.run(
                ['wmic', 'cpu', 'get', 'name'],
                capture_output=True, text=True, timeout=3, encoding='utf-8', errors='ignore'
            )
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                name = lines[1].strip()
                if name:
                    # Robust cleaning
                    name = name.replace('(R)', '').replace('(TM)', '')
                    name = name.replace('Processor', '').replace('CPU', '')
                    name = name.replace('12th Gen', '').replace('13th Gen', '').replace('14th Gen', '')
                    import re
                    name = re.sub(r'\s+', ' ', name) # Remove double spaces
                    return name.strip()
        except Exception:
            pass
    
    # Fallback to platform.processor()
    name = platform.processor()
    if name and "Family" not in name:
        return name
    
    return "CPU"


class ProcessListPage(BasePage):
    """Page with Top Processes for a specific resource type."""
    
    _cpu_name_cache = None  # Cache CPU name to avoid repeated WMI calls
    
    def __init__(self, title, res_type, engine, process_manager, parent=None):
        super().__init__(title, parent)
        self.res_type = res_type
        self.engine = engine
        self.process_manager = process_manager
        
        if self.res_type in ('cpu', 'vram'):
            # Match GpuPage header container exactly for CPU/VRAM
            self.header_container = QWidget()
            header_layout = QVBoxLayout(self.header_container)
            header_layout.setContentsMargins(4, 0, 4, 8)
            header_layout.setSpacing(4)
            
            self.lbl_h_name = QLabel(get_cpu_name() if self.res_type == 'cpu' else "NVIDIA GPU")
            self.lbl_h_name.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: 11px;")
            header_layout.addWidget(self.lbl_h_name)

            self.lbl_h_main = QLabel("0.0%")
            self.lbl_h_main.setStyleSheet(f"color: {Theme.TEXT_MAIN}; font-size: 15px; font-weight: bold;")
            header_layout.addWidget(self.lbl_h_main)
            
            self.lbl_h_stats = QLabel("0C/0T | 0.0GHz")
            self.lbl_h_stats.setStyleSheet(f"color: {Theme.TEXT_MAIN}; font-size: 12px;")
            header_layout.addWidget(self.lbl_h_stats)
            
            self.content_area.addWidget(self.header_container)

            # Separator matching GpuPage
            sep = QFrame()
            sep.setFrameShape(QFrame.HLine)
            sep.setFrameShadow(QFrame.Sunken)
            sep.setStyleSheet(f"background-color: {Theme.BG_SIDEBAR}; border: none; max-height: 1px; margin-top: 4px;")
            self.content_area.addWidget(sep)
            
            # Legacy mapping for updates
            self.lbl_v_name = self.lbl_h_name
            self.lbl_v_vram = self.lbl_h_main
            self.lbl_v_stats = self.lbl_h_stats
        else:
            self.lbl_detail = QLabel()
            self.lbl_detail.setFixedHeight(45)
            self.lbl_detail.setStyleSheet(f"color: {Theme.ACCENT}; font-size: 14px; font-weight: bold;")
            self.content_area.addWidget(self.lbl_detail)
        
        lbl_proc = QLabel("Top Processes")
        lbl_proc.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: 11px;")
        if self.res_type in ('cpu', 'vram'):
            lbl_proc.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: 11px; margin-top: 4px;")
        self.content_area.addWidget(lbl_proc)
        
        self.proc_container = QWidget()
        self.proc_layout = QVBoxLayout(self.proc_container)
        self.proc_layout.setContentsMargins(0, 0, 0, 0)
        self.proc_layout.setSpacing(4)
        self.content_area.addWidget(self.proc_container)
        
    def update_stats(self, stats: SystemStats):
        """Update detail label and process list."""
        self._update_detail_label(stats)
        self._update_process_list()
    
    def _update_detail_label(self, stats: SystemStats):
        """Update the detail label based on resource type."""
        if self.res_type == 'cpu' and hasattr(self, 'lbl_h_name'):
            # Get CPU name (cached)
            if ProcessListPage._cpu_name_cache is None:
                ProcessListPage._cpu_name_cache = get_cpu_name()
            
            name = ProcessListPage._cpu_name_cache
            self.lbl_h_name.setText(name)
            
            # Load
            self.lbl_h_main.setText(f"{stats.cpu_percent:.1f}%")
            
            # Core/Clock/Temp
            cores = psutil.cpu_count(logical=False) or 0
            threads = psutil.cpu_count(logical=True) or 0
            core_info = f"{cores}C/{threads}T" if cores else ""
            
            freq = psutil.cpu_freq()
            clock = f"{freq.current/1000:.1f}GHz" if freq else "0.0GHz"
            
            temp = f"{stats.cpu_temp:.0f}°C" if stats.cpu_temp > 0 else ""
            temp_color = Theme.RED if stats.cpu_temp > 75 else Theme.GREEN
            
            stats_text = f"{core_info} <span style='color:{Theme.TEXT_DIM};'>|</span> {clock}"
            if temp:
                stats_text += f" <span style='color:{Theme.TEXT_DIM};'>|</span> <span style='color:{temp_color}; font-weight:bold;'>{temp}</span>"
            
            self.lbl_h_stats.setText(stats_text)

        elif self.res_type == 'ram':
            self.lbl_detail.setText(
                f"<span style='color:{Theme.TEXT_DIM};'>Used:</span> "
                f"<span style='color:{Theme.ACCENT}; font-weight:bold;'>{stats.ram_used_gb:.1f}GB</span> "
                f"<span style='color:{Theme.TEXT_DIM};'>/ {stats.ram_total_gb:.1f}GB</span>"
            )
        elif self.res_type == 'gpu':
            name = stats.gpu_name or "GPU"
            if len(name) > 25:
                name = name[:22] + ".."
            temp = f"{stats.gpu_temp:.0f}°C" if stats.gpu_temp > 0 else ""
            load = f"{stats.gpu_load:.0f}%" if stats.gpu_load > 0 else ""
            temp_color = Theme.RED if stats.gpu_temp > 80 else Theme.GREEN
            self.lbl_detail.setText(f"""
                <div style='color:{Theme.TEXT_DIM}; font-size:10px;'>{name}</div>
                <div style='margin-top:2px;'>
                    <span style='color:{Theme.ACCENT}; font-weight:bold; font-size:13px;'>{load}</span>
                    {f"<span style='color:{Theme.TEXT_DIM}; margin:0 4px;'>|</span><span style='color:{temp_color}; font-weight:bold; font-size:13px;'>{temp}</span>" if temp else ""}
                </div>
            """)
        elif self.res_type == 'vram' and hasattr(self, 'lbl_v_name'):
            name = stats.gpu_name or "NVIDIA GPU"
            self.lbl_v_name.setText(name)
            
            vram_percent = (stats.vram_used_gb / stats.vram_total_gb * 100) if stats.vram_total_gb > 0 else 0
            vram_color = Theme.get_color(vram_percent)
            self.lbl_v_vram.setText(f"""
                <span style='color:{vram_color};'>{stats.vram_used_gb:.1f}GB</span> 
                <span style='color:{Theme.TEXT_DIM};'>/ {stats.vram_total_gb:.1f}GB</span>
            """)
            
            temp = f"{stats.gpu_temp:.0f}°C"
            temp_color = Theme.RED if stats.gpu_temp > 80 else Theme.GREEN
            clock = f"{stats.gpu_clock_mhz/1000:.1f}GHz" if stats.gpu_clock_mhz > 0 else "0.0GHz"
            power = f"{stats.gpu_power_w:.0f}W" if stats.gpu_power_w > 0 else "0W"
            
            self.lbl_v_stats.setText(f"""
                {clock} <span style='color:{Theme.TEXT_DIM};'>|</span> 
                {power} <span style='color:{Theme.TEXT_DIM};'>|</span> 
                <span style='color:{temp_color}; font-weight:bold;'>{temp}</span>
            """)
    
    def _update_process_list(self):
        """Update the process list."""
        count = 5 if self.res_type in ('cpu', 'vram') else 6
        procs = self.engine.get_top_processes(self.res_type, count)
        
        # Anti-flicker: keep old list if no data
        if not procs:
            if self.proc_layout.count() > 0:
                return
            lbl = QLabel("No active processes detected." if self.res_type in ('cpu', 'ram') else "No GPU processes")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: 10px;")
            self.proc_layout.addWidget(lbl)
            return

        while self.proc_layout.count():
            item = self.proc_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        for p in procs:
            usage_str = ""
            color = Theme.TEXT_MAIN
            if self.res_type == 'cpu':
                usage_str = f"{p.cpu_percent:.1f}%"
                color = Theme.get_color(p.cpu_percent)
            elif self.res_type == 'ram':
                usage_str = f"{p.ram_mb:.0f} MB"
            elif self.res_type == 'gpu':
                if p.gpu_percent > 0:
                    usage_str = f"{p.gpu_percent:.0f}%"
                    color = Theme.get_color(p.gpu_percent)
                else:
                    usage_str = f"{p.vram_mb:.0f} MB"
            elif self.res_type == 'vram':
                if p.vram_mb > 1: # Hide if almost zero
                    usage_str = f"{p.vram_mb:.0f} MB"
                else:
                    usage_str = ""
            
            row = ProcessRow(p.name, p.pid, usage_str, color, self.process_manager)
            self.proc_layout.addWidget(row)
