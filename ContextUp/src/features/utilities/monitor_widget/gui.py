"""
Monitor Widget GUI v9.0 - Modular Architecture
- Vertical collapsed view with C/R/G/V/D/N/S rows.
- Side-expanding panel for detailed stats.
- Dedicated Disk/Network/Server tabs.
"""
import sys
import os

# DEBUG: Early crash detection
try:
    with open(os.path.join(os.path.dirname(__file__), "monitor_boot_debug.log"), "a") as f:
        f.write(f"Booting: {sys.executable}\n")
        f.write(f"Script: {sys.argv}\n")
        f.write(f"CWD: {os.getcwd()}\n")
        f.write(f"Path: {sys.path}\n")
        f.write(f"__file__: {__file__}\n")
except: pass

try:
    from pathlib import Path
    import platform
    import time
    import logging
    import psutil
    import qtawesome as qta

    from PySide6.QtCore import Qt, QTimer, QPoint, QSize, Signal, QObject
    from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                 QHBoxLayout, QLabel, QFrame, QSystemTrayIcon, QMenu,
                                 QPushButton, QSlider, QCheckBox, QStackedWidget)
    from PySide6.QtGui import QIcon, QCursor, QAction, QColor

    from features.utilities.monitor_widget.theme import Theme
    from features.utilities.monitor_widget.engine import MonitorEngine, SystemStats
    from features.utilities.monitor_widget.process_manager import ProcessManager
    from features.utilities.monitor_widget.components.sidebar import SidebarItem
    from features.utilities.monitor_widget.pages.process_page import ProcessListPage
    from features.utilities.monitor_widget.pages.gpu_page import GpuPage
    from features.utilities.monitor_widget.pages.disk_page import DiskPage
    from features.utilities.monitor_widget.pages.net_page import NetPage
    from features.utilities.monitor_widget.pages.server_page import ServerPage
    from features.utilities.monitor_widget.monitor_controls import MonitorController

    # Success Logic
    try:
        with open(os.path.join(os.path.dirname(__file__), "monitor_boot_debug.log"), "a") as f:
            f.write("Imports SUCCESS.\n")
    except: pass

except Exception as e:
    import traceback
    
    # Log the initial failure
    try:
        with open(os.path.join(os.path.dirname(__file__), "monitor_boot_debug.log"), "a") as f:
            f.write(f"Initial Import Failed: {e}\nAttempting path fix...\n")
    except: pass

    # Path Fix Logic
    try:
        from pathlib import Path
        current_file = Path(__file__).resolve()
        # file: src/features/utilities/monitor_widget/gui.py
        # src: current_file.parent.parent.parent.parent
        src_dir = current_file.parent.parent.parent.parent
        
        if str(src_dir) not in sys.path:
            sys.path.insert(0, str(src_dir))
            
        # Re-attempt imports with fixed path
        from features.tools.monitor_widget.theme import Theme
        from features.tools.monitor_widget.engine import MonitorEngine, SystemStats
        from features.tools.monitor_widget.process_manager import ProcessManager
        from features.tools.monitor_widget.components.sidebar import SidebarItem
        from features.tools.monitor_widget.pages.process_page import ProcessListPage
        from features.tools.monitor_widget.pages.gpu_page import GpuPage
        from features.tools.monitor_widget.pages.disk_page import DiskPage
        from features.tools.monitor_widget.pages.net_page import NetPage
        from features.tools.monitor_widget.pages.server_page import ServerPage
        from features.tools.monitor_widget.monitor_controls import MonitorController
        
        with open(os.path.join(os.path.dirname(__file__), "monitor_boot_debug.log"), "a") as f:
            f.write("Imports SUCCESS (Recovered).\n")
            
    except Exception as e2:
        # If it still fails, log everything and crash
        with open(os.path.join(os.path.dirname(__file__), "monitor_boot_debug.log"), "a") as f:
            f.write(f"CRITICAL IMPORT ERROR AFTER FIX: {e2}\n{traceback.format_exc()}\n")
        pass



# Global Debug Path
DEBUG_LOG_PATH = os.path.join(os.path.dirname(__file__), "monitor_debug.log")
BOOT_LOG_PATH = os.path.join(os.path.dirname(__file__), "monitor_boot_debug.log")

