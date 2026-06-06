import os
from utils.extract import extract_all_products
from utils.transform import transform
from utils.load import load_to_csv, load_to_postgresql, load_to_google_sheets


#  Konfigurasi 
CSV_PATH = "products.csv"

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:password@localhost:5432/fashion_db",
)


SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "1wJ9sBWLJZOxBD3WaPti22tLqbt8pIXi2bRcNfyYz5a0")
CREDENTIALS_PATH = "google-sheets-api.json"
SHEET_NAME = "Products"


def run_etl():
    print("=" * 50)
    print("ETL Pipeline — Fashion Studio")
    print("=" * 50)

    # 1. Extract 
    print("\n[Step 1] Extracting data...")
    raw_products = extract_all_products()

    if not raw_products:
        print("No products extracted. Aborting pipeline.")
        return

    #  2. Transform 
    print("\n[Step 2] Transforming data...")
    df = transform(raw_products)

    if df.empty:
        print("DataFrame is empty after transformation. Aborting pipeline.")
        return

    #  3. Load 
    print("\n[Step 3] Loading data...")

    # 3a. CSV
    load_to_csv(df, CSV_PATH)

    # 3b. PostgreSQL 
    if "password" not in DB_URL:
        load_to_postgresql(df, DB_URL)
    else:
        print("[Load PostgreSQL] Skipped — DATABASE_URL not configured.")

    # 3c. Google Sheets 
    if os.path.exists(CREDENTIALS_PATH) and SPREADSHEET_ID != "your-spreadsheet-id-here":
        load_to_google_sheets(df, CREDENTIALS_PATH, SPREADSHEET_ID, SHEET_NAME)
    else:
        print("[Load Sheets] Skipped — credentials or SPREADSHEET_ID not configured.")

    print("\n" + "=" * 50)
    print(f"Pipeline selesai! Total produk bersih: {len(df)}")
    print("=" * 50)


if __name__ == "__main__":
    run_etl()
