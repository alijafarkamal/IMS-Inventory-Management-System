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

    def add_method(self, method: PaymentMethod):
        self.db.add(method)
        self.db.flush()
        return method

    def add_payment(self, payment: Payment):
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
    def authorize(self, payment: Payment): ...
    def capture(self, payment: Payment): ...
    def refund(self, payment: Payment, amount: Optional[float] = None): ...

class MockGateway:
    def authorize(self, payment: Payment) -> GatewayResult:
        logger.info(f"[MockGateway] authorize payment {payment.id}")
        return GatewayResult(status="Authorized", reference=f"MOCK-AUTH-{payment.id}")

    def capture(self, payment: Payment):
        logger.info(f"[MockGateway] capture payment {payment.id}")
        return GatewayResult(status="Captured", reference=f"MOCK-CAP-{payment.id}")

    def refund(self, payment: Payment, amount: Optional[float] = None):
        logger.info(f"[MockGateway] refund payment {payment.id} amount={amount}")
        return GatewayResult(status="Refunded", reference=f"MOCK-REF-{payment.id}")
    
class StripeGateway:
    def __init__(self, api_key: str):
        try:
            import stripe 
            stripe.api_key = api_key
            self.stripe = stripe
        except Exception:
            logger.warning("Stripe SDK not available; falling back to MockGateway behavior")
            self.stripe = None
    def authorize(self, payment: Payment):
        if not self.stripe:
            return GatewayResult(status="Authorized", reference=f"STRIPE-MOCK-AUTH-{payment.id}")
        # For simplicity, treat authorization as PaymentIntent creation in test mode
        intent = self.stripe.PaymentIntent.create(amount=int(payment.amount * 100), currency=payment.currency.lower(), capture_method="manual")
        return GatewayResult(status="Authorized", reference=intent.get("id"))
    def capture(self, payment: Payment):
        if not self.stripe:
            return GatewayResult(status="Captured", reference=f"STRIPE-MOCK-CAP-{payment.id}")
        ref = payment.reference
        if not ref:
            return GatewayResult(status="Failed", reference=None)
        intent = self.stripe.PaymentIntent.capture(ref)
        return GatewayResult(status="Captured", reference=intent.get("id"))
    def refund(self, payment: Payment, amount: Optional[float] = None):
        if not self.stripe:
            return GatewayResult(status="Refunded", reference=f"STRIPE-MOCK-REF-{payment.id}")
        ref = payment.reference
        if not ref:
            return GatewayResult(status="Failed", reference=None)
        self.stripe.Refund.create(payment_intent=ref, amount=int((amount or float(payment.amount)) * 100))
        return GatewayResult(status="Refunded", reference=ref)


class PayPalGateway:
    def __init__(self, client_id: str, secret: str, sandbox: bool = True) -> None:
        try:
            import paypalrestsdk  
            paypalrestsdk.configure({
                "mode": "sandbox" if sandbox else "live",
                "client_id": client_id,
                "client_secret": secret,
            })
            self.paypal = paypalrestsdk
        except Exception:
            logger.warning("PayPal SDK not available; falling back to MockGateway behavior")
            self.paypal = None
    def authorize(self, payment: Payment):
        if not self.paypal:
            return GatewayResult(status="Authorized", reference=f"PP-MOCK-AUTH-{payment.id}")
        p = self.paypal.Payment({
            "intent": "authorize",
            "payer": {"payment_method": "paypal"},
            "transactions": [{"amount": {"total": str(payment.amount), "currency": payment.currency}}],
            "redirect_urls": {"return_url": "http://localhost/return", "cancel_url": "http://localhost/cancel"}
        })
        if p.create():
            return GatewayResult(status="Authorized", reference=p.id)
        return GatewayResult(status="Failed", reference=None)

    def capture(self, payment: Payment):
        if not self.paypal:
            return GatewayResult(status="Captured", reference=f"PP-MOCK-CAP-{payment.id}")
        return GatewayResult(status="Captured", reference=payment.reference or f"PP-CAP-{payment.id}")
    def refund(self, payment: Payment, amount: Optional[float] = None):
        if not self.paypal:
            return GatewayResult(status="Refunded", reference=f"PP-MOCK-REF-{payment.id}")
        return GatewayResult(status="Refunded", reference=payment.reference or f"PP-REF-{payment.id}")
class PaymentProcessor:
    def __init__(self, gateway: PaymentGateway, repo: PaymentRepository) -> None:
        self.gateway = gateway
        self.repo = repo

    def process_authorize_capture(self, payment_id: int):
        payment = self.repo.get_payment(payment_id)
        if not payment:
            raise ValueError(f"Payment {payment_id} not found")
    
        auth = self.gateway.authorize(payment)
        payment.status = auth.status
        payment.reference = auth.reference
        self.repo.commit()
        self.repo.refresh(payment)
        if payment.status == "Authorized":
            cap = self.gateway.capture(payment)
            payment.status = cap.status
            payment.reference = cap.reference or payment.reference
            self.repo.commit()
            self.repo.refresh(payment)
        return payment
    def refund(self, payment_id: int, amount: Optional[float] = None):
        payment = self.repo.get_payment(payment_id)
        if not payment:
            raise ValueError(f"Payment {payment_id} not found")
        res = self.gateway.refund(payment, amount=amount)
        payment.status = res.status
        self.repo.commit()
        self.repo.refresh(payment)
        return payment

    