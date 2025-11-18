# Inventory Management System

A production-ready desktop inventory management application built with Python, Tkinter, and SQLite. Features role-based access control, product management, stock tracking, batch/lot management, sales/purchase orders, comprehensive reporting, and audit logging.

## Features

- **User Authentication & RBAC**: Login system with Admin, Manager, and Staff roles
- **Product Management**: Full CRUD operations with automatic SKU generation
- **Stock Management**: Multi-warehouse stock tracking with batch/lot support and expiry dates
- **Order Management**: Sales orders, purchase orders, and returns with automatic stock updates
- **Low Stock Alerts**: Automated daily checks with UI notifications
- **Audit Logging**: Complete audit trail of all inventory changes
- **Reports**: Stock availability, sales vs stock, slow/fast movers, supplier performance with Excel export
- **Data Backup**: Automated daily database backups
- **Modern UI**: Clean, responsive interface using ttkbootstrap

## Requirements

- Ubuntu (tested on 20.04+)
- Python 3.10 or higher
- pip and venv

## Installation

### 1. Install System Dependencies

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-dev build-essential
```

### 2. Clone/Setup Project

```bash
cd /path/to/SDA-Project
```

### 3. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Initialize Database

```bash
# Run Alembic migrations
cd inventory_app/src
alembic upgrade head
cd ../../..
```

### 6. Seed Sample Data (Optional)

```bash
python scripts/seed_sample_data.py
```

This creates:
- Admin user (username: `admin`, password: `admin123`)
- Sample categories, suppliers, warehouses
- 20 sample products with stock levels
- Sample batches with expiry dates

## Running the Application

### Development Mode

```bash
source venv/bin/activate
python -m inventory_app.main
```

Or from the project root:

```bash
source venv/bin/activate
cd inventory_app/src
python -m inventory_app.main
```

### Default Login Credentials

After seeding sample data:
- **Username**: `admin`
- **Password**: `admin123`
- **Role**: Admin

## Running Tests

```bash
source venv/bin/activate
pytest -v
```

Or with coverage:

```bash
pytest --cov=inventory_app --cov-report=html
```

## Building Linux Executable

### Using PyInstaller

```bash
bash packaging/build_linux.sh
```

The executable will be created at `dist/inventory_app`.

### Manual Build

```bash
source venv/bin/activate
pip install pyinstaller

pyinstaller --name="inventory_app" \
    --onefile \
    --windowed \
    --add-data="inventory_app/src/inventory_app:inventory_app" \
    --hidden-import="ttkbootstrap" \
    --hidden-import="sqlalchemy.dialects.sqlite" \
    inventory_app/src/inventory_app/main.py
```

## Database Backup & Restore

### Manual Backup

```bash
# Backup
cp data/inventory.db backups/inventory_backup_$(date +%Y%m%d_%H%M%S).db

# Or use SQLite dump
sqlite3 data/inventory.db .dump > backups/inventory_backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restore from Backup

```bash
# Restore from SQLite file
cp backups/inventory_backup_YYYYMMDD_HHMMSS.db data/inventory.db

# Or restore from SQL dump
sqlite3 data/inventory.db < backups/inventory_backup_YYYYMMDD_HHMMSS.sql
```

### Automated Backups

The application automatically creates daily backups at 2:00 AM. Backups are stored in the `backups/` directory. Only the last 30 backups are kept.

## Project Structure

