"""Main application entry point."""
import sys
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from inventory_app.ui.styles import apply_theme
from inventory_app.ui.login import LoginWindow
from inventory_app.ui.dashboard import DashboardWindow
from inventory_app.ui.products import ProductsWindow
from inventory_app.ui.orders import OrdersWindow
from inventory_app.ui.reports import ReportsWindow
from inventory_app.services.scheduler_service import start_scheduler, stop_scheduler
from inventory_app.utils.logging import logger
from inventory_app.models.user import User
from inventory_app.db.session import get_db_session
from inventory_app.services.auth_service import create_user


class InventoryApp:
    """Main application class."""
    
    def __init__(self):
        """Initialize the application."""
        # Create root window
        self.root = ttk.Window(themename="cosmo")
        self.root.title("Inventory Management System")
        self.root.geometry("1200x800")
        apply_theme(self.root)
        
        self.current_user: User | None = None
        self.current_screen = None
        
        start_scheduler()

        # Setup Notebook (tabbed interface)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=BOTH, expand=TRUE)
        self.screens = {}

        # Auto-login: create or fetch admin then initialize tabs
        try:
            self.auto_login_admin()
            self.init_tabs()
        except Exception as e:
            logger.error(f"Auto-login failed: {e}")
            self.show_login()  # fallback
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def show_login(self):
        """Show login window."""
        LoginWindow(self.root, on_success_callback=self.on_login_success)
    
    def on_login_success(self, user: User):
        """Handle successful login."""
        self.current_user = user
        logger.info(f"User {user.username} logged in")
        # Initialize tabs if not already created
        if not self.screens:
            self.init_tabs()
        else:
            self.show_dashboard()

    def auto_login_admin(self):
        """Create or fetch the default admin user and proceed to dashboard without showing login."""
        db = None
        try:
            db = get_db_session()
            admin = db.query(User).filter(User.username == "admin").first()
            if not admin:
                # Create default admin
                create_user(
                    db,
                    username="admin",
                    password="admin123",
                    email="admin@inventory.local",
                    full_name="Administrator",
                    role="Admin"
                )
                admin = db.query(User).filter(User.username == "admin").first()

            if not admin:
                raise RuntimeError("Failed to create or retrieve admin user")
            # Set current user; tabs will be initialized after this call in __init__
            self.current_user = admin
            logger.info("Auto-login admin user established")
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
        tab_defs = [
            ("dashboard", "Dashboard", DashboardWindow),
            ("products", "Products", ProductsWindow),
            ("orders", "Orders", OrdersWindow),
            ("reports", "Reports", ReportsWindow)
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
        app = InventoryApp()
        app.run()
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise


if __name__ == "__main__":
    main()

