"""
DiskPage - Page showing disk usage and I/O speeds.
"""
from PySide6.QtWidgets import QLabel, QWidget, QVBoxLayout, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt
import qtawesome as qta

from ..theme import Theme
from ..engine import SystemStats
from ..components.base_page import BasePage
from ..components.rows import DriveRow
from ..disk_cleaner import DiskCleaner
from ..components.cleanup_dialog import CleanupDialog


class DiskPage(BasePage):
    """Page showing disk drives and I/O speeds."""
    
    def __init__(self, title, engine, parent=None):
        super().__init__(title, parent)
        self.engine = engine
        self.cleaner = DiskCleaner()
        
        self.lbl_speed = QLabel("R: 0.0 MB/s  W: 0.0 MB/s")
        self.lbl_speed.setStyleSheet(f"color: {Theme.TEXT_MAIN}; font-size: 13px; font-weight: bold; margin-bottom: 8px;")
        self.content_area.addWidget(self.lbl_speed)
        
        self.drives_container = QWidget()
        self.drives_layout = QVBoxLayout(self.drives_container)
        self.drives_layout.setContentsMargins(0, 0, 0, 0)
        self.content_area.addWidget(self.drives_container)
        
        # Cleanup Button
        self.content_area.addStretch()
        btn_cleanup = QPushButton(" Manage Capacity")
        btn_cleanup.setIcon(qta.icon('fa5s.broom', color=Theme.TEXT_MAIN))
        btn_cleanup.setCursor(Qt.PointingHandCursor)
        btn_cleanup.setFixedHeight(30)
        btn_cleanup.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BG_SIDEBAR};
                color: {Theme.TEXT_MAIN};
                border: 1px solid {Theme.BG_SECTION};
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {Theme.BG_SECTION};
            }}
        """)
        btn_cleanup.clicked.connect(self._show_cleanup)
        self.content_area.addWidget(btn_cleanup)

    def _show_cleanup(self):
        """Show cleanup dialog."""
        from ..gui import log_debug
        try:
            log_debug("Opening Cleanup Dialog...")
            dlg = CleanupDialog(self.cleaner, self)
            log_debug("Dialog initialized.")
            dlg.exec()
            log_debug("Dialog closed.")
        except Exception as e:
            import traceback
            log_debug(f"Cleanup Dialog Error: {e}\n{traceback.format_exc()}")

    def update_stats(self, stats: SystemStats):
        """Update disk speed and drive list."""
        self.lbl_speed.setText(f"Read: {stats.disk_read_speed:.1f} MB/s   Write: {stats.disk_write_speed:.1f} MB/s")
        
        if not stats.drives:
            if self.drives_layout.count() > 0:
                return  # Keep old list
            else:
                self.drives_layout.addWidget(QLabel("No drives found", styleSheet=f"color:{Theme.TEXT_DIM}"))
                return
            
        while self.drives_layout.count():
            item = self.drives_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            
        for drive in stats.drives:
            self.drives_layout.addWidget(DriveRow(drive))