# Configure Standard Logging for Imported Modules
logging.basicConfig(
    filename=DEBUG_LOG_PATH,
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def trace(msg):
    try:
        with open(BOOT_LOG_PATH, "a") as f:
            f.write(f"{msg}\n")
    except: pass

def is_admin():
    """Check if running with admin privileges."""
    try:
        return os.getuid() == 0
    except AttributeError:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0


def restart_as_admin():
    """Restart the script with admin privileges."""
    import ctypes
    from pathlib import Path
    
    # Adaptive Root Finding
    current = Path(__file__).resolve()
    project_root = current.parent.parent.parent.parent # Default fallback
    
    # Walk up to find 'src' or 'ContextUp' or 'MonitorWidget_Standalone'
    temp = current
    while temp.parent != temp:
        if temp.name in ['src', 'ContextUp', 'MonitorWidget_Standalone']:
            project_root = temp.parent
            break
        temp = temp.parent
        
    python_path = sys.executable
    script_path = str(Path(__file__).resolve())
    
    trace(f"Restarting... Root: {project_root}")
    
    ret = ctypes.windll.shell32.ShellExecuteW(
        None, "runas", python_path, f'"{script_path}"', str(project_root), 1
    )
    if ret > 32:
        sys.exit(0)


# DEBUG: Trace
trace("Defining Classes...")

class StatsBridge(QObject):
    """Bridge to safely pass stats from background thread to UI thread."""
    stats_updated = Signal(object)


class MonitorWidgetWindow(QMainWindow):
    """Main monitor widget window."""
    
    SIDEBAR_WIDTH = 120
    EXPANDED_WIDTH = 400
    HEIGHT = 285
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Monitor Widget")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.setFixedHeight(self.HEIGHT)
        self.setFixedWidth(self.SIDEBAR_WIDTH)
        
        # Stats Bridge
        self.bridge = StatsBridge()
        self.bridge.stats_updated.connect(self._on_stats_update)
        
        # Engine
        self.engine = MonitorEngine()
        self.process_manager = ProcessManager()
        self.engine.add_callback(lambda stats: self.bridge.stats_updated.emit(stats))
        
        # State
        self.expanded = False
        self.opacity_val = 1.0
        self.current_page = 0
        self._drag_pos = None

        self._init_ui()
        self.engine.start()

    def _init_ui(self):
        """Initialize the user interface."""
        self.central_widget = QWidget()
        self.central_widget.setObjectName("central")
        self.central_widget.setAttribute(Qt.WA_TranslucentBackground)
        self.central_widget.setStyleSheet("background: transparent;")
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self._init_sidebar()
        self._init_content_panel()
        self._update_opacity(self.opacity_val)
        
        # Enable dragging on entire window background
        self.central_widget.mousePressEvent = self._start_drag
        self.central_widget.mouseMoveEvent = self._do_drag
        self.sidebar.mousePressEvent = self._start_drag
        self.sidebar.mouseMoveEvent = self._do_drag
        
    def _init_sidebar(self):
        """Initialize the sidebar."""
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(self.SIDEBAR_WIDTH)
        self.sidebar.setStyleSheet(f"background-color: {Theme.BG_SIDEBAR}; border-top-left-radius: 8px; border-bottom-left-radius: 8px;")
        
        self.side_layout = QVBoxLayout(self.sidebar)
        self.side_layout.setContentsMargins(0, 4, 0, 0)
        self.side_layout.setSpacing(1)
        
        # Top Row: Always on top + Task Manager
        top_row = QWidget()
        top_layout = QHBoxLayout(top_row)
        top_layout.setContentsMargins(8, 0, 8, 0)
        top_layout.setSpacing(4)
        
        chk_top = QCheckBox("Top")
        chk_top.setChecked(True)
        chk_top.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: 10px; background: transparent; border: none;")
        chk_top.stateChanged.connect(self._toggle_top)
        top_layout.addWidget(chk_top)
        
        top_layout.addStretch()
        
        # Task Manager Button
        btn_task = QPushButton()
        btn_task.setIcon(qta.icon('fa5s.table', color=Theme.TEXT_DIM))
        btn_task.setFixedSize(16, 16)
        btn_task.setToolTip("Open Task Manager")
        btn_task.setCursor(Qt.PointingHandCursor)
        btn_task.setStyleSheet("background: transparent; border: none;")
        btn_task.clicked.connect(lambda: os.startfile("taskmgr"))
        top_layout.addWidget(btn_task)
        
        self.side_layout.addWidget(top_row)
        
        # Dummy btn_close for compatibility (hidden, with parent to avoid taskbar)
        self.btn_close = QPushButton(self.sidebar)
        self.btn_close.hide()

        # Sidebar items
        self.btn_c = SidebarItem("CPU", "cpu")
        self.btn_r = SidebarItem("RAM", "ram")
        self.btn_g = SidebarItem("GPU", "gpu")
        self.btn_v = SidebarItem("VRAM", "vram")
        self.btn_d = SidebarItem("DISK", "disk")
        self.btn_n = SidebarItem("NET", "net")
        self.btn_s = SidebarItem("SRV", "server")
        
        self.items = [self.btn_c, self.btn_r, self.btn_g, self.btn_v, self.btn_d, self.btn_n, self.btn_s]
        
        for i, btn in enumerate(self.items):
            self.side_layout.addWidget(btn)
            btn.clicked.connect(lambda checked=False, idx=i: self._toggle_expand(idx))
            
        self.side_layout.addStretch()
        self.main_layout.addWidget(self.sidebar)
        
    def _init_content_panel(self):
        """Initialize the expandable content panel."""
        self.content_panel = QWidget()
        self.content_panel.setObjectName("content")
        self.content_panel.setVisible(False)
        
        self.stack = QStackedWidget(self.content_panel)
        # Monitor Controller
        self.controller = MonitorController()
        
        # Pages
        # C, R: ProcessList
        self.page_c = ProcessListPage("CPU Usage", "cpu", self.engine, self.process_manager)
        self.page_r = ProcessListPage("RAM Usage", "ram", self.engine, self.process_manager)
        
        # G: GPU Page (Monitoring + Controls)
        self.page_g = GpuPage("GPU Monitor", self.engine, self.controller)
        
        # V: ProcessList (VRAM)
        self.page_v = ProcessListPage("VRAM Usage", "vram", self.engine, self.process_manager)
        
        # D, N, S: Dedicated
        self.page_d = DiskPage("Disk Usage", self.engine)
        self.page_n = NetPage("Network Usage", self.engine)
        self.page_s = ServerPage("Local Servers", self.engine, self.process_manager)
        
        self.pages = [self.page_c, self.page_r, self.page_g, self.page_v, self.page_d, self.page_n, self.page_s]
        
        for p in self.pages:
            self.stack.addWidget(p)
            # Connect opacity slider
            if hasattr(p, 'opacity_slider'):
                p.opacity_slider.valueChanged.connect(lambda v: self._update_opacity(v/100.0))
            # Connect close button
            if hasattr(p, 'btn_close'):
                p.btn_close.clicked.connect(self.close)
            
        c_layout = QVBoxLayout(self.content_panel)
        c_layout.setContentsMargins(0, 0, 0, 0)
        c_layout.addWidget(self.stack)
        
        # Enable dragging on content panel
        self.content_panel.mouseMoveEvent = self._do_drag
        
        self.main_layout.addWidget(self.content_panel)

    def closeEvent(self, event):
        """Handle window close event."""
        if hasattr(self, 'controller'):
            self.controller.restore_state()
        super().closeEvent(event)
    
    def _collapse_panel(self):
        """Collapse the expanded panel."""
        if self.expanded:
            self.expanded = False
            self.content_panel.setHidden(True)
            self.items[self.current_page].setChecked(False)
            self.setFixedSize(self.SIDEBAR_WIDTH, self.HEIGHT)
            self.btn_close.hide()
        
    def _init_settings(self, layout):
        """Initialize settings row (opacity slider + always on top checkbox)."""
        s_slider = QSlider(Qt.Horizontal)
        s_slider.setRange(20, 100)
        s_slider.setValue(100)
        s_slider.setFixedHeight(10)
        s_slider.setStyleSheet(f"""
            QSlider {{ background: transparent; }}
            QSlider::groove:horizontal {{ height: 2px; background: {Theme.hex_to_rgba(Theme.TEXT_DIM, 0.2)}; border-radius: 1px; }}
            QSlider::handle:horizontal {{ background: {Theme.TEXT_DIM}; width: 8px; height: 8px; border-radius: 4px; margin-top: -3px; }}
        """)
        s_slider.valueChanged.connect(lambda v: self._update_opacity(v/100.0))
        s_slider.setToolTip("Opacity")
        
        chk_top = QCheckBox("Top")
        chk_top.setChecked(True)
        chk_top.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: 10px; margin-left: 8px; background: transparent; border: none;")
        chk_top.stateChanged.connect(self._toggle_top)
        
        settings_row = QHBoxLayout()
        settings_row.setContentsMargins(8, 0, 8, 4)
        settings_row.setSpacing(4)
        settings_row.addWidget(s_slider, 1)
        settings_row.addWidget(chk_top)
        layout.addLayout(settings_row)
    
    def _reposition_close_btn(self):
        """Reposition close button to top-right of current window width. Hide when collapsed."""
        if self.expanded:
            w = self.width()
            self.btn_close.move(w - 24, 4)
            self.btn_close.show()
            self.btn_close.raise_()
        else:
            self.btn_close.hide()
    
    def _update_opacity(self, value):
        """Update window opacity using window-level opacity (not per-element RGBA)."""
        self.opacity_val = value
        # Use window-level opacity - this applies to the entire window uniformly
        # without causing overlap artifacts between internal UI elements
        self.setWindowOpacity(value)
        
        # Keep background colors solid (no RGBA)
        self.sidebar.setStyleSheet(f"background-color: {Theme.BG_SIDEBAR}; border-top-left-radius: 8px; border-bottom-left-radius: 8px;")
        self.content_panel.setStyleSheet(f"background-color: {Theme.BG_MAIN}; border-top-right-radius: 8px; border-bottom-right-radius: 8px;")

    def _toggle_expand(self, index):
        """Toggle sidebar expansion or switch tabs."""
        if self.expanded and self.current_page == index:
            # Collapse
            self.expanded = False
            self.content_panel.setHidden(True)
            self.items[index].setChecked(False)
            self.setFixedSize(self.SIDEBAR_WIDTH, self.HEIGHT)
            self._reposition_close_btn()
        else:
            # Expand or switch tab
            if not self.expanded:
                self.expanded = True
                self.content_panel.setHidden(False)
                self.setFixedSize(self.EXPANDED_WIDTH, self.HEIGHT)
            
            self._reposition_close_btn()
            
            for i, btn in enumerate(self.items):
                btn.setChecked(i == index)
            
            self.current_page = index
            self.stack.setCurrentIndex(index)
            
            # Sync opacity slider of the current page
            current_page_widget = self.pages[index]
            if hasattr(current_page_widget, 'opacity_slider'):
                # Block signals to prevent feedback loop
                current_page_widget.opacity_slider.blockSignals(True)
                current_page_widget.opacity_slider.setValue(int(self.opacity_val * 100))
                current_page_widget.opacity_slider.blockSignals(False)
            
            stats = self.engine.get_stats()
            current_page_widget.update_stats(stats)
            
    def _on_stats_update(self, stats: SystemStats):
        """Handle stats update from engine."""
        # Update sidebar items
        self.btn_c.update_data(stats.cpu_percent)
        self.btn_r.update_data(stats.ram_percent)
        self.btn_g.update_data(stats.gpu_load)
        self.btn_v.update_data(stats.vram_percent)
        
        # Disk
        total_io = stats.disk_read_speed + stats.disk_write_speed
        d_vis_pct = min(total_io, 100)
        self.btn_d.update_data(d_vis_pct, f"{total_io:.0f} MB/s", Theme.get_color(d_vis_pct))
        
        # Net
        total_net = stats.net_recv_speed + stats.net_sent_speed
        n_vis_pct = min(total_net * 5, 100)
        self.btn_n.update_data(n_vis_pct, f"{total_net:.1f} MB/s", Theme.get_color(n_vis_pct))
        
        # Server
        srv_count = len(stats.server_points)
        s_pct = min(srv_count * 10, 100)
        self.btn_s.update_data(s_pct, f"{srv_count} Port", Theme.get_color(s_pct))
        
        # Update active page
        if self.expanded:
            self.pages[self.current_page].update_stats(stats)
            
    def _start_drag(self, event):
        """Start window drag."""
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def _do_drag(self, event):
        """Handle window drag with snap-to-edge."""
        if event.buttons() == Qt.LeftButton and self._drag_pos:
            new_pos = event.globalPosition().toPoint() - self._drag_pos
            
            # Snap-to-edge
            snap_margin = 25
            screen = QApplication.screenAt(event.globalPosition().toPoint())
            if screen:
                geo = screen.availableGeometry()
                if abs(new_pos.x() - geo.left()) < snap_margin:
                    new_pos.setX(geo.left())
                if abs(new_pos.y() - geo.top()) < snap_margin:
                    new_pos.setY(geo.top())
                if abs((new_pos.x() + self.width()) - geo.right()) < snap_margin:
                    new_pos.setX(geo.right() - self.width())
                if abs((new_pos.y() + self.height()) - geo.bottom()) < snap_margin:
                    new_pos.setY(geo.bottom() - self.height())
            
            self.move(new_pos)
            event.accept()
            
    def _toggle_top(self, state):
        """Toggle always-on-top."""
        is_top = state == Qt.Checked
        self.setWindowFlag(Qt.WindowStaysOnTopHint, is_top)
        self.setWindowFlag(Qt.Tool, True)  # Always hide from taskbar
        self.setWindowFlag(Qt.FramelessWindowHint, True)
        self.show()

    def closeEvent(self, event):
        """Clean up on close."""
        self.engine.stop()
        super().closeEvent(event)



def log_debug(msg):
    """Write debug message to log file."""
    try:
        with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"{msg}\n")
    except:
        pass


