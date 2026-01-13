"""
Row components - ProcessRow and DriveRow for list displays.
"""
import os
import qtawesome as qta
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QProgressBar

from ..theme import Theme


class ProcessRow(QWidget):
    """Row for Process List with kill button."""
    
    def __init__(self, name, pid, usage_text, color, process_manager, parent=None):
        super().__init__(parent)
        self.process_manager = process_manager
        self.setFixedHeight(24)
        # Transparent background for cleaner list design
        self.setStyleSheet("background: transparent;")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        
        self.lbl_name = QLabel(f"{name}")
        self.lbl_name.setToolTip(f"PID: {pid}")
        self.lbl_name.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: 11px;")
        
        self.lbl_usage = QLabel(usage_text)
        self.lbl_usage.setFixedWidth(70)
        self.lbl_usage.setStyleSheet(f"color: {Theme.TEXT_MAIN}; font-weight: bold; font-size: 11px;")
        self.lbl_usage.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        btn_kill = QPushButton()
        btn_kill.setIcon(qta.icon('fa5s.times', color=Theme.RED))
        btn_kill.setFixedSize(18, 18)
        btn_kill.setCursor(Qt.PointingHandCursor)
        btn_kill.setStyleSheet("background: transparent; border: none;")
        btn_kill.clicked.connect(lambda: self.process_manager.kill_process(pid))
        
        layout.addWidget(self.lbl_name, 1)
        layout.addWidget(self.lbl_usage)
        layout.addWidget(btn_kill)


class DriveRow(QWidget):
    """Row for Drive List with inline progress bar."""
    
    def __init__(self, info, parent=None):
        super().__init__(parent)
        self._mountpoint = info.mountpoint
        self.setFixedHeight(30) # Increased height
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2) # More breathing room
        layout.setSpacing(10)
        
        # Drive letter (Clickable)
        btn_name = QPushButton(f"{info.mountpoint[0]}:")
        btn_name.setCursor(Qt.PointingHandCursor)
        btn_name.setFixedWidth(24)
        btn_name.setFlat(True)
        btn_name.setStyleSheet(f"""
            QPushButton {{ 
                color: {Theme.ACCENT}; 
                font-weight: bold; 
                font-size: 12px; 
                border: none; 
                background: transparent; 
                text-align: left;
            }}
            QPushButton:hover {{ color: {Theme.TEXT_MAIN}; }}
        """)
        btn_name.clicked.connect(self._open_mountpoint)
        
        # Usage bar (Thinner, Brighter Background)
        bar = QProgressBar()
        bar.setFixedHeight(6) # Thinner
        bar.setTextVisible(False)
        bar.setRange(0, 100)
        bar.setValue(int(info.percent))
        color = Theme.get_color(info.percent)
        
        # Brighter background for better visibility
        bg_color = Theme.hex_to_rgba(Theme.TEXT_DIM, 0.2) 
        
        bar.setStyleSheet(f"""
            QProgressBar {{ 
                background: {bg_color}; 
                border-radius: 3px; 
                border: none; 
            }}
            QProgressBar::chunk {{ 
                background: {color}; 
                border-radius: 3px; 
            }}
        """)
        
        # Usage text (Monospaced for alignment)
        lbl_usage = QLabel(f"{info.used_gb:>5.1f} / {info.total_gb:>4.0f} GB")
        lbl_usage.setFixedWidth(100) # Fixed width for alignment
        lbl_usage.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl_usage.setStyleSheet(f"color: {Theme.TEXT_MAIN}; font-size: 10px; font-family: Consolas, monospace;")
        
        layout.addWidget(btn_name)
        layout.addWidget(bar, 1) # Expand to fill space
        layout.addWidget(lbl_usage)

    def _open_mountpoint(self):
        """Open the drive mountpoint; ignore failures to avoid UI crash."""
        try:
            os.startfile(self._mountpoint)
        except OSError:
            pass
