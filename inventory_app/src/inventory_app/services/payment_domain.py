"""Payment domain: repositories, gateway interfaces, and processor.

SRP/DIP: PaymentProcessor depends on PaymentGateway abstraction.
Gateways: StripeGateway, PayPalGateway, MockGateway.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol
from inventory_app.models import payment
from sqlalchemy.orm import Session

from inventory_app.models.payment import Payment, PaymentMethod
from inventory_app.utils.logging import logger


class PaymentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_payment(self, payment_id: int) -> Optional[Payment]:
        return self.db.query(Payment).filter(Payment.id == payment_id).first()

    def add_method(self, method: PaymentMethod) -> PaymentMethod:
        self.db.add(method)
        self.db.flush()
        return method

    def add_payment(self, payment: Payment) -> Payment:
        self.db.add(payment)
        self.db.flush()
        return payment

    def commit(self) -> None:
        self.db.commit()

    def refresh(self, obj) -> None:
        self.db.refresh(obj)


@dataclass
class GatewayResult:
    status: str
    reference: Optional[str] = None


class PaymentGateway(Protocol):
    def authorize(self, payment: Payment) -> GatewayResult: ...
    def capture(self, payment: Payment) -> GatewayResult: ...
    def refund(self, payment: Payment, amount: Optional[float] = None) -> GatewayResult: ...

class MockGateway:
    def authorize(self, payment: Payment) -> GatewayResult:
        logger.info(f"[MockGateway] authorize payment {payment.id}")
        return GatewayResult(status="Authorized", reference=f"MOCK-AUTH-{payment.id}")

    def capture(self, payment: Payment) -> GatewayResult:
        logger.info(f"[MockGateway] capture payment {payment.id}")
        return GatewayResult(status="Captured", reference=f"MOCK-CAP-{payment.id}")

    def refund(self, payment: Payment, amount: Optional[float] = None) -> GatewayResult:
        logger.info(f"[MockGateway] refund payment {payment.id} amount={amount}")
        return GatewayResult(status="Refunded", reference=f"MOCK-REF-{payment.id}")