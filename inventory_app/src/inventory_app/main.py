"""Main application entry point."""
import sys
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from inventory_app.ui.styles import apply_theme, THEME
from inventory_app.ui.login import LoginWindow
from inventory_app.ui.dashboard import DashboardWindow
from inventory_app.ui.products import ProductsWindow
from inventory_app.ui.orders import OrdersWindow
from inventory_app.ui.reports import ReportsWindow
from inventory_app.services.scheduler_service import start_scheduler, stop_scheduler
from inventory_app.utils.logging import logger
from inventory_app.models.user import User
from inventory_app.db.session import get_db_session
from inventory_app.startup import bootstrap
from inventory_app.config import ROLE_ADMIN, ROLE_MANAGER, ROLE_STAFF


class InventoryApp:
    """Main application class."""
    
    def __init__(self):
        """Initialize the application."""
        # Create root window
        self.root = ttk.Window(themename=THEME)
        self.root.title("Inventory Management System")
        self.root.geometry("1200x800")
        apply_theme(self.root)
        
        self.current_user: User | None = None
        self.current_screen = None
        
        start_scheduler()

        # Setup Notebook (tabbed interface) - create but populate after login
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=BOTH, expand=TRUE)
        self.screens = {}

        # Show in-window login overlay after bootstrap
        self.show_login_overlay()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def show_login(self):
        """Legacy: Show separate login window (unused)."""
        LoginWindow(self.root, on_success_callback=self.on_login_success)

    def show_login_overlay(self):
        """Show a centered login box on the main window (no separate window)."""
        # Full overlay frame to sit above notebook (which is empty initially)
        self.login_overlay = ttk.Frame(self.root, style="Overlay.TFrame", padding=10)
        self.login_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Centered panel
        panel = ttk.Frame(self.login_overlay, style="LoginCard.TFrame", padding=24)
        panel.place(relx=0.5, rely=0.45, anchor="center")

        ttk.Label(panel, text="Inventory Management System", style="LoginTitle.TLabel").pack(pady=(0, 16))

        form = ttk.Frame(panel)
        form.pack()

        ttk.Label(form, text="Username:", width=12).grid(row=0, column=0, sticky=E, padx=6, pady=6)
        self.login_username = ttk.Entry(form, width=28)
        self.login_username.grid(row=0, column=1, padx=6, pady=6)
        # Do not prefill username

        ttk.Label(form, text="Password:", width=12).grid(row=1, column=0, sticky=E, padx=6, pady=6)
        self.login_password = ttk.Entry(form, width=28, show="*")
        self.login_password.grid(row=1, column=1, padx=6, pady=6)
        # Do not prefill password

        # Show/Hide password toggle
        toggles = ttk.Frame(panel)
        toggles.pack(fill=X)
        self.show_pw_var = ttk.BooleanVar(value=False)
        show_pw = ttk.Checkbutton(
            toggles,
            text="Show password",
            variable=self.show_pw_var,
            command=lambda: self.login_password.configure(show="" if self.show_pw_var.get() else "*")
        )
        show_pw.pack(anchor=W)

        self.login_error = ttk.Label(panel, text="", foreground="red")
        self.login_error.pack(pady=(8, 0))

        btns = ttk.Frame(panel)
        btns.pack(pady=14)
        ttk.Button(btns, text="Sign In", bootstyle=PRIMARY, command=self.handle_login, width=12).pack(side=LEFT, padx=6)
        ttk.Button(btns, text="Exit", bootstyle=DANGER, command=self.on_closing, width=10).pack(side=LEFT, padx=6)

        # Enter-to-submit
        self.login_password.bind("<Return>", lambda e: self.handle_login())
    
    def on_login_success(self, user: User):
        """Handle successful login from overlay or legacy window."""
        self.current_user = user
        logger.info(f"User {user.username} logged in")
        # Remove overlay if present
        if hasattr(self, "login_overlay") and self.login_overlay is not None:
            try:
                self.login_overlay.destroy()
            except Exception:
                pass
            self.login_overlay = None
        # Initialize tabs if not already created
        if not self.screens:
            self.init_tabs()
        else:
            self.show_dashboard()

    # Admin bootstrap moved to startup module

    def handle_login(self):
        """Authenticate from overlay and proceed."""
        username = self.login_username.get().strip() if hasattr(self, "login_username") else ""
        password = self.login_password.get() if hasattr(self, "login_password") else ""
        if not username or not password:
            if hasattr(self, "login_error"):
                self.login_error.config(text="Please enter username and password")
            return
        db = None
        try:
            db = get_db_session()
            from inventory_app.services.auth_service import authenticate_user
            user = authenticate_user(db, username, password)
            if user:
                self.on_login_success(user)
            else:
                if hasattr(self, "login_error"):
                    self.login_error.config(text="Invalid username or password")
        except Exception as e:
            logger.error(f"Login error: {e}")
            if hasattr(self, "login_error"):
                self.login_error.config(text=f"Error: {str(e)}")
        finally:
            if db:
                try:
                    db.close()
                except Exception:
                    pass
    
    def show_dashboard(self):
        # Retained for compatibility; selects dashboard tab
        self.select_tab("dashboard")
    
    def navigate(self, screen_name: str):
        # Map old navigation calls to tab selection
        self.select_tab(screen_name)
    
    def clear_screen(self):
        """Clear current screen."""
        if self.current_screen:
            try:
                self.current_screen.destroy()
            except:
                pass
            self.current_screen = None

    def init_tabs(self):
        """Initialize tabs for dashboard, products, orders, reports."""
        # Determine visible tabs based on role
        role = getattr(self.current_user, "role", None)
        tab_defs = []
        if role == ROLE_ADMIN:
            tab_defs = [
                ("dashboard", "Dashboard", DashboardWindow),
                ("products", "Products", ProductsWindow),
                ("orders", "Orders", OrdersWindow),
                ("reports", "Reports", ReportsWindow)
            ]
        elif role == ROLE_MANAGER:
            tab_defs = [
                ("dashboard", "Dashboard", DashboardWindow),
                ("products", "Products", ProductsWindow),
                ("orders", "Orders", OrdersWindow),
                ("reports", "Reports", ReportsWindow)
            ]
        elif role == ROLE_STAFF:
            # Staff get a limited set of tabs
            tab_defs = [
                ("dashboard", "Dashboard", DashboardWindow),
                ("products", "Products", ProductsWindow),
                ("orders", "Orders", OrdersWindow)
            ]
        else:
            # Unknown roles fallback to minimal tabs
            tab_defs = [
                ("dashboard", "Dashboard", DashboardWindow),
                ("products", "Products", ProductsWindow),
                ("orders", "Orders", OrdersWindow)
            ]
        for key, label, cls in tab_defs:
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=label)
            # Instantiate screen into frame
            instance = cls(frame, self.current_user, on_navigate_callback=self.navigate)
            self.screens[key] = instance
        # Select dashboard by default
        self.select_tab("dashboard")

    def select_tab(self, name: str):
        """Select tab by logical name using index lookup."""
        order = ["dashboard", "products", "orders", "reports"]
        if name not in order:
            logger.warning(f"Unknown tab: {name}")
            return
        idx = order.index(name)
        tabs = self.notebook.tabs()
        if idx < len(tabs):
            self.notebook.select(tabs[idx])
        else:
            logger.error(f"Tab index {idx} out of range for {name}")
    
    def on_closing(self):
        """Handle window closing."""
        stop_scheduler()
        self.root.destroy()
        sys.exit(0)
    
    def run(self):
        """Run the application."""
        self.root.mainloop()


def main():
    """Main entry point."""
    try:
        # Composition root bootstrap: init DB, ensure admin
        bootstrap()
        app = InventoryApp()
        app.run()
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise


if __name__ == "__main__":
    main()

