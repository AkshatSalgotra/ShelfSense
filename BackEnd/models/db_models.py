import uuid
from sqlalchemy import (
    Column, String, Integer, Numeric, Boolean, Text, Float,
    ForeignKey, DateTime, Date, CheckConstraint, func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from database import Base


# ─── Shops ───────────────────────────────────────────────────────────────────

class Shop(Base):
    __tablename__ = "shops"

    shop_id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shop_name       = Column(String(255), nullable=False)
    owner_name      = Column(String(255), nullable=False)
    phone           = Column(String(15), nullable=True)
    email           = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(Text, nullable=False)
    address         = Column(Text)
    city            = Column(String(100))
    district        = Column(String(100))
    state           = Column(String(100))
    pincode         = Column(String(10))
    gstin           = Column(String(15))
    created_at      = Column(DateTime, server_default=func.now())
    is_active       = Column(Boolean, default=True)

    products  = relationship("Product", back_populates="shop", cascade="all, delete")
    suppliers = relationship("Supplier", back_populates="shop", cascade="all, delete")
    inventory = relationship("Inventory", back_populates="shop", cascade="all, delete")
    sales_log = relationship("SalesLog", back_populates="shop", cascade="all, delete")
    alerts    = relationship("ReorderAlert", back_populates="shop", cascade="all, delete")
    forecasts = relationship("MLForecast", back_populates="shop", cascade="all, delete")
    users     = relationship("User", back_populates="shop", cascade="all, delete")


# ─── Users ───────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    user_id       = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shop_id       = Column(UUID(as_uuid=True), ForeignKey("shops.shop_id", ondelete="CASCADE"), nullable=False)
    full_name     = Column(String(255), nullable=False)
    phone         = Column(String(15), unique=True, nullable=False)
    email         = Column(String(255), unique=True)
    password_hash = Column(Text, nullable=False)
    role          = Column(String(20), nullable=False)
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime, server_default=func.now())
    last_login    = Column(DateTime)

    __table_args__ = (
        CheckConstraint("role IN ('owner','cashier','manager')", name="chk_user_role"),
    )

    shop = relationship("Shop", back_populates="users")


# ─── Categories ───────────────────────────────────────────────────────────────

class Category(Base):
    __tablename__ = "categories"

    category_id = Column(Integer, primary_key=True, autoincrement=True)
    name        = Column(String(100), unique=True, nullable=False)
    description = Column(Text)

    products = relationship("Product", back_populates="category")


# ─── Suppliers ────────────────────────────────────────────────────────────────

class Supplier(Base):
    __tablename__ = "suppliers"

    supplier_id    = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shop_id        = Column(UUID(as_uuid=True), ForeignKey("shops.shop_id", ondelete="CASCADE"), nullable=False)
    supplier_name  = Column(String(255), nullable=False)
    contact_person = Column(String(255))
    phone          = Column(String(15))
    email          = Column(String(255))
    lead_time_days = Column(Integer, default=1)
    address        = Column(Text)
    created_at     = Column(DateTime, server_default=func.now())

    shop     = relationship("Shop", back_populates="suppliers")
    products = relationship("Product", back_populates="supplier")


# ─── Products ────────────────────────────────────────────────────────────────

class Product(Base):
    __tablename__ = "products"

    product_id        = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shop_id           = Column(UUID(as_uuid=True), ForeignKey("shops.shop_id", ondelete="CASCADE"), nullable=False)
    category_id       = Column(Integer, ForeignKey("categories.category_id"), nullable=True)
    supplier_id       = Column(UUID(as_uuid=True), ForeignKey("suppliers.supplier_id"), nullable=True)
    product_name      = Column(String(255), nullable=False)
    sku_code          = Column(String(100), nullable=True)
    unit              = Column(String(50), nullable=False, default="units")
    current_stock     = Column(Float, nullable=False, default=0.0)
    reorder_threshold = Column(Float, nullable=False, default=10.0)
    cost_price        = Column(Numeric(10, 2), nullable=True)
    selling_price     = Column(Numeric(10, 2), nullable=True)
    is_active         = Column(Boolean, default=True)
    created_at        = Column(DateTime(timezone=True), server_default=func.now())
    updated_at        = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    shop      = relationship("Shop", back_populates="products")
    category  = relationship("Category", back_populates="products")
    supplier  = relationship("Supplier", back_populates="products")
    inventory = relationship("Inventory", back_populates="product", uselist=False)
    sales_log = relationship("SalesLog", back_populates="product")
    alerts    = relationship("ReorderAlert", back_populates="product")
    forecasts = relationship("MLForecast", back_populates="product")


