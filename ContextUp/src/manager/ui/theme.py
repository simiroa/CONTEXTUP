"""
Centralized UI theme constants for ContextUp Manager.
Extreme Minimal Design: 3 colors only (Gray, Red, Blue)
"""

class Theme:
    # --- Backgrounds ---
    BG_MAIN = ("#f0f2f5", "#050505")         # Main background (Solid Black)
    BG_SIDEBAR = ("#e3e6e8", "#050505")      # Sidebar (Solid Black)
    BG_SIDEBAR_FOOTER = ("#e3e6e8", "#050505")
    BG_CARD = ("#ffffff", "#121212")         # Cards (Slightly Brighter for contrast)
    BG_DANGER_CARD = ("#fee2e2", "#1a0808")  # Subdued danger
    
    # --- Action Colors: MINIMAL PALETTE ---
    
    # PRIMARY: Only for Apply Changes button
    PRIMARY = ("#3b7ecb", "#3b7ecb")
    PRIMARY_HOVER = ("#2e629f", "#2e629f")
    
    # STANDARD: Darker Grey for standard buttons
    STANDARD = ("#4a4a4a", "#1a1a1a")
    STANDARD_HOVER = ("#5a5a5a", "#222222")
    
    # DANGER: Subdued Red
    DANGER = ("#8c2e2e", "#4a1a1a")
    DANGER_HOVER = ("#a63a3a", "#5a2222")
    
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
