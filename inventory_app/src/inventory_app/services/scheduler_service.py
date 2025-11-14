"""Scheduler service for background tasks."""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from pathlib import Path
import shutil
from inventory_app.db.session import get_db_session
from inventory_app.services.inventory_service import get_low_stock_items
from inventory_app.config import BACKUPS_DIR, DB_PATH
from inventory_app.utils.logging import logger

scheduler = BackgroundScheduler()


def check_low_stock():
    """Check for low stock items and log them."""
    db = next(get_db_session())
    try:
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
    except Exception as e:
        logger.error(f"Error checking low stock: {e}")
    finally:
        db.close()


def backup_database():
    """Create a backup of the database."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = BACKUPS_DIR / f"inventory_backup_{timestamp}.db"
        
        if DB_PATH.exists():
            shutil.copy2(DB_PATH, backup_file)
            logger.info(f"Database backup created: {backup_file}")
            
            # Keep only last 30 backups
            backups = sorted(BACKUPS_DIR.glob("inventory_backup_*.db"))
            if len(backups) > 30:
                for old_backup in backups[:-30]:
                    old_backup.unlink()
                    logger.info(f"Deleted old backup: {old_backup}")
        else:
            logger.warning("Database file not found, skipping backup")
    except Exception as e:
        logger.error(f"Error creating backup: {e}")


def start_scheduler():
    """Start the background scheduler."""
    # Schedule low stock check daily at 9 AM
    scheduler.add_job(
        check_low_stock,
        trigger=CronTrigger(hour=9, minute=0),
        id="low_stock_check",
        name="Daily low stock check",
        replace_existing=True
    )
    
    # Schedule daily backup at 2 AM
    scheduler.add_job(
        backup_database,
        trigger=CronTrigger(hour=2, minute=0),
        id="daily_backup",
        name="Daily database backup",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Scheduler started")


def stop_scheduler():
    """Stop the background scheduler."""
    scheduler.shutdown()
    logger.info("Scheduler stopped")

