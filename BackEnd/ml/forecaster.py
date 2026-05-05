import pandas as pd
import holidays
from prophet import Prophet
from typing import List, Optional
from sqlalchemy.orm import Session
from models.db_models import SalesLog, Product


# ─── Holiday Generation ───────────────────────────────────────────────────────

def get_holidays_df(state: Optional[str] = None, years: List[int] = None) -> pd.DataFrame:
    if years is None:
        from datetime import datetime
        current_year = datetime.utcnow().year
        years = [current_year - 1, current_year, current_year + 1]

    india_holidays = holidays.India(years=years)
    rows = []
    for date, name in india_holidays.items():
        rows.append({
            "holiday":      name.replace(" ", "_"),
            "ds":           pd.Timestamp(date),
            "lower_window": -2,
            "upper_window": 1,
        })

    STATE_SUBDIV_MAP = {
        "Andhra Pradesh": "AP", "Arunachal Pradesh": "AR", "Assam": "AS",
        "Bihar": "BR", "Chhattisgarh": "CG", "Goa": "GA", "Gujarat": "GJ",
        "Haryana": "HR", "Himachal Pradesh": "HP", "Jharkhand": "JH",
        "Karnataka": "KA", "Kerala": "KL", "Madhya Pradesh": "MP",
        "Maharashtra": "MH", "Manipur": "MN", "Meghalaya": "ML",
        "Mizoram": "MZ", "Nagaland": "NL", "Odisha": "OD", "Punjab": "PB",
        "Rajasthan": "RJ", "Sikkim": "SK", "Tamil Nadu": "TN",
        "Telangana": "TS", "Tripura": "TR", "Uttar Pradesh": "UP",
        "Uttarakhand": "UK", "West Bengal": "WB",
    }

    if state and state in STATE_SUBDIV_MAP:
        try:
            state_holidays = holidays.India(subdiv=STATE_SUBDIV_MAP[state], years=years)
            for date, name in state_holidays.items():
                rows.append({
                    "holiday":      name.replace(" ", "_"),
                    "ds":           pd.Timestamp(date),
                    "lower_window": -1,
                    "upper_window": 1,
                })
        except Exception:
            pass

    df = pd.DataFrame(rows).drop_duplicates(subset=["holiday", "ds"])
    return df


# ─── Confidence Level ─────────────────────────────────────────────────────────

def get_confidence_level(record_count: int) -> str:
    if record_count < 20:
        return "low"
    elif record_count < 60:
        return "medium"
    return "high"


# ─── Sales → Daily DataFrame ──────────────────────────────────────────────────

def sales_to_daily_df(sales: List[SalesLog]) -> pd.DataFrame:
    records = [
        {"ds": s.sale_date, "y": s.quantity_sold}
        for s in sales if s.sale_date is not None and s.quantity_sold is not None
    ]
    if not records:
        return pd.DataFrame(columns=["ds", "y"])
    df = pd.DataFrame(records)
    df["ds"] = pd.to_datetime(df["ds"])
    df = df.groupby("ds", as_index=False)["y"].sum()
    return df.sort_values("ds").reset_index(drop=True)


# ─── Rule-Based Forecast ──────────────────────────────────────────────────────

def rule_based_forecast(sales: List[SalesLog], forecast_days: int) -> float:
    if not sales:
        return 0.0
    total_sold = sum(s.quantity_sold for s in sales)
    dates = [s.sale_date for s in sales if s.sale_date]
    if len(dates) < 2:
        avg_daily = total_sold
    else:
        date_range_days = (max(dates) - min(dates)).days or 1
        avg_daily = total_sold / date_range_days
    return round(avg_daily * forecast_days, 2)


# ─── Prophet Fit + Predict ────────────────────────────────────────────────────

def fit_and_predict(df: pd.DataFrame, forecast_days: int, holidays_df: pd.DataFrame) -> Optional[float]:
    try:
        if len(df) < 2:
            return None
        model = Prophet(
            holidays=holidays_df,
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            changepoint_prior_scale=0.05,
        )
        model.fit(df)
        future = model.make_future_dataframe(periods=forecast_days, freq="D")
        forecast = model.predict(future)
        predicted = forecast.tail(forecast_days)["yhat"].clip(lower=0).sum()
        return round(float(predicted), 2)
    except Exception:
        return None


# ─── Tier 1: SKU-Level ────────────────────────────────────────────────────────

def sku_forecast(sales: List[SalesLog], forecast_days: int, holidays_df: pd.DataFrame) -> Optional[float]:
    if len(sales) < 20:
        return None
    return fit_and_predict(sales_to_daily_df(sales), forecast_days, holidays_df)


# ─── Tier 2: Category-Level ───────────────────────────────────────────────────

def category_forecast(product: Product, forecast_days: int, holidays_df: pd.DataFrame, db: Session) -> float:
    """
    Borrows demand signal from sibling products in the same category.
    Uses category_id FK — properly joined through the Category relationship.
    """
    if not product.category_id:
        return 0.0

    sibling_products = (
        db.query(Product)
        .filter(
            Product.shop_id     == product.shop_id,
            Product.category_id == product.category_id,
            Product.product_id  != product.product_id,
        )
        .all()
    )

    if not sibling_products:
        return 0.0

    sibling_ids = [p.product_id for p in sibling_products]
    sibling_sales = (
        db.query(SalesLog)
        .filter(
            SalesLog.shop_id    == product.shop_id,
            SalesLog.product_id.in_(sibling_ids),
        )
        .all()
    )

    if not sibling_sales:
        return 0.0

    df = sales_to_daily_df(sibling_sales)
    category_prediction = fit_and_predict(df, forecast_days, holidays_df)

    if category_prediction is None:
        category_prediction = rule_based_forecast(sibling_sales, forecast_days)

    num_products = len(sibling_products) + 1
    return round(category_prediction / num_products, 2)


# ─── Public Entry Point ───────────────────────────────────────────────────────

def generate_forecast(
    product: Product,
    sales: List[SalesLog],
    forecast_days: int,
    db: Session,
    state: Optional[str] = None,
) -> dict:
    from datetime import datetime
    current_year = datetime.utcnow().year
    holidays_df = get_holidays_df(state=state, years=[current_year - 1, current_year, current_year + 1])

    record_count = len(sales)
    confidence = get_confidence_level(record_count)
    model_tier = "sku"

    predicted_demand = sku_forecast(sales, forecast_days, holidays_df)

    if predicted_demand is None:
        model_tier = "category"
        predicted_demand = category_forecast(product, forecast_days, holidays_df, db)

    if predicted_demand == 0.0 and record_count > 0:
        model_tier = "rule_based"
        predicted_demand = rule_based_forecast(sales, forecast_days)

    predicted_demand = predicted_demand or 0.0
    suggested_reorder = max(predicted_demand - product.current_stock, 0.0)

    return {
        "product_id":        product.product_id,
        "product_name":      product.product_name,
        "forecast_days":     forecast_days,
        "predicted_demand":  round(predicted_demand, 2),
        "current_stock":     product.current_stock,
        "suggested_reorder": round(suggested_reorder, 2),
        "confidence":        confidence,
        "model_tier":        model_tier,
    }