"""
BasePage component - Base class for all detail pages with header controls.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QPushButton
from PySide6.QtGui import QFont
import qtawesome as qta

from ..theme import Theme
from ..engine import SystemStats


class BasePage(QWidget):
    """Base class for Detail Pages with header controls."""
    
    def __init__(self, title, parent=None, add_stretch=True):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(12, 8, 12, 12)
        self.layout.setSpacing(8)
        # Ensure all labels in the page are transparent by default
        self.setStyleSheet("QLabel { background: transparent; }")
        
        # Header row with title, opacity slider, and close button
        header_row = QHBoxLayout()
        header_row.setSpacing(8)
        
        # Title
        self.lbl_title = QLabel(title)
        self.lbl_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.lbl_title.setStyleSheet(f"color: {Theme.TEXT_MAIN};")
        header_row.addWidget(self.lbl_title)
        
        header_row.addStretch()
        
        # Opacity slider (compact)
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(20, 100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.setFixedSize(60, 12)
        self.opacity_slider.setToolTip("Opacity")
        self.opacity_slider.setStyleSheet(f"""
            QSlider {{ background: transparent; }}
            QSlider::groove:horizontal {{ height: 3px; background: {Theme.BG_SECTION}; border-radius: 1px; }}
            QSlider::handle:horizontal {{ background: {Theme.TEXT_DIM}; width: 8px; height: 8px; border-radius: 4px; margin-top: -2px; }}
            QSlider::handle:horizontal:hover {{ background: {Theme.TEXT_MAIN}; }}
        """)
        header_row.addWidget(self.opacity_slider)
        
        # Close button
        self.btn_close = QPushButton()
        self.btn_close.setIcon(qta.icon('fa5s.times', color=Theme.TEXT_DIM))
        self.btn_close.setFixedSize(18, 18)
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setStyleSheet("background: transparent; border: none;")
        header_row.addWidget(self.btn_close)
        
        self.layout.addLayout(header_row)
        
        self.content_area = QVBoxLayout()
        self.content_area.setSpacing(6)
        self.layout.addLayout(self.content_area)
        if add_stretch:
            self.layout.addStretch()
        
    def update_stats(self, stats: SystemStats):
        """Override in subclass to update with new stats."""
        pass
