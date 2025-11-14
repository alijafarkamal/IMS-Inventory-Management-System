"""Tests for order service."""
import pytest
from decimal import Decimal
from inventory_app.db.session import Base, engine, get_db_session
from inventory_app.models.product import Product, Category, Supplier
from inventory_app.models.stock import Warehouse
from inventory_app.models.user import User
from inventory_app.models.order import Order
from inventory_app.services.auth_service import hash_password
from inventory_app.services.product_service import create_product
from inventory_app.services.order_service import create_order
from inventory_app.services.inventory_service import get_warehouse_stock, create_warehouse
from inventory_app.config import ORDER_TYPE_SALE, ORDER_TYPE_PURCHASE


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


def test_create_sale_order(db_session, product, warehouse, user):
    """Test creating a sale order."""
    # First add stock
    from inventory_app.services.inventory_service import adjust_stock
    adjust_stock(db_session, product.id, warehouse.id, 100, user, "Initial stock")
    
    # Create sale order
    items = [{
        "product_id": product.id,
        "quantity": 10,
        "unit_price": 10.00,
        "warehouse_id": warehouse.id
    }]
    
    order = create_order(db_session, ORDER_TYPE_SALE, user, items)
    
    assert order.order_type == ORDER_TYPE_SALE
    assert order.total_amount == Decimal("100.00")
    assert order.status == "Completed"
    
    # Check stock was reduced
    stock = get_warehouse_stock(db_session, product.id, warehouse.id)
    assert stock == 90


def test_create_purchase_order(db_session, product, warehouse, user):
    """Test creating a purchase order."""
    items = [{
        "product_id": product.id,
        "quantity": 50,
        "unit_price": 8.00,
        "warehouse_id": warehouse.id
    }]
    
    order = create_order(db_session, ORDER_TYPE_PURCHASE, user, items)
    
    assert order.order_type == ORDER_TYPE_PURCHASE
    assert order.total_amount == Decimal("400.00")
    assert order.status == "Completed"
    
    # Check stock was increased
    stock = get_warehouse_stock(db_session, product.id, warehouse.id)
    assert stock == 50


def test_create_sale_order_insufficient_stock(db_session, product, warehouse, user):
    """Test sale order with insufficient stock."""
    # Add only 5 units
    from inventory_app.services.inventory_service import adjust_stock
    adjust_stock(db_session, product.id, warehouse.id, 5, user, "Initial stock")
    
    # Try to sell 10 units
    items = [{
        "product_id": product.id,
        "quantity": 10,
        "unit_price": 10.00,
        "warehouse_id": warehouse.id
    }]
    
    with pytest.raises(ValueError, match="Insufficient stock"):
        create_order(db_session, ORDER_TYPE_SALE, user, items)

