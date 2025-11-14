"""Products management screen."""
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from decimal import Decimal
from inventory_app.db.session import get_db_session
from inventory_app.services.product_service import (
    create_product, update_product, delete_product, search_products,
    get_all_categories, get_all_suppliers, get_product
)
from inventory_app.services.inventory_service import get_stock_levels, get_all_warehouses, create_batch
from inventory_app.models.user import User
from inventory_app.utils.logging import logger
from datetime import datetime


class ProductsWindow:
    """Products management window."""
    
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
        
        ttk.Label(header_frame, text="Products", font=("Helvetica", 18, "bold")).pack(side=LEFT)
        
        # Search frame
        search_frame = ttk.Frame(self.frame)
        search_frame.pack(fill=X, pady=10)
        
        ttk.Label(search_frame, text="Search:").pack(side=LEFT, padx=5)
        self.search_entry = ttk.Entry(search_frame, width=30)
        self.search_entry.pack(side=LEFT, padx=5)
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_products())
        
        ttk.Button(
            search_frame,
            text="Search",
            command=self.refresh_products,
            bootstyle=PRIMARY
        ).pack(side=LEFT, padx=5)
        
        # Category filter
        ttk.Label(search_frame, text="Category:").pack(side=LEFT, padx=10)
        self.category_var = ttk.StringVar(value="All")
        self.category_combo = ttk.Combobox(search_frame, textvariable=self.category_var, width=20, state="readonly")
        self.category_combo.pack(side=LEFT, padx=5)
        self.category_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_products())
        
        # Buttons
        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(fill=X, pady=10)
        
        ttk.Button(
            btn_frame,
            text="Add Product",
            command=self.add_product,
            bootstyle=SUCCESS
        ).pack(side=LEFT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="Edit Product",
            command=self.edit_product,
            bootstyle=PRIMARY
        ).pack(side=LEFT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="View Details",
            command=self.view_product_details,
            bootstyle=INFO
        ).pack(side=LEFT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="Deactivate",
            command=self.deactivate_product,
            bootstyle=DANGER
        ).pack(side=LEFT, padx=5)
        
        # Products table
        columns = ("ID", "Name", "SKU", "Category", "Price", "Supplier", "Stock", "Status")
        self.tree = ttk.Treeview(self.frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        
        scrollbar = ttk.Scrollbar(self.frame, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=LEFT, fill=BOTH, expand=TRUE)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        # Load categories and products
        self.load_categories()
        self.refresh_products()
    
    def load_categories(self):
        """Load categories into combobox."""
        db = next(get_db_session())
        try:
            categories = get_all_categories(db)
            self.category_combo["values"] = ["All"] + [cat.name for cat in categories]
        finally:
            db.close()
    
    def refresh_products(self):
        """Refresh products list."""
        db = next(get_db_session())
        try:
            # Clear tree
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Get search query
            query = self.search_entry.get().strip()
            category_name = self.category_var.get()
            category_id = None
            
            if category_name != "All":
                categories = get_all_categories(db)
                for cat in categories:
                    if cat.name == category_name:
                        category_id = cat.id
                        break
            
            # Search products
            products = search_products(db, query=query if query else None, category_id=category_id)
            
            # Populate tree
            for product in products:
                # Get stock
                stock = get_stock(db, product.id)
                
                # Get category and supplier names
                category_name = product.category.name if product.category else "N/A"
                supplier_name = product.supplier.name if product.supplier else "N/A"
                status = "Active" if product.is_active else "Inactive"
                
                self.tree.insert(
                    "",
                    END,
                    values=(
                        product.id,
                        product.name,
                        product.sku,
                        category_name,
                        f"${product.price:.2f}",
                        supplier_name,
                        stock,
                        status
                    ),
                    tags=("active" if product.is_active else "inactive",)
                )
            
            # Color code
            self.tree.tag_configure("inactive", foreground="gray")
        finally:
            db.close()
    
    def get_selected_product_id(self):
        """Get selected product ID."""
        selection = self.tree.selection()
        if not selection:
            return None
        item = self.tree.item(selection[0])
        return item["values"][0] if item["values"] else None
    
    def add_product(self):
        """Open add product dialog."""
        ProductDialog(self.frame, self.user, on_save=self.refresh_products)
    
    def edit_product(self):
        """Open edit product dialog."""
        product_id = self.get_selected_product_id()
        if not product_id:
            messagebox.showwarning("No Selection", "Please select a product to edit")
            return
        
        db = next(get_db_session())
        try:
            product = get_product(db, product_id)
            if product:
                ProductDialog(self.frame, self.user, product=product, on_save=self.refresh_products)
        finally:
            db.close()
    
    def view_product_details(self):
        """View product details."""
        product_id = self.get_selected_product_id()
        if not product_id:
            messagebox.showwarning("No Selection", "Please select a product to view")
            return
        
        ProductDetailWindow(self.frame, product_id, self.user)
    
    def deactivate_product(self):
        """Deactivate selected product."""
        product_id = self.get_selected_product_id()
        if not product_id:
            messagebox.showwarning("No Selection", "Please select a product to deactivate")
            return
        
        if not messagebox.askyesno("Confirm", "Are you sure you want to deactivate this product?"):
            return
        
        db = next(get_db_session())
        try:
            delete_product(db, product_id, user=self.user)
            messagebox.showinfo("Success", "Product deactivated successfully")
            self.refresh_products()
        except Exception as e:
            logger.error(f"Error deactivating product: {e}")
            messagebox.showerror("Error", f"Failed to deactivate product: {str(e)}")
        finally:
            db.close()
    
    def destroy(self):
        """Clean up."""
        self.frame.destroy()


class ProductDialog:
    """Product add/edit dialog."""
    
    def __init__(self, parent, user, product=None, on_save=None):
        self.user = user
        self.product = product
        self.on_save = on_save
        
        self.window = ttk.Toplevel(parent)
        self.window.title("Add Product" if not product else "Edit Product")
        self.window.geometry("500x400")
        self.window.transient(parent)
        self.window.grab_set()
        
        # Form frame
        form_frame = ttk.Frame(self.window, padding=20)
        form_frame.pack(fill=BOTH, expand=TRUE)
        
        # Name
        ttk.Label(form_frame, text="Name *:").grid(row=0, column=0, sticky=W, pady=5)
        self.name_entry = ttk.Entry(form_frame, width=40)
        self.name_entry.grid(row=0, column=1, pady=5, padx=10)
        
        # Category
        ttk.Label(form_frame, text="Category *:").grid(row=1, column=0, sticky=W, pady=5)
        self.category_var = ttk.StringVar()
        self.category_combo = ttk.Combobox(form_frame, textvariable=self.category_var, width=37, state="readonly")
        self.category_combo.grid(row=1, column=1, pady=5, padx=10)
        
        # Price
        ttk.Label(form_frame, text="Price *:").grid(row=2, column=0, sticky=W, pady=5)
        self.price_entry = ttk.Entry(form_frame, width=40)
        self.price_entry.grid(row=2, column=1, pady=5, padx=10)
        
        # Supplier
        ttk.Label(form_frame, text="Supplier:").grid(row=3, column=0, sticky=W, pady=5)
        self.supplier_var = ttk.StringVar()
        self.supplier_combo = ttk.Combobox(form_frame, textvariable=self.supplier_var, width=37, state="readonly")
        self.supplier_combo.grid(row=3, column=1, pady=5, padx=10)
        
        # Description
        ttk.Label(form_frame, text="Description:").grid(row=4, column=0, sticky=W, pady=5)
        self.desc_text = ttk.Text(form_frame, width=40, height=5)
        self.desc_text.grid(row=4, column=1, pady=5, padx=10)
        
        # Buttons
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text="Save", command=self.save, bootstyle=SUCCESS).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.window.destroy).pack(side=LEFT, padx=5)
        
        # Load data
        self.load_data()
        
        if product:
            self.name_entry.insert(0, product.name)
            self.price_entry.insert(0, str(product.price))
            if product.supplier:
                self.supplier_var.set(product.supplier.name)
            if product.description:
                self.desc_text.insert("1.0", product.description)
    
    def load_data(self):
        """Load categories and suppliers."""
        db = next(get_db_session())
        try:
            categories = get_all_categories(db)
            self.category_combo["values"] = [cat.name for cat in categories]
            
            suppliers = get_all_suppliers(db)
            self.supplier_combo["values"] = ["None"] + [sup.name for sup in suppliers]
            self.supplier_combo.set("None")
            
            if self.product:
                self.category_var.set(self.product.category.name)
                if self.product.supplier:
                    self.supplier_var.set(self.product.supplier.name)
        finally:
            db.close()
    
    def save(self):
        """Save product."""
        name = self.name_entry.get().strip()
        price_str = self.price_entry.get().strip()
        category_name = self.category_var.get()
        supplier_name = self.supplier_var.get()
        description = self.desc_text.get("1.0", END).strip()
        
        if not name or not price_str or not category_name:
            messagebox.showerror("Error", "Please fill in all required fields")
            return
        
        try:
            price = Decimal(price_str)
        except:
            messagebox.showerror("Error", "Invalid price")
            return
        
        db = next(get_db_session())
        try:
            # Get category ID
            categories = get_all_categories(db)
            category_id = None
            for cat in categories:
                if cat.name == category_name:
                    category_id = cat.id
                    break
            
            if not category_id:
                messagebox.showerror("Error", "Invalid category")
                return
            
            # Get supplier ID
            supplier_id = None
            if supplier_name and supplier_name != "None":
                suppliers = get_all_suppliers(db)
                for sup in suppliers:
                    if sup.name == supplier_name:
                        supplier_id = sup.id
                        break
            
            if self.product:
                update_product(
                    db, self.product.id,
                    name=name,
                    category_id=category_id,
                    price=price,
                    supplier_id=supplier_id,
                    description=description if description else None,
                    user=self.user
                )
            else:
                create_product(
                    db, name, category_id, price,
                    supplier_id=supplier_id,
                    description=description if description else None,
                    user=self.user
                )
            
            messagebox.showinfo("Success", "Product saved successfully")
            self.window.destroy()
            if self.on_save:
                self.on_save()
        except Exception as e:
            logger.error(f"Error saving product: {e}")
            messagebox.showerror("Error", f"Failed to save product: {str(e)}")
        finally:
            db.close()


