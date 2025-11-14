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


class InventoryApp:
    """Main application class."""
    
    def __init__(self):
        """Initialize the application."""
        # Create root window
        self.root = ttk.Window(themename="cosmo")
        self.root.title("Inventory Management System")
        self.root.geometry("1200x800")
        
        # Apply theme
        apply_theme(self.root)
        
        # Current user
        self.current_user: User | None = None
        
        # Current screen
        self.current_screen = None
        
        # Start scheduler
        start_scheduler()
        
        # Show login
        self.show_login()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def show_login(self):
        """Show login window."""
        LoginWindow(self.root, on_success_callback=self.on_login_success)
    
    def on_login_success(self, user: User):
        """Handle successful login."""
        self.current_user = user
        logger.info(f"User {user.username} logged in")
        self.show_dashboard()
    
    def show_dashboard(self):
        """Show dashboard."""
        self.clear_screen()
        self.current_screen = DashboardWindow(
            self.root,
            self.current_user,
            on_navigate_callback=self.navigate
        )
    
    def navigate(self, screen_name: str):
        """Navigate to a screen."""
        self.clear_screen()
        
        if screen_name == "dashboard":
            self.show_dashboard()
        elif screen_name == "products":
            self.current_screen = ProductsWindow(
                self.root,
                self.current_user,
                on_navigate_callback=self.navigate
            )
        elif screen_name == "orders":
            self.current_screen = OrdersWindow(
                self.root,
                self.current_user,
                on_navigate_callback=self.navigate
            )
        elif screen_name == "reports":
            self.current_screen = ReportsWindow(
                self.root,
                self.current_user,
                on_navigate_callback=self.navigate
            )
        else:
            logger.warning(f"Unknown screen: {screen_name}")
    
    def clear_screen(self):
        """Clear current screen."""
        if self.current_screen:
            try:
                self.current_screen.destroy()
            except:
                pass
            self.current_screen = None
    
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

