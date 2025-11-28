# PROJECT NOTES — Inventory Management System Proposal

Date: 2025-11-28
Source: User — "Inventory Management System" requirements (Part 1)

## Summary (short)
The proposal describes a full-featured Inventory Management System covering product CRUD, stock tracking (warehouse + batch/lot), automatic stock updates from sales/purchases/returns, alerts for low stock, expiry/batch tracking, audit logs, transactions (purchase orders, sales orders, returns), reporting (stock, sales vs stock, slow/fast moving, supplier performance), and role-based security (authentication, RBAC, encryption, backups).

## Requirements (grouped)
- Products & Catalog: add/update/delete/deactivate products; categories; SKU generation; search by name/SKU/category.
- Inventory Control: stock levels per product and warehouse; batch/lot and expiry; low-stock notifications; audit logs.
- Transactions: record purchase orders, sales orders, and returns; inventory auto-updates after transactions.
- Reporting: stock availability, sales vs stock, fast/slow movers, supplier performance.
- Security & Ops: RBAC (Admin/Manager/Staff), authentication, encrypt sensitive data, user activity logs, backup/recovery.

## MVP (priority) — implement first
1. Product CRUD (name, SKU, category, price, supplier). SKU auto-generation.
2. Maintain stock levels and update after simple sales/purchases.
3. Search by name/SKU/category.
4. Basic authentication + RBAC (Admin, Manager, Staff).
5. Low-stock alert (configurable threshold).
6. Simple audit log for inventory changes.

## Suggested Data Models (high level)
- Product: id, name, sku, category_id, description, price, supplier_id, is_active, created_at, updated_at
- Category: id, name, parent_id
- Supplier: id, name, contact_info
- Warehouse: id, name, address
- StockLevel: id, product_id, warehouse_id, quantity, reserved_quantity
- Batch/Lot: id, product_id, batch_number, expiry_date, quantity, warehouse_id
- Transaction (abstract): id, type (purchase/sale/return), date, party_id, user_id
- TransactionLine: id, transaction_id, product_id, batch_id, quantity, unit_price
- User: id, username, password_hash, role
- AuditLog: id, user_id, action, entity_type, entity_id, diff, timestamp

## Suggested APIs / Endpoints (examples)
- `POST /api/products` — create product
- `GET /api/products?search=...` — search/list
- `PUT /api/products/{id}` — update product
- `POST /api/transactions/sales` — record a sale (updates stock)
- `POST /api/transactions/purchases` — record purchase (updates stock)
- `POST /api/returns` — handle returns
- `GET /api/reports/stock` — stock availability
- `GET /api/reports/fast-slow-moving` — movement reports
- `POST /api/auth/login` — authentication

## Notifications & Monitoring
- Low-stock alerts: run periodic job (cron/GitHub Actions scheduled) or check at transaction time; notify via email/Slack or in-app notifications.
- Expiry & batch alerts: scheduled checks for approaching expiry.

## Audit & Data Integrity
- Write audit entries on create/update/delete for products, stock changes, transactions.
- Use DB transactions when applying inventory changes to keep consistency.

## Security
- Password hashing (bcrypt/argon2), HTTPS for transport, encrypt sensitive fields if storing financial data.
- RBAC enforced at API layer.
- Backups: periodic DB dump and restore testing.

## Testing & CI
- Unit tests for models and transactions (inventory updates and edge cases).
- Integration tests for API endpoints affecting stock.
- Add GitHub Actions to run tests and linters on PRs.

## Team tasks & suggested split (3 people)
- Member A (Models & Business Logic): define DB schema, implement Product, StockLevel, Batch models, implement transactional inventory updates and audit logging.
- Member B (API & Frontend): implement REST endpoints, search, UI pages (if front-end present), and authentication flows.
- Member C (Testing, CI, Ops): add tests, pre-commit hooks, GitHub Actions workflows, branch protection, deployment/backups.

## Branching & Workflow (per-task)
- Create short-lived branches: `feature/products`, `feature/transactions`, `feature/reports`.
- Use PRs with at least one reviewer and passing CI before merging to `main`.

