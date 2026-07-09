from pathlib import Path
import pandas as pd
import numpy as np
from sqlalchemy import create_engine


BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
DB_DIR = BASE_DIR / "data" / "db"


PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
DB_DIR.mkdir(parents=True, exist_ok=True)

engine = create_engine(f"sqlite:///{DB_DIR / 'bluestock_mf.db'}")

print("Initializing BlueStock Production ETL Pipeline...")

with open(BASE_DIR / "sql" / "schema.sql", "r") as f:
    schema_ddl = f.read()

with engine.connect() as conn:
    for statement in schema_ddl.split(';'):
        if statement.strip():
            conn.execute(statement)


files = [f"0{i}_" if i<10 else "10_" for i in range(1,11)] # mapping names safely

def run_pipeline():

    df_fund = pd.read_csv(RAW_DIR / "01_fund_master.csv").rename(columns={'scheme_name': 'fund_name'})
    df_fund['launch_date'] = pd.to_datetime(df_fund['launch_date'], errors='coerce')
    df_fund.to_csv(PROCESSED_DIR / "cleaned_01_fund_master.csv", index=False)
    df_fund[['amfi_code', 'fund_name', 'fund_house', 'category', 'launch_date']].to_sql('dim_fund', con=engine, if_exists='replace', index=False)


    df_nav = pd.read_csv(RAW_DIR / "02_nav_history.csv")
    df_nav['date'] = pd.to_datetime(df_nav['date'], errors='coerce')
    df_nav = df_nav.drop_duplicates().dropna(subset=['nav'])
    df_nav = df_nav[df_nav['nav'] > 0].sort_values(['amfi_code', 'date'])
    

    df_nav = df_nav.set_index('date').groupby('amfi_code', group_keys=False).apply(
        lambda x: x.asfreq('D').ffill()
    ).drop(columns='amfi_code', errors='ignore').reset_index()
    
    df_nav.to_csv(PROCESSED_DIR / "cleaned_02_nav_history.csv", index=False)
    df_nav.to_sql('fact_nav', con=engine, if_exists='replace', index=False)


    df_trans = pd.read_csv(RAW_DIR / "08_investor_transactions.csv").rename(columns={'transaction_date': 'date', 'amount_inr': 'amount'})
    df_trans['date'] = pd.to_datetime(df_trans['date'], errors='coerce')
    df_trans['transaction_type'] = df_trans['transaction_type'].str.strip().str.upper()
    df_trans['kyc_status'] = df_trans['kyc_status'].str.strip().str.upper()
    df_trans = df_trans[df_trans['amount'] > 0]
    df_trans.to_csv(PROCESSED_DIR / "cleaned_08_investor_transactions.csv", index=False)
    df_trans[['amfi_code', 'investor_id', 'date', 'transaction_type', 'amount', 'state', 'kyc_status']].to_sql('fact_transactions', con=engine, if_exists='replace', index=False)

    df_perf = pd.read_csv(RAW_DIR / "07_scheme_performance.csv").rename(columns={
        'return_1yr_pct': 'return_1y', 'return_3yr_pct': 'return_3y', 'return_5yr_pct': 'return_5y', 'expense_ratio_pct': 'expense_ratio'
    })
    df_perf['anomaly_flag'] = df_perf[['return_1y', 'return_3y', 'return_5y']].apply(lambda x: (x > 100) | (x < -90)).any(axis=1).astype(int)
    df_perf.to_csv(PROCESSED_DIR / "cleaned_07_scheme_performance.csv", index=False)
    df_perf[['amfi_code', 'return_1y', 'return_3y', 'return_5y', 'expense_ratio', 'aum_crore', 'anomaly_flag']].to_sql('fact_performance', con=engine, if_exists='replace', index=False)

   
    for idx, name in enumerate(["03_aum_by_fund_house.csv", "04_monthly_sip_inflows.csv", "05_category_inflows.csv", "06_industry_folio_count.csv", "09_portfolio_holdings.csv", "10_benchmark_indices.csv"], start=3):
        df_temp = pd.read_csv(RAW_DIR / name)
        df_temp.to_csv(PROCESSED_DIR / f"cleaned_{name}", index=False)

    print("Pipeline Execution Completed. All 10 Processed files exported. SQLite DB Generated successfully.")

if __name__ == "__main__":
    run_pipeline()