# ─── Inventory ───────────────────────────────────────────────────────────────

class Inventory(Base):
    __tablename__ = "inventory"

    inventory_id  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shop_id       = Column(UUID(as_uuid=True), ForeignKey("shops.shop_id", ondelete="CASCADE"), nullable=False)
    product_id    = Column(UUID(as_uuid=True), ForeignKey("products.product_id", ondelete="CASCADE"), nullable=False)
    current_stock = Column(Integer, nullable=False, default=0)
    last_updated  = Column(DateTime, server_default=func.now(), onupdate=func.now())

    shop    = relationship("Shop", back_populates="inventory")
    product = relationship("Product", back_populates="inventory")


# ─── Inventory Log ────────────────────────────────────────────────────────────

class InventoryLog(Base):
    __tablename__ = "inventory_log"

    log_id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shop_id         = Column(UUID(as_uuid=True), ForeignKey("shops.shop_id"), nullable=False)
    product_id      = Column(UUID(as_uuid=True), ForeignKey("products.product_id"), nullable=False)
    change_type     = Column(String(30), nullable=False)
    quantity_change = Column(Integer, nullable=False)
    stock_before    = Column(Integer, nullable=False)
    stock_after     = Column(Integer, nullable=False)
    reference_id    = Column(UUID(as_uuid=True))
    note            = Column(Text)
    created_by      = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    created_at      = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "change_type IN ('sale','restock','manual_correction','damage','return')",
            name="chk_change_type"
        ),
    )


# ─── Customers ───────────────────────────────────────────────────────────────

class Customer(Base):
    __tablename__ = "customers"

    customer_id    = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shop_id        = Column(UUID(as_uuid=True), ForeignKey("shops.shop_id", ondelete="CASCADE"), nullable=False)
    name           = Column(String(255))
    phone          = Column(String(15))
    loyalty_points = Column(Integer, default=0)
    created_at     = Column(DateTime, server_default=func.now())

    orders = relationship("Order", back_populates="customer")


# ─── Orders ──────────────────────────────────────────────────────────────────

class Order(Base):
    __tablename__ = "orders"

    order_id        = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shop_id         = Column(UUID(as_uuid=True), ForeignKey("shops.shop_id", ondelete="CASCADE"), nullable=False)
    customer_id     = Column(UUID(as_uuid=True), ForeignKey("customers.customer_id"))
    cashier_id      = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    order_number    = Column(String(50), unique=True, nullable=False)
    status          = Column(String(20), nullable=False, default="pending")
    subtotal        = Column(Numeric(10, 2), nullable=False, default=0)
    discount_amount = Column(Numeric(10, 2), default=0)
    tax_amount      = Column(Numeric(10, 2), default=0)
    total_amount    = Column(Numeric(10, 2), nullable=False, default=0)
    razorpay_order_id = Column(String(100), nullable=True, index=True)  # NEW
    note            = Column(Text)
    created_at      = Column(DateTime, server_default=func.now())
    completed_at    = Column(DateTime)

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending','completed','cancelled','refunded')",
            name="chk_order_status"
        ),
    )

    customer    = relationship("Customer", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete")
    payments    = relationship("Payment", back_populates="order", cascade="all, delete")
    sales_log   = relationship("SalesLog", back_populates="order")


# ─── Order Items ─────────────────────────────────────────────────────────────

class OrderItem(Base):
    __tablename__ = "order_items"

    order_item_id   = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id        = Column(UUID(as_uuid=True), ForeignKey("orders.order_id", ondelete="CASCADE"), nullable=False)
    product_id      = Column(UUID(as_uuid=True), ForeignKey("products.product_id"), nullable=False)
    quantity        = Column(Integer, nullable=False)
    unit_price      = Column(Numeric(10, 2), nullable=False)
    tax_percent     = Column(Numeric(5, 2), default=0)
    discount_amount = Column(Numeric(10, 2), default=0)
    line_total      = Column(Numeric(10, 2), nullable=False)

    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_order_item_qty"),
    )

    order = relationship("Order", back_populates="order_items")


