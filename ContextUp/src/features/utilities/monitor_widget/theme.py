"""
Monitor Widget Theme - Color constants and utility functions.
"""


class Theme:
    """Theme constants for consistent styling across the widget."""

    # Background colors
    BG_MAIN = "#1e1e24"
    BG_SIDEBAR = "#25252b"
    BG_SECTION = "#2d2d34"

    # Text colors
    TEXT_MAIN = "#ffffff"
    TEXT_DIM = "#8b8b94"

    # Accent colors
    ACCENT = "#ffffff"  # White
    RED = "#ed4245"
    ORANGE = "#faa61a"
    GREEN = "#3ba55c"
    BLUE = "#5865f2"
    PURPLE = "#9b59b6"

    @staticmethod
    def get_color(percent: float) -> str:
        """Get color based on resource usage percentage."""
        if percent >= 90:
            return Theme.RED
        if percent >= 70:
            return Theme.ORANGE
        if percent >= 40:
            return "#ffff00"  # Yellow
        return Theme.GREEN

    @staticmethod
    def get_bg_section(alpha: float = 0.5) -> str:
        """Get semi-transparent section background."""
        return Theme.hex_to_rgba(Theme.BG_SECTION, alpha)

    @staticmethod
    def hex_to_rgba(hex_color: str, alpha: float) -> str:
        """Convert hex color to rgba string."""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"rgba({r}, {g}, {b}, {alpha})"
