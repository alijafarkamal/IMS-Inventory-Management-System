"""Login screen."""
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from inventory_app.services.auth_service import authenticate_user
from inventory_app.db.session import get_db_session
from inventory_app.utils.logging import logger


class LoginWindow:
    """Login window for user authentication."""
    
    def __init__(self, root, on_success_callback):
        """
        Initialize login window.
        
        Args:
            root: Tkinter root window
            on_success_callback: Callback function called with (user) on successful login
        """
        self.root = root
        self.on_success = on_success_callback
        self.user = None
        
        # Create login window
        self.window = ttk.Toplevel(root)
        self.window.title("Login")
        self.window.geometry("400x250")
        self.window.resizable(False, False)
        self.window.transient(root)
        self.window.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(self.window, padding=20)
        main_frame.pack(fill=BOTH, expand=TRUE)
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text="Inventory Management System",
            font=("Helvetica", 16, "bold")
        )
        title_label.pack(pady=(0, 30))
        
        # Username
        username_frame = ttk.Frame(main_frame)
        username_frame.pack(fill=X, pady=10)
        
        ttk.Label(username_frame, text="Username:", width=12).pack(side=LEFT, padx=5)
        self.username_entry = ttk.Entry(username_frame, width=25)
        self.username_entry.pack(side=LEFT, padx=5, fill=X, expand=TRUE)
        self.username_entry.focus()
        
        # Password
        password_frame = ttk.Frame(main_frame)
        password_frame.pack(fill=X, pady=10)
        
        ttk.Label(password_frame, text="Password:", width=12).pack(side=LEFT, padx=5)
        self.password_entry = ttk.Entry(password_frame, width=25, show="*")
        self.password_entry.pack(side=LEFT, padx=5, fill=X, expand=TRUE)
        
        # Bind Enter key
        self.password_entry.bind("<Return>", lambda e: self.login())
        
        # Error label
        self.error_label = ttk.Label(
            main_frame,
            text="",
            foreground="red",
            font=("Helvetica", 9)
        )
        self.error_label.pack(pady=10)
        
        # Login button
        login_btn = ttk.Button(
            main_frame,
            text="Login",
            command=self.login,
            bootstyle=PRIMARY,
            width=20
        )
        login_btn.pack(pady=20)
        
        # Focus on username
        self.username_entry.focus()
    
    def login(self):
        """Handle login."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username or not password:
            self.error_label.config(text="Please enter username and password")
            return
        
        db = get_db_session()
        try:
            user = authenticate_user(db, username, password)
            if user:
                self.user = user
                self.error_label.config(text="", foreground="green")
                self.error_label.config(text="Login successful!")
                self.window.after(500, self.close_and_callback)
            else:
                self.error_label.config(text="Invalid username or password", foreground="red")
        except Exception as e:
            logger.error(f"Login error: {e}")
            self.error_label.config(text=f"Error: {str(e)}", foreground="red")
        finally:
            db.close()
    
    def close_and_callback(self):
        """Close window and call success callback."""
        self.window.destroy()
        if self.user:
            self.on_success(self.user)

