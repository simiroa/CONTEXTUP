from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QWidget,
    QPushButton, QCheckBox, QFrame, QProgressBar, QScrollArea
)
from PySide6.QtGui import QColor, QCursor
import qtawesome as qta
from ..theme import Theme

class CleanupWorker(QThread):
    finished = Signal()
    
    def __init__(self, cleaner, active_tasks):
        super().__init__()
        self.cleaner = cleaner
        self.tasks = active_tasks
        
    def run(self):
        if 'temp' in self.tasks: self.cleaner.clean_temp_files()
        if 'bin' in self.tasks: self.cleaner.clean_recycle_bin()
        if 'hiber' in self.tasks: self.cleaner.toggle_hibernate(False)
        if 'winsxs' in self.tasks: self.cleaner.clean_winsxs()
        if 'delivery' in self.tasks: self.cleaner.clean_delivery_optimization()
        if 'downloads' in self.tasks: self.cleaner._clean_folder(self.cleaner.downloads)
        if 'adobe' in self.tasks: self.cleaner._clean_folder(self.cleaner.adobe_cache)
        if 'shader' in self.tasks: self.cleaner.clean_shaders()
        if 'engine' in self.tasks: self.cleaner.clean_engine_cache()
        if 'wsl' in self.tasks: self.cleaner.compact_wsl()
        self.finished.emit()

