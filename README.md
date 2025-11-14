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

