"""Customer management service."""
from sqlalchemy.orm import Session
from inventory_app.models.customer import Customer


def get_all_customers(db: Session) -> list[Customer]:
    return db.query(Customer).filter(Customer.is_active == True).order_by(Customer.name).all()


def create_customer(
    db: Session,
    name: str,
    email: str | None = None,
    phone: str | None = None,
    address: str | None = None,
) -> Customer:
    customer = Customer(name=name, email=email, phone=phone, address=address, is_active=True)
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer
