"""Tests for low stock detection."""
import pytest
from inventory_app.db.session import Base, engine, get_db_session
from inventory_app.models.product import Product, Category, Supplier
from inventory_app.models.stock import Warehouse
from inventory_app.models.user import User
from inventory_app.services.auth_service import hash_password
from inventory_app.services.product_service import create_product
from inventory_app.services.inventory_service import (
    adjust_stock, get_low_stock_items, create_warehouse
)
from inventory_app.config import LOW_STOCK_THRESHOLD


@pytest.fixture
def db_session():
    """Create a test database session."""
    Base.metadata.create_all(bind=engine)
    db = next(get_db_session())
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def user(db_session):
    """Create a test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=hash_password("password"),
        full_name="Test User",
        role="Staff"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def category(db_session):
    """Create a test category."""
    category = Category(name="Test Category")
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category


@pytest.fixture
def supplier(db_session):
    """Create a test supplier."""
    supplier = Supplier(name="Test Supplier")
    db_session.add(supplier)
    db_session.commit()
    db_session.refresh(supplier)
    return supplier


@pytest.fixture
def product(db_session, category, supplier):
    """Create a test product."""
    product = create_product(
        db_session,
        name="Test Product",
        category_id=category.id,
        price=10.00,
        supplier_id=supplier.id
    )
    return product


@pytest.fixture
def warehouse(db_session):
    """Create a test warehouse."""
    warehouse = create_warehouse(db_session, "Test Warehouse")
    return warehouse


def test_low_stock_detection(db_session, product, warehouse, user):
    """Test low stock detection."""
    # Add stock below threshold
    adjust_stock(db_session, product.id, warehouse.id, LOW_STOCK_THRESHOLD - 1, user, "Low stock")
    
    low_stock = get_low_stock_items(db_session, threshold=LOW_STOCK_THRESHOLD)
    
    assert len(low_stock) == 1
    assert low_stock[0]["product_id"] == product.id
    assert low_stock[0]["quantity"] == LOW_STOCK_THRESHOLD - 1


def test_no_low_stock_when_above_threshold(db_session, product, warehouse, user):
    """Test no low stock when above threshold."""
    # Add stock above threshold
    adjust_stock(db_session, product.id, warehouse.id, LOW_STOCK_THRESHOLD + 10, user, "Adequate stock")
    
    low_stock = get_low_stock_items(db_session, threshold=LOW_STOCK_THRESHOLD)
    
    assert len(low_stock) == 0


def test_low_stock_only_active_products(db_session, product, warehouse, user):
    """Test that only active products are included in low stock."""
    # Add low stock
    adjust_stock(db_session, product.id, warehouse.id, 5, user, "Low stock")
    
    # Deactivate product
    product.is_active = False
    db_session.commit()
    
    low_stock = get_low_stock_items(db_session)
    
    # Should not include deactivated product
    assert len(low_stock) == 0

