"""
Centralized UI theme constants for ContextUp Manager.
Extreme Minimal Design: 3 colors only (Gray, Red, Blue)
"""

class Theme:
    # --- Backgrounds ---
    BG_MAIN = ("#f0f2f5", "#0d0d0d")         # Main background
    BG_SIDEBAR = ("#e3e6e8", "#080808")      # Sidebar
    BG_SIDEBAR_FOOTER = ("#e3e6e8", "#080808")
    BG_CARD = ("#ffffff", "#161616")         # Cards
    BG_DANGER_CARD = ("#fee2e2", "#1a0d0d")  # Subtle danger bg
    
    # --- Action Colors: MINIMAL PALETTE ---
    
    # PRIMARY: Only for Apply Changes button
    PRIMARY = ("#3b7ecb", "#3b7ecb")
    PRIMARY_HOVER = ("#2e629f", "#2e629f")
    
    # GRAY: ALL standard buttons (Check, Restart, Upgrade, Export, Import, Backup, Refresh, Edit, Add, Save)
    STANDARD = ("#4a4a4a", "#3a3a3a")
    STANDARD_HOVER = ("#5a5a5a", "#4a4a4a")
    
    # DANGER: ONLY destructive actions (Reset, Delete, Stop, Factory Reset)
    DANGER = ("#8c2e2e", "#6b2323")
    DANGER_HOVER = ("#a63a3a", "#7d2a2a")
    
    # --- Legacy aliases for compatibility ---
    SUCCESS = STANDARD
    SUCCESS_HOVER = STANDARD_HOVER
    WARNING = STANDARD
    WARNING_HOVER = STANDARD_HOVER
    NEUTRAL = STANDARD
    NEUTRAL_HOVER = STANDARD_HOVER
    GRAY_BTN = STANDARD
    GRAY_BTN_HOVER = STANDARD_HOVER
    
    # --- Text Colors ---
    TEXT_MAIN = ("gray10", "#e0e0e0")
    TEXT_DIM = ("gray40", "#888888")
    TEXT_DANGER = "#a66" #66")                   # Soft red for errors
    TEXT_SUCCESS = TEXT_DIM                  # No green - use gray
    
    # --- Accent ---
    ACCENT = PRIMARY
