"""Orders management screen."""
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from decimal import Decimal
from datetime import datetime
from inventory_app.db.session import get_db_session
from inventory_app.services.order_service import create_order, get_orders
from inventory_app.services.product_service import search_products, get_all_suppliers
from inventory_app.services.inventory_service import get_all_warehouses, get_warehouse_stock
from inventory_app.config import ORDER_TYPE_SALE, ORDER_TYPE_PURCHASE, ORDER_TYPE_RETURN
from inventory_app.models.user import User
from inventory_app.utils.logging import logger


class OrdersWindow:
    """Orders management window."""
    
    def __init__(self, parent, user: User, on_navigate_callback):
        self.parent = parent
        self.user = user
        self.on_navigate = on_navigate_callback
        
        # Main frame
        self.frame = ttk.Frame(parent, padding=10)
        self.frame.pack(fill=BOTH, expand=TRUE)
        
        # Header
        header_frame = ttk.Frame(self.frame)
        header_frame.pack(fill=X, pady=(0, 10))
        
        ttk.Label(header_frame, text="Orders", font=("Helvetica", 18, "bold")).pack(side=LEFT)
        
        # Buttons
        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(fill=X, pady=10)
        
        ttk.Button(
            btn_frame,
            text="Create Sale Order",
            command=lambda: self.create_order_dialog(ORDER_TYPE_SALE),
            bootstyle=SUCCESS
        ).pack(side=LEFT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="Create Purchase Order",
            command=lambda: self.create_order_dialog(ORDER_TYPE_PURCHASE),
            bootstyle=PRIMARY
        ).pack(side=LEFT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="Create Return Order",
            command=lambda: self.create_order_dialog(ORDER_TYPE_RETURN),
            bootstyle=INFO
        ).pack(side=LEFT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="Refresh",
            command=self.refresh_orders,
            bootstyle=SECONDARY
        ).pack(side=LEFT, padx=5)
        
        # Orders table
        columns = ("Date", "Order #", "Type", "Party", "User", "Total", "Status")
        self.tree = ttk.Treeview(self.frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)
        
        scrollbar = ttk.Scrollbar(self.frame, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=LEFT, fill=BOTH, expand=TRUE)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        self.refresh_orders()
    
    def refresh_orders(self):
        """Refresh orders list."""
        db = get_db_session()
        try:
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            orders = get_orders(db)
            for order in orders:
                    # Determine party name (customer for sales/returns, supplier for purchases if available in notes)
                    party_name = "N/A"
                    try:
                        if hasattr(order, 'customer') and order.customer:
                            party_name = order.customer.name
                        elif order.order_type == ORDER_TYPE_PURCHASE and order.notes:
                            # notes can contain "[Supplier: Name]" appended by UI; extract it
                            note = order.notes
                            start = note.find("[Supplier:")
                            if start != -1:
                                end = note.find("]", start)
                                if end != -1:
                                    party_name = note[start+10:end].strip()
                    except Exception:
                        party_name = "N/A"

                    self.tree.insert(
                        "",
                        END,
                        values=(
                            order.order_date.strftime("%Y-%m-%d %H:%M"),
                            order.order_number,
                            order.order_type,
                            party_name,
                            order.user.full_name if order.user else "N/A",
                            f"${order.total_amount:.2f}",
                            order.status
                        )
                    )
        finally:
            db.close()
    
    def create_order_dialog(self, order_type: str):
        """Open create order dialog."""
        OrderDialog(self.frame, self.user, order_type, on_save=self.refresh_orders)
    
    def destroy(self):
        """Clean up."""
        self.frame.destroy()


