"""
NetPage - Page showing network I/O and utilities.
"""
import json
import re
import ssl
import socket
import subprocess
import threading
import urllib.request
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import qtawesome as qta
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                QPushButton, QFrame, QProgressBar)

from ..theme import Theme
from ..engine import SystemStats
from ..components.base_page import BasePage


class SpeedTestSignals(QObject):
    """Signals for real-time speed test updates."""
    progress = Signal(str, int, float, float)  # phase, percent, current_speed_mbps, max_speed_mbps
    finished = Signal(dict)  # results dict


class NetPage(BasePage):
    """Network page with speed display, IP info, speed test, and internet toggle."""
    
    def __init__(self, title, engine, parent=None):
        super().__init__(title, parent)
        self.engine = engine
        self._testing = False
        self._results = {}
        
        # Speed test signals
        self._test_signals = SpeedTestSignals()
        self._test_signals.progress.connect(self._on_test_progress)
        self._test_signals.finished.connect(self._on_test_done)
        
        # Speed Display with icons
        speed_row = QHBoxLayout()
        speed_row.setSpacing(16)
        
        # Download
        down_container = QHBoxLayout()
        down_container.setSpacing(4)
        lbl_down_icon = QLabel()
        lbl_down_icon.setPixmap(qta.icon('fa5s.arrow-down', color=Theme.GREEN).pixmap(16, 16))
        self.lbl_down = QLabel("0.0 MB/s")
        self.lbl_down.setStyleSheet(f"color: {Theme.GREEN}; font-size: 16px; font-weight: bold;")
        down_container.addWidget(lbl_down_icon)
        down_container.addWidget(self.lbl_down)
        down_container.addStretch()
        
        # Upload
        up_container = QHBoxLayout()
        up_container.setSpacing(4)
        lbl_up_icon = QLabel()
        lbl_up_icon.setPixmap(qta.icon('fa5s.arrow-up', color=Theme.BLUE).pixmap(16, 16))
        self.lbl_up = QLabel("0.0 MB/s")
        self.lbl_up.setStyleSheet(f"color: {Theme.BLUE}; font-size: 16px; font-weight: bold;")
        up_container.addWidget(lbl_up_icon)
        up_container.addWidget(self.lbl_up)
        up_container.addStretch()
        
        speed_row.addLayout(down_container)
        speed_row.addLayout(up_container)
        self.content_area.addLayout(speed_row)
        
        # IP & ISP Display Section
        self.ip_panel = QFrame()
        self.ip_panel.setStyleSheet(f"background: {Theme.BG_SECTION}; border-radius: 6px;")
        ip_layout = QVBoxLayout(self.ip_panel)
        ip_layout.setContentsMargins(8, 8, 8, 8)
        ip_layout.setSpacing(2)
        
        self.lbl_local_ip = QLabel("Local IP: Loading...")
        self.lbl_local_ip.setStyleSheet(f"color: {Theme.TEXT_MAIN}; font-size: 11px;")
        self.lbl_public_ip = QLabel("Public IP: Loading...")
        self.lbl_public_ip.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: 11px;")
        self.lbl_isp = QLabel("ISP: -")
        self.lbl_isp.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: 10px;")
        
        ip_layout.addWidget(self.lbl_local_ip)
        ip_layout.addWidget(self.lbl_public_ip)
        ip_layout.addWidget(self.lbl_isp)
        self.content_area.addWidget(self.ip_panel)
        
        # Speed Test Progress Section (hidden initially)
        self.test_panel = QFrame()
        self.test_panel.setStyleSheet(f"background: {Theme.BG_SECTION}; border-radius: 6px;")
        self.test_panel.setVisible(False)
        test_layout = QVBoxLayout(self.test_panel)
        test_layout.setContentsMargins(8, 8, 8, 8)
        test_layout.setSpacing(4)
        
        # Phase label
        self.lbl_phase = QLabel("⏳ Preparing...")
        self.lbl_phase.setStyleSheet(f"color: {Theme.TEXT_MAIN}; font-size: 11px;")
        test_layout.addWidget(self.lbl_phase)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(14)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background: {Theme.BG_SIDEBAR};
                border-radius: 7px;
                text-align: center;
                color: {Theme.TEXT_MAIN};
                font-size: 9px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Theme.ACCENT}, stop:1 {Theme.GREEN});
                border-radius: 7px;
            }}
        """)
        test_layout.addWidget(self.progress_bar)
        
        # Real-time speed display
        self.lbl_realtime_speed = QLabel("")
        self.lbl_realtime_speed.setStyleSheet(f"color: {Theme.GREEN}; font-size: 13px; font-weight: bold;")
        self.lbl_realtime_speed.setAlignment(Qt.AlignCenter)
        test_layout.addWidget(self.lbl_realtime_speed)
        
        self.content_area.addWidget(self.test_panel)
        
        # Results Panel (hidden initially)
        self.results_panel = QFrame()
        self.results_panel.setStyleSheet(f"background: {Theme.BG_SECTION}; border-radius: 6px;")
        self.results_panel.setVisible(False)
        results_layout = QVBoxLayout(self.results_panel)
        results_layout.setContentsMargins(8, 6, 8, 6)
        results_layout.setSpacing(3)
        
        # Results header
        results_header = QLabel("📊 Speed Test Results")
        results_header.setStyleSheet(f"color: {Theme.ACCENT}; font-size: 11px; font-weight: bold;")
        results_layout.addWidget(results_header)
        
        # Ping row
        ping_row = QHBoxLayout()
        ping_row.setSpacing(8)
        self.lbl_ping = QLabel("Ping: - ms")
        self.lbl_ping.setStyleSheet(f"color: {Theme.TEXT_MAIN}; font-size: 11px;")
        self.lbl_jitter = QLabel("Jitter: - ms")
        self.lbl_jitter.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: 11px;")
        ping_row.addWidget(self.lbl_ping)
        ping_row.addWidget(self.lbl_jitter)
        ping_row.addStretch()
        results_layout.addLayout(ping_row)
        
        # Speed row
        speed_row_result = QHBoxLayout()
        speed_row_result.setSpacing(8)
        self.lbl_down_result = QLabel("↓ - Mbps")
        self.lbl_down_result.setStyleSheet(f"color: {Theme.GREEN}; font-size: 12px; font-weight: bold;")
        self.lbl_up_result = QLabel("↑ - Mbps")
        self.lbl_up_result.setStyleSheet(f"color: {Theme.BLUE}; font-size: 12px; font-weight: bold;")
        speed_row_result.addWidget(self.lbl_down_result)
        speed_row_result.addWidget(self.lbl_up_result)
        speed_row_result.addStretch()
        results_layout.addLayout(speed_row_result)
        
        self.content_area.addWidget(self.results_panel)
        
        # Action Row
        action_row = QHBoxLayout()
        action_row.setSpacing(8)
        
        # Speed Test Button
        self.btn_test = QPushButton(" Speed Test")
        self.btn_test.setIcon(qta.icon('fa5s.tachometer-alt', color=Theme.TEXT_MAIN))
        self.btn_test.setCursor(Qt.PointingHandCursor)
        self.btn_test.setFixedHeight(28)
        self.btn_test.setStyleSheet(f"""
            QPushButton {{ background: {Theme.BG_SECTION}; color: {Theme.TEXT_MAIN}; border-radius: 4px; border: none; font-size: 11px; }}
            QPushButton:hover {{ background: {Theme.ACCENT}; color: white; }}
        """)
        self.btn_test.clicked.connect(self._run_speed_test)
        
        # Network Settings Button
        self.btn_settings = QPushButton()
        self.btn_settings.setIcon(qta.icon('fa5s.cog', color=Theme.TEXT_MAIN))
        self.btn_settings.setFixedSize(28, 28)
        self.btn_settings.setCursor(Qt.PointingHandCursor)
        self.btn_settings.setToolTip("Open Network Settings")
        self.btn_settings.setStyleSheet(f"""
            QPushButton {{ background: {Theme.BG_SECTION}; border-radius: 4px; border: none; }}
            QPushButton:hover {{ background: {Theme.ACCENT}; }}
        """)
        self.btn_settings.clicked.connect(self._open_network_settings)
        
        action_row.addWidget(self.btn_test, 1)
        action_row.addWidget(self.btn_settings)
        self.content_area.addLayout(action_row)
        
        self.lbl_result = QLabel("")
        self.lbl_result.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: 10px; margin-top: 3px;")
        self.lbl_result.setWordWrap(True)
        self.content_area.addWidget(self.lbl_result)
        
        # Delayed IP fetch
        QTimer.singleShot(500, self._fetch_ips)

    def _fetch_ips(self):
        """Fetch local IP, public IP, and ISP info."""
        def fetch():
            local_ip = "Unknown"
            public_ip = "Offline"
            isp_info = ""
            
            # Local IP
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.settimeout(2.0)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                s.close()
            except Exception:
                try:
                    local_ip = socket.gethostbyname(socket.gethostname())
                except Exception:
                    pass
            
            # Public IP + ISP (using ip-api.com for both)
            try:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                
                req = urllib.request.Request(
                    "http://ip-api.com/json/?fields=query,isp,org",
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                with urllib.request.urlopen(req, timeout=5.0) as res:
                    data = json.loads(res.read().decode('utf-8'))
                    public_ip = data.get('query', 'Unknown')
                    isp = data.get('isp', '')
                    org = data.get('org', '')
                    isp_info = isp if isp else org
            except Exception:
                # Fallback to simple IP services
                for service_url in ["https://api.ipify.org", "https://icanhazip.com"]:
                    try:
                        req = urllib.request.Request(service_url, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(req, timeout=5.0, context=ctx) as res:
                            public_ip = res.read().decode('utf-8').strip()
                            break
                    except Exception:
                        continue
            
            self._test_signals.finished.emit({
                '__type': 'ip_update',
                'local_ip': local_ip,
                'public_ip': public_ip,
                'isp': isp_info
            })
        
        threading.Thread(target=fetch, daemon=True).start()

    def _on_ips_fetched(self, local, public, isp=""):
        self.lbl_local_ip.setText(f"Local IP: {local}")
        self.lbl_public_ip.setText(f"Public IP: {public}")
        if isp:
            self.lbl_isp.setText(f"ISP: {isp}")
        else:
            self.lbl_isp.setVisible(False)

    def _get_network_adapters(self):
        """Get list of physical network adapters."""
        try:
            cmd = 'powershell -NoProfile -Command "Get-NetAdapter -Physical | Select-Object -ExpandProperty Name | ConvertTo-Json"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=4)
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout)
                if isinstance(data, str):
                    return [data]
                if isinstance(data, list):
                    return [name for name in data if name]
        except Exception:
            pass

        try:
            result = subprocess.run("netsh interface show interface", shell=True, capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=4)
            if result.returncode != 0:
                return []
            lines = result.stdout.splitlines()
            start_idx = 0
            for i, line in enumerate(lines):
                if line.strip().startswith("---"):
                    start_idx = i + 1
                    break
            preferred = []
            fallback = []
            for line in lines[start_idx:]:
                if not line.strip():
                    continue
                parts = re.split(r"\s{2,}", line.strip())
                if len(parts) < 4:
                    continue
                name = "  ".join(parts[3:]).strip()
                if not name:
                    continue
                iface_type = parts[2].lower()
                lower_name = name.lower()
                if any(token in lower_name for token in ("loopback", "teredo", "tunnel", "virtual", "vmware", "vbox", "bluetooth", "isatap")):
                    continue
                if iface_type in ("dedicated", "wireless"):
                    preferred.append(name)
                else:
                    fallback.append(name)
            return preferred if preferred else fallback
        except Exception:
            return []

    def _open_network_settings(self):
        """Open Windows Network Settings."""
        try:
            subprocess.Popen('ms-settings:network', shell=True)
        except Exception:
            try:
                subprocess.Popen('control.exe ncpa.cpl', shell=True)
            except Exception:
                pass

    def _on_test_progress(self, phase, percent, current_speed, max_speed):
        """Update UI with real-time speed test progress."""
        self.progress_bar.setValue(percent)
        
        # Phase icons
        phase_icons = {
            'ping': '🔍 Measuring ping...',
            'download': '⬇️ Testing download...',
            'upload': '⬆️ Testing upload...',
            'done': '✅ Complete!'
        }
        self.lbl_phase.setText(phase_icons.get(phase, f"⏳ {phase}"))
        
        # Speed display
        if phase in ('download', 'upload'):
            arrow = '↓' if phase == 'download' else '↑'
            color = Theme.GREEN if phase == 'download' else Theme.BLUE
            
            if current_speed > 1000:
                speed_text = f"{arrow} {current_speed/1000:.2f} Gbps"
            else:
                speed_text = f"{arrow} {current_speed:.1f} Mbps"
            
            if max_speed > 1000:
                max_text = f"(Max: {max_speed/1000:.2f} Gbps)"
            else:
                max_text = f"(Max: {max_speed:.1f} Mbps)"
            
            self.lbl_realtime_speed.setText(f"{speed_text}  {max_text}")
            self.lbl_realtime_speed.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: bold;")
        elif phase == 'ping':
            self.lbl_realtime_speed.setText(f"⏱️ {current_speed:.1f} ms" if current_speed > 0 else "⏱️ ...")

    def _measure_ping(self, host="8.8.8.8", count=5):
        """Measure ping latency and jitter."""
        latencies = []
        
        for i in range(count):
            try:
                start = time.time()
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2.0)
                s.connect((host, 53))
                latency = (time.time() - start) * 1000  # ms
                s.close()
                latencies.append(latency)
                
                # Report progress
                progress = int(((i + 1) / count) * 100)
                self._test_signals.progress.emit('ping', progress, latency, 0)
                time.sleep(0.3)
            except Exception:
                continue
        
        if latencies:
            avg_ping = sum(latencies) / len(latencies)
            # Jitter = average deviation from mean
            jitter = sum(abs(l - avg_ping) for l in latencies) / len(latencies)
            return avg_ping, jitter
        return 0, 0

    def _measure_download(self, duration=5.0):
        """Measure download speed."""
        urls = [
            "https://speed.cloudflare.com/__down?bytes=100000000",
            "https://speed.hetzner.de/100MB.bin",
        ]
        
        max_speed = 0.0
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        for url in urls:
            try:
                start = time.time()
                bytes_read = 0
                last_update = start
                chunk_bytes = 0
                
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                
                with urllib.request.urlopen(req, timeout=12.0, context=ctx) as response:
                    while True:
                        chunk = response.read(256 * 1024)
                        if not chunk:
                            break
                        
                        bytes_read += len(chunk)
                        chunk_bytes += len(chunk)
                        now = time.time()
                        elapsed = now - start
                        
                        if now - last_update >= 0.2:
                            interval = now - last_update
                            current_speed = (chunk_bytes / (1024*1024)) / interval * 8
                            overall_speed = (bytes_read / (1024*1024)) / elapsed * 8
                            max_speed = max(max_speed, current_speed, overall_speed)
                            
                            progress = min(int((elapsed / duration) * 100), 100)
                            self._test_signals.progress.emit('download', progress, current_speed, max_speed)
                            
                            last_update = now
                            chunk_bytes = 0
                        
                        if elapsed >= duration:
                            break
                
                # Final speed
                total_time = max(time.time() - start, 0.1)
                final_speed = (bytes_read / (1024*1024)) / total_time * 8
                max_speed = max(max_speed, final_speed)
                self._test_signals.progress.emit('download', 100, final_speed, max_speed)
                break
                
            except Exception:
                continue
        
        return max_speed

    def _measure_upload(self, duration=5.0):
        """Measure upload speed using Cloudflare speed test."""
        max_speed = 0.0
        
        try:
            # Generate random data for upload
            upload_size = 10 * 1024 * 1024  # 10MB per request
            dummy_data = b'0' * upload_size
            
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            start = time.time()
            total_sent = 0
            last_update = start
            chunk_sent = 0
            
            while time.time() - start < duration:
                try:
                    req = urllib.request.Request(
                        "https://speed.cloudflare.com/__up",
                        data=dummy_data,
                        headers={
                            'User-Agent': 'Mozilla/5.0',
                            'Content-Type': 'application/octet-stream',
                            'Content-Length': str(len(dummy_data))
                        },
                        method='POST'
                    )
                    
                    upload_start = time.time()
                    with urllib.request.urlopen(req, timeout=10.0, context=ctx) as response:
                        response.read()
                    upload_time = time.time() - upload_start
                    
                    total_sent += upload_size
                    chunk_sent += upload_size
                    now = time.time()
                    elapsed = now - start
                    
                    if now - last_update >= 0.3:
                        current_speed = (chunk_sent / (1024*1024)) / (now - last_update) * 8
                        overall_speed = (total_sent / (1024*1024)) / elapsed * 8
                        max_speed = max(max_speed, current_speed, overall_speed)
                        
                        progress = min(int((elapsed / duration) * 100), 100)
                        self._test_signals.progress.emit('upload', progress, current_speed, max_speed)
                        
                        last_update = now
                        chunk_sent = 0
                        
                except Exception:
                    time.sleep(0.5)
                    continue
            
            # Final calculation
            total_time = max(time.time() - start, 0.1)
            final_speed = (total_sent / (1024*1024)) / total_time * 8
            max_speed = max(max_speed, final_speed)
            self._test_signals.progress.emit('upload', 100, final_speed, max_speed)
            
        except Exception:
            pass
        
        return max_speed

    def _run_speed_test(self):
        """Run comprehensive speed test: ping + download + upload."""
        if self._testing:
            return
        self._testing = True
        self._results = {}
        self.btn_test.setEnabled(False)
        self.lbl_result.setText("")
        
        # Show test panel, hide results
        self.test_panel.setVisible(True)
        self.results_panel.setVisible(False)
        self.progress_bar.setValue(0)
        self.lbl_phase.setText("⏳ Preparing...")
        self.lbl_realtime_speed.setText("")
        
        def run_all_tests():
            results = {
                'ping': 0,
                'jitter': 0,
                'download': 0,
                'upload': 0
            }
            
            try:
                # Phase 1: Ping (about 2 seconds)
                ping, jitter = self._measure_ping(count=5)
                results['ping'] = ping
                results['jitter'] = jitter
                
                # Phase 2: Download (5 seconds)
                results['download'] = self._measure_download(duration=5.0)
                
                # Phase 3: Upload (5 seconds)
                results['upload'] = self._measure_upload(duration=5.0)
                
            except Exception as e:
                results['error'] = str(e)[:50]
            
            self._test_signals.finished.emit(results)
        
        threading.Thread(target=run_all_tests, daemon=True).start()
        
    def _on_test_done(self, results):
        """Handle test completion."""
        # Check if this is an IP update
        if results.get('__type') == 'ip_update':
            self._on_ips_fetched(
                results.get('local_ip', 'Unknown'),
                results.get('public_ip', 'Unknown'),
                results.get('isp', '')
            )
            return
        
        # Speed test finished
        self._testing = False
        self.btn_test.setEnabled(True)
        
        # Update phase label
        self.lbl_phase.setText("✅ Complete!")
        self.progress_bar.setValue(100)
        
        # Hide test panel, show results
        QTimer.singleShot(1000, lambda: self._show_results(results))
    
    def _show_results(self, results):
        """Display test results."""
        self.test_panel.setVisible(False)
        self.results_panel.setVisible(True)
        
        # Ping & Jitter
        ping = results.get('ping', 0)
        jitter = results.get('jitter', 0)
        self.lbl_ping.setText(f"Ping: {ping:.1f} ms")
        self.lbl_jitter.setText(f"Jitter: {jitter:.1f} ms")
        
        # Download speed
        down_speed = results.get('download', 0)
        if down_speed > 1000:
            self.lbl_down_result.setText(f"↓ {down_speed/1000:.2f} Gbps")
        else:
            self.lbl_down_result.setText(f"↓ {down_speed:.1f} Mbps")
        
        # Upload speed
        up_speed = results.get('upload', 0)
        if up_speed > 1000:
            self.lbl_up_result.setText(f"↑ {up_speed/1000:.2f} Gbps")
        else:
            self.lbl_up_result.setText(f"↑ {up_speed:.1f} Mbps")
        
        # Status message
        if results.get('error'):
            self.lbl_result.setText(f"⚠️ {results['error']}")
        else:
            self.lbl_result.setText(f"Test completed at {time.strftime('%H:%M:%S')}")

    def update_stats(self, stats: SystemStats):
        """Update network speed display (real-time I/O)."""
        self.lbl_down.setText(f"{stats.net_recv_speed:.1f} MB/s")
        self.lbl_up.setText(f"{stats.net_sent_speed:.1f} MB/s")