class ProductDetailWindow:
    """Product detail window showing batches and stock."""
    
    def __init__(self, parent, product_id, user):
        self.product_id = product_id
        self.user = user
        
        self.window = ttk.Toplevel(parent)
        self.window.title("Product Details")
        self.window.geometry("800x600")
        self.window.transient(parent)
        
        # Main frame
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill=BOTH, expand=TRUE)
        
        # Product info
        self.load_product_info(main_frame)
        
        # Stock levels
        stock_frame = ttk.LabelFrame(main_frame, text="Stock by Warehouse", padding=10)
        stock_frame.pack(fill=BOTH, expand=TRUE, pady=10)
        
        stock_columns = ("Warehouse", "Quantity", "Reserved")
        self.stock_tree = ttk.Treeview(stock_frame, columns=stock_columns, show="headings", height=5)
        for col in stock_columns:
            self.stock_tree.heading(col, text=col)
            self.stock_tree.column(col, width=200)
        self.stock_tree.pack(fill=BOTH, expand=TRUE)
        
        # Batches
        batch_frame = ttk.LabelFrame(main_frame, text="Batches/Lots", padding=10)
        batch_frame.pack(fill=BOTH, expand=TRUE, pady=10)
        
        batch_columns = ("Batch #", "Warehouse", "Quantity", "Expiry Date", "Received Date")
        self.batch_tree = ttk.Treeview(batch_frame, columns=batch_columns, show="headings", height=8)
        for col in batch_columns:
            self.batch_tree.heading(col, text=col)
            self.batch_tree.column(col, width=120)
        self.batch_tree.pack(fill=BOTH, expand=TRUE)
        
        # Add batch button
        ttk.Button(
            main_frame,
            text="Add Batch",
            command=self.add_batch,
            bootstyle=SUCCESS
        ).pack(pady=10)
        
        self.refresh_data()
    
    def load_product_info(self, parent):
        """Load product information."""
        db = next(get_db_session())
        try:
            product = get_product(db, self.product_id)
            if product:
                info_frame = ttk.LabelFrame(parent, text="Product Information", padding=10)
                info_frame.pack(fill=X, pady=10)
                
                ttk.Label(info_frame, text=f"Name: {product.name}", font=("Helvetica", 12, "bold")).pack(anchor=W)
                ttk.Label(info_frame, text=f"SKU: {product.sku}").pack(anchor=W)
                ttk.Label(info_frame, text=f"Category: {product.category.name if product.category else 'N/A'}").pack(anchor=W)
                ttk.Label(info_frame, text=f"Price: ${product.price:.2f}").pack(anchor=W)
                ttk.Label(info_frame, text=f"Supplier: {product.supplier.name if product.supplier else 'N/A'}").pack(anchor=W)
        finally:
            db.close()
    
    def refresh_data(self):
        """Refresh stock and batch data."""
        db = next(get_db_session())
        try:
            # Clear trees
            for item in self.stock_tree.get_children():
                self.stock_tree.delete(item)
            for item in self.batch_tree.get_children():
                self.batch_tree.delete(item)
            
            # Load stock levels
            stock_levels = get_stock_levels(db, self.product_id)
            warehouses = get_all_warehouses(db)
            warehouse_dict = {w.id: w.name for w in warehouses}
            
            for stock in stock_levels:
                self.stock_tree.insert(
                    "",
                    END,
                    values=(
                        warehouse_dict.get(stock.warehouse_id, "Unknown"),
                        stock.quantity,
                        stock.reserved_quantity
                    )
                )
            
            # Load batches
            from inventory_app.services.inventory_service import get_batches
            batches = get_batches(db, product_id=self.product_id)
            
            for batch in batches:
                expiry_str = batch.expiry_date.strftime("%Y-%m-%d") if batch.expiry_date else "N/A"
                received_str = batch.received_date.strftime("%Y-%m-%d") if batch.received_date else "N/A"
                
                # Color code near expiry
                tags = []
                if batch.expiry_date:
                    days_until_expiry = (batch.expiry_date.date() - datetime.now().date()).days
                    if days_until_expiry < 30:
                        tags.append("near_expiry")
                
                self.batch_tree.insert(
                    "",
                    END,
                    values=(
                        batch.batch_number,
                        warehouse_dict.get(batch.warehouse_id, "Unknown"),
                        batch.quantity,
                        expiry_str,
                        received_str
                    ),
                    tags=tuple(tags)
                )
            
            self.batch_tree.tag_configure("near_expiry", foreground="orange")
        finally:
            db.close()
    
    def add_batch(self):
        """Add new batch dialog."""
        BatchDialog(self.window, self.product_id, self.user, on_save=self.refresh_data)


