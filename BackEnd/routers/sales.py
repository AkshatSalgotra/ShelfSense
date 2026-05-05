from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from uuid import UUID
from database import get_db
from models.db_models import Shop, Product, SalesLog
from schemas.pydantic_schemas import SaleCreate, SaleOut
from core.security import get_current_shop

router = APIRouter(prefix="/sales", tags=["Sales"])


@router.post("/", response_model=SaleOut, status_code=201)
def log_sale(
    data: SaleCreate,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop)
):
    product = db.query(Product).filter(
        Product.product_id == data.product_id,
        Product.shop_id == shop.shop_id
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.current_stock < data.quantity_sold:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient stock. Available: {product.current_stock}"
        )

    product.current_stock -= data.quantity_sold

    sale = SalesLog(
        shop_id       = shop.shop_id,
        product_id    = data.product_id,
        quantity_sold = data.quantity_sold,
        sale_date     = data.sale_date or date.today(),
        note          = data.note,
    )
    db.add(sale)
    db.commit()
    db.refresh(sale)
    return sale


@router.get("/", response_model=List[SaleOut])
def get_sales(
    product_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop)
):
    query = db.query(SalesLog).filter(SalesLog.shop_id == shop.shop_id)
    if product_id:
        query = query.filter(SalesLog.product_id == product_id)
    return query.order_by(SalesLog.sale_date.desc()).all()


@router.get("/summary")
def sales_summary(
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop)
):
    """Returns total units sold and transaction count per product."""
    sales = db.query(SalesLog).filter(SalesLog.shop_id == shop.shop_id).all()
    summary = {}
    for sale in sales:
        pid = str(sale.product_id)
        if pid not in summary:
            summary[pid] = {
                "product_id":         sale.product_id,
                "total_units_sold":   0.0,
                "total_transactions": 0,
            }
        summary[pid]["total_units_sold"]   += sale.quantity_sold
        summary[pid]["total_transactions"] += 1
    return list(summary.values())