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
def process_payment(
    db: Session,
    amount: float,
    currency: str,
    method_type: str,
    method_details: dict,
    description: Optional[str] = None,
) -> Payment:
    """Process a payment using the specified method."""
    repo = PaymentRepository(db)
    payment = Payment(
        amount=amount,
        currency=currency,
        method_type=method_type,
        description=description,
        status="Pending",
    )
    repo.add_payment(payment)
    repo.commit()
    repo.refresh(payment)

    gateway = _select_gateway(method_type)
    processor = PaymentProcessor(gateway=gateway)

    result = processor.process_payment(
        payment=payment,
        method_details=method_details,
    )
