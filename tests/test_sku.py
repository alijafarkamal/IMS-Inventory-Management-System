"""Tests for SKU generation."""
import pytest
from inventory_app.db.session import Base, engine, get_db_session
from inventory_app.models.product import Product, Category
from inventory_app.utils.sku import generate_sku


@pytest.fixture
def db_session():
    """Create a test database session."""
    Base.metadata.create_all(bind=engine)
    db = next(get_db_session())
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def category(db_session):
    """Create a test category."""
    category = Category(name="Electronics", description="Electronic products")
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category


def test_generate_sku_basic(db_session, category):
    """Test basic SKU generation."""
    sku = generate_sku("Test Product", category.id, db_session=db_session)
    assert sku.startswith("INV-")
    assert category.name[:4].upper() in sku
    assert sku.endswith("-0001")


def test_generate_sku_sequential(db_session, category):
    """Test sequential SKU generation."""
    sku1 = generate_sku("Product 1", category.id, db_session=db_session)
    sku2 = generate_sku("Product 2", category.id, db_session=db_session)
    
    # Extract sequence numbers
    seq1 = int(sku1.split("-")[-1])
    seq2 = int(sku2.split("-")[-1])
    
    assert seq2 == seq1 + 1


def test_generate_sku_uniqueness(db_session, category):
    """Test SKU uniqueness."""
    skus = set()
    for i in range(10):
        sku = generate_sku(f"Product {i}", category.id, db_session=db_session)
        assert sku not in skus, f"Duplicate SKU generated: {sku}"
        skus.add(sku)


def test_generate_sku_no_category(db_session):
    """Test SKU generation without category."""
    sku = generate_sku("Generic Product", None, db_session=db_session)
    assert sku.startswith("INV-GEN-")
    assert sku.endswith("-0001")

