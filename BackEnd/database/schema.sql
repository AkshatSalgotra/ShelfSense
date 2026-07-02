
-- ============================================================
--  ShelfSense — PostgreSQL Database Schema
-- ============================================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
--  1. SHOPS & USERS
-- ============================================================

CREATE TABLE shops (
    shop_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shop_name       VARCHAR(255) NOT NULL,
    owner_name      VARCHAR(255) NOT NULL,
    phone           VARCHAR(15) UNIQUE NOT NULL,
    email           VARCHAR(255) UNIQUE,
    address         TEXT,
    hashed_password TEXT,
    city            VARCHAR(100),
    district        VARCHAR(100),
    state           VARCHAR(100),
    pincode         VARCHAR(10),
    gstin           VARCHAR(15),                          -- GST number
    created_at      TIMESTAMP DEFAULT NOW(),
    is_active       BOOLEAN DEFAULT TRUE
);

-- Users = shop owners + cashiers under a shop
CREATE TABLE users (
    user_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shop_id         UUID NOT NULL REFERENCES shops(shop_id) ON DELETE CASCADE,
    full_name       VARCHAR(255) NOT NULL,
    phone           VARCHAR(15) UNIQUE NOT NULL,
    email           VARCHAR(255) UNIQUE,
    password_hash   TEXT NOT NULL,
    role            VARCHAR(20) NOT NULL CHECK (role IN ('owner', 'cashier', 'manager')),
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW(),
    last_login      TIMESTAMP
);

-- ============================================================
--  2. PRODUCTS & INVENTORY
-- ============================================================

CREATE TABLE categories (
    category_id     SERIAL PRIMARY KEY,
    name            VARCHAR(100) UNIQUE NOT NULL,        -- snacks, dairy, grains etc.
    description     TEXT
);

