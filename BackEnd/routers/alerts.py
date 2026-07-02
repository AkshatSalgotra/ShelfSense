from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from datetime import datetime, timezone, date

from database import get_db
from models.db_models import ReorderAlert, Product, Inventory, MLForecast
from core.security import get_pos_actor

router = APIRouter(prefix="/alerts", tags=["alerts"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class AlertResponse(BaseModel):
    alert_id: str
    product_id: str
    product_name: str
    alert_type: str                  # low_stock | out_of_stock
    current_stock: float
    threshold: float
    recommended_qty: float           # from ML forecast if available, else heuristic
    forecast_source: str             # "ml_forecast" | "heuristic"
    is_resolved: bool
    created_at: datetime


class ResolveAlertRequest(BaseModel):
    quantity_restocked: float


# ---------------------------------------------------------------------------
# GET /alerts  — all active alerts for the shop
# ---------------------------------------------------------------------------
@router.get("", response_model=List[AlertResponse])
def get_active_alerts(
    db: Session = Depends(get_db),
    current_user=Depends(get_pos_actor),
):
    alerts = (
        db.query(ReorderAlert)
        .filter(
            ReorderAlert.shop_id == current_user.shop_id,
            ReorderAlert.is_resolved == False,
        )
        .order_by(ReorderAlert.created_at.desc())
        .all()
    )

    response = []
    for alert in alerts:
        product = db.query(Product).filter(Product.product_id == alert.product_id).first()
        product_name = product.product_name if product else "Unknown"

        # Try to get recommended qty from ML forecast
        recommended_qty, forecast_source = _get_recommended_qty(
            db, alert.product_id, current_user.shop_id, alert.threshold
        )

        response.append(AlertResponse(
            alert_id=str(alert.alert_id),
            product_id=str(alert.product_id),
            product_name=product_name,
            alert_type=alert.alert_type,
            current_stock=alert.current_stock,
            threshold=alert.threshold,
            recommended_qty=recommended_qty,
            forecast_source=forecast_source,
            is_resolved=alert.is_resolved,
            created_at=alert.created_at,
        ))

    return response


# ---------------------------------------------------------------------------
# POST /alerts/{alert_id}/resolve  — manager marks alert resolved after restock
# Also updates inventory to reflect restocked quantity
# ---------------------------------------------------------------------------
@router.post("/{alert_id}/resolve")
def resolve_alert(
    alert_id: str,
    payload: ResolveAlertRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_pos_actor),
):
    alert = (
        db.query(ReorderAlert)
        .filter(
            ReorderAlert.alert_id == alert_id,
            ReorderAlert.shop_id == current_user.shop_id,
        )
        .first()
    )
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    if alert.is_resolved:
        return {"message": "Alert already resolved"}

    now = datetime.now(timezone.utc)

    # Update inventory
    inventory = (
        db.query(Inventory)
        .filter(Inventory.product_id == alert.product_id)
        .first()
    )
    if inventory:
        inventory.current_stock += payload.quantity_restocked
        inventory.last_updated = now

    # Resolve alert
    alert.is_resolved = True
    alert.resolved_at = now

    db.commit()

    return {
        "message": "Alert resolved",
        "alert_id": alert_id,
        "quantity_restocked": payload.quantity_restocked,
        "new_stock": inventory.current_stock if inventory else None,
    }


# ---------------------------------------------------------------------------
# Helper — get recommended restock qty from ML forecast, fallback to heuristic
# ---------------------------------------------------------------------------
def _get_recommended_qty(
    db: Session,
    product_id,
    shop_id,
    threshold: float,
) -> tuple[float, str]:
    """
    Look up the latest ML forecast for this product.
    Recommended qty = forecasted 30-day demand (so they restock enough for a month).
    Falls back to threshold * 3 if no forecast exists.
    """
    today = date.today()

    forecast = (
        db.query(MLForecast)
        .filter(
            MLForecast.product_id == product_id,
            MLForecast.shop_id == shop_id,
            MLForecast.forecast_date >= today,
            MLForecast.horizon_days == 30,
        )
        .order_by(MLForecast.generated_at.desc())
        .first()
    )

    if forecast and forecast.predicted_qty:
        # Restock enough to cover forecasted demand + 20% buffer
        recommended = float(forecast.predicted_qty) * 1.2
        return round(recommended, 1), "ml_forecast"

    # Heuristic fallback: 3x the reorder threshold
    return round(threshold * 3, 1), "heuristic"