```
inventory_app/
├── src/
│   └── inventory_app/
│       ├── main.py              # Application entry point
│       ├── config.py            # Configuration
│       ├── ui/                  # UI components
│       │   ├── login.py
│       │   ├── dashboard.py
│       │   ├── products.py
│       │   ├── orders.py
│       │   ├── reports.py
│       │   └── styles.py
│       ├── models/              # SQLAlchemy models
│       │   ├── user.py
│       │   ├── product.py
│       │   ├── stock.py
│       │   ├── order.py
│       │   └── audit.py
│       ├── services/            # Business logic
│       │   ├── auth_service.py
│       │   ├── product_service.py
│       │   ├── inventory_service.py
│       │   ├── order_service.py
│       │   ├── report_service.py
│       │   └── scheduler_service.py
│       ├── db/                  # Database
│       │   ├── session.py
│       │   └── alembic/         # Migrations
│       └── utils/               # Utilities
│           ├── sku.py
│           ├── crypto.py
│           └── logging.py
├── tests/                       # Unit tests
├── scripts/                     # Utility scripts
│   └── seed_sample_data.py
├── packaging/                   # Build scripts
│   └── build_linux.sh
├── data/                        # Database files (created at runtime)
├── backups/                     # Backup files (created at runtime)
├── logs/                        # Log files (created at runtime)
├── requirements.txt
└── README.md
```

## Key Components

### Models

- **User**: User accounts with role-based access
- **Product**: Products with SKU, category, price, supplier
- **Category**: Product categories
- **Supplier**: Supplier information
- **Warehouse**: Warehouse locations
- **StockLevel**: Stock quantities per product per warehouse
- **Batch**: Batch/lot tracking with expiry dates
- **Order**: Sales, purchase, and return orders
- **OrderItem**: Order line items
- **InventoryAudit**: Audit log for all changes

### Services

- **auth_service**: Authentication and authorization
- **product_service**: Product CRUD operations
- **inventory_service**: Stock adjustments, batch management, low stock detection
- **order_service**: Order creation and processing
- **report_service**: Report generation and Excel export
- **scheduler_service**: Background tasks (low stock checks, backups)

### UI Screens

- **Login**: User authentication
- **Dashboard**: Overview with low stock alerts and recent transactions
- **Products**: Product list, search, add/edit, view details with batches
- **Orders**: Create sales/purchase/return orders
- **Reports**: Generate and export reports

## Role-Based Access Control

- **Admin**: Full access to all features
- **Manager**: Can manage products, orders, and view reports
- **Staff**: Can view products, create orders, view reports

## Configuration

Edit `inventory_app/src/inventory_app/config.py` to customize:

- Database path
- Low stock threshold
- SKU prefix and format
- Backup retention
- Logging settings

## Database Schema (Local SQLite) — Tables, Keys, and Flows

This section defines the complete local database schema used by the application, aligned to the 26 requirements. Most tables already exist in the code; a few optional tables/columns are included to fully support customer-linked sales orders and richer audit/notification capabilities.

### Conventions
- PK: Primary Key, FK: Foreign Key, UQ: Unique, IX: Index
- All timestamp fields come from a common `TimestampMixin` in models (created_at, updated_at).

### Core Master Data

- `users` (PK: `id`)
   - `username` (UQ, IX)
   - `email` (UQ)
   - `password_hash`
   - `full_name`
   - `role` (text: `Admin` | `Manager` | `Staff`)
   - `is_active` (bool)
   - Supports Req 22, 23, 24 (via hashed passwords), 25 (via audits), 26 (indirect)

- `roles` (PK: `id`) [optional / future]
   - `name` (UQ)
   - `description`
   - Note: current app stores role on `users.role`. This table can back future granular RBAC.

- `categories` (PK: `id`)
   - `name` (UQ)
   - `description`
   - Supports Req 7

- `suppliers` (PK: `id`)
   - `name` (UQ)
   - `contact_person`, `email`, `phone`, `address`
   - Used by products and purchase orders; supports reporting (Req 21)

- `customers` (PK: `id`) [planned]
   - `name` (IX)
   - `email` (UQ, nullable)
   - `phone` (nullable)
   - `address` (nullable)
   - Supports Req 15 (customer-linked sales orders)

- `products` (PK: `id`)
   - `name` (IX)
   - `sku` (UQ, IX)
   - `category_id` (FK → `categories.id`)
   - `price` (numeric)
   - `supplier_id` (FK → `suppliers.id`, nullable)
   - `is_active` (bool)
   - `description` (nullable)
   - Supports Req 1–3, 6–8

