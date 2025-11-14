"""Report generation service with Excel export."""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from inventory_app.models.product import Product, Supplier
from inventory_app.models.stock import StockLevel
from inventory_app.models.order import Order, OrderItem
from inventory_app.config import ORDER_TYPE_SALE, ORDER_TYPE_PURCHASE
import pandas as pd
from pathlib import Path
from inventory_app.utils.logging import logger


def stock_availability_report(db: Session) -> pd.DataFrame:
    """Generate stock availability report."""
    query = db.query(
        Product.id,
        Product.name,
        Product.sku,
        Product.category_id,
        func.sum(StockLevel.quantity).label("total_stock")
    ).join(
        StockLevel, Product.id == StockLevel.product_id, isouter=True
    ).filter(
        Product.is_active == True
    ).group_by(
        Product.id, Product.name, Product.sku, Product.category_id
    )
    
    df = pd.read_sql(query.statement, db.bind)
    return df


def sales_vs_stock_report(db: Session, start_date: datetime = None, end_date: datetime = None) -> pd.DataFrame:
    """Generate sales vs stock report."""
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()
    
    # Get sales data
    sales_query = db.query(
        OrderItem.product_id,
        func.sum(OrderItem.quantity).label("sold_quantity"),
        func.sum(OrderItem.subtotal).label("sales_revenue")
    ).join(
        Order, OrderItem.order_id == Order.id
    ).filter(
        and_(
            Order.order_type == ORDER_TYPE_SALE,
            Order.status == "Completed",
            Order.order_date >= start_date,
            Order.order_date <= end_date
        )
    ).group_by(OrderItem.product_id)
    
    sales_df = pd.read_sql(sales_query.statement, db.bind)
    
    # Get stock data
    stock_query = db.query(
        StockLevel.product_id,
        func.sum(StockLevel.quantity).label("current_stock")
    ).group_by(StockLevel.product_id)
    
    stock_df = pd.read_sql(stock_query.statement, db.bind)
    
    # Merge
    result = sales_df.merge(stock_df, on="product_id", how="outer")
    result = result.fillna(0)
    
    # Add product names
    products = db.query(Product.id, Product.name, Product.sku).filter(Product.is_active == True).all()
    product_dict = {p.id: {"name": p.name, "sku": p.sku} for p in products}
    
    result["product_name"] = result["product_id"].map(lambda x: product_dict.get(x, {}).get("name", ""))
    result["sku"] = result["product_id"].map(lambda x: product_dict.get(x, {}).get("sku", ""))
    
    return result[["product_id", "sku", "product_name", "sold_quantity", "sales_revenue", "current_stock"]]


def slow_fast_movers_report(db: Session, start_date: datetime = None, end_date: datetime = None) -> pd.DataFrame:
    """Generate slow/fast movers report."""
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()
    
    query = db.query(
        Product.id,
        Product.name,
        Product.sku,
        func.sum(OrderItem.quantity).label("total_sold"),
        func.count(OrderItem.id).label("order_count")
    ).join(
        OrderItem, Product.id == OrderItem.product_id, isouter=True
    ).join(
        Order, OrderItem.order_id == Order.id, isouter=True
    ).filter(
        and_(
            Order.order_type == ORDER_TYPE_SALE,
            Order.status == "Completed",
            Order.order_date >= start_date,
            Order.order_date <= end_date
        )
    ).group_by(Product.id, Product.name, Product.sku)
    
    df = pd.read_sql(query.statement, db.bind)
    df = df.fillna(0)
    
    # Classify as fast/slow mover
    df["mover_type"] = df["total_sold"].apply(
        lambda x: "Fast Mover" if x > 100 else ("Slow Mover" if x < 10 else "Normal")
    )
    
    return df


def supplier_performance_report(db: Session, start_date: datetime = None, end_date: datetime = None) -> pd.DataFrame:
    """Generate supplier performance report."""
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()
    
    query = db.query(
        Supplier.id,
        Supplier.name,
        func.count(Order.id).label("order_count"),
        func.sum(Order.total_amount).label("total_purchases"),
        func.avg(Order.total_amount).label("avg_order_value")
    ).join(
        Product, Supplier.id == Product.supplier_id, isouter=True
    ).join(
        OrderItem, Product.id == OrderItem.product_id, isouter=True
    ).join(
        Order, OrderItem.order_id == Order.id, isouter=True
    ).filter(
        and_(
            Order.order_type == ORDER_TYPE_PURCHASE,
            Order.status == "Completed",
            Order.order_date >= start_date,
            Order.order_date <= end_date
        )
    ).group_by(Supplier.id, Supplier.name)
    
    df = pd.read_sql(query.statement, db.bind)
    df = df.fillna(0)
    
    return df


def export_reports_to_excel(
    db: Session,
    output_path: Path,
    start_date: datetime = None,
    end_date: datetime = None
):
    """Export all reports to an Excel file with multiple sheets."""
    logger.info(f"Exporting reports to {output_path}")
    
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        # Stock Availability
        stock_df = stock_availability_report(db)
        stock_df.to_excel(writer, sheet_name="Stock Availability", index=False)
        
        # Sales vs Stock
        sales_df = sales_vs_stock_report(db, start_date, end_date)
        sales_df.to_excel(writer, sheet_name="Sales vs Stock", index=False)
        
        # Slow/Fast Movers
        movers_df = slow_fast_movers_report(db, start_date, end_date)
        movers_df.to_excel(writer, sheet_name="Slow Fast Movers", index=False)
        
        # Supplier Performance
        supplier_df = supplier_performance_report(db, start_date, end_date)
        supplier_df.to_excel(writer, sheet_name="Supplier Performance", index=False)
    
    logger.info(f"Reports exported successfully to {output_path}")

