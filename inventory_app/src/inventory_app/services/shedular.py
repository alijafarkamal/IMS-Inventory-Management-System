"""Scheduler service for background tasks.

Uses domain classes for SRP/DI, preserves API and schedules.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from pathlib import Path
import shutil
from inventory_app.db.session import get_db_session
from inventory_app.config import BACKUPS_DIR, DB_PATH
from inventory_app.utils.logging import logger
from inventory_app.services.scheduler_domain import LowStockChecker, DatabaseBackups



scheduler = BackgroundScheduler()
def check_low_stock():
    """Check for low stock items and log them (delegates)."""
    db = next(get_db_session())
    try:
        LowStockChecker().run(db)
    except Exception as e:
        logger.error(f"Error checking low stock: {e}")
    finally:
        db.close()


def backup_database():
    """Create a backup of the database (delegates)."""
    try:
        DatabaseBackups(BACKUPS_DIR, DB_PATH, keep=30).run()
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

