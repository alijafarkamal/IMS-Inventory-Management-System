"""Product domain components for SRP/DI.

Classes used by `product_service` to separate responsibilities:
- ProductRepository: data access for products and related lookups
- CategoryRepository: data access for categories
- SupplierRepository: data access for suppliers
- SkuGenerator: small abstraction over SKU generation
- ProductManager: orchestrates create/update/deactivate using repos and SKU generator
"""
from __future__ import annotations

from typing import Optional, List
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import or_

from inventory_app.models.product import Product, Category, Supplier


class ProductRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, product_id: int) -> Optional[Product]:
        return self.db.query(Product).filter(Product.id == product_id).first()

    def add(self, product: Product) -> None:
        self.db.add(product)

    def commit(self) -> None:
        self.db.commit()

    def refresh(self, product: Product) -> None:
        self.db.refresh(product)

    def search(self, query: Optional[str], category_id: Optional[int], active_only: bool) -> List[Product]:
        q = self.db.query(Product)
        if active_only:
            q = q.filter(Product.is_active == True)
        if query:
            q = q.filter(or_(Product.name.ilike(f"%{query}%"), Product.sku.ilike(f"%{query}%")))
        if category_id:
            q = q.filter(Product.category_id == category_id)
        # Ensure deterministic ordering by ID ascending and avoid accidental duplicates
        q = q.order_by(Product.id.asc())
        return q.all()


class CategoryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_all(self) -> List[Category]:
        return self.db.query(Category).order_by(Category.name).all()

    def exists_by_name(self, name: str) -> bool:
        return self.db.query(Category).filter(Category.name == name).first() is not None

    def add(self, category: Category) -> None:
        self.db.add(category)

    def commit(self) -> None:
        self.db.commit()

    def refresh(self, category: Category) -> None:
        self.db.refresh(category)


class SupplierRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_all(self) -> List[Supplier]:
        return self.db.query(Supplier).order_by(Supplier.name).all()

    def exists_by_name(self, name: str) -> bool:
        return self.db.query(Supplier).filter(Supplier.name == name).first() is not None

    def add(self, supplier: Supplier) -> None:
        self.db.add(supplier)

    def commit(self) -> None:
        self.db.commit()

    def refresh(self, supplier: Supplier) -> None:
        self.db.refresh(supplier)


class SkuGenerator:
    def generate(self, *, name: str, category_id: int, db: Session) -> str:
        # Delegates to existing util; separated for DI/testing
        from inventory_app.utils.sku import generate_sku  # local import to avoid cycle
        return generate_sku(name, category_id, db_session=db)


class ProductManager:
    def __init__(self, products: ProductRepository, categories: CategoryRepository, suppliers: SupplierRepository, sku_gen: SkuGenerator) -> None:
        self.products = products
        self.categories = categories
        self.suppliers = suppliers
        self.sku_gen = sku_gen

    def create_product(
        self,
        *,
        name: str,
        category_id: int,
        price: Decimal,
        supplier_id: int | None,
        description: str | None,
        db: Session,
    ) -> Product:
        sku = self.sku_gen.generate(name=name, category_id=category_id, db=db)
        product = Product(
            name=name,
            sku=sku,
            category_id=category_id,
            price=price,
            supplier_id=supplier_id,
            description=description,
            is_active=True,
        )
        self.products.add(product)
        self.products.commit()
        self.products.refresh(product)
        return product

    def update_product(
        self,
        *,
        product_id: int,
        name: str | None,
        category_id: int | None,
        price: Decimal | None,
        supplier_id: int | None,
        description: str | None,
        is_active: bool | None,
    ) -> Product:
        product = self.products.get_by_id(product_id)
        if not product:
            raise ValueError(f"Product with ID {product_id} not found")

        if name is not None:
            product.name = name
        if category_id is not None:
            product.category_id = category_id
        if price is not None:
            product.price = price
        if supplier_id is not None:
            product.supplier_id = supplier_id
        if description is not None:
            product.description = description
        if is_active is not None:
            product.is_active = is_active

        self.products.commit()
        self.products.refresh(product)
        return product

    def deactivate_product(self, *, product_id: int) -> bool:
        product = self.products.get_by_id(product_id)
        if not product:
            raise ValueError(f"Product with ID {product_id} not found")
        product.is_active = False
        self.products.commit()
        return True
