"""Dashboard screen."""
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from datetime import datetime
from inventory_app.db.session import get_db_session
from inventory_app.services.inventory_service import get_low_stock_items
from inventory_app.models.order import Order
from inventory_app.models.product import Product
from inventory_app.utils.logging import logger


class DashboardWindow:
    """Main dashboard window."""
    
    def __init__(self, parent, user, on_navigate_callback):
        """
        Initialize dashboard.
        
        Args:
            parent: Parent widget
            user: Current user
            on_navigate_callback: Callback for navigation (screen_name)
        """
        self.parent = parent
        self.user = user
        self.on_navigate = on_navigate_callback
        
        # Main frame
        self.frame = ttk.Frame(parent, padding=10)
        self.frame.pack(fill=BOTH, expand=TRUE)
        
        # Header
        header_frame = ttk.Frame(self.frame)
        header_frame.pack(fill=X, pady=(0, 20))
        
        title_label = ttk.Label(
            header_frame,
            text="Dashboard",
            font=("Helvetica", 18, "bold")
        )
        title_label.pack(side=LEFT)
        
        user_label = ttk.Label(
            header_frame,
            text=f"Welcome, {user.full_name} ({user.role})",
            font=("Helvetica", 10)
        )
        user_label.pack(side=RIGHT)
        
        # Refresh button
        ttk.Button(
            header_frame,
            text="Refresh",
            command=self.refresh_data,
            bootstyle=SECONDARY
        ).pack(side=RIGHT, padx=10)
        
        # Quick stats frame
        stats_frame = ttk.Labelframe(self.frame, text="Quick Statistics", padding=10)
        stats_frame.pack(fill=X, pady=10)
        
        self.stats_container = ttk.Frame(stats_frame)
        self.stats_container.pack(fill=X)
        
        # Low stock alerts
        alerts_frame = ttk.Labelframe(self.frame, text="Low Stock Alerts", padding=10)
        alerts_frame.pack(fill=BOTH, expand=TRUE, pady=10)
        
        # Treeview for low stock items
        columns = ("Product", "SKU", "Warehouse", "Quantity", "Threshold")
        self.low_stock_tree = ttk.Treeview(
            alerts_frame,
            columns=columns,
            show="headings",
            height=8
        )
        
        for col in columns:
            self.low_stock_tree.heading(col, text=col)
            self.low_stock_tree.column(col, width=150)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(alerts_frame, orient=VERTICAL, command=self.low_stock_tree.yview)
        self.low_stock_tree.configure(yscrollcommand=scrollbar.set)
        
        self.low_stock_tree.pack(side=LEFT, fill=BOTH, expand=TRUE)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        # Color code rows
        self.low_stock_tree.tag_configure("low", foreground="red")
        
        # Recent transactions
        recent_frame = ttk.Labelframe(self.frame, text="Recent Transactions", padding=10)
        recent_frame.pack(fill=BOTH, expand=TRUE, pady=10)
        
        recent_columns = ("Date", "Type", "Order #", "Amount", "Status")
        self.recent_tree = ttk.Treeview(
            recent_frame,
            columns=recent_columns,
            show="headings",
            height=8
        )
        
        for col in recent_columns:
            self.recent_tree.heading(col, text=col)
            self.recent_tree.column(col, width=120)
        
        recent_scrollbar = ttk.Scrollbar(recent_frame, orient=VERTICAL, command=self.recent_tree.yview)
        self.recent_tree.configure(yscrollcommand=recent_scrollbar.set)
        
        self.recent_tree.pack(side=LEFT, fill=BOTH, expand=TRUE)
        recent_scrollbar.pack(side=RIGHT, fill=Y)
        
        # Quick actions removed in favor of tabbed navigation
        
        # Refresh data
        self.refresh_data()
        # Listen for global orders-updated events so dashboard refreshes
        try:
            root = self.frame.winfo_toplevel()
            root.bind("<<OrdersUpdated>>", lambda e: self.refresh_data())
        except Exception:
            pass
    
    def refresh_data(self):
        """Refresh dashboard data."""
        db = get_db_session()
        try:
            # Update low stock items
            for item in self.low_stock_tree.get_children():
                self.low_stock_tree.delete(item)
            
            low_stock = get_low_stock_items(db)
            for item in low_stock[:20]:  # Show top 20
                self.low_stock_tree.insert(
                    "",
                    END,
                    values=(
                        item["product_name"],
                        item["sku"],
                        item["warehouse_name"],
                        item["quantity"],
                        item["threshold"]
                    ),
                    tags=("low",)
                )
            
            # Update recent transactions
            for item in self.recent_tree.get_children():
                self.recent_tree.delete(item)
            
            recent_orders = db.query(Order).order_by(Order.order_date.desc()).limit(20).all()
            for order in recent_orders:
                self.recent_tree.insert(
                    "",
                    END,
                    values=(
                        order.order_date.strftime("%Y-%m-%d %H:%M"),
                        order.order_type,
                        order.order_number,
                        f"${order.total_amount:.2f}",
                        order.status
                    )
                )
            
            # Update stats
            for widget in self.stats_container.winfo_children():
                widget.destroy()
            
            total_products = db.query(Product).filter(Product.is_active == True).count()
            total_orders_today = db.query(Order).filter(
                Order.order_date >= datetime.now().replace(hour=0, minute=0, second=0)
            ).count()
            
            ttk.Label(
                self.stats_container,
                text=f"Active Products: {total_products}",
                font=("Helvetica", 12)
            ).pack(side=LEFT, padx=20)
            
            ttk.Label(
                self.stats_container,
                text=f"Orders Today: {total_orders_today}",
                font=("Helvetica", 12)
            ).pack(side=LEFT, padx=20)
            
            ttk.Label(
                self.stats_container,
                text=f"Low Stock Items: {len(low_stock)}",
                font=("Helvetica", 12),
                foreground="red" if low_stock else "green"
            ).pack(side=LEFT, padx=20)
            
        except Exception as e:
            logger.error(f"Error refreshing dashboard: {e}")
        finally:
            db.close()
    
    def destroy(self):
        """Clean up."""
        self.frame.destroy()

