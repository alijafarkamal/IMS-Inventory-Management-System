"""SKU generation utility."""
from inventory_app.config import SKU_PREFIX, SKU_LENGTH
from inventory_app.db.session import get_db_session
from inventory_app.models.product import Product
from inventory_app.utils.logging import logger


def generate_sku(name: str, category_id: int = None, db_session=None) -> str:
    """
    Generate a unique, human-readable SKU.
    
    Format: INV-{CATEGORY_CODE}-{SEQUENCE}
    Example: INV-ELEC-0001
    
    Args:
        name: Product name
        category_id: Optional category ID for category code
        db_session: Optional database session (if None, creates new one)
        
    Returns:
        Unique SKU string
    """
    should_close = False
    if db_session is None:
        db = next(get_db_session())
        should_close = True
    else:
        db = db_session
    
    try:
        # Get category code if provided
        category_code = "GEN"
        if category_id:
            from inventory_app.models.product import Category
            category = db.query(Category).filter(Category.id == category_id).first()
            if category:
                # Use first 4 uppercase letters of category name
                category_code = category.name[:4].upper().replace(" ", "")
        
        # Find the highest sequence number for this category
        existing_skus = db.query(Product.sku).filter(
            Product.sku.like(f"{SKU_PREFIX}-{category_code}-%")
        ).all()
        
        max_seq = 0
        for (sku,) in existing_skus:
            try:
                # Extract sequence number from SKU
                parts = sku.split("-")
                if len(parts) == 3:
                    seq = int(parts[2])
                    max_seq = max(max_seq, seq)
            except (ValueError, IndexError):
                continue
        
        # Generate new SKU
        new_seq = max_seq + 1
        sku = f"{SKU_PREFIX}-{category_code}-{new_seq:04d}"
        
        # Ensure uniqueness (in case of race condition)
        while db.query(Product).filter(Product.sku == sku).first():
            new_seq += 1
            sku = f"{SKU_PREFIX}-{category_code}-{new_seq:04d}"
        
        logger.info(f"Generated SKU: {sku} for product: {name}")
        return sku
    finally:
        if should_close:
            db.close()

