from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from dotenv import load_dotenv
import os

from database import engine, Base, SessionLocal
from models.db_models import Product, Inventory, ReorderAlert
from routers import auth, inventory, sales, predictions, orders, payments, products, alerts, staff
from routers.alerts import _get_recommended_qty


load_dotenv()


# ---------------------------------------------------------------------------
# Startup scan — alerts for products already below threshold
# ---------------------------------------------------------------------------
async def check_existing_stock_levels():
    db: Session = SessionLocal()
    try:
        all_inventories = db.query(Inventory).all()
        alerts_created = 0
        now = datetime.now(timezone.utc)

        for inv in all_inventories:
            product = db.query(Product).filter(Product.product_id == inv.product_id).first()
            if not product or product.reorder_threshold is None:
                continue
            if inv.current_stock > product.reorder_threshold:
                continue

            existing = (
                db.query(ReorderAlert)
                .filter(
                    ReorderAlert.product_id == inv.product_id,
                    ReorderAlert.is_resolved == False,
                )
                .first()
            )
            if existing:
                continue

            alert_type = "out_of_stock" if inv.current_stock <= 0 else "low_stock"
            rec_qty, _ = _get_recommended_qty(
                db, inv.product_id, inv.shop_id, float(product.reorder_threshold)
            )
            db.add(ReorderAlert(
                shop_id=inv.shop_id,
                product_id=inv.product_id,
                alert_type=alert_type,
                current_stock=float(inv.current_stock),
                threshold=float(product.reorder_threshold),
                recommended_qty=rec_qty,
                is_resolved=False,
                created_at=now,
            ))
            alerts_created += 1

        db.commit()
        print(f"[Startup] Stock scan complete — {alerts_created} alert(s) created")
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    await check_existing_stock_levels()
    yield


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="ShelfSense API",
    description="ML-powered inventory management for kirana stores",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(inventory.router)
app.include_router(sales.router)
app.include_router(predictions.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(alerts.router)
app.include_router(staff.router)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health")
def health_check():
    return {"status": "ok", "message": "ShelfSense API is running"}