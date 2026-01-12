"""
ServerPage - Page showing local servers/ports.
"""
import os
import webbrowser
import qtawesome as qta
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QScrollArea, QLineEdit
)

from ..theme import Theme
from ..engine import SystemStats
from ..components.base_page import BasePage


class ServerPage(BasePage):
    """Page showing local servers and open ports."""
    
    def __init__(self, engine, process_manager, parent=None):
        super().__init__("Local Servers", parent, add_stretch=False)
        self.engine = engine
        self.process_manager = process_manager
        self._all_points = []
        
        # Search Box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search port or name...")
        self.search_box.setStyleSheet(f"""
            QLineEdit {{
                background: {Theme.BG_SECTION}; 
                color: {Theme.TEXT_MAIN}; 
                border: 1px solid {Theme.BG_SIDEBAR}; 
                border-radius: 4px; 
                padding: 4px 8px;
            }}
            QLineEdit:focus {{ border-color: {Theme.ACCENT}; }}
        """)
        self.search_box.textChanged.connect(self._filter_list)
        self.content_area.addWidget(self.search_box)
        
        # Scrollable list area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet(f"""
            QScrollArea {{ background: transparent; border: none; }}
            QScrollBar:vertical {{
                background: rgba(0,0,0,0.05);
                width: 6px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {Theme.BG_SECTION};
                min-height: 30px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {Theme.ACCENT};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        self.list_layout = QVBoxLayout(self.scroll_content)
        self.list_layout.setContentsMargins(0, 0, 5, 0)
        self.list_layout.setSpacing(4)
        self.list_layout.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.scroll_content)
        self.content_area.addWidget(self.scroll, 1)
        
    def _filter_list(self, query):
        self._rebuild_list(query.lower())
        
    def _rebuild_list(self, filter_query=""):
        """Rebuild the server list."""
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            
        if not self._all_points:
            lbl = QLabel("Searching for active ports...")
            lbl.setStyleSheet(f"color:{Theme.TEXT_DIM}")
            self.list_layout.addWidget(lbl)
            return
        
        count = 0
        for sp in self._all_points:
            # Filter check (include server_type in search)
            if filter_query:
                search_text = f"{sp.port} {sp.name} {sp.server_type}".lower()
                if filter_query not in search_text:
                    continue
            
            count += 1
            card = QFrame()
            card.setStyleSheet("background: transparent;")
            card.setFixedHeight(24)
            h = QHBoxLayout(card)
            h.setContentsMargins(4, 0, 4, 0)
            h.setSpacing(4)
            
            # Server type badge with color
            type_colors = {
                'comfyui': '#ff6b00', 'docker': '#2496ed', 'jupyter': '#f37626',
                'vite': '#646cff', 'webpack': '#8dd6f9', 'react': '#61dafb',
                'vue': '#42b883', 'angular': '#dd1b16', 'flask': '#ffffff',
                'django': '#092e20', 'fastapi': '#009688', 'nodejs': '#339933',
                'streamlit': '#ff4b4b', 'gradio': '#ff7c00',
                'unity': '#ffffff', 'unreal': '#313131', 'blender': '#f5792a',
                'webserver': '#888888'
            }
            
            # Server type indicator (small bar instead of text)
            if sp.server_type:
                badge_color = type_colors.get(sp.server_type, Theme.TEXT_DIM)
                indicator = QFrame()
                indicator.setFixedSize(3, 14)
                indicator.setStyleSheet(f"background-color: {badge_color}; border-radius: 1px;")
                h.addWidget(indicator)
            else:
                # Add spacing if no type to align with typed entries
                spacer = QFrame()
                spacer.setFixedSize(3, 14)
                spacer.setStyleSheet("background: transparent;")
                h.addWidget(spacer)
            
            # Port number
            lbl_port = QLabel(f":{sp.port}")
            lbl_port.setFixedWidth(45)
            lbl_port.setStyleSheet(f"color: {Theme.ACCENT}; font-weight: bold; font-family: 'Consolas'; font-size: 11px;")
            h.addWidget(lbl_port)
            
            # Process name
            display_name = sp.name
            if len(display_name) > 18:
                display_name = display_name[:16] + ".."
            lbl_name = QLabel(display_name)
            lbl_name.setStyleSheet(f"color: {Theme.TEXT_MAIN}; font-size: 11px;")
            lbl_name.setToolTip(f"PID: {sp.pid}\nPath: {sp.exe_path}" if sp.exe_path else f"PID: {sp.pid}")
            h.addWidget(lbl_name, 1)
            
            # Link/Open Icon
            btn_open = QPushButton()
            btn_open.setIcon(qta.icon('fa5s.external-link-alt', color=Theme.ACCENT))
            btn_open.setFixedSize(18, 18)
            btn_open.setCursor(Qt.PointingHandCursor)
            btn_open.setStyleSheet("background: transparent; border: none;")
            btn_open.clicked.connect(lambda checked=False, u=f"http://localhost:{sp.port}": webbrowser.open(u))
            h.addWidget(btn_open)
            
            # Kill Button
            btn_kill = QPushButton()
            btn_kill.setIcon(qta.icon('fa5s.times-circle', color=Theme.RED))
            btn_kill.setFixedSize(18, 18)
            btn_kill.setCursor(Qt.PointingHandCursor)
            btn_kill.setStyleSheet("background: transparent; border: none;")
            btn_kill.clicked.connect(lambda p=sp.pid: self.process_manager.kill_process(p))
            h.addWidget(btn_kill)
            
            self.list_layout.addWidget(card)
            
        if count == 0:
            lbl = QLabel("No servers match filter.")
            lbl.setStyleSheet(f"color:{Theme.TEXT_DIM}")
            self.list_layout.addWidget(lbl)
        
    def update_stats(self, stats: SystemStats):
        """Update server list."""
        points = stats.server_points
        
        # Anti-flicker
        if not points and self._all_points:
            return
        
        if points == self._all_points:
            return

        self._all_points = points
        filter_text = self.search_box.text().lower() if self.search_box.text() else ""
        self._rebuild_list(filter_text)