CREATE TABLE suppliers (
    supplier_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shop_id         UUID NOT NULL REFERENCES shops(shop_id) ON DELETE CASCADE,
    supplier_name   VARCHAR(255) NOT NULL,
    contact_person  VARCHAR(255),
    phone           VARCHAR(15),
    email           VARCHAR(255),
    lead_time_days  INT DEFAULT 1,                       -- days to deliver after order
    address         TEXT,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE products (
    product_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shop_id         UUID NOT NULL REFERENCES shops(shop_id) ON DELETE CASCADE,
    category_id     INT REFERENCES categories(category_id),
    supplier_id     UUID REFERENCES suppliers(supplier_id),
    product_name    VARCHAR(255) NOT NULL,
    sku_code        VARCHAR(100),                        -- barcode / custom SKU
    unit            VARCHAR(50) NOT NULL,                -- piece, kg, litre, packet
    cost_price      NUMERIC(10, 2),
    selling_price   NUMERIC(10, 2),
    tax_percent     NUMERIC(5, 2) DEFAULT 0,             -- GST %
    reorder_threshold INT DEFAULT 10,                    -- alert fires below this
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW(),
    UNIQUE (shop_id, sku_code)
);

CREATE TABLE inventory (
    inventory_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shop_id         UUID NOT NULL REFERENCES shops(shop_id) ON DELETE CASCADE,
    product_id      UUID NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    current_stock   INT NOT NULL DEFAULT 0,
    last_updated    TIMESTAMP DEFAULT NOW(),
    UNIQUE (shop_id, product_id)
);

-- Full audit trail of every stock change
CREATE TABLE inventory_log (
    log_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shop_id         UUID NOT NULL REFERENCES shops(shop_id),
    product_id      UUID NOT NULL REFERENCES products(product_id),
    change_type     VARCHAR(30) NOT NULL CHECK (
                        change_type IN ('sale', 'restock', 'manual_correction', 'damage', 'return')
                    ),
    quantity_change INT NOT NULL,                        -- negative for sale/damage
    stock_before    INT NOT NULL,
    stock_after     INT NOT NULL,
    reference_id    UUID,                                -- order_id or restock_id
    note            TEXT,
    created_by      UUID REFERENCES users(user_id),
    created_at      TIMESTAMP DEFAULT NOW()
);

-- ============================================================
--  3. CASHIER SYSTEM — ORDERS
-- ============================================================

CREATE TABLE customers (
    customer_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shop_id         UUID NOT NULL REFERENCES shops(shop_id) ON DELETE CASCADE,
    name            VARCHAR(255),
    phone           VARCHAR(15),
    loyalty_points  INT DEFAULT 0,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE orders (
    order_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shop_id         UUID NOT NULL REFERENCES shops(shop_id) ON DELETE CASCADE,
    customer_id     UUID REFERENCES customers(customer_id),
    cashier_id      UUID NOT NULL REFERENCES users(user_id),
    order_number    VARCHAR(50) UNIQUE NOT NULL,         -- human readable: ORD-20240101-001
    status          VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (
                        status IN ('pending', 'completed', 'cancelled', 'refunded')
                    ),
    subtotal        NUMERIC(10, 2) NOT NULL DEFAULT 0,
    discount_amount NUMERIC(10, 2) DEFAULT 0,
    tax_amount      NUMERIC(10, 2) DEFAULT 0,
    total_amount    NUMERIC(10, 2) NOT NULL DEFAULT 0,
    note            TEXT,
    created_at      TIMESTAMP DEFAULT NOW(),
    completed_at    TIMESTAMP
);

CREATE TABLE order_items (
    order_item_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id        UUID NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id      UUID NOT NULL REFERENCES products(product_id),
    quantity        INT NOT NULL CHECK (quantity > 0),
    unit_price      NUMERIC(10, 2) NOT NULL,             -- price at time of sale
    tax_percent     NUMERIC(5, 2) DEFAULT 0,
    discount_amount NUMERIC(10, 2) DEFAULT 0,
    line_total      NUMERIC(10, 2) NOT NULL              -- (unit_price * qty) - discount + tax
);

-- ============================================================
--  4. PAYMENTS
-- ============================================================

CREATE TABLE payments (
    payment_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id        UUID NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    transaction_id  VARCHAR(255) UNIQUE,                 -- from Razorpay / UPI / cash register
    payment_method  VARCHAR(30) NOT NULL CHECK (
                        payment_method IN ('cash', 'upi', 'card', 'wallet', 'credit', 'other')
                    ),
    payment_status  VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (
                        payment_status IN ('pending', 'success', 'failed', 'refunded')
                    ),
    amount_paid     NUMERIC(10, 2) NOT NULL,
    change_returned NUMERIC(10, 2) DEFAULT 0,            -- cash change given back
    upi_ref         VARCHAR(100),                        -- UPI VPA / ref number
    card_last4      VARCHAR(4),                          -- last 4 digits if card
    gateway         VARCHAR(50),                         -- razorpay, paytm, phonepe etc.
    gateway_response JSONB,                              -- raw response from payment gateway
    paid_at         TIMESTAMP DEFAULT NOW()
);

-- ============================================================
--  5. ALERTS & ML
-- ============================================================

CREATE TABLE reorder_alerts (
    alert_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shop_id         UUID NOT NULL REFERENCES shops(shop_id),
    product_id      UUID NOT NULL REFERENCES products(product_id),
    alert_type      VARCHAR(20) NOT NULL CHECK (
                        alert_type IN ('low_stock', 'out_of_stock', 'anomaly')
                    ),
    current_stock   INT NOT NULL,
    threshold       INT NOT NULL,
    recommended_qty INT,                                 -- from Prophet
    is_resolved     BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP DEFAULT NOW(),
    resolved_at     TIMESTAMP
);

CREATE TABLE sales_log (
    log_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shop_id         UUID NOT NULL REFERENCES shops(shop_id),
    product_id      UUID NOT NULL REFERENCES products(product_id),
    order_id        UUID REFERENCES orders(order_id),
    quantity_sold   INT NOT NULL,
    sale_date       DATE NOT NULL DEFAULT CURRENT_DATE,
    note            TEXT,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE ml_forecasts (
    forecast_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shop_id         UUID NOT NULL REFERENCES shops(shop_id),
    product_id      UUID NOT NULL REFERENCES products(product_id),
    forecast_date   DATE NOT NULL,
    horizon_days    INT NOT NULL CHECK (horizon_days IN (7, 14, 30)),
    predicted_qty   NUMERIC(10, 2) NOT NULL,
    lower_bound     NUMERIC(10, 2),
    upper_bound     NUMERIC(10, 2),
    confidence      VARCHAR(10) CHECK (confidence IN ('high', 'medium', 'low')),
    model_tier      VARCHAR(10) CHECK (model_tier IN ('sku', 'category')),   -- tier 1 or 2
    generated_at    TIMESTAMP DEFAULT NOW(),
    UNIQUE (shop_id, product_id, forecast_date, horizon_days)
);

-- ============================================================
--  6. INDEXES
-- ============================================================

CREATE INDEX idx_products_shop     ON products(shop_id);
CREATE INDEX idx_inventory_shop    ON inventory(shop_id);
CREATE INDEX idx_orders_shop       ON orders(shop_id);
CREATE INDEX idx_orders_cashier    ON orders(cashier_id);
CREATE INDEX idx_orders_status     ON orders(status);
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_payments_order    ON payments(order_id);
CREATE INDEX idx_payments_txn      ON payments(transaction_id);
CREATE INDEX idx_sales_log_date    ON sales_log(shop_id, sale_date);
CREATE INDEX idx_alerts_shop       ON reorder_alerts(shop_id, is_resolved);
CREATE INDEX idx_forecast_product  ON ml_forecasts(shop_id, product_id, forecast_date);
CREATE INDEX idx_inv_log_product   ON inventory_log(product_id, created_at);

-- ============================================================
--  7. AUTO-UPDATE updated_at on products
-- ============================================================

CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_products_updated
BEFORE UPDATE ON products
FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- ============================================================
--  8. SEED — default categories
-- ============================================================

INSERT INTO categories (name, description) VALUES
    ('snacks',        'Chips, namkeen, biscuits, wafers'),
    ('beverages',     'Cold drinks, water, juice, tea, coffee'),
    ('dairy',         'Milk, curd, butter, cheese, paneer'),
    ('grains',        'Atta, rice, dal, oil, salt, spices'),
    ('sweets',        'Mithai, chocolates, toffees, indian sweets'),
    ('instant_food',  'Noodles, ready to eat, soup mixes'),
    ('personal_care', 'Soap, shampoo, toothpaste, detergent'),
    ('bakery',        'Bread, cakes, rusk, toast'),
    ('pooja_items',   'Agarbatti, camphor, kumkum, diyas'),
    ('stationery',    'Pens, notebooks, staples, tape');


ALTER TABLE products 
ADD COLUMN current_stock FLOAT NOT NULL DEFAULT 0.0;

-- reorder_threshold is INT in SQL but Float in model — cast it
ALTER TABLE products 
ALTER COLUMN reorder_threshold TYPE FLOAT;

select * from products;

ALTER TABLE products ALTER COLUMN cost_price DROP NOT NULL;
ALTER TABLE products ALTER COLUMN selling_price DROP NOT NULL;


-- 1. shops.phone — make nullable so registration works without phone
ALTER TABLE shops ALTER COLUMN phone DROP NOT NULL;

-- 2. products.cost_price and selling_price — already flagged, make nullable
ALTER TABLE products ALTER COLUMN cost_price DROP NOT NULL;
ALTER TABLE products ALTER COLUMN selling_price DROP NOT NULL;

-- 3. sales_log.quantity_sold — INT will crash when inserting float quantities
ALTER TABLE sales_log ALTER COLUMN quantity_sold TYPE FLOAT;

-- 4. reorder_alerts — all three INT columns need to match Float in model
ALTER TABLE reorder_alerts ALTER COLUMN current_stock TYPE FLOAT;
ALTER TABLE reorder_alerts ALTER COLUMN threshold TYPE FLOAT;
ALTER TABLE reorder_alerts ALTER COLUMN recommended_qty TYPE FLOAT;

select * from products;