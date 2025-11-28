"""UI styling and theme configuration."""
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

# Theme configuration (flatly has crisp, high-contrast colors)
THEME = "flatly"  # Options: cosmo, flatly, journal, litera, lumen, minty, pulse, sandstone, united, yeti

# Color scheme
COLORS = {
    # Bootstrap 5 vibrant palette
    "primary": "#0d6efd",   # sharp blue
    "success": "#198754",   # sharp green
    "warning": "#ffc107",
    "danger":  "#dc3545",   # sharp red
    "info":    "#0dcaf0",
    "low_stock": "#dc3545",
    "near_expiry": "#ffc107",
    "normal": "#198754"
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
    # Subtle app background for SaaS-like feel
    style.configure(
        "Overlay.TFrame",
        background="#f2f5f9",
    )
    # Clean white card for login panel
    style.configure(
        "LoginCard.TFrame",
        background="#ffffff",
        borderwidth=0,
        relief="flat",
    )
    style.configure(
        "LoginTitle.TLabel",
        font=("Helvetica", 18, "bold")
    )
    # Make primary/success/danger buttons feel punchier
    style.configure("TButton", padding=6)
    return style

