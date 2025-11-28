"""Scheduler domain components for SRP/DI.

- LowStockChecker: checks low stock and logs
- DatabaseBackups: creates DB backups and prunes old ones
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil

from sqlalchemy.orm import Session

from inventory_app.config import BACKUPS_DIR, DB_PATH
from inventory_app.utils.logging import logger
from inventory_app.services.inventory_service import get_low_stock_items


class LowStockChecker:
    def run(self, db: Session) -> None:
        low_stock = get_low_stock_items(db)
        if low_stock:
            logger.warning(f"Found {len(low_stock)} items with low stock")
            for item in low_stock:
                logger.warning(
                    f"Low stock: {item['product_name']} (SKU: {item['sku']}) "
                    f"in {item['warehouse_name']}: {item['quantity']} units"
                )
        else:
            logger.info("No low stock items found")


class DatabaseBackups:
    def __init__(self, backups_dir: Path = BACKUPS_DIR, db_path: Path = DB_PATH, keep: int = 30) -> None:
        self.backups_dir = backups_dir
        self.db_path = db_path
        self.keep = keep

    def run(self) -> None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backups_dir / f"inventory_backup_{timestamp}.db"

        if self.db_path.exists():
            shutil.copy2(self.db_path, backup_file)
            logger.info(f"Database backup created: {backup_file}")
            backups = sorted(self.backups_dir.glob("inventory_backup_*.db"))
            if len(backups) > self.keep:
                for old_backup in backups[:-self.keep]:
                    old_backup.unlink()
                    logger.info(f"Deleted old backup: {old_backup}")
        else:
            logger.warning("Database file not found, skipping backup")
