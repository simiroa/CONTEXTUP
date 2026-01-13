"""
SidebarItem component - Vertical resource indicator with sparkline.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton, QHBoxLayout, QLabel
from PySide6.QtGui import QFont, QColor, QPainter, QPen, QPainterPath
from collections import deque

from ..theme import Theme


class SidebarItem(QPushButton):
    """
    Vertical Item: [Label] [Value]
    Background fills based on percentage with mini sparkline graph.
    """
    
    def __init__(self, label: str, res_type: str, parent=None):
        super().__init__(parent)
        self.label_text = label
        self.res_type = res_type
        self.setFixedHeight(36)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self._percent = 0.0
        self._value_text = "0%"
        self._color = Theme.GREEN
        self.history = deque(maxlen=40)  # Trend history
        
        # Setup Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        
        self.lbl_name = QLabel(label)
        self.lbl_name.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.lbl_name.setStyleSheet(f"color: {Theme.TEXT_DIM}; background: transparent;")
        
        self.lbl_value = QLabel(self._value_text)
        self.lbl_value.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.lbl_value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.lbl_value.setStyleSheet(f"color: {Theme.TEXT_MAIN}; background: transparent;")
        
        layout.addWidget(self.lbl_name)
        layout.addStretch()
        layout.addWidget(self.lbl_value)
        
    def update_data(self, percent: float, text: str = None, color: str = None):
        """Update the sidebar item with new data."""
        self._percent = percent
        self._value_text = text if text else f"{int(percent)}%"
        self._color = color if color else Theme.get_color(percent)
        
        # SRV label should always be green
        label_color = self._color
        if self.lbl_name.text() == "SRV":
            label_color = Theme.GREEN

        self.lbl_name.setStyleSheet(f"color: {label_color}; background: transparent; font-weight: bold;")
        self.lbl_value.setText(self._value_text)
        self.lbl_value.setStyleSheet(f"color: {self._color}; background: transparent;")
        
        # Add to history for trend
        self.history.append(percent)
        self.update()

    def paintEvent(self, event):
        """Custom paint for background effects and sparkline."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Active State Background
        if self.isChecked():
            color = QColor(Theme.BG_SECTION)
            color.setAlpha(120)
            painter.fillRect(self.rect(), color)
            
            # Active indicator line (Right side)
            ind_color = QColor(Theme.ACCENT)
            ind_color.setAlpha(200)
            painter.fillRect(self.width() - 3, 4, 3, self.height()-8, ind_color)
        elif self.underMouse():
            # Hover effect (only if not checked)
            painter.fillRect(self.rect(), QColor(Theme.BG_SIDEBAR).lighter(110))
        
        # Progress background (Always draw)
        if self._percent > 0:
            width = int(self.width() * (min(self._percent, 100) / 100))
            color = QColor(self._color)
            color.setAlpha(30)
            painter.fillRect(0, 0, width, self.height(), color)
        
        # Sparkline (Always draw)
        if len(self.history) > 1:
            self._draw_sparkline(painter)
        
    def _draw_sparkline(self, painter: QPainter):
        """Draw the trend sparkline at the bottom."""
        w = self.width()
        h = self.height()
        step = w / (self.history.maxlen - 1)
        
        path = QPainterPath()
        path.moveTo(0, h)
        
        for i, val in enumerate(self.history):
            y_base = h - 1
            h_max = 14
            y = y_base - (min(val, 100) / 100.0 * h_max)
            path.lineTo(i * step, y)
        
        path.lineTo((len(self.history) - 1) * step, h)
        path.closeSubpath()
        
        # Fill
        fill_color = QColor(self._color)
        fill_color.setAlpha(40)
        painter.fillPath(path, fill_color)
        
        # Line
        painter.setPen(QPen(QColor(self._color), 1.2))
        line_path = QPainterPath()
        for i, val in enumerate(self.history):
            y_base = h - 1
            h_max = 14
            y = y_base - (min(val, 100) / 100.0 * h_max)
            if i == 0:
                line_path.moveTo(0, y)
            else:
                line_path.lineTo(i * step, y)
        painter.drawPath(line_path)