### Inventory & Warehouses

- `warehouses` (PK: `id`)
   - `name` (UQ)
   - `location` (nullable)
   - `is_active` (bool)
   - Supports Req 13

- `stock_levels` (PK: `id`)
   - `product_id` (FK → `products.id`)
   - `warehouse_id` (FK → `warehouses.id`)
   - `quantity` (int, default 0)
   - `reserved_quantity` (int, default 0)
   - Composite uniqueness is enforced at the application level (one row per product+warehouse). Supports Req 4, 5, 13, 16

- `batches` (PK: `id`)
   - `product_id` (FK → `products.id`)
   - `warehouse_id` (FK → `warehouses.id`)
   - `batch_number` (text)
   - `quantity` (int)
   - `expiry_date` (datetime, nullable)
   - `received_date` (datetime)
   - Supports Req 10, 11; FEFO selection during sales is handled in service logic.

### Orders & Transactions

- `orders` (PK: `id`)
   - `order_number` (UQ, IX; e.g., `SO-00001`, `PO-00001`, `RT-00001`)
   - `order_type` (text: `Sale` | `Purchase` | `Return`)
   - `status` (text: `Pending` | `Completed` | `Cancelled`)
   - `total_amount` (numeric)
   - `user_id` (FK → `users.id`) creator/owner of the order
   - `order_date` (datetime)
   - `notes` (text, nullable)
   - `customer_id` (FK → `customers.id`, nullable) [planned; for sales orders]
   - `supplier_id` (FK → `suppliers.id`, nullable) [planned; for purchase orders]
   - Supports Req 14–17, 19–21

- `order_items` (PK: `id`)
   - `order_id` (FK → `orders.id`)
   - `product_id` (FK → `products.id`)
   - `warehouse_id` (FK → `warehouses.id`)
   - `quantity` (int)
   - `unit_price` (numeric)
   - `subtotal` (numeric)

- `order_item_batches` (PK: `id`) [optional / planned]
   - Links order items to specific batches consumed (for full traceability).
   - `order_item_id` (FK → `order_items.id`)
   - `batch_id` (FK → `batches.id`)
   - `quantity` (int)
   - Enables explicit batch consumption history (enhances Req 10–11, 12).

### Audits, Notifications, Backup

- `inventory_audit` (PK: `id`)
   - `user_id` (FK → `users.id`)
   - `action` (text; e.g., `STOCK_ADJUST`, `ORDER_CREATE`, `PRODUCT_UPDATE`)
   - `entity_type` (text; e.g., `StockLevel`, `Order`, `Product`)
   - `entity_id` (int)
   - `old_values` (JSON)
   - `new_values` (JSON)
   - `reason` (text, nullable)
   - `timestamp` (datetime)
   - Supports Req 12, 25

- `notifications` (PK: `id`) [optional / planned]
   - `type` (text; e.g., `LOW_STOCK`, `NEAR_EXPIRY`)
   - `payload` (JSON; includes product, warehouse, thresholds)
   - `seen` (bool, default false)
   - `created_at` (datetime)
   - Backed by the scheduler for low stock checks (Req 9). Current code logs warnings; this table enables persistent UI notifications.

## GUI Actions → DB CRUD & Query Flows

- Add Product (Req 1, 8)
   - INSERT `products` (auto SKU generated), optional `suppliers`
   - Audit: INSERT `inventory_audit` (`PRODUCT_CREATE`)

- Update Product (Req 2)
   - UPDATE `products` (name, category, price, supplier, description)
   - Audit: `PRODUCT_UPDATE` (old/new JSON)

- Deactivate Product (Req 3)
   - UPDATE `products.is_active` = false
   - Audit: `PRODUCT_DEACTIVATE`

