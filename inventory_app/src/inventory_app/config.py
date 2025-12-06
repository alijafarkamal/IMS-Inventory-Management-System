"""Configuration settings for the inventory management system."""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent.parent.parent
SRC_DIR = BASE_DIR / "inventory_app" / "src"
DATA_DIR = BASE_DIR / "data"
BACKUPS_DIR = BASE_DIR / "backups"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
BACKUPS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Database
DB_PATH = DATA_DIR / "inventory.db"
DB_URL = f"sqlite:///{DB_PATH}"

# Application settings
APP_NAME = "Inventory Management System"
APP_VERSION = "1.0.0"

# Security
PASSWORD_HASH_ALGORITHM = "bcrypt"
ENCRYPTION_KEY_LENGTH = 32

# Inventory settings
LOW_STOCK_THRESHOLD = 10  # Alert when stock < this value
SKU_PREFIX = "INV"
SKU_LENGTH = 10

# Roles
ROLE_ADMIN = "Admin"
ROLE_MANAGER = "Manager"
ROLE_STAFF = "Staff"

# Order types
ORDER_TYPE_SALE = "Sale"
ORDER_TYPE_PURCHASE = "Purchase"
ORDER_TYPE_RETURN = "Return"
ORDER_TYPE_CUSTOMER_RETURN = "CustomerReturn"
ORDER_TYPE_SUPPLIER_RETURN = "SupplierReturn"

# Payment gateway configuration (read from environment; optional .env support)
try:
	from dotenv import load_dotenv  # type: ignore
	load_dotenv()
except Exception:
	pass

STRIPE_API_KEY = os.getenv("STRIPE_API_KEY", "")
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID", "")
PAYPAL_SECRET = os.getenv("PAYPAL_SECRET", "")
PAYPAL_SANDBOX = os.getenv("PAYPAL_SANDBOX", "true").lower() != "false"

