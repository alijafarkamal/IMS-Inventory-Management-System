"""UI styling and theme configuration."""
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

# Theme configuration
THEME = "cosmo"  # Options: cosmo, flatly, journal, litera, lumen, minty, pulse, sandstone, united, yeti

# Color scheme
COLORS = {
    "primary": "#007bff",
    "success": "#28a745",
    "warning": "#ffc107",
    "danger": "#dc3545",
    "info": "#17a2b8",
    "low_stock": "#dc3545",
    "near_expiry": "#ffc107",
    "normal": "#28a745"
}

# Fonts
FONTS = {
    "title": ("Helvetica", 18, "bold"),
    "heading": ("Helvetica", 14, "bold"),
    "normal": ("Helvetica", 10),
    "small": ("Helvetica", 8)
}

def apply_theme(root):
    """Apply ttkbootstrap theme to root window."""
    style = ttk.Style(theme=THEME)
    return style