class OrderDialog:
    """Create order dialog."""
    
    def __init__(self, parent, user: User, order_type: str, on_save=None):
        self.user = user
        self.order_type = order_type
        self.on_save = on_save
        self.items = []  # List of {product_id, quantity, unit_price, warehouse_id}
        
        self.window = ttk.Toplevel(parent)
        self.window.title(f"Create {order_type} Order")
        # Dynamically size to ~60% of screen width and 65% of screen height (minimum 1000x650)
        try:
            screen_w = self.window.winfo_screenwidth()
            screen_h = self.window.winfo_screenheight()
            target_w = max(1000, int(screen_w * 0.6))
            target_h = max(650, int(screen_h * 0.65))
            # Center the window
            x = int((screen_w - target_w) / 2)
            y = int((screen_h - target_h) / 2 * 0.9)  # slightly higher than true center
            self.window.geometry(f"{target_w}x{target_h}+{x}+{y}")
        except Exception:
            # Fallback to larger static size
            self.window.geometry("1000x650")
        self.window.transient(parent)
        self.window.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill=BOTH, expand=TRUE)

        # Party selection (Supplier for Purchase, Customer for Sale)
        party_frame = ttk.LabelFrame(main_frame, text="Party", padding=10)
        party_frame.pack(fill=X, pady=10)

        self.supplier_var = None
        self.customer_entry = None
        if order_type == ORDER_TYPE_PURCHASE:
            ttk.Label(party_frame, text="Supplier:").grid(row=0, column=0, sticky=W, padx=5)
            self.supplier_var = ttk.StringVar()
            self.supplier_combo = ttk.Combobox(party_frame, textvariable=self.supplier_var, width=30, state="readonly")
            self.supplier_combo.grid(row=0, column=1, padx=5)
            self.load_suppliers()
        elif order_type in (ORDER_TYPE_SALE, ORDER_TYPE_RETURN):
            # Use a combobox populated with existing customers (predefined options)
            ttk.Label(party_frame, text="Customer:").grid(row=0, column=0, sticky=W, padx=5)
            self.customer_var = ttk.StringVar()
            self.customer_combo = ttk.Combobox(party_frame, textvariable=self.customer_var, width=32, state="readonly")
            self.customer_combo.grid(row=0, column=1, padx=5)
            self.load_customers()

        # (Removed duplicate party block - first party_frame above handles supplier/customer)
        
        # Add item frame
        add_frame = ttk.LabelFrame(main_frame, text="Add Item", padding=10)
        add_frame.pack(fill=X, pady=10)
        
        # Product search
        ttk.Label(add_frame, text="Product:").grid(row=0, column=0, sticky=W, padx=5)
        self.product_var = ttk.StringVar()
        self.product_combo = ttk.Combobox(add_frame, textvariable=self.product_var, width=30)
        self.product_combo.grid(row=0, column=1, padx=5)
        self.product_combo.bind("<KeyRelease>", self.search_products)
        self.product_combo.bind("<<ComboboxSelected>>", self.update_stock_display)
        
        # Warehouse
        ttk.Label(add_frame, text="Warehouse:").grid(row=0, column=2, sticky=W, padx=5)
        self.warehouse_var = ttk.StringVar()
        self.warehouse_combo = ttk.Combobox(add_frame, textvariable=self.warehouse_var, width=20, state="readonly")
        self.warehouse_combo.grid(row=0, column=3, padx=5)
        self.warehouse_combo.bind("<<ComboboxSelected>>", self.update_stock_display)
        
        # Stock availability display (for sales orders)
        if order_type == ORDER_TYPE_SALE:
            self.stock_label = ttk.Label(add_frame, text="", foreground="blue", font=("Helvetica", 9))
            self.stock_label.grid(row=0, column=4, padx=5)
        
        # Quantity
        ttk.Label(add_frame, text="Quantity:").grid(row=1, column=0, sticky=W, padx=5, pady=5)
        self.quantity_entry = ttk.Entry(add_frame, width=15)
        self.quantity_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # Unit price
        ttk.Label(add_frame, text="Unit Price:").grid(row=1, column=2, sticky=W, padx=5, pady=5)
        self.price_entry = ttk.Entry(add_frame, width=15)
        self.price_entry.grid(row=1, column=3, padx=5, pady=5)
        
        ttk.Button(
            add_frame,
            text="Add Item",
            command=self.add_item,
            bootstyle=SUCCESS
        ).grid(row=1, column=4, padx=5, pady=5)
        
        # Items table
        items_frame = ttk.LabelFrame(main_frame, text="Order Items", padding=10)
        items_frame.pack(fill=BOTH, expand=TRUE, pady=10)
        
        item_columns = ("Product", "Warehouse", "Quantity", "Unit Price", "Subtotal")
        self.items_tree = ttk.Treeview(items_frame, columns=item_columns, show="headings", height=10)
        
        for col in item_columns:
            self.items_tree.heading(col, text=col)
            self.items_tree.column(col, width=150)
        
        items_scrollbar = ttk.Scrollbar(items_frame, orient=VERTICAL, command=self.items_tree.yview)
        self.items_tree.configure(yscrollcommand=items_scrollbar.set)
        
        self.items_tree.pack(side=LEFT, fill=BOTH, expand=TRUE)
        items_scrollbar.pack(side=RIGHT, fill=Y)
        
        # Remove item button
        ttk.Button(
            items_frame,
            text="Remove Selected",
            command=self.remove_item,
            bootstyle=DANGER
        ).pack(pady=5)
        
        # Total and notes
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=X, pady=10)
        
        self.total_label = ttk.Label(bottom_frame, text="Total: $0.00", font=("Helvetica", 12, "bold"))
        self.total_label.pack(side=LEFT, padx=10)
        
        ttk.Label(bottom_frame, text="Notes:").pack(side=LEFT, padx=10)
        self.notes_entry = ttk.Entry(bottom_frame, width=40)
        self.notes_entry.pack(side=LEFT, padx=5, fill=X, expand=TRUE)
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=X, pady=10)
        
        ttk.Button(
            btn_frame,
            text="Create Order",
            command=self.create_order,
            bootstyle=PRIMARY
        ).pack(side=LEFT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="Cancel",
            command=self.window.destroy
        ).pack(side=LEFT, padx=5)
        
        # Load warehouses
        self.load_warehouses()
        self.load_products()

    def load_suppliers(self):
        db = get_db_session()
        try:
            suppliers = get_all_suppliers(db)
            self.supplier_map = {s.name: s.id for s in suppliers}
            if hasattr(self, 'supplier_combo'):
                self.supplier_combo["values"] = list(self.supplier_map.keys())
        finally:
            db.close()

    def load_customers(self):
        db = get_db_session()
        try:
            customers = get_all_customers(db)
            self.customer_map = {c.name: c.id for c in customers}
            if hasattr(self, 'customer_combo'):
                if customers:
                    self.customer_combo["state"] = "readonly"
                    self.customer_combo["values"] = list(self.customer_map.keys())
                else:
                    # No customers in DB: show informative placeholder and disable selection
                    self.customer_combo["values"] = ["-- No customers defined --"]
                    try:
                        self.customer_combo.current(0)
                    except Exception:
                        pass
                    self.customer_combo["state"] = "disabled"
        finally:
            db.close()
    
    def load_warehouses(self):
        """Load warehouses."""
        db = get_db_session()
        try:
            warehouses = get_all_warehouses(db)
            self.warehouse_combo["values"] = [w.name for w in warehouses]
        finally:
            db.close()
    
    def load_products(self):
        """Load products for search."""
        db = get_db_session()
        try:
            products = search_products(db, active_only=True)
            self.product_names = {p.name: p for p in products}
            self.product_combo["values"] = list(self.product_names.keys())
        finally:
            db.close()
    
    def search_products(self, event=None):
        """Search products as user types."""
        query = self.product_var.get().strip()
        if not query:
            return
        
        db = get_db_session()
        try:
            products = search_products(db, query=query, active_only=True)
            self.product_names = {p.name: p for p in products}
            self.product_combo["values"] = list(self.product_names.keys())
        finally:
            db.close()
    
    def update_stock_display(self, event=None):
        """Update stock availability display for sales orders."""
        if self.order_type != ORDER_TYPE_SALE:
            return
        
        product_name = self.product_var.get().strip()
        warehouse_name = self.warehouse_var.get()
        
        if not product_name or not warehouse_name or product_name not in self.product_names:
            self.stock_label.config(text="")
            return
        
        product = self.product_names[product_name]
        
        db = get_db_session()
        try:
            warehouses = get_all_warehouses(db)
            warehouse_id = None
            for w in warehouses:
                if w.name == warehouse_name:
                    warehouse_id = w.id
                    break
            
            if warehouse_id:
                stock = get_warehouse_stock(db, product.id, warehouse_id)
                if stock > 0:
                    self.stock_label.config(text=f"Available: {stock} units", foreground="green")
                else:
                    self.stock_label.config(text=f"Available: {stock} units (OUT OF STOCK)", foreground="red")
        finally:
            db.close()

    
    def add_item(self):
        """Add item to order."""
        product_name = self.product_var.get().strip()
        warehouse_name = self.warehouse_var.get()
        quantity_str = self.quantity_entry.get().strip()
        price_str = self.price_entry.get().strip()
        
        if not product_name or not warehouse_name or not quantity_str or not price_str:
            messagebox.showerror("Error", "Please fill in all fields")
            return
        
        if product_name not in self.product_names:
            messagebox.showerror("Error", "Product not found")
            return
        
        try:
            quantity = int(quantity_str)
            unit_price = Decimal(price_str)
        except:
            messagebox.showerror("Error", "Invalid quantity or price")
            return
        
        product = self.product_names[product_name]
        
        # Get warehouse ID
        db = get_db_session()
        try:
            warehouses = get_all_warehouses(db)
            warehouse_id = None
            for w in warehouses:
                if w.name == warehouse_name:
                    warehouse_id = w.id
                    break
            
            if not warehouse_id:
                messagebox.showerror("Error", "Invalid warehouse")
                return
            
            # Check stock availability for sales orders
            if self.order_type == ORDER_TYPE_SALE:
                available_stock = get_warehouse_stock(db, product.id, warehouse_id)
                if available_stock < quantity:
                    messagebox.showerror(
                        "Insufficient Stock", 
                        f"Product '{product.name}' has only {available_stock} units available in {warehouse_name}.\n"
                        f"You requested {quantity} units.\n\n"
                        f"Please select a different warehouse or reduce the quantity."
                    )
                    return
            
            # Add to items list
            item = {
                "product_id": product.id,
                "quantity": quantity,
                "unit_price": float(unit_price),
                "warehouse_id": warehouse_id
            }
            self.items.append(item)
            
            # Add to tree
            subtotal = unit_price * quantity
            self.items_tree.insert(
                "",
                END,
                values=(
                    product.name,
                    warehouse_name,
                    quantity,
                    f"${unit_price:.2f}",
                    f"${subtotal:.2f}"
                )
            )
            
            # Update total
            self.update_total()
            
            # Clear fields
            self.product_var.set("")
            self.quantity_entry.delete(0, END)
            self.price_entry.delete(0, END)
        finally:
            db.close()
    
    def remove_item(self):
        """Remove selected item."""
        selection = self.items_tree.selection()
        if not selection:
            return
        
        item_index = self.items_tree.index(selection[0])
        self.items_tree.delete(selection[0])
        self.items.pop(item_index)
        self.update_total()
    
    def update_total(self):
        """Update total label."""
        total = sum(item["unit_price"] * item["quantity"] for item in self.items)
        self.total_label.config(text=f"Total: ${total:.2f}")
    
    def create_order(self):
        """Create the order."""
        if not self.items:
            messagebox.showerror("Error", "Please add at least one item")
            return
        
        notes = self.notes_entry.get().strip()
        # Append party info into notes to satisfy UI requirement without schema change
        if self.order_type == ORDER_TYPE_PURCHASE and self.supplier_var is not None:
            supplier_name = self.supplier_var.get().strip()
            if not supplier_name:
                messagebox.showerror("Error", "Please select a supplier")
                return
            notes = (notes + " ").strip()
            notes += f"[Supplier: {supplier_name}]"
        elif self.order_type in (ORDER_TYPE_SALE, ORDER_TYPE_RETURN):
            # Require selecting an existing customer from the predefined list
            customer_name = self.customer_var.get().strip() if hasattr(self, "customer_var") else ""
            if not customer_name:
                messagebox.showerror("Error", "Please select a customer")
                return
            customer_id = None
            if hasattr(self, 'customer_map'):
                customer_id = self.customer_map.get(customer_name)
            if not customer_id:
                messagebox.showerror("Error", "Selected customer is not valid. Please add customers first from the Customers screen.")
                return
            notes = (notes + " ").strip()
            notes += f"[Customer: {customer_name}]"
        
        db = get_db_session()
        try:
            create_order(
                db,
                self.order_type,
                self.user,
                self.items,
                notes=notes if notes else None,
                customer_id=customer_id if self.order_type in (ORDER_TYPE_SALE, ORDER_TYPE_RETURN) else None
            )
            messagebox.showinfo("Success", f"{self.order_type} order created successfully")
            # Notify other parts of the UI (dashboard) that orders have been updated
            try:
                root = self.window.winfo_toplevel()
                root.event_generate("<<OrdersUpdated>>", when="tail")
            except Exception:
                pass
            self.window.destroy()
            if self.on_save:
                self.on_save()
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            messagebox.showerror("Error", f"Failed to create order: {str(e)}")
        finally:
            db.close()

