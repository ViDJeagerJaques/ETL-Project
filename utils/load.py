import os
import json
import pandas as pd
from sqlalchemy import create_engine
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


#  CSV

def load_to_csv(df: pd.DataFrame, filepath: str = "products.csv") -> None:
    """Save DataFrame to a CSV file."""
    try:
        df.to_csv(filepath, index=False)
        print(f"[Load CSV] Saved {len(df)} rows to '{filepath}'.")
    except Exception as e:
        print(f"[Load CSV] Error: {e}")
        raise


#  PostgreSQL 

def load_to_postgresql(
    df: pd.DataFrame,
    db_url: str,
    table_name: str = "products",
) -> None:
    """
    Save DataFrame to a PostgreSQL table.

    Args:
        df       : Cleaned DataFrame.
        db_url   : SQLAlchemy connection string,
                   e.g. 'postgresql+psycopg2://user:pass@host:5432/dbname'
        table_name: Target table (created/replaced automatically).
    """
    try:
        engine = create_engine(db_url)
        df.to_sql(table_name, engine, if_exists="replace", index=False)
        print(f"[Load PostgreSQL] Saved {len(df)} rows to table '{table_name}'.")
    except Exception as e:
        print(f"[Load PostgreSQL] Error: {e}")
        raise


# Google Sheets 

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def _get_sheets_service(credentials_path: str):
    """Build and return a Google Sheets API service object."""
    creds = Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
    service = build("sheets", "v4", credentials=creds)
    return service


def load_to_google_sheets(
    df: pd.DataFrame,
    credentials_path: str = "google-sheets-api.json",
    spreadsheet_id: str = None,
    sheet_name: str = "Sheet1",
) -> None:
    """
    Upload DataFrame to Google Sheets.

    Args:
        df              : Cleaned DataFrame.
        credentials_path: Path to the service-account JSON key file.
        spreadsheet_id  : The ID from the Sheets URL
                          (https://docs.google.com/spreadsheets/d/<ID>/edit).
        sheet_name      : Target worksheet name.
    """
    if not spreadsheet_id:
        raise ValueError("spreadsheet_id must be provided.")

    try:
        service = _get_sheets_service(credentials_path)

        
        header = df.columns.tolist()
        rows = df.astype(str).values.tolist()
        values = [header] + rows

        body = {"values": values}

        
        range_notation = f"{sheet_name}!A1"
        service.spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id,
            range=range_notation,
        ).execute()

        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_notation,
            valueInputOption="RAW",
            body=body,
        ).execute()

        print(
            f"[Load Sheets] Uploaded {len(df)} rows to "
            f"spreadsheet '{spreadsheet_id}', sheet '{sheet_name}'."
        )
    except Exception as e:
        print(f"[Load Sheets] Error: {e}")
        raise
