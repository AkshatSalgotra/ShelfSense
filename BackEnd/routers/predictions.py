from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from database import get_db
from models.db_models import Shop, Product, SalesLog
from schemas.pydantic_schemas import PredictionOut
from core.security import get_current_manager
from ml.forecaster import generate_forecast

router = APIRouter(prefix="/predictions", tags=["Predictions"])


@router.get("/all", response_model=List[PredictionOut])
def predict_all(
    days: int = Query(default=14, ge=1, le=90, alias="days"),
    forecast_days: int = Query(default=14, ge=1, le=90),
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_manager),
):
    """Runs forecasts for all products in the shop at once."""
    # Use 'days' if provided via alias, else 'forecast_days'
    actual_days = days if days != 14 else forecast_days
    
    products = db.query(Product).filter(Product.shop_id == shop.shop_id).all()
    results = []
    for product in products:
        sales = db.query(SalesLog).filter(
            SalesLog.product_id == product.product_id,
            SalesLog.shop_id == shop.shop_id
        ).all()
        result = generate_forecast(
            product=product,
            sales=sales,
            forecast_days=actual_days,
            db=db,
            state=shop.state,
        )
        results.append(PredictionOut(**result))
    return results


@router.get("/{product_id}", response_model=PredictionOut)
def predict_product(
    product_id: UUID,
    days: int = Query(default=14, ge=1, le=90, alias="days"),
    forecast_days: int = Query(default=14, ge=1, le=90),
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_manager),
):
    actual_days = days if days != 14 else forecast_days
    
    product = db.query(Product).filter(
        Product.product_id == product_id,
        Product.shop_id == shop.shop_id
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    sales = db.query(SalesLog).filter(
        SalesLog.product_id == product_id,
        SalesLog.shop_id == shop.shop_id
    ).all()

    result = generate_forecast(
        product=product,
        sales=sales,
        forecast_days=actual_days,
        db=db,
        state=shop.state,
    )
    return PredictionOut(**result)