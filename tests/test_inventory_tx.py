"""Tests for inventory transactions."""
import pytest
from datetime import datetime
from inventory_app.db.session import Base, engine, get_db_session
from inventory_app.models.product import Product, Category, Supplier
from inventory_app.models.stock import Warehouse, StockLevel
from inventory_app.models.user import User
from inventory_app.services.inventory_service import (
    adjust_stock, get_stock, get_warehouse_stock, create_batch
)
from inventory_app.services.auth_service import create_user, hash_password
from inventory_app.services.product_service import create_product


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
    warehouse = Warehouse(name="Test Warehouse", location="Test Location")
    db_session.add(warehouse)
    db_session.commit()
    db_session.refresh(warehouse)
    return warehouse


def test_adjust_stock_increase(db_session, product, warehouse, user):
    """Test stock increase."""
    adjust_stock(
        db_session,
        product.id,
        warehouse.id,
        10,
        user,
        "Test increase"
    )
    
    stock = get_warehouse_stock(db_session, product.id, warehouse.id)
    assert stock == 10


def test_adjust_stock_decrease(db_session, product, warehouse, user):
    """Test stock decrease."""
    # First increase
    adjust_stock(
        db_session,
        product.id,
        warehouse.id,
        20,
        user,
        "Initial stock"
    )
    
    # Then decrease
    adjust_stock(
        db_session,
        product.id,
        warehouse.id,
        -5,
        user,
        "Sale"
    )
    
    stock = get_warehouse_stock(db_session, product.id, warehouse.id)
    assert stock == 15


def test_adjust_stock_insufficient(db_session, product, warehouse, user):
    """Test insufficient stock error."""
    adjust_stock(
        db_session,
        product.id,
        warehouse.id,
        10,
        user,
        "Initial stock"
    )
    
    # Try to decrease more than available
    with pytest.raises(ValueError, match="Insufficient stock"):
        adjust_stock(
            db_session,
            product.id,
            warehouse.id,
            -20,
            user,
            "Sale"
        )


def test_get_total_stock(db_session, product, warehouse, user):
    """Test getting total stock across warehouses."""
    # Create another warehouse
    warehouse2 = Warehouse(name="Warehouse 2")
    db_session.add(warehouse2)
    db_session.commit()
    db_session.refresh(warehouse2)
    
    # Add stock to both warehouses
    adjust_stock(db_session, product.id, warehouse.id, 10, user, "Stock 1")
    adjust_stock(db_session, product.id, warehouse2.id, 15, user, "Stock 2")
    
    total = get_stock(db_session, product.id)
    assert total == 25


def test_create_batch(db_session, product, warehouse, user):
    """Test batch creation."""
    batch = create_batch(
        db_session,
        product.id,
        warehouse.id,
        "BATCH001",
        50,
        expiry_date=datetime(2025, 12, 31),
        user=user
    )
    
    assert batch.batch_number == "BATCH001"
    assert batch.quantity == 50
    
    # Check stock was updated
    stock = get_warehouse_stock(db_session, product.id, warehouse.id)
    assert stock == 50