PowerShell example to create a feature branch and push:
```powershell
Set-Location 'T:\Code\PYTHON\IMS\IMS-Inventory-Management-System'
git checkout main
git pull origin main
git checkout -b feature/products
git push -u origin feature/products
```

## Next actionable steps (recommended)
1. Create issues corresponding to MVP features (Products CRUD, Stock updates, Auth).
2. Design DB schema and migration plan (e.g., using Alembic / Django migrations / Flask-Migrate depending on stack).
3. Implement `Product` and `StockLevel` models + unit tests.
4. Add a minimal GitHub Actions workflow to run tests on PRs.
5. Configure pre-commit hooks (formatters, linters).

## Questions / Clarifications
- Which Python web framework is preferred here (Flask, FastAPI, Django)? The repo looks like a Flask or similar app — confirm.
- Do you already have a preferred DB (Postgres, MySQL, SQLite for dev)?
- Do you want real-time notifications (e.g., via webhook/Slack) or in-app only?

---

If you want, I can now:
- Turn these next actionable steps into GitHub issues and create the `feature/products` branch, or
- Implement `Product` and `StockLevel` models and a migration plus unit tests (MVP task 1), or
- Add a GitHub Actions workflow and a `.pre-commit-config.yaml` to the repo.

Tell me which next action you want me to take.

## UML Diagram (received)

Date received: 2025-11-28

Summary (short):
The attached UML shows an object model for orders, transactions, inventory, reporting, users/roles, notifications, payments, and audit/security. Key classes included are `Order` (and subtypes like `PurchaseOrder`, `SalesOrder`, `ReturnOrder`, `CustomerReturnOrder`, `SupplierReturnOrder`), `OrderLine`, `Product`, `BatchLot`/`Batch`, `Stock`/`StockLevel`, `Warehouse`, `Category`, `Supplier`, `Customer`, `User`, `Role`, `AuditLog`, `Report` (and concrete reports such as `ProductMovementReport`, `StockAvailabilityReport`, `SalesVsStockReport`, `SupplierPerformanceReport`), `Notification`, `Payment` and `PaymentMethod` (with `Cash`, `Card`, `Banking`), and `Notification`.

Key relationships & notes:
- `Order` aggregates `OrderLine` (many lines per order).
- `Order` links to `Supplier` (for purchases) or `Customer` (for sales/returns).
- `Product` relates to `BatchLot`/`Batch` (many batches per product) and to `Stock`/`StockLevel` (per warehouse).
- `StockLevel` holds `quantity`, `minThreshold`, and `reorderPoint` fields — used for low-stock notifications.
- `BatchLot` contains `batchNumber`, `manufactureDate`, and `expiryDate` to support expiry tracking.
- `AuditLog` records user actions (`userId`, `action`, `entity`, `timestamp`).
- `Report` is an abstract class generating various report types.
- `Payment` has a `PaymentMethod` strategy with implementations for `Cash`, `Card`, and `Banking`.
- `Notification` includes `type` (email, SMS, system) and `date` — used for alerts.
- `Role` enumerates `Admin`, `Manager`, `Staff` with described permissions.

Action items from UML:
- Ensure `Order` and `Transaction` models cover subtypes: purchase, sale, supplier/customer returns.
- Implement `OrderLine` model to record product, batch (optional), quantity, and price details.
- Add `Batch`/`Lot` support to `Product` model and migrations for `expiryDate`.
- Implement `StockLevel` per `Warehouse` with `minThreshold` and `reorderPoint` fields and scheduled checks for notifications.
- Add `AuditLog` hooks on create/update/delete for inventory and orders.
- Add `Payment` abstractions only if payment processing will be implemented; otherwise store simple payment records.

Questions raised by UML:
- Do you want `Payment` processing integrated now, or deferred to a future phase? (card/bank integration involves PCI considerations.)
- Which notification channels to implement first (in-app, email, Slack, SMS)?
- Confirm the required reports to implement in MVP (stock availability, sales vs stock, fast/slow movers).

I'll keep this UML summary in the notes and integrate its classes when we implement models.