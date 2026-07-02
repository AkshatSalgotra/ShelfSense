from sqlalchemy.orm import Session
from datetime import datetime, timezone
from models.db_models import Product, Inventory, ReorderAlert
from routers.alerts import _get_recommended_qty
from uuid import UUID

def trigger_reorder_alert(db: Session, product_id: UUID, shop_id: UUID):
    """
    Checks current stock against threshold and creates a ReorderAlert if needed.
    """
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product or product.reorder_threshold is None:
        return None

    # Get current stock from inventory table
    inventory = db.query(Inventory).filter(Inventory.product_id == product_id).first()
    current_stock = inventory.current_stock if inventory else 0

    if current_stock <= product.reorder_threshold:
        # Check if an active (unresolved) alert already exists
        existing_alert = (
            db.query(ReorderAlert)
            .filter(
                ReorderAlert.product_id == product_id,
                ReorderAlert.is_resolved == False,
            )
            .first()
        )

        if not existing_alert:
            now = datetime.now(timezone.utc)
            alert_type = "out_of_stock" if current_stock <= 0 else "low_stock"
            
            # Get recommended qty (from ML or heuristic)
            rec_qty, _ = _get_recommended_qty(
                db, product_id, shop_id, float(product.reorder_threshold)
            )

            alert = ReorderAlert(
                shop_id=shop_id,
                product_id=product_id,
                alert_type=alert_type,
                current_stock=float(current_stock),
                threshold=float(product.reorder_threshold),
                recommended_qty=rec_qty,
                is_resolved=False,
                created_at=now,
            )
            db.add(alert)
            db.commit()
            return alert
    
    return None
