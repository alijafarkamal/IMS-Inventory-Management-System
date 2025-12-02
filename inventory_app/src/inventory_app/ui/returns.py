"""Returns management screen (Customer and Supplier returns)."""
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from decimal import Decimal

from inventory_app.db.session import get_db_session
from inventory_app.services.order_service import create_order
from inventory_app.services.product_service import search_products
from inventory_app.services.customer_service import get_all_customers
from inventory_app.services.product_service import get_all_suppliers
from inventory_app.services.inventory_service import get_all_warehouses
from inventory_app.config import (
    ORDER_TYPE_CUSTOMER_RETURN,
    ORDER_TYPE_SUPPLIER_RETURN,
)
from inventory_app.models.user import User
from inventory_app.utils.logging import logger


class ReturnsWindow:
    """Returns management window."""

    def __init__(self, parent, user: User, on_navigate_callback):
        self.parent = parent
        self.user = user
        self.on_navigate = on_navigate_callback

        self.frame = ttk.Frame(parent, padding=10)
        self.frame.pack(fill=BOTH, expand=TRUE)

        header = ttk.Frame(self.frame)
        header.pack(fill=X, pady=(0, 10))
        ttk.Label(header, text="Returns", font=("Helvetica", 18, "bold")).pack(side=LEFT)

        actions = ttk.Frame(self.frame)
        actions.pack(fill=X, pady=10)
        ttk.Button(actions, text="Customer Return", bootstyle=WARNING, command=lambda: self.open_dialog(ORDER_TYPE_CUSTOMER_RETURN)).pack(side=LEFT, padx=5)
        ttk.Button(actions, text="Supplier Return", bootstyle=DANGER, command=lambda: self.open_dialog(ORDER_TYPE_SUPPLIER_RETURN)).pack(side=LEFT, padx=5)

    def open_dialog(self, order_type: str):
        ReturnOrderDialog(self.frame, self.user, order_type)

    def destroy(self):
        self.frame.destroy()


