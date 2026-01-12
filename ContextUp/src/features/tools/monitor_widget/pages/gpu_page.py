from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QSlider, QComboBox, QPushButton, QFrame
)
import qtawesome as qta

from ..theme import Theme
from ..engine import SystemStats
from ..components.base_page import BasePage

class GpuPage(BasePage):
    """Page with GPU Stats and Monitor Controls."""
    
    def __init__(self, title, engine, controller, parent=None):
        super().__init__(title, parent)
        self.engine = engine
        self.controller = controller
        
        # --- Detail Header (GPU Info) ---
        header_container = QWidget()
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(4, 0, 4, 8)
        header_layout.setSpacing(4)
        
        # 1. GPU Name (Smaller, Dimmed)
        self.lbl_name = QLabel("NVIDIA GPU")
        self.lbl_name.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: 11px;")
        self.lbl_name.setWordWrap(True) # Allow multi-line if needed
        self.lbl_name.setToolTip("GPU Model Name")
        header_layout.addWidget(self.lbl_name)

        # 2. VRAM Stats (Clean)
        self.lbl_vram = QLabel("0.0 GB / 0.0 GB")
        self.lbl_vram.setStyleSheet(f"color: {Theme.TEXT_MAIN}; font-size: 15px; font-weight: bold;")
        self.lbl_vram.setToolTip("VRAM Usage (Used / Total)")
        header_layout.addWidget(self.lbl_vram)
        
        # 3. Hardware Stats (Brighter/Dynamic)
        self.lbl_stats = QLabel("0.0GHz | 0W | 0°C")
        self.lbl_stats.setStyleSheet(f"color: {Theme.TEXT_MAIN}; font-size: 12px;")
        self.lbl_stats.setToolTip("Core Clock | Power Usage | Temperature")
        header_layout.addWidget(self.lbl_stats)
        
        self.content_area.addWidget(header_container)
        
        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        sep.setStyleSheet(f"background-color: {Theme.BG_SIDEBAR}; border: none; max-height: 1px; margin-top: 4px;")
        self.content_area.addWidget(sep)
        
        # --- Monitor Controls ---
        lbl_controls = QLabel("Monitor Controls")
        lbl_controls.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: 10px; margin-top: 8px;")
        self.content_area.addWidget(lbl_controls)
        
        self.controls_container = QWidget()
        ctrl_layout = QVBoxLayout(self.controls_container)
        ctrl_layout.setContentsMargins(0, 4, 0, 0)
        ctrl_layout.setSpacing(10)
        
        # 1. First Row: Night Mode & Monitor Sleep
        row1_layout = QHBoxLayout()
        
        # Night Mode
        self.btn_night = QPushButton()
        self.btn_night.setCheckable(True)
        self.btn_night.setFixedSize(55, 22)
        self.btn_night.setCursor(Qt.PointingHandCursor)
        self.btn_night.toggled.connect(self._on_night_toggle)
        
        lbl_night = QLabel("Night Mode")
        lbl_night.setStyleSheet(f"color: {Theme.TEXT_MAIN}; font-size: 11px;")
        
        # Monitor Sleep
        btn_sleep = QPushButton("Sleep")
        btn_sleep.setFixedSize(55, 22)
        btn_sleep.setCursor(Qt.PointingHandCursor)
        btn_sleep.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BG_SIDEBAR};
                color: {Theme.TEXT_MAIN};
                border-radius: 11px;
                font-weight: bold;
                font-size: 10px;
                border: 1px solid {Theme.BG_SECTION};
            }}
            QPushButton:hover {{ background-color: {Theme.RED}; color: white; }}
        """)
        btn_sleep.clicked.connect(self.controller.turn_off_monitor)
        
        lbl_sleep = QLabel("Mon Sleep")
        lbl_sleep.setStyleSheet(f"color: {Theme.TEXT_MAIN}; font-size: 11px;")
        
        row1_layout.addWidget(lbl_night)
        row1_layout.addWidget(self.btn_night)
        row1_layout.addSpacing(15)
        row1_layout.addWidget(lbl_sleep)
        row1_layout.addWidget(btn_sleep)
        row1_layout.addStretch()
        ctrl_layout.addLayout(row1_layout)
        
        # 2. Second Row: Brightness Slider
        bright_layout = QHBoxLayout()
        lbl_bright = QLabel("Brightness")
        lbl_bright.setStyleSheet(f"color: {Theme.TEXT_MAIN}; font-size: 11px;")
        self.slider_bright = QSlider(Qt.Horizontal)
        self.slider_bright.setRange(0, 100)
        self.slider_bright.setFixedHeight(20)
        self.slider_bright.valueChanged.connect(self._on_brightness_change)
        
        self.lbl_bright_val = QLabel("100%")
        self.lbl_bright_val.setFixedWidth(35)
        self.lbl_bright_val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.lbl_bright_val.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: 11px;")
        
        bright_layout.addWidget(lbl_bright)
        bright_layout.addWidget(self.slider_bright)
        bright_layout.addWidget(self.lbl_bright_val)
        ctrl_layout.addLayout(bright_layout)
        
        # 3. Third Row: Refresh Rate
        rate_layout = QHBoxLayout()
        lbl_rate = QLabel("Refresh Rate")
        lbl_rate.setStyleSheet(f"color: {Theme.TEXT_MAIN}; font-size: 11px;")
        
        self.combo_rate = QComboBox()
        self.combo_rate.setStyleSheet(f"background: {Theme.BG_SIDEBAR}; color: {Theme.TEXT_MAIN}; border: 1px solid {Theme.BG_SIDEBAR}; padding: 2px;")
        self.combo_rate.setFixedHeight(24)
        
        btn_apply = QPushButton("Apply")
        btn_apply.setFixedSize(50, 24)
        btn_apply.setCursor(Qt.PointingHandCursor)
        btn_apply.setStyleSheet(f"background: {Theme.ACCENT}; color: {Theme.BG_MAIN}; border-radius: 4px; font-weight: bold;")
        btn_apply.clicked.connect(self._on_apply_rate)
        
        rate_layout.addWidget(lbl_rate)
        rate_layout.addWidget(self.combo_rate, 1)
        rate_layout.addWidget(btn_apply)
        ctrl_layout.addLayout(rate_layout)
        
        self.content_area.addWidget(self.controls_container)
        self.content_area.addStretch()
        
        # Init Controls
        self._update_night_btn_style(False)
        self._init_controls()

    def _init_controls(self):
        # Brightness
        b = self.controller.get_brightness()
        self.slider_bright.setValue(b)
        self.lbl_bright_val.setText(f"{b}%")
        
        # Rates
        rates = self.controller.get_supported_refresh_rates()
        current = self.controller.get_current_refresh_rate()
        
        self.combo_rate.clear()
        for r in rates:
            self.combo_rate.addItem(f"{r} Hz", r)
            if r == current:
                self.combo_rate.setCurrentIndex(self.combo_rate.count() - 1)

    def update_stats(self, stats: SystemStats):
        """Update GPU stats header."""
        name = stats.gpu_name or "NVIDIA GPU"
        
        # 1. Name
        self.lbl_name.setText(name)
        
        # 2. VRAM
        vram_percent = (stats.vram_used_gb / stats.vram_total_gb * 100) if stats.vram_total_gb > 0 else 0
        vram_color = Theme.get_color(vram_percent)
        self.lbl_vram.setText(f"""
            <span style='color:{vram_color};'>{stats.vram_used_gb:.1f}GB</span> 
            <span style='color:{Theme.TEXT_DIM};'>/ {stats.vram_total_gb:.1f}GB</span>
        """)
        
        # 3. Hardware Stats
        temp = f"{stats.gpu_temp:.0f}°C"
        temp_color = Theme.RED if stats.gpu_temp > 80 else Theme.GREEN
        
        clock = f"{stats.gpu_clock_mhz/1000:.1f}GHz" if stats.gpu_clock_mhz > 0 else "0.0GHz"
        power = f"{stats.gpu_power_w:.0f}W" if stats.gpu_power_w > 0 else "0W"
        
        # Use HTML for color formatting in the stats line only
        self.lbl_stats.setText(f"""
            {clock} <span style='color:{Theme.TEXT_DIM};'>|</span> 
            {power} <span style='color:{Theme.TEXT_DIM};'>|</span> 
            <span style='color:{temp_color}; font-weight:bold;'>{temp}</span>
        """)

    def _on_brightness_change(self, value):
        self.lbl_bright_val.setText(f"{value}%")
        self.controller.set_brightness(value)

    def _on_apply_rate(self):
        idx = self.combo_rate.currentIndex()
        if idx >= 0:
            rate = self.combo_rate.itemData(idx)
            self.controller.set_refresh_rate(rate)

    def _on_night_toggle(self, checked):
        self._update_night_btn_style(checked)
        self.controller.toggle_night_mode(checked)

    def _update_night_btn_style(self, checked):
        color = Theme.ACCENT if checked else Theme.BG_SIDEBAR
        text = "ON" if checked else "OFF"
        self.btn_night.setText(text)
        self.btn_night.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: {Theme.BG_MAIN if checked else Theme.TEXT_DIM};
                border-radius: 10px;
                font-weight: bold;
                font-size: 10px;
            }}
        """)
