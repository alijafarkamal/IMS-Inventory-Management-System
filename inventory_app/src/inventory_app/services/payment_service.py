from __future__ import annotations

import os
from typing import Optional
from sqlalchemy.orm import Session

from inventory_app.services.payment_domain import (
    PaymentRepository, PaymentProcessor, MockGateway, StripeGateway, PayPalGateway, PaymentGateway,
)
from inventory_app.models.payment import Payment, PaymentMethod
from inventory_app.utils.logging import logger
def _select_gateway(method_type: str) -> PaymentGateway:
    method_type = (method_type or "").lower()
    if method_type in {"card", "stripe"}:
        api_key = os.getenv("STRIPE_API_KEY", None)
        if api_key is not None and api_key != "":
            return StripeGateway(api_key)
        logger.warning("STRIPE_API_KEY not set; using MockGateway for Stripe")
        return MockGateway()
    if method_type in {"paypal"}:
        client_id = os.getenv("PAYPAL_CLIENT_ID", "")
        secret = os.getenv("PAYPAL_SECRET", "")
        sandbox = os.getenv("PAYPAL_SANDBOX", "true").lower() != "false"
        if client_id and secret:
            return PayPalGateway(client_id, secret, sandbox=sandbox)
        logger.warning("PayPal credentials not set; using MockGateway for PayPal")
        return MockGateway()
    return MockGateway()
class PaymentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = PaymentRepository(db)

    def ensure_method(self, method_type: str, display_name: Optional[str] = None):
        mt = method_type.strip().upper()
        method = self.db.query(PaymentMethod).filter(PaymentMethod.method_type == mt).first()
        if method:
            return method
        method = PaymentMethod(method_type=mt, display_name=display_name or mt.title())
        self.repo.add_method(method)
        self.repo.commit()
        self.repo.refresh(method)
        return method

    def create_payment(self, order_id: int, method_type: str, amount: float, currency: str = "USD"):
        method = self.ensure_method(method_type)
        payment = Payment(order_id=order_id, method_id=method.id, amount=amount, currency=currency, status="Initiated")
        self.repo.add_payment(payment)
        self.repo.commit()
        self.repo.refresh(payment)
        return payment

    def authorize_and_capture(self, payment_id: int, method_type: str):
        gateway = _select_gateway(method_type)
        processor = PaymentProcessor(gateway=gateway, repo=self.repo)
        return processor.process_authorize_capture(payment_id)

    def refund(self, payment_id: int, method_type: str, amount: Optional[float] = None):
        gateway = _select_gateway(method_type)
        processor = PaymentProcessor(gateway=gateway, repo=self.repo)
        return processor.refund(payment_id, amount=amount)


