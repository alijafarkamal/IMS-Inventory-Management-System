"""Seed sample data for the inventory management system."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "inventory_app" / "src"))

from inventory_app.db.session import Base, engine, get_db_session
from inventory_app.models.user import User
from inventory_app.models.product import Category, Supplier, Product
from inventory_app.models.stock import Warehouse, Batch
from inventory_app.services.auth_service import create_user, hash_password
from inventory_app.services.product_service import create_category, create_supplier, create_product
from inventory_app.services.inventory_service import create_warehouse, create_batch, adjust_stock
from inventory_app.utils.logging import logger
from datetime import datetime, timedelta
from decimal import Decimal


def seed_data():
    """Seed sample data."""
    logger.info("Starting data seeding...")
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = get_db_session()
    try:
        # Create admin user
        logger.info("Creating admin user...")
        try:
            admin = create_user(
                db,
                username="admin",
                password="admin123",
                email="admin@inventory.com",
                full_name="Administrator",
                role="Admin"
            )
            logger.info(f"Created admin user: {admin.username}")
        except ValueError as e:
            logger.warning(f"Admin user may already exist: {e}")
            admin = db.query(User).filter(User.username == "admin").first()
        
        # Create categories
        logger.info("Creating categories...")
        categories = {}
        category_names = ["Electronics", "Clothing", "Food", "Books", "Toys"]
        for cat_name in category_names:
            try:
                category = create_category(db, cat_name, f"{cat_name} category")
                categories[cat_name] = category
                logger.info(f"Created category: {cat_name}")
            except ValueError:
                category = db.query(Category).filter(Category.name == cat_name).first()
                categories[cat_name] = category
        
        # Create suppliers
        logger.info("Creating suppliers...")
        suppliers = {}
        supplier_data = [
            ("TechCorp", "John Doe", "john@techcorp.com", "555-0101", "123 Tech St"),
            ("Fashion Inc", "Jane Smith", "jane@fashion.com", "555-0102", "456 Fashion Ave"),
            ("FoodMart", "Bob Johnson", "bob@foodmart.com", "555-0103", "789 Food Blvd"),
        ]
        for name, contact, email, phone, address in supplier_data:
            try:
                supplier = create_supplier(db, name, contact, email, phone, address)
                suppliers[name] = supplier
                logger.info(f"Created supplier: {name}")
            except ValueError:
                supplier = db.query(Supplier).filter(Supplier.name == name).first()
                suppliers[name] = supplier
        
        # Create warehouses
        logger.info("Creating warehouses...")
        warehouses = {}
        warehouse_data = [
            ("Main Warehouse", "123 Main St, City"),
            ("East Warehouse", "456 East Ave, City"),
            ("West Warehouse", "789 West Blvd, City"),
        ]
        for name, location in warehouse_data:
            try:
                warehouse = create_warehouse(db, name, location)
                warehouses[name] = warehouse
                logger.info(f"Created warehouse: {name}")
            except ValueError:
                warehouse = db.query(Warehouse).filter(Warehouse.name == name).first()
                warehouses[name] = warehouse
        
        # Create products
        logger.info("Creating products...")
        products_data = [
            ("Laptop Computer", "Electronics", "TechCorp", Decimal("999.99")),
            ("Wireless Mouse", "Electronics", "TechCorp", Decimal("29.99")),
            ("Keyboard", "Electronics", "TechCorp", Decimal("79.99")),
            ("T-Shirt", "Clothing", "Fashion Inc", Decimal("19.99")),
            ("Jeans", "Clothing", "Fashion Inc", Decimal("49.99")),
            ("Sneakers", "Clothing", "Fashion Inc", Decimal("89.99")),
            ("Canned Soup", "Food", "FoodMart", Decimal("3.99")),
            ("Bread", "Food", "FoodMart", Decimal("2.99")),
            ("Milk", "Food", "FoodMart", Decimal("4.99")),
            ("Python Programming", "Books", None, Decimal("49.99")),
            ("JavaScript Guide", "Books", None, Decimal("39.99")),
            ("Action Figure", "Toys", None, Decimal("14.99")),
            ("Board Game", "Toys", None, Decimal("24.99")),
            ("Smartphone", "Electronics", "TechCorp", Decimal("699.99")),
            ("Tablet", "Electronics", "TechCorp", Decimal("399.99")),
            ("Headphones", "Electronics", "TechCorp", Decimal("99.99")),
            ("Dress Shirt", "Clothing", "Fashion Inc", Decimal("59.99")),
            ("Running Shoes", "Clothing", "Fashion Inc", Decimal("119.99")),
            ("Cookbook", "Books", None, Decimal("29.99")),
            ("Puzzle", "Toys", None, Decimal("19.99")),
        ]
        
        products = []
        for name, cat_name, sup_name, price in products_data:
            try:
                category = categories.get(cat_name)
                supplier = suppliers.get(sup_name) if sup_name else None
                
                product = create_product(
                    db,
                    name=name,
                    category_id=category.id,
                    price=price,
                    supplier_id=supplier.id if supplier else None
                )
                products.append(product)
                logger.info(f"Created product: {name} (SKU: {product.sku})")
            except Exception as e:
                logger.warning(f"Error creating product {name}: {e}")
        
        # Create batches and stock
        logger.info("Creating batches and stock...")
        import random
        
        for product in products[:15]:  # Add stock to first 15 products
            warehouse = random.choice(list(warehouses.values()))
            quantity = random.randint(5, 100)
            
            # Create batch
            batch_number = f"BATCH-{product.sku}-001"
            expiry_date = datetime.now() + timedelta(days=random.randint(30, 365))
            
            try:
                batch = create_batch(
                    db,
                    product.id,
                    warehouse.id,
                    batch_number,
                    quantity,
                    expiry_date=expiry_date,
                    user=admin
                )
                logger.info(f"Created batch {batch_number} with {quantity} units for {product.name}")
            except Exception as e:
                logger.warning(f"Error creating batch for {product.name}: {e}")
                # Fallback: just adjust stock
                try:
                    adjust_stock(db, product.id, warehouse.id, quantity, admin, "Initial stock")
                except Exception as e2:
                    logger.warning(f"Error adjusting stock for {product.name}: {e2}")
        
        # Create some low stock items
        logger.info("Creating low stock items...")
        for product in products[15:18]:  # Last 3 products get low stock
            warehouse = random.choice(list(warehouses.values()))
            quantity = random.randint(1, 5)  # Low stock
            
            try:
                adjust_stock(db, product.id, warehouse.id, quantity, admin, "Low stock test")
                logger.info(f"Created low stock for {product.name}: {quantity} units")
            except Exception as e:
                logger.warning(f"Error creating low stock for {product.name}: {e}")
        
        db.commit()
        logger.info("Data seeding completed successfully!")
        
    except Exception as e:
        logger.error(f"Error seeding data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()