class CleanupDialog(QDialog):
    """Cute Popup for Disk Cleanup Selection."""
    
    def __init__(self, cleaner, parent=None):
        from ..gui import log_debug
        log_debug("CleanupDialog: Starting __init__")
        super().__init__(parent)
        self.cleaner = cleaner
        # Added Qt.Window to ensure it's treated as a top-level window
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog | Qt.WindowStaysOnTopHint | Qt.Window)
        log_debug("CleanupDialog: Flags set")
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(320, 450)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        # Main Container (Rounded)
        self.container = QFrame()
        self.container.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_SIDEBAR};
                border-radius: 12px;
                border: 1px solid {Theme.BG_SECTION};
            }}
        """)
        self.layout.addWidget(self.container)
        
        self.c_layout = QVBoxLayout(self.container)
        self.c_layout.setContentsMargins(16, 16, 16, 16)
        
        # Header
        header = QHBoxLayout()
        lbl_icon = QLabel()
        lbl_icon.setPixmap(qta.icon('fa5s.broom', color=Theme.ACCENT).pixmap(24, 24))
        lbl_title = QLabel("Capacity Manager")
        lbl_title.setStyleSheet(f"color: {Theme.TEXT_MAIN}; font-size: 16px; font-weight: bold;")
        
        btn_close = QPushButton()
        btn_close.setIcon(qta.icon('fa5s.times', color=Theme.TEXT_DIM))
        btn_close.setFlat(True)
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.clicked.connect(self.close)
        
        header.addWidget(lbl_icon)
        header.addWidget(lbl_title)
        header.addStretch()
        header.addWidget(btn_close)
        self.c_layout.addLayout(header)
        
        # Description
        lbl_desc = QLabel("Select items to clean up and reclaim space.")
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet(f"color: {Theme.TEXT_DIM}; margin-bottom: 10px;")
        self.c_layout.addWidget(lbl_desc)
        
        # Items Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background: transparent; border: none;")
        self.scroll_content = QWidget()
        self.item_layout = QVBoxLayout(self.scroll_content)
        self.item_layout.setSpacing(12)
        
        # Checkboxes
        self.checks = {}
        self.size_labels = {}
        self.row_containers = {}
        
        # Core Items
        self._add_item('temp', 'Temp Files', 'fa5s.trash-alt', True)
        self._add_item('bin', 'Recycle Bin', 'fa5s.trash', True)
        self._add_item('downloads', 'Downloads', 'fa5s.download', False)
        self._add_item('adobe', 'Adobe Cache', 'fa5s.compact-disc', False)
        
        # Advanced Items
        self._add_item('shader', 'Shader Cache', 'fa5s.microchip', False)
        self._add_item('engine', '3D Engine Cache', 'fa5s.cube', False)
        self._add_item('wsl', 'WSL2 Compaction', 'fa5b.linux', False)
        
        # System Items
        self._add_item('delivery', 'Deliv. Opt.', 'fa5s.network-wired', False)
        self._add_item('hiber', 'Hibernate File', 'fa5s.power-off', False)
        self._add_item('winsxs', 'WinSxS (Old updates)', 'fa5b.windows', False)
        
        self.item_layout.addStretch()
        self.scroll.setWidget(self.scroll_content)
        self.c_layout.addWidget(self.scroll)
        
        # Footer (Progress + Button)
        self.progress = QProgressBar()
        self.progress.setFixedHeight(4)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet(f"QProgressBar {{ background: {Theme.BG_SECTION}; border-radius: 2px; }} QProgressBar::chunk {{ background: {Theme.ACCENT}; }}")
        self.progress.hide()
        self.c_layout.addWidget(self.progress)
        
        self.btn_action = QPushButton("Clean Selected")
        self.btn_action.setCursor(Qt.PointingHandCursor)
        self.btn_action.setFixedHeight(36)
        self.btn_action.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.ACCENT};
                color: {Theme.BG_MAIN};
                border-radius: 8px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{ background-color: {Theme.TEXT_MAIN}; }}
            QPushButton:disabled {{ background-color: {Theme.BG_SECTION}; color: {Theme.TEXT_DIM}; }}
        """)
        self.btn_action.clicked.connect(self._start_clean)
        self.c_layout.addWidget(self.btn_action)
        
        log_debug("CleanupDialog: UI constructed")
        
        # Drag Logic
        self._drag_pos = None

    def showEvent(self, event):
        from ..gui import log_debug
        log_debug("CleanupDialog: showEvent triggered")
        super().showEvent(event)
        QTimer.singleShot(100, self._start_scan) # Run scan after showing

    def _start_scan(self):
        """Scan categories for sizes and hide empty ones."""
        self.btn_action.setText("Analyzing...")
        self.btn_action.setEnabled(False)
        for key in self.checks.keys():
            size_str, raw_bytes = self.cleaner.get_size_for_category(key)
            
            if key in self.size_labels:
                self.size_labels[key].setText(size_str)
            
            # Hide if 0 bytes
            if key in self.row_containers:
                is_visible = raw_bytes > 0
                self.row_containers[key].setVisible(is_visible)
                
        self.btn_action.setText("Clean Selected")
        self.btn_action.setEnabled(True)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
            
    def _add_item(self, key, text, icon_name, tooltip, checked=False):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        chk = QCheckBox(text)
        chk.setChecked(checked)
        chk.setToolTip(tooltip)
    def _add_item(self, key, text, icon_name, checked=False):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Get info from cleaner
        info = self.cleaner.get_info(key)
        tooltip = f"{info['desc']}\n\n[Risk] {info['risk']}"
        
        chk = QCheckBox(text)
        chk.setChecked(checked)
        chk.setToolTip(tooltip)
        chk.setCursor(Qt.PointingHandCursor) # Make text area feel interactive
        chk.setStyleSheet(f"""
            QCheckBox {{ color: {Theme.TEXT_MAIN}; spacing: 8px; font-size: 11px; }}
            QCheckBox::indicator {{ width: 14px; height: 14px; border-radius: 4px; border: 1px solid {Theme.TEXT_DIM}; }}
            QCheckBox::indicator:checked {{ background-color: {Theme.ACCENT}; border: 1px solid {Theme.ACCENT}; }}
        """)
        
        icon = QLabel()
        icon.setPixmap(qta.icon(icon_name, color=Theme.TEXT_DIM).pixmap(14, 14))
        icon.setToolTip("Click to open folder")
        
        # Open folder on click (simplified for now via QPushButton overlay or similar)
        # Actually, let's just use a dedicated button for "Open" to be explicit
        btn_open = QPushButton()
        btn_open.setToolTip("Open folder")
        btn_open.setIcon(qta.icon('fa5s.folder-open', color=Theme.TEXT_DIM))
        btn_open.setFixedSize(20, 20)
        btn_open.setFlat(True)
        btn_open.setStyleSheet("QPushButton { border: none; background: transparent; } QPushButton:hover { color: white; }")
        btn_open.clicked.connect(lambda: self._open_path(key))
        
        layout.addWidget(icon)
        layout.addWidget(chk, 1) # Expand
        
        lbl_size = QLabel("...")
        lbl_size.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: 10px; font-family: Consolas;")
        layout.addWidget(lbl_size)
        layout.addWidget(btn_open)
        
        self.item_layout.addWidget(container)
        self.checks[key] = chk
        self.size_labels[key] = lbl_size
        self.row_containers[key] = container

    def _open_path(self, key):
        """Open category folder."""
        import os
        path = self.cleaner.get_path(key)
        if path and os.path.exists(path):
            os.startfile(path)

    def _start_clean(self):
        active_tasks = [k for k, v in self.checks.items() if v.isChecked()]
        if not active_tasks: return
        
        self.btn_action.setText("Cleaning...")
        self.btn_action.setDisabled(True)
        self.progress.show()
        self.progress.setRange(0, 0) # Indeterminate
        
        self.worker = CleanupWorker(self.cleaner, active_tasks)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()
        
    def _on_finished(self):
        self.progress.hide()
        self.btn_action.setText("Done!")
        self.btn_action.setDisabled(False)
        self.btn_action.setStyleSheet(f"background-color: {Theme.GREEN}; color: white; border-radius: 8px;")
        
        # Auto-close after 1 second
        QTimer.singleShot(1000, self.accept)
