import sys
sys.path.insert(0, 'inventory_app/src')
from inventory_app.db.session import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text('DROP TABLE IF EXISTS _alembic_tmp_orders'))
    conn.commit()
print("Temp table dropped successfully")
