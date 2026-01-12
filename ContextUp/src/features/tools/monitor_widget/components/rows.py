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
        self.lbl_name.setStyleSheet(f"color: {Theme.TEXT_MAIN}; font-size: 11px;")
        
        self.lbl_usage = QLabel(usage_text)
        self.lbl_usage.setFixedWidth(70)
        self.lbl_usage.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 11px;")
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
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(8)
        
        # Drive letter
        lbl_name = QLabel(f"{info.mountpoint[0]}:")
        lbl_name.setStyleSheet(f"color: {Theme.ACCENT}; font-weight: bold; font-size: 12px;")
        lbl_name.setFixedWidth(24)
        
        # Usage bar (compact)
        bar = QProgressBar()
        bar.setFixedHeight(12)
        bar.setFixedWidth(100)
        bar.setTextVisible(False)
        bar.setRange(0, 100)
        bar.setValue(int(info.percent))
        color = Theme.get_color(info.percent)
        # Use solid color for progress bar background
        bar.setStyleSheet(f"""
            QProgressBar {{ background: {Theme.BG_SECTION}; border-radius: 6px; border: none; }}
            QProgressBar::chunk {{ background: {color}; border-radius: 6px; }}
        """)
        
        # Usage text
        lbl_usage = QLabel(f"{info.used_gb:.1f}/{info.total_gb:.0f} GB")
        lbl_usage.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: 10px;")
        
        # Open button (Icon)
        btn_open = QPushButton()
        btn_open.setIcon(qta.icon('fa5s.folder-open', color=Theme.ACCENT))
        btn_open.setCursor(Qt.PointingHandCursor)
        btn_open.setFixedSize(20, 20)
        btn_open.setStyleSheet("background: transparent; border: none;")
        btn_open.clicked.connect(self._open_mountpoint)
        
        layout.addWidget(lbl_name)
        layout.addWidget(bar)
        layout.addWidget(lbl_usage)
        layout.addStretch()
        layout.addWidget(btn_open)

    def _open_mountpoint(self):
        """Open the drive mountpoint; ignore failures to avoid UI crash."""
        try:
            os.startfile(self._mountpoint)
        except OSError:
            pass
