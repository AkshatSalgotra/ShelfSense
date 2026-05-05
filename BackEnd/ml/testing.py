import pandas as pd
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta
from sklearn.metrics import mean_absolute_error, mean_squared_error

# Import your existing functions from forecaster.py
from ml.forecaster import sku_forecast, get_holidays_df

# --- Mock Classes to interface with your ORM logic ---
class MockProduct:
    def __init__(self, product_id, sku_name, category_id):
        self.product_id = product_id
        self.product_name = sku_name
        self.category_id = category_id
        self.shop_id = 1
        self.current_stock = 0

class MockSalesLog:
    def __init__(self, sale_date, quantity_sold):
        self.sale_date = pd.to_datetime(sale_date)
        self.quantity_sold = quantity_sold

# --- Main Evaluator ---
def run_backtest():
    # 1. Load Data
    print("Loading datasets...")
    df_2025 = pd.read_csv("ml\shelfsense_training_2025_updated.csv")
    df_2026 = pd.read_csv("ml\shelfsense_training_2026_updated.csv")

    df_all = pd.concat([df_2025, df_2026], ignore_index=True)
    df_all['ds'] = pd.to_datetime(df_all['ds'])
    
    holidays_df = get_holidays_df(years=[2025, 2026])
    
    # Define Evaluation Rounds (Train end date, Test month)
    rounds = [
        {"train_end": "2025-03-31", "test_start": "2026-01-01", "test_end": "2026-01-31"},
        {"train_end": "2025-06-30", "test_start": "2026-01-01", "test_end": "2026-01-31"},
        {"train_end": "2025-12-31", "test_start": "2026-01-01", "test_end": "2026-01-31"},
    ]
    
    results = []
    unique_skus = df_all['sku_name'].unique()
    
    print(f"Starting evaluation for {len(unique_skus)} SKUs across {len(rounds)} rounds...")

    for round_idx, r in enumerate(rounds):
        print(f"\n--- Running Round {round_idx + 1} ---")
        print(f"Training: 2024-01-01 to {r['train_end']} | Testing: {r['test_start']} to {r['test_end']}")
        
        train_end_dt = pd.to_datetime(r['train_end'])
        test_start_dt = pd.to_datetime(r['test_start'])
        test_end_dt = pd.to_datetime(r['test_end'])
        forecast_days = (test_end_dt - test_start_dt).days + 1
        
        for sku in unique_skus:
            sku_data = df_all[df_all['sku_name'] == sku]
            
            # Split Data
            train_df = sku_data[sku_data['ds'] <= train_end_dt]
            test_df = sku_data[(sku_data['ds'] >= test_start_dt) & (sku_data['ds'] <= test_end_dt)]
            
            # Convert train_df to MockSalesLog list for your forecaster
            sales_logs = [MockSalesLog(row['ds'], row['y']) for _, row in train_df.iterrows()]
            
            # Actual target for the month
            actual_sales_sum = test_df['y'].sum()
            
            # Predict using your sku_forecast
            predicted_sales = sku_forecast(sales_logs, forecast_days, holidays_df)
            
            if predicted_sales is not None:
                results.append({
                    "round": round_idx + 1,
                    "sku": sku,
                    "actual": actual_sales_sum,
                    "predicted": predicted_sales,
                    "error": abs(actual_sales_sum - predicted_sales)
                })

    # Compile and analyze results
    results_df = pd.DataFrame(results)

    r3 = results_df[results_df['round'] == 3].copy()
    r3['pct_error'] = r3['error'] / r3['actual'].replace(0, 1) * 100
    print(r3.sort_values('pct_error', ascending=False)[['sku', 'actual', 'predicted', 'error', 'pct_error']].head(15).to_string()) 
    
    print("\n--- Evaluation Complete ---")
    for r in range(1, len(rounds) + 1):
        round_res = results_df[results_df['round'] == r]
        mae = mean_absolute_error(round_res['actual'], round_res['predicted'])
        rmse = np.sqrt(mean_squared_error(round_res['actual'], round_res['predicted']))
        
        print(f"Round {r} Metrics:")
        print(f"  MAE:  {mae:.2f} (Average prediction off by ~{mae:.0f} units)")
        print(f"  RMSE: {rmse:.2f}")

if __name__ == "__main__":
    run_backtest()