# ─── Payments ────────────────────────────────────────────────────────────────

class Payment(Base):
    __tablename__ = "payments"

    payment_id       = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id         = Column(UUID(as_uuid=True), ForeignKey("orders.order_id", ondelete="CASCADE"), nullable=False)
    transaction_id   = Column(String(255), unique=True)
    payment_method   = Column(String(30), nullable=False)
    payment_status   = Column(String(20), nullable=False, default="pending")
    amount_paid      = Column(Numeric(10, 2), nullable=False)
    change_returned  = Column(Numeric(10, 2), default=0)
    upi_ref          = Column(String(100))
    card_last4       = Column(String(4))
    gateway          = Column(String(50))
    gateway_response = Column(JSONB)
    paid_at          = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "payment_method IN ('cash','upi','card','wallet','credit','other')",
            name="chk_payment_method"
        ),
        CheckConstraint(
            "payment_status IN ('pending','success','failed','refunded')",
            name="chk_payment_status"
        ),
    )

    order = relationship("Order", back_populates="payments")


# ─── Reorder Alerts ───────────────────────────────────────────────────────────

class ReorderAlert(Base):
    __tablename__ = "reorder_alerts"

    alert_id        = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shop_id         = Column(UUID(as_uuid=True), ForeignKey("shops.shop_id"), nullable=False)
    product_id      = Column(UUID(as_uuid=True), ForeignKey("products.product_id"), nullable=False)
    alert_type      = Column(String(20), nullable=False)
    current_stock   = Column(Float, nullable=False)
    threshold       = Column(Float, nullable=False)
    recommended_qty = Column(Float)
    is_resolved     = Column(Boolean, default=False)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at     = Column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint(
            "alert_type IN ('low_stock','out_of_stock','anomaly')",
            name="chk_alert_type"
        ),
    )

    shop    = relationship("Shop", back_populates="alerts")
    product = relationship("Product", back_populates="alerts")


# ─── Sales Log ───────────────────────────────────────────────────────────────

class SalesLog(Base):
    __tablename__ = "sales_log"

    log_id        = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shop_id       = Column(UUID(as_uuid=True), ForeignKey("shops.shop_id", ondelete="CASCADE"), nullable=False)
    product_id    = Column(UUID(as_uuid=True), ForeignKey("products.product_id", ondelete="CASCADE"), nullable=False)
    order_id      = Column(UUID(as_uuid=True), ForeignKey("orders.order_id"), nullable=True)
    quantity_sold = Column(Float, nullable=False)
    sale_date     = Column(Date, nullable=False, server_default=func.current_date())
    note          = Column(Text, nullable=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())

    shop    = relationship("Shop", back_populates="sales_log")
    product = relationship("Product", back_populates="sales_log")
    order   = relationship("Order", back_populates="sales_log")


# ─── ML Forecasts ────────────────────────────────────────────────────────────

class MLForecast(Base):
    __tablename__ = "ml_forecasts"

    forecast_id   = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shop_id       = Column(UUID(as_uuid=True), ForeignKey("shops.shop_id"), nullable=False)
    product_id    = Column(UUID(as_uuid=True), ForeignKey("products.product_id"), nullable=False)
    forecast_date = Column(Date, nullable=False)
    horizon_days  = Column(Integer, nullable=False)
    predicted_qty = Column(Numeric(10, 2), nullable=False)
    lower_bound   = Column(Numeric(10, 2))
    upper_bound   = Column(Numeric(10, 2))
    confidence    = Column(String(10))
    model_tier    = Column(String(20))
    generated_at  = Column(DateTime(timezone=True), server_default=func.now())

    shop    = relationship("Shop", back_populates="forecasts")
    product = relationship("Product", back_populates="forecasts")