def kill_existing_instances():
    """Ensure only one instance of the monitor is running."""
    curr_pid = os.getpid()
    curr_script = os.path.abspath(__file__).lower()
    
    for proc in psutil.process_iter(['pid', 'cmdline']):
        try:
            if proc.info['pid'] == curr_pid:
                continue
            cmdline = proc.info.get('cmdline')
            if cmdline:
                cmd_str = " ".join(cmdline).lower()
                if "gui.py" in cmd_str and ("monitor_widget" in cmd_str or "ContextUp" in cmd_str):
                    log_debug(f"Killing existing instance: PID {proc.info['pid']}")
                    proc.kill()
                    proc.wait(timeout=1)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
            pass
        except Exception as e:
            log_debug(f"Error killing process: {e}")


if __name__ == "__main__":
    trace("Entering Main Block.")
    
    # Hide console window on Windows
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.user32.ShowWindow(
                ctypes.windll.kernel32.GetConsoleWindow(), 0
            )
        except Exception:
            pass
    
    kill_existing_instances()
    
    try:
        with open(DEBUG_LOG_PATH, "w") as f:
            f.write("Startup...\n")
    except:
        trace("Failed to init main log.")

    try:
        log_debug(f"Checking admin... is_admin={is_admin()}")
        if not is_admin():
            log_debug("Restarting as admin...")
            restart_as_admin()
            log_debug("Restart triggered.")
            sys.exit(0)
            
        log_debug("Creating QApplication...")
        app = QApplication(sys.argv)
        
        log_debug("Creating Window...")
        window = MonitorWidgetWindow()
        app.aboutToQuit.connect(window.engine.stop)
        log_debug("Showing Window...")
        window.show()
        log_debug("Entering Exec...")
        sys.exit(app.exec())
    except Exception as e:
        import traceback
        err_msg = f"CRITICAL CRASH IN MAIN: {e}\n{traceback.format_exc()}"
        try:
            with open(DEBUG_LOG_PATH, "a") as f:
                f.write(err_msg)
        except: pass
        
        trace(err_msg)
        sys.exit(1)

