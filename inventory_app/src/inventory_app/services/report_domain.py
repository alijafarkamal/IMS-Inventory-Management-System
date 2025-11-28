"""Report domain components for SRP/DI.

- ReportRepository: builds DataFrames for each report
- ExcelExporter: writes multiple DataFrames to an Excel file
- Reporter: orchestrates repository + exporter
"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict

import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from inventory_app.models.product import Product, Supplier
from inventory_app.models.stock import StockLevel
from inventory_app.models.order import Order, OrderItem
from inventory_app.config import ORDER_TYPE_SALE, ORDER_TYPE_PURCHASE


class ReportRepository:
    def stock_availability(self, db: Session) -> pd.DataFrame:
        query = (
            db.query(
                Product.id,
                Product.name,
                Product.sku,
                Product.category_id,
                func.sum(StockLevel.quantity).label("total_stock"),
            )
            .join(StockLevel, Product.id == StockLevel.product_id, isouter=True)
            .filter(Product.is_active == True)
            .group_by(Product.id, Product.name, Product.sku, Product.category_id)
        )
        return pd.read_sql(query.statement, db.bind)

    def sales_vs_stock(self, db: Session, start_date: datetime | None, end_date: datetime | None) -> pd.DataFrame:
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        sales_query = (
            db.query(
                OrderItem.product_id,
                func.sum(OrderItem.quantity).label("sold_quantity"),
                func.sum(OrderItem.subtotal).label("sales_revenue"),
            )
            .join(Order, OrderItem.order_id == Order.id)
            .filter(
                and_(
                    Order.order_type == ORDER_TYPE_SALE,
                    Order.status == "Completed",
                    Order.order_date >= start_date,
                    Order.order_date <= end_date,
                )
            )
            .group_by(OrderItem.product_id)
        )
        sales_df = pd.read_sql(sales_query.statement, db.bind)

        stock_query = db.query(StockLevel.product_id, func.sum(StockLevel.quantity).label("current_stock")).group_by(
            StockLevel.product_id
        )
        stock_df = pd.read_sql(stock_query.statement, db.bind)

        result = sales_df.merge(stock_df, on="product_id", how="outer").fillna(0)
        products = db.query(Product.id, Product.name, Product.sku).filter(Product.is_active == True).all()
        product_dict = {p.id: {"name": p.name, "sku": p.sku} for p in products}
        result["product_name"] = result["product_id"].map(lambda x: product_dict.get(x, {}).get("name", ""))
        result["sku"] = result["product_id"].map(lambda x: product_dict.get(x, {}).get("sku", ""))
        return result[["product_id", "sku", "product_name", "sold_quantity", "sales_revenue", "current_stock"]]

    def slow_fast_movers(self, db: Session, start_date: datetime | None, end_date: datetime | None) -> pd.DataFrame:
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        query = (
            db.query(
                Product.id,
                Product.name,
                Product.sku,
                func.sum(OrderItem.quantity).label("total_sold"),
                func.count(OrderItem.id).label("order_count"),
            )
            .join(OrderItem, Product.id == OrderItem.product_id, isouter=True)
            .join(Order, OrderItem.order_id == Order.id, isouter=True)
            .filter(
                and_(
                    Order.order_type == ORDER_TYPE_SALE,
                    Order.status == "Completed",
                    Order.order_date >= start_date,
                    Order.order_date <= end_date,
                )
            )
            .group_by(Product.id, Product.name, Product.sku)
        )
        df = pd.read_sql(query.statement, db.bind).fillna(0)
        df["mover_type"] = df["total_sold"].apply(lambda x: "Fast Mover" if x > 100 else ("Slow Mover" if x < 10 else "Normal"))
        return df

    def supplier_performance(self, db: Session, start_date: datetime | None, end_date: datetime | None) -> pd.DataFrame:
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        query = (
            db.query(
                Supplier.id,
                Supplier.name,
                func.count(Order.id).label("order_count"),
                func.sum(Order.total_amount).label("total_purchases"),
                func.avg(Order.total_amount).label("avg_order_value"),
            )
            .join(Product, Supplier.id == Product.supplier_id, isouter=True)
            .join(OrderItem, Product.id == OrderItem.product_id, isouter=True)
            .join(Order, OrderItem.order_id == Order.id, isouter=True)
            .filter(
                and_(
                    Order.order_type == ORDER_TYPE_PURCHASE,
                    Order.status == "Completed",
                    Order.order_date >= start_date,
                    Order.order_date <= end_date,
                )
            )
            .group_by(Supplier.id, Supplier.name)
        )
        return pd.read_sql(query.statement, db.bind).fillna(0)


class ExcelExporter:
    def export(self, output_path: Path, sheets: Dict[str, pd.DataFrame]) -> None:
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            for name, df in sheets.items():
                df.to_excel(writer, sheet_name=name, index=False)


class Reporter:
    def __init__(self, repo: ReportRepository, exporter: ExcelExporter) -> None:
        self.repo = repo
        self.exporter = exporter

    def export_all(self, db: Session, output_path: Path, start_date: datetime | None, end_date: datetime | None) -> None:
        sheets = {
            "Stock Availability": self.repo.stock_availability(db),
            "Sales vs Stock": self.repo.sales_vs_stock(db, start_date, end_date),
            "Slow Fast Movers": self.repo.slow_fast_movers(db, start_date, end_date),
            "Supplier Performance": self.repo.supplier_performance(db, start_date, end_date),
        }
        self.exporter.export(output_path, sheets)