class BatchDialog:
    """Add batch dialog."""
    
    def __init__(self, parent, product_id, user, on_save=None):
        self.product_id = product_id
        self.user = user
        self.on_save = on_save
        
        self.window = ttk.Toplevel(parent)
        self.window.title("Add Batch")
        self.window.geometry("400x300")
        self.window.transient(parent)
        self.window.grab_set()
        
        form_frame = ttk.Frame(self.window, padding=20)
        form_frame.pack(fill=BOTH, expand=TRUE)
        
        # Batch number
        ttk.Label(form_frame, text="Batch Number *:").grid(row=0, column=0, sticky=W, pady=5)
        self.batch_entry = ttk.Entry(form_frame, width=30)
        self.batch_entry.grid(row=0, column=1, pady=5, padx=10)
        
        # Warehouse
        ttk.Label(form_frame, text="Warehouse *:").grid(row=1, column=0, sticky=W, pady=5)
        self.warehouse_var = ttk.StringVar()
        self.warehouse_combo = ttk.Combobox(form_frame, textvariable=self.warehouse_var, width=27, state="readonly")
        self.warehouse_combo.grid(row=1, column=1, pady=5, padx=10)
        
        # Quantity
        ttk.Label(form_frame, text="Quantity *:").grid(row=2, column=0, sticky=W, pady=5)
        self.quantity_entry = ttk.Entry(form_frame, width=30)
        self.quantity_entry.grid(row=2, column=1, pady=5, padx=10)
        
        # Expiry date
        ttk.Label(form_frame, text="Expiry Date (YYYY-MM-DD):").grid(row=3, column=0, sticky=W, pady=5)
        self.expiry_entry = ttk.Entry(form_frame, width=30)
        self.expiry_entry.grid(row=3, column=1, pady=5, padx=10)
        
        # Buttons
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text="Save", command=self.save, bootstyle=SUCCESS).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.window.destroy).pack(side=LEFT, padx=5)
        
        # Load warehouses
        self.load_warehouses()
    
    def load_warehouses(self):
        """Load warehouses."""
        db = next(get_db_session())
        try:
            warehouses = get_all_warehouses(db)
            self.warehouse_combo["values"] = [w.name for w in warehouses]
        finally:
            db.close()
    
    def save(self):
        """Save batch."""
        batch_number = self.batch_entry.get().strip()
        warehouse_name = self.warehouse_var.get()
        quantity_str = self.quantity_entry.get().strip()
        expiry_str = self.expiry_entry.get().strip()
        
        if not batch_number or not warehouse_name or not quantity_str:
            messagebox.showerror("Error", "Please fill in all required fields")
            return
        
        try:
            quantity = int(quantity_str)
        except:
            messagebox.showerror("Error", "Invalid quantity")
            return
        
        expiry_date = None
        if expiry_str:
            try:
                expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d")
            except:
                messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD")
                return
        
        db = next(get_db_session())
        try:
            # Get warehouse ID
            warehouses = get_all_warehouses(db)
            warehouse_id = None
            for w in warehouses:
                if w.name == warehouse_name:
                    warehouse_id = w.id
                    break
            
            if not warehouse_id:
                messagebox.showerror("Error", "Invalid warehouse")
                return
            
            from inventory_app.services.inventory_service import create_batch
            create_batch(
                db, self.product_id, warehouse_id,
                batch_number, quantity, expiry_date, user=self.user
            )
            
            messagebox.showinfo("Success", "Batch created successfully")
            self.window.destroy()
            if self.on_save:
                self.on_save()
        except Exception as e:
            logger.error(f"Error creating batch: {e}")
            messagebox.showerror("Error", f"Failed to create batch: {str(e)}")
        finally:
            db.close()

