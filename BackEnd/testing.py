"""
testing.py — Backtest ShelfSense forecaster on 2024-2025 synthetic data.

Usage:
    python testing.py --sales sales_2024_2025.csv

Evaluation rounds:
    Round 1 : Train 2024-01-01 → 2024-06-30  |  Test Jan 2025
    Round 2 : Train 2024-01-01 → 2024-09-30  |  Test Jan 2025
    Round 3 : Train 2024-01-01 → 2024-12-31  |  Test Jan 2025

Excludes zero-actual SKUs from MAE/RMSE (they distort the metric).
"""

import argparse
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error

from ml.forecaster import sku_forecast, get_holidays_df


# ---------------------------------------------------------------------------
# Mock class — matches the interface sku_forecast expects
# ---------------------------------------------------------------------------
class MockSalesLog:
    def __init__(self, sale_date, quantity_sold):
        self.sale_date     = pd.to_datetime(sale_date)
        self.quantity_sold = quantity_sold


# ---------------------------------------------------------------------------
# Backtest
# ---------------------------------------------------------------------------
def run_backtest(sales_csv: str):
    # ── Load & validate ──────────────────────────────────────────────────────
    print(f"Loading {sales_csv}...")
    df = pd.read_csv(sales_csv)

    required = {"date", "sku_code", "product_name", "quantity_sold"}
    missing  = required - set(df.columns)
    if missing:
        print(f"[ERROR] CSV missing columns: {missing}")
        return

    df["date"]          = pd.to_datetime(df["date"])
    df["quantity_sold"] = pd.to_numeric(df["quantity_sold"], errors="coerce").fillna(0)

    unique_skus = df["sku_code"].unique()
    date_min    = df["date"].min().date()
    date_max    = df["date"].max().date()
    print(f"[OK] {len(df)} rows | {len(unique_skus)} SKUs | {date_min} → {date_max}")

    holidays_df = get_holidays_df(years=[2024, 2025])

    # ── Evaluation rounds ────────────────────────────────────────────────────
    rounds = [
        {
            "label"      : "6 months training",
            "train_end"  : "2024-06-30",
            "test_start" : "2025-01-01",
            "test_end"   : "2025-01-31",
        },
        {
            "label"      : "9 months training",
            "train_end"  : "2024-09-30",
            "test_start" : "2025-01-01",
            "test_end"   : "2025-01-31",
        },
        {
            "label"      : "12 months training",
            "train_end"  : "2024-12-31",
            "test_start" : "2025-01-01",
            "test_end"   : "2025-01-31",
        },
    ]

    all_results = []

    for round_idx, r in enumerate(rounds, start=1):
        print(f"\n{'─'*60}")
        print(f"Round {round_idx} — {r['label']}")
        print(f"  Train : 2024-01-01 → {r['train_end']}")
        print(f"  Test  : {r['test_start']} → {r['test_end']}")
        print(f"{'─'*60}")

        train_end_dt  = pd.to_datetime(r["train_end"])
        test_start_dt = pd.to_datetime(r["test_start"])
        test_end_dt   = pd.to_datetime(r["test_end"])
        forecast_days = (test_end_dt - test_start_dt).days + 1

        skus_done    = 0
        skus_skipped = 0

        for sku_code in unique_skus:
            sku_df = df[df["sku_code"] == sku_code]

            train_df = sku_df[sku_df["date"] <= train_end_dt]
            test_df  = sku_df[
                (sku_df["date"] >= test_start_dt) &
                (sku_df["date"] <= test_end_dt)
            ]

            if train_df.empty or test_df.empty:
                skus_skipped += 1
                continue

            actual = test_df["quantity_sold"].sum()

            # Build MockSalesLog list for sku_forecast
            sales_logs = [
                MockSalesLog(row["date"], row["quantity_sold"])
                for _, row in train_df.iterrows()
            ]

            predicted = sku_forecast(sales_logs, forecast_days, holidays_df)

            if predicted is None:
                skus_skipped += 1
                continue

            product_name = sku_df["product_name"].iloc[0]

            all_results.append({
                "round"       : round_idx,
                "round_label" : r["label"],
                "sku_code"    : sku_code,
                "product_name": product_name,
                "actual"      : actual,
                "predicted"   : round(predicted, 2),
                "abs_error"   : abs(actual - predicted),
                "zero_actual" : actual == 0,
            })
            skus_done += 1

        print(f"  Done: {skus_done} SKUs evaluated, {skus_skipped} skipped")

    # ── Results ──────────────────────────────────────────────────────────────
    if not all_results:
        print("\n[ERROR] No results collected.")
        return

    results_df = pd.DataFrame(all_results)

    print(f"\n{'═'*60}")
    print("EVALUATION SUMMARY")
    print(f"{'═'*60}")

    for round_idx in range(1, len(rounds) + 1):
        r_df     = results_df[results_df["round"] == round_idx]
        label    = rounds[round_idx - 1]["label"]

        # Exclude zero-actual SKUs from metrics — they inflate MAE unfairly
        r_nonzero = r_df[~r_df["zero_actual"]]
        n_zero    = r_df["zero_actual"].sum()

        mae  = mean_absolute_error(r_nonzero["actual"], r_nonzero["predicted"])
        rmse = np.sqrt(mean_squared_error(r_nonzero["actual"], r_nonzero["predicted"]))
        mape = (
            (r_nonzero["abs_error"] / r_nonzero["actual"]).mean() * 100
            if len(r_nonzero) else float("nan")
        )

        print(f"\nRound {round_idx} — {label}")
        print(f"  SKUs evaluated : {len(r_df)} ({n_zero} zero-actual excluded from metrics)")
        print(f"  MAE            : {mae:.2f}  (avg off by ~{mae:.0f} units/month)")
        print(f"  RMSE           : {rmse:.2f}")
        print(f"  MAPE           : {mape:.1f}%")

    # ── Worst performers (Round 3 — most training data) ───────────────────
    r3 = results_df[
        (results_df["round"] == 3) & (~results_df["zero_actual"])
    ].copy()

    r3["pct_error"] = (r3["abs_error"] / r3["actual"] * 100).round(1)
    r3_sorted = r3.sort_values("pct_error", ascending=False)

    print(f"\n{'─'*60}")
    print("TOP 15 WORST PERFORMERS (Round 3, non-zero actuals)")
    print(f"{'─'*60}")
    print(
        r3_sorted[["sku_code", "product_name", "actual", "predicted", "abs_error", "pct_error"]]
        .head(15)
        .to_string(index=False)
    )

    # ── Save full results ─────────────────────────────────────────────────
    out_path = "ml/backtest_results.csv"
    results_df.to_csv(out_path, index=False)
    print(f"\n[OK] Full results saved to {out_path}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sales", required=True, help="Path to sales_2024_2025.csv")
    args = parser.parse_args()
    run_backtest(args.sales)