- Create Warehouse (Req 13)
   - INSERT `warehouses`

- Create Batch (Req 10, 11)
   - INSERT `batches`; UPDATE `stock_levels` via service; Audit `BATCH_CREATE` + `STOCK_ADJUST`

- Adjust Stock (automatic) (Req 4, 5, 16)
   - UPDATE/INSERT `stock_levels`; optional batch decrement
   - Audit: `STOCK_ADJUST`

- Create Purchase Order (Req 14, 16)
   - INSERT `orders` (`Purchase`), INSERT `order_items`
   - Auto-Update: increase `stock_levels`, Audit `ORDER_CREATE` + `STOCK_ADJUST`

- Create Sales Order (Req 15, 16)
   - INSERT `orders` (`Sale`), INSERT `order_items`
   - Auto-Update: decrease `stock_levels`, FEFO batch decrement when available
   - Audit: `ORDER_CREATE` + `STOCK_ADJUST`

- Process Return (Req 17)
   - INSERT `orders` (`Return`), INSERT `order_items`
   - Auto-Update: increase `stock_levels`; Audit `ORDER_CREATE` + `STOCK_ADJUST`

- Search Products (Req 6)
   - SELECT on `products` with `name`/`sku` ILIKE + optional `category_id`

- Reports (Req 18–21)
   - Stock availability: JOIN `products` + aggregate `stock_levels`
   - Sales vs Stock: aggregate `order_items` (sales) + `stock_levels`
   - Slow/Fast movers: aggregate sales `order_items` by product
   - Supplier performance: aggregate purchase `orders`/`order_items` by supplier

- Low Stock Notifications (Req 9)
   - Scheduler evaluates `stock_levels` < threshold.
   - Current: log warnings. Optional: INSERT `notifications` rows for UI display.

- Authentication & RBAC (Req 22–25)
   - Users stored in `users` with `role` string hierarchy (Admin > Manager > Staff)
   - Passwords stored as bcrypt hashes
   - Sensitive operations write `inventory_audit`

- Backup (Req 26)
   - Filesystem-level backups of DB file (`backups/`), managed by scheduler.

## Planned Schema Additions (to fully meet all requirements)

1) `customers` table + `orders.customer_id` (nullable) for sales orders.
2) `orders.supplier_id` (nullable) for explicit supplier linkage on purchase orders.
3) `order_item_batches` for explicit batch consumption traceability in sales.
4) `notifications` table for persistent low-stock and expiry alerts.

These can be added via Alembic migrations without breaking existing data.

## Migration to PostgreSQL

To migrate from SQLite to PostgreSQL:

1. Update `DB_URL` in `config.py`:
   ```python
   DB_URL = "postgresql://user:password@localhost/inventory"
   ```

2. Install PostgreSQL driver:
   ```bash
   pip install psycopg2-binary
   ```

3. Run migrations:
   ```bash
   alembic upgrade head
   ```

4. The application will work with PostgreSQL without code changes.

## Troubleshooting

### Database Locked Error

If you see "database is locked" errors:
- Ensure only one instance of the application is running
- Check for stale lock files in the `data/` directory

### Import Errors

If you encounter import errors:
- Ensure you're in the correct directory
- Activate the virtual environment
- Check that all dependencies are installed: `pip install -r requirements.txt`

### UI Not Displaying

- Ensure ttkbootstrap is installed: `pip install ttkbootstrap`
- Check that you're using Python 3.10+
- Try running with `python -m inventory_app.main` from the `inventory_app/src` directory

## Development

### Adding New Features

1. Create models in `models/`
2. Create services in `services/`
3. Create UI components in `ui/`
4. Add tests in `tests/`
5. Create migration if needed: `alembic revision --autogenerate -m "description"`

### Running Migrations

```bash
# Create new migration
cd inventory_app/src
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## License

This project is provided as-is for educational and development purposes.

## Support

For issues or questions, please check the logs in `logs/inventory_app.log`.

