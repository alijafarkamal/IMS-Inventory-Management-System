"""Report generation service with Excel export.

Thin wrappers delegating to domain classes for SRP/DI.
Public API and outputs preserved.
"""
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
from inventory_app.services.report_domain import ReportRepository, ExcelExporter, Reporter


def stock_availability_report(db: Session) -> pd.DataFrame:
    return ReportRepository().stock_availability(db)


def sales_vs_stock_report(db: Session, start_date: datetime = None, end_date: datetime = None) -> pd.DataFrame:
    """Generate sales vs stock report (delegates to ReportRepository)."""
    return ReportRepository().sales_vs_stock(db, start_date, end_date)


def slow_fast_movers_report(db: Session, start_date: datetime = None, end_date: datetime = None) -> pd.DataFrame:
    """Generate slow/fast movers report (delegates to ReportRepository)."""
    return ReportRepository().slow_fast_movers(db, start_date, end_date)


def supplier_performance_report(db: Session, start_date: datetime = None, end_date: datetime = None) -> pd.DataFrame:
    """Generate supplier performance report (delegates to ReportRepository)."""
    return ReportRepository().supplier_performance(db, start_date, end_date)


def export_reports_to_excel(
    db: Session,
    output_path: Path,
    start_date: datetime = None,
    end_date: datetime = None,
):
    """Export all reports to an Excel file with multiple sheets (delegates)."""
    logger.info(f"Exporting reports to {output_path}")
    Reporter(repo=ReportRepository(), exporter=ExcelExporter()).export_all(db, output_path, start_date, end_date)
    logger.info(f"Reports exported successfully to {output_path}")