class ReturnOrderDialog:
    """Create return order dialog with simplified inputs (no unit price)."""

    def __init__(self, parent, user: User, order_type: str):
        self.user = user
        self.order_type = order_type
        self.items = []

        self.window = ttk.Toplevel(parent)
        self.window.title("Create Return Order")
        try:
            screen_w = self.window.winfo_screenwidth()
            screen_h = self.window.winfo_screenheight()
            target_w = max(900, int(screen_w * 0.55))
            target_h = max(560, int(screen_h * 0.6))
            x = int((screen_w - target_w) / 2)
            y = int((screen_h - target_h) / 2 * 0.92)
            self.window.geometry(f"{target_w}x{target_h}+{x}+{y}")
        except Exception:
            self.window.geometry("900x560")
        self.window.transient(parent)
        self.window.grab_set()

        main = ttk.Frame(self.window, padding=10)
        main.pack(fill=BOTH, expand=TRUE)

        # Party selection
        party = ttk.Labelframe(main, text="Party", padding=8)
        party.pack(fill=X, pady=8)
        if order_type == ORDER_TYPE_CUSTOMER_RETURN:
            ttk.Label(party, text="Customer:").grid(row=0, column=0, sticky=W, padx=5)
            self.customer_var = ttk.StringVar()
            self.customer_combo = ttk.Combobox(party, textvariable=self.customer_var, width=32, state="readonly")
            self.customer_combo.grid(row=0, column=1, padx=5)
            self.load_customers()
        else:
            ttk.Label(party, text="Supplier:").grid(row=0, column=0, sticky=W, padx=5)
            self.supplier_var = ttk.StringVar()
            self.supplier_combo = ttk.Combobox(party, textvariable=self.supplier_var, width=30, state="readonly")
            self.supplier_combo.grid(row=0, column=1, padx=5)
            self.load_suppliers()

        # Add item
        add = ttk.Labelframe(main, text="Add Item", padding=8)
        add.pack(fill=X, pady=8)
        ttk.Label(add, text="Product:").grid(row=0, column=0, sticky=W, padx=5)
        self.product_var = ttk.StringVar()
        self.product_combo = ttk.Combobox(add, textvariable=self.product_var, width=30)
        self.product_combo.grid(row=0, column=1, padx=5)
        self.product_combo.bind("<KeyRelease>", self.search_products)

        ttk.Label(add, text="Warehouse:").grid(row=0, column=2, sticky=W, padx=5)
        self.warehouse_var = ttk.StringVar()
        self.warehouse_combo = ttk.Combobox(add, textvariable=self.warehouse_var, width=20, state="readonly")
        self.warehouse_combo.grid(row=0, column=3, padx=5)
        self.load_warehouses()

        ttk.Label(add, text="Quantity:").grid(row=1, column=0, sticky=W, padx=5, pady=5)
        self.qty_entry = ttk.Entry(add, width=15)
        self.qty_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(add, text="Add Item", bootstyle=SUCCESS, command=self.add_item).grid(row=1, column=3, padx=5, pady=5)

        # Items
        items = ttk.Labelframe(main, text="Items", padding=8)
        items.pack(fill=BOTH, expand=TRUE, pady=8)
        cols = ("Product", "Warehouse", "Quantity")
        self.tree = ttk.Treeview(items, columns=cols, show="headings", height=8)
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=160)
        self.tree.pack(fill=BOTH, expand=TRUE)

        # Reason and actions
        bottom = ttk.Frame(main)
        bottom.pack(fill=X, pady=8)
        ttk.Label(bottom, text="Reason:").pack(side=LEFT, padx=6)
        self.reason_entry = ttk.Entry(bottom, width=50)
        self.reason_entry.pack(side=LEFT, padx=6, fill=X, expand=TRUE)

        actions = ttk.Frame(main)
        actions.pack(fill=X, pady=8)
        ttk.Button(actions, text="Create Return", bootstyle=SUCCESS, command=self.create_return, width=18).pack(side=LEFT, padx=6)
        ttk.Button(actions, text="Cancel", bootstyle=SECONDARY, command=self.window.destroy, width=12).pack(side=LEFT, padx=6)

        self.load_products()

    def load_customers(self):
        db = get_db_session()
        try:
            customers = get_all_customers(db)
            self.customer_map = {c.name: c.id for c in customers}
            self.customer_combo["values"] = list(self.customer_map.keys())
        finally:
            db.close()

    def load_suppliers(self):
        db = get_db_session()
        try:
            suppliers = get_all_suppliers(db)
            self.supplier_map = {s.name: s.id for s in suppliers}
            self.supplier_combo["values"] = list(self.supplier_map.keys())
        finally:
            db.close()

    def load_warehouses(self):
        db = get_db_session()
        try:
            warehouses = get_all_warehouses(db)
            self.warehouse_combo["values"] = [w.name for w in warehouses]
        finally:
            db.close()

    def load_products(self):
        db = get_db_session()
        try:
            products = search_products(db, active_only=True)
            self.product_names = {p.name: p for p in products}
            self.product_combo["values"] = list(self.product_names.keys())
        finally:
            db.close()

    def search_products(self, event=None):
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

    def add_item(self):
        product_name = self.product_var.get().strip()
        warehouse_name = self.warehouse_var.get()
        qty_str = self.qty_entry.get().strip()
        if not product_name or not warehouse_name or not qty_str:
            messagebox.showerror("Error", "Please fill in all fields")
            return
        if product_name not in self.product_names:
            messagebox.showerror("Error", "Product not found")
            return
        try:
            quantity = int(qty_str)
        except Exception:
            messagebox.showerror("Error", "Invalid quantity")
            return
        product = self.product_names[product_name]
        # Resolve warehouse id
        db = get_db_session()
        try:
            from inventory_app.services.inventory_service import get_all_warehouses
            warehouses = get_all_warehouses(db)
            warehouse_id = None
            for w in warehouses:
                if w.name == warehouse_name:
                    warehouse_id = w.id
                    break
            if not warehouse_id:
                messagebox.showerror("Error", "Invalid warehouse")
                return
            self.items.append({
                "product_id": product.id,
                "quantity": quantity,
                "unit_price": 0.0,
                "warehouse_id": warehouse_id,
            })
            self.tree.insert("", END, values=(product.name, warehouse_name, quantity))
            self.qty_entry.delete(0, END)
            self.product_var.set("")
        finally:
            db.close()

    def create_return(self):
        if not self.items:
            messagebox.showerror("Error", "Add at least one item")
            return
        notes = self.reason_entry.get().strip() if hasattr(self, "reason_entry") else ""
        db = get_db_session()
        customer_id = None
        try:
            # Party notes and customer_id
            if self.order_type == ORDER_TYPE_CUSTOMER_RETURN:
                name = self.customer_var.get().strip() if hasattr(self, "customer_var") else ""
                if not name:
                    messagebox.showerror("Error", "Select a customer")
                    return
                customer_id = self.customer_map.get(name)
                if not customer_id:
                    messagebox.showerror("Error", "Invalid customer")
                    return
                notes = (notes + " ").strip() + f"[Customer: {name}]"
            else:
                name = self.supplier_var.get().strip() if hasattr(self, "supplier_var") else ""
                if not name:
                    messagebox.showerror("Error", "Select a supplier")
                    return
                notes = (notes + " ").strip() + f"[Supplier: {name}]"

            order = create_order(
                db,
                self.order_type,
                self.user,
                self.items,
                notes=notes if notes else None,
                customer_id=customer_id if self.order_type == ORDER_TYPE_CUSTOMER_RETURN else None,
            )
            messagebox.showinfo("Success", f"{self.order_type} created: {order.order_number}")
            self.window.destroy()
        except Exception as e:
            logger.error(f"Return creation error: {e}")
            messagebox.showerror("Error", f"Failed to create return: {e}")
        finally:
            db.close()
