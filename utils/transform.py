import pandas as pd
from datetime import datetime


EXCHANGE_RATE_USD_TO_IDR = 16000


def transform(products: list) -> pd.DataFrame:
    df = pd.DataFrame(products)

    print(f"[Transform] Raw rows: {len(df)}")

    if df.empty:
        return df


    df = df.drop_duplicates()
    print(f"[Transform] After drop_duplicates: {len(df)}")

    df["timestamp"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
    df["timestamp"] = df["timestamp"].astype("object")

    df = df[df["title"].notna()]
    df = df[df["title"].str.strip() != ""]
    df = df[~df["title"].str.contains("Unknown Product", na=False)]


    df = df[df["price"].notna()]
    df = df[~df["price"].str.contains("Unavailable", case=False, na=True)]
    df["price"] = df["price"].str.replace("$", "", regex=False).str.strip()
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df.dropna(subset=["price"])
    df["price"] = df["price"] * EXCHANGE_RATE_USD_TO_IDR


    df = df[df["rating"].notna()]
    df = df[~df["rating"].str.contains("Invalid|Not Rated", case=False, na=True)]
    df["rating"] = df["rating"].str.extract(r"([\d.]+)\s*/\s*5")
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df = df.dropna(subset=["rating"])
    df = df[df["rating"] <= 5.0]


    df["colors"] = df["colors"].str.extract(r"(\d+)")
    df["colors"] = pd.to_numeric(df["colors"], errors="coerce")
    df = df.dropna(subset=["colors"])
    df["colors"] = df["colors"].astype(int)

  
    df["size"] = df["size"].str.replace("Size:", "", regex=False).str.strip()
    df = df[df["size"].notna()]
    df = df[df["size"].str.strip() != ""]


    df["title"] = df["title"].astype("object")
    df["size"] = df["size"].astype("object")
    df["gender"] = df["gender"].astype("object")
    df["gender"] = df["gender"].str.replace("Gender:", "", regex=False).str.strip()

    df = df.reset_index(drop=True)

    print(f"[Transform] Final clean rows: {len(df)}")
    return df