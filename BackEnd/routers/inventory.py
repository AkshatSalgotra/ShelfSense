from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from database import get_db
from models.db_models import Shop, Product, Category, Inventory
from schemas.pydantic_schemas import ProductCreate, ProductUpdate, ProductOut
from core.security import get_current_manager
from core.alerts_logic import trigger_reorder_alert

router = APIRouter(prefix="/inventory", tags=["Inventory"])


def _get_or_create_category(db: Session, category_name: str) -> Category:
    cat = db.query(Category).filter(Category.name == category_name).first()
    if not cat:
        cat = Category(name=category_name)
        db.add(cat)
        db.flush()
    return cat


def _current_stock(product: Product) -> float:
    """Always read stock from the inventory table, fall back to products.current_stock."""
    if product.inventory and product.inventory.current_stock is not None:
        return float(product.inventory.current_stock)
    return float(product.current_stock or 0)


def _to_product_out(product: Product) -> ProductOut:
    return ProductOut(
        product_id        = product.product_id,
        shop_id           = product.shop_id,
        product_name      = product.product_name,
        category          = product.category.name if product.category else None,
        unit              = product.unit,
        current_stock     = _current_stock(product),      # ← inventory table
        reorder_threshold = product.reorder_threshold,
        cost_price        = float(product.cost_price) if product.cost_price else None,
        selling_price     = float(product.selling_price) if product.selling_price else None,
        sku_code          = product.sku_code,
    )


@router.get("/", response_model=List[ProductOut])
def list_products(
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_manager),
):
    products = db.query(Product).filter(Product.shop_id == shop.shop_id).all()
    return [_to_product_out(p) for p in products]


@router.get("/alerts", response_model=List[ProductOut])
def low_stock_alerts(
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_manager),
):
    """Returns products where inventory stock is below reorder threshold."""
    products = db.query(Product).filter(Product.shop_id == shop.shop_id).all()
    return [
        _to_product_out(p) for p in products
        if _current_stock(p) < p.reorder_threshold     # ← inventory table
    ]


@router.post("/", response_model=ProductOut, status_code=201)
def add_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_manager),
):
    category_id = None
    if data.category:
        cat = _get_or_create_category(db, data.category)
        category_id = cat.category_id

    product = Product(
        shop_id           = shop.shop_id,
        product_name      = data.product_name,
        category_id       = category_id,
        unit              = data.unit or "units",
        current_stock     = data.current_stock or 0.0,
        reorder_threshold = data.reorder_threshold or 10.0,
        cost_price        = data.cost_price,
        selling_price     = data.selling_price,
        sku_code          = data.sku_code,
    )
    db.add(product)
    db.flush()  # get product_id before creating inventory row

    # Always create a matching inventory row so stock is tracked correctly
    inventory = Inventory(
        shop_id       = shop.shop_id,
        product_id    = product.product_id,
        current_stock = int(data.current_stock or 0),
    )
    db.add(inventory)
    db.commit()
    db.refresh(product)
    
    # Check for alerts immediately
    trigger_reorder_alert(db, product.product_id, shop.shop_id)
    
    return _to_product_out(product)


@router.get("/{product_id}", response_model=ProductOut)
def get_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_manager),
):
    product = db.query(Product).filter(
        Product.product_id == product_id,
        Product.shop_id    == shop.shop_id,
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return _to_product_out(product)


@router.patch("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: UUID,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_manager),
):
    product = db.query(Product).filter(
        Product.product_id == product_id,
        Product.shop_id    == shop.shop_id,
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # exclude_none=True is the key addition — drops fields the client
    # left blank / sent as null, so only truly-provided values are applied
    update_data = data.model_dump(exclude_unset=True, exclude_none=True)

    if "category" in update_data:
        cat_name = update_data.pop("category")
        if cat_name:
            cat = _get_or_create_category(db, cat_name)
            product.category_id = cat.category_id
        else:
            product.category_id = None

    if "current_stock" in update_data:
        new_stock = update_data["current_stock"]
        if product.inventory:
            product.inventory.current_stock = int(new_stock)
        else:
            db.add(Inventory(
                shop_id       = shop.shop_id,
                product_id    = product.product_id,
                current_stock = int(new_stock),
            ))

    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)

    # Check for alerts if stock was changed
    if "current_stock" in update_data:
        trigger_reorder_alert(db, product.product_id, shop.shop_id)

    return _to_product_out(product)


@router.delete("/{product_id}", status_code=204)
def delete_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_manager),
):
    product = db.query(Product).filter(
        Product.product_id == product_id,
        Product.shop_id    == shop.shop_id,
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()