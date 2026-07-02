import hmac
import hashlib
import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timezone
from routers.alerts import _get_recommended_qty

from database import get_db
from models.db_models import Order, OrderItem, Payment, Inventory, InventoryLog, SalesLog, ReorderAlert, Product
from core.security import get_pos_actor, PosActor
from core.alerts_logic import trigger_reorder_alert

router = APIRouter(prefix="/payments", tags=["payments"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class VerifyPaymentRequest(BaseModel):
    razorpay_order_id:  str
    razorpay_payment_id: str
    razorpay_signature: str


class VerifyPaymentResponse(BaseModel):
    success:      bool
    order_id:     str
    order_number: str
    payment_id:   str
    total_amount: float
    message:      str


# ---------------------------------------------------------------------------
# POST /payments/verify
# ---------------------------------------------------------------------------
@router.post("/verify", response_model=VerifyPaymentResponse)
def verify_payment(
    payload: VerifyPaymentRequest,
    db: Session = Depends(get_db),
    actor: PosActor = Depends(get_pos_actor),
):
    # ---- 1. Signature check (skipped in development) ----------------------
    if os.getenv("ENV") != "development":
        key_secret   = os.getenv("RAZORPAY_KEY_SECRET", "")
        body         = f"{payload.razorpay_order_id}|{payload.razorpay_payment_id}"
        expected_sig = hmac.new(
            key_secret.encode("utf-8"),
            body.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected_sig, payload.razorpay_signature):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payment signature")

    # ---- 2. Find order -----------------------------------------------------
    order = (
        db.query(Order)
        .filter(
            Order.razorpay_order_id == payload.razorpay_order_id,
            Order.shop_id           == actor.shop_id,
        )
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # ---- Idempotency -------------------------------------------------------
    if order.status == "completed":
        existing_payment = db.query(Payment).filter(Payment.order_id == order.order_id).first()
        return VerifyPaymentResponse(
            success      = True,
            order_id     = str(order.order_id),
            order_number = order.order_number,
            payment_id   = existing_payment.transaction_id if existing_payment else payload.razorpay_payment_id,
            total_amount = float(order.total_amount),
            message      = "Payment already recorded",
        )

    if order.status == "cancelled":
        raise HTTPException(status_code=409, detail="Order was cancelled")

    now = datetime.now(timezone.utc)

    # ---- 3. Record payment -------------------------------------------------
    payment = Payment(
        order_id         = order.order_id,
        transaction_id   = payload.razorpay_payment_id,
        payment_method   = "upi",
        payment_status   = "success",
        amount_paid      = order.total_amount,
        change_returned  = 0,
        gateway          = "razorpay",
        gateway_response = {
            "razorpay_payment_id": payload.razorpay_payment_id,
            "razorpay_order_id":   payload.razorpay_order_id,
            "razorpay_signature":  payload.razorpay_signature,
        },
        paid_at = now,
    )
    db.add(payment)

    # ---- 4. Decrement inventory + audit + sales log -----------------------
    order_items    = db.query(OrderItem).filter(OrderItem.order_id == order.order_id).all()
    alerts_created = 0

    for item in order_items:
        inventory = (
            db.query(Inventory)
            .filter(Inventory.product_id == item.product_id)
            .with_for_update()
            .first()
        )
        if not inventory:
            continue

        stock_before = inventory.current_stock
        stock_after  = stock_before - item.quantity

        inventory.current_stock = stock_after
        inventory.last_updated  = now

        db.add(InventoryLog(
            shop_id         = actor.shop_id,
            product_id      = item.product_id,
            change_type     = "sale",
            quantity_change = -item.quantity,
            stock_before    = stock_before,
            stock_after     = stock_after,
            reference_id    = order.order_id,
            note            = f"Sale via order {order.order_number}",
            created_by      = actor.user_id,   # always a real UUID now
            created_at      = now,
        ))

        db.add(SalesLog(
            shop_id       = actor.shop_id,
            product_id    = item.product_id,
            order_id      = order.order_id,
            quantity_sold = item.quantity,
            sale_date     = now.date(),
            note          = f"order:{order.order_number}",
            created_at    = now,
        ))

        # ---- 5. Reorder alert check ----------------------------------------
        trigger_reorder_alert(db, item.product_id, actor.shop_id)
        alerts_created += 1 # Simplified counter for API response

    # ---- 6. Mark order completed -------------------------------------------
    order.status       = "completed"
    order.completed_at = now

    db.commit()

    return VerifyPaymentResponse(
        success      = True,
        order_id     = str(order.order_id),
        order_number = order.order_number,
        payment_id   = payload.razorpay_payment_id,
        total_amount = float(order.total_amount),
        message      = f"Payment verified. {alerts_created} reorder alert(s) triggered.",
    )


# ---------------------------------------------------------------------------
# GET /payments/order/{order_id}
# ---------------------------------------------------------------------------
@router.get("/order/{order_id}")
def get_payment_for_order(
    order_id: str,
    db: Session = Depends(get_db),
    actor: PosActor = Depends(get_pos_actor),
):
    order = (
        db.query(Order)
        .filter(Order.order_id == order_id, Order.shop_id == actor.shop_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    payment = db.query(Payment).filter(Payment.order_id == order_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    return {
        "payment_id":       str(payment.payment_id),
        "transaction_id":   payment.transaction_id,
        "amount_paid":      float(payment.amount_paid),
        "payment_status":   payment.payment_status,
        "payment_method":   payment.payment_method,
        "gateway":          payment.gateway,
        "gateway_response": payment.gateway_response,
        "paid_at":          payment.paid_at,
    }