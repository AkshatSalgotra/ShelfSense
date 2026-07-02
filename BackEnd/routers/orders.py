import razorpay
import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from datetime import datetime, timezone

from database import get_db
from models.db_models import Order, OrderItem, Product, Inventory
from core.security import get_pos_actor, PosActor

router = APIRouter(prefix="/orders", tags=["orders"])


def get_razorpay_client():
    key_id     = os.getenv("RAZORPAY_KEY_ID")
    key_secret = os.getenv("RAZORPAY_KEY_SECRET")
    if not key_id or not key_secret:
        raise HTTPException(status_code=503, detail="Razorpay credentials not configured")
    return razorpay.Client(auth=(key_id, key_secret))


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class CartItem(BaseModel):
    product_id: str
    quantity: int


class CreateOrderRequest(BaseModel):
    items: List[CartItem]
    customer_id: uuid.UUID | None = None


class CreateOrderResponse(BaseModel):
    order_id: str
    order_number: str
    razorpay_order_id: str
    amount_paise: int
    amount_rupees: float
    currency: str = "INR"
    key_id: str


class OrderItemDetail(BaseModel):
    product_id: str
    product_name: str
    quantity: int
    unit_price: float
    line_total: float


class OrderDetail(BaseModel):
    order_id: str
    order_number: str
    status: str
    total_amount: float
    razorpay_order_id: str | None
    created_at: datetime
    items: List[OrderItemDetail]


# ---------------------------------------------------------------------------
# POST /orders
# ---------------------------------------------------------------------------
@router.post("", response_model=CreateOrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: CreateOrderRequest,
    db: Session = Depends(get_db),
    actor: PosActor = Depends(get_pos_actor),
):
    if not payload.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    line_items = []
    total      = 0.0

    for cart_item in payload.items:
        product = (
            db.query(Product)
            .filter(
                Product.product_id == cart_item.product_id,
                Product.shop_id    == actor.shop_id,
                Product.is_active  == True,
            )
            .first()
        )
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {cart_item.product_id} not found")
        if cart_item.quantity <= 0:
            raise HTTPException(status_code=400, detail=f"Invalid quantity for {product.product_name}")
        if product.selling_price is None:
            raise HTTPException(status_code=400, detail=f"Product {product.product_name} has no selling price set")

        inventory = (
            db.query(Inventory)
            .filter(Inventory.product_id == cart_item.product_id)
            .first()
        )
        available = inventory.current_stock if inventory else 0
        if available < cart_item.quantity:
            raise HTTPException(
                status_code=409,
                detail=f"Insufficient stock for {product.product_name}. Available: {available}",
            )

        unit_price = float(product.selling_price)
        line_total = unit_price * cart_item.quantity
        total     += line_total
        line_items.append((product, inventory, cart_item.quantity, unit_price, line_total))

    order_number = f"ORD-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"

    order = Order(
        shop_id         = actor.shop_id,
        customer_id     = payload.customer_id,
        cashier_id      = actor.user_id,       # always a real UUID now
        order_number    = order_number,
        status          = "pending",
        subtotal        = round(total, 2),
        discount_amount = 0,
        tax_amount      = 0,
        total_amount    = round(total, 2),
        created_at      = datetime.now(timezone.utc),
    )
    db.add(order)
    db.flush()

    for product, _, qty, unit_price, line_total in line_items:
        db.add(OrderItem(
            order_id        = order.order_id,
            product_id      = product.product_id,
            quantity        = qty,
            unit_price      = unit_price,
            tax_percent     = 0,
            discount_amount = 0,
            line_total      = line_total,
        ))

    # Create Razorpay order
    client      = get_razorpay_client()
    amount_paise = int(round(total * 100))

    try:
        rp_order = client.order.create({
            "amount":   amount_paise,
            "currency": "INR",
            "receipt":  order_number,
            "notes": {
                "shop_id":  str(actor.shop_id),
                "order_id": str(order.order_id),
            },
        })
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=502, detail=f"Razorpay error: {str(e)}")

    order.razorpay_order_id = rp_order["id"]
    db.commit()

    return CreateOrderResponse(
        order_id          = str(order.order_id),
        order_number      = order_number,
        razorpay_order_id = rp_order["id"],
        amount_paise      = amount_paise,
        amount_rupees     = round(total, 2),
        key_id            = os.getenv("RAZORPAY_KEY_ID"),
    )


# ---------------------------------------------------------------------------
# GET /orders/{order_id}
# ---------------------------------------------------------------------------
@router.get("/{order_id}", response_model=OrderDetail)
def get_order(
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

    items = []
    for oi in order.order_items:
        product = db.query(Product).filter(Product.product_id == oi.product_id).first()
        items.append(OrderItemDetail(
            product_id   = str(oi.product_id),
            product_name = product.product_name if product else "Unknown",
            quantity     = oi.quantity,
            unit_price   = float(oi.unit_price),
            line_total   = float(oi.line_total),
        ))

    return OrderDetail(
        order_id          = str(order.order_id),
        order_number      = order.order_number,
        status            = order.status,
        total_amount      = float(order.total_amount),
        razorpay_order_id = order.razorpay_order_id,
        created_at        = order.created_at,
        items             = items,
    )