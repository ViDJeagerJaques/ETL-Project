import os
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock, call
from utils.load import load_to_csv, load_to_postgresql, load_to_google_sheets


#  Fixtures 

@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "title": ["Casual T-Shirt", "Slim Pants"],
        "price": [319840.0, 479840.0],
        "rating": [4.5, 3.8],
        "colors": [3, 2],
        "size": ["M", "L"],
        "gender": ["Men", "Women"],
    })


# load_to_csv 

class TestLoadToCsv:
    def test_creates_csv_file(self, sample_df, tmp_path):
        path = str(tmp_path / "test_products.csv")
        load_to_csv(sample_df, path)
        assert os.path.exists(path)

    def test_csv_has_correct_row_count(self, sample_df, tmp_path):
        path = str(tmp_path / "test_products.csv")
        load_to_csv(sample_df, path)
        loaded = pd.read_csv(path)
        assert len(loaded) == len(sample_df)

    def test_csv_has_correct_columns(self, sample_df, tmp_path):
        path = str(tmp_path / "test_products.csv")
        load_to_csv(sample_df, path)
        loaded = pd.read_csv(path)
        assert list(loaded.columns) == list(sample_df.columns)


#  load_to_postgresql 

class TestLoadToPostgresql:
    @patch("utils.load.create_engine")
    def test_calls_to_sql(self, mock_create_engine, sample_df):
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        with patch.object(sample_df.__class__, "to_sql") as mock_to_sql:
            load_to_postgresql(sample_df, "postgresql+psycopg2://user:pass@localhost/db")
            mock_to_sql.assert_called_once()

    @patch("utils.load.create_engine")
    def test_uses_replace_if_exists(self, mock_create_engine, sample_df):
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        with patch.object(pd.DataFrame, "to_sql") as mock_to_sql:
            load_to_postgresql(sample_df, "postgresql+psycopg2://user:pass@localhost/db")
            _, kwargs = mock_to_sql.call_args
            assert kwargs.get("if_exists") == "replace"

    @patch("utils.load.create_engine")
    def test_raises_on_engine_error(self, mock_create_engine, sample_df):
        mock_create_engine.side_effect = Exception("Connection failed")
        with pytest.raises(Exception, match="Connection failed"):
            load_to_postgresql(sample_df, "bad_url")


# load_to_google_sheets 

class TestLoadToGoogleSheets:
    def test_raises_without_spreadsheet_id(self, sample_df):
        with pytest.raises(ValueError, match="spreadsheet_id"):
            load_to_google_sheets(sample_df, spreadsheet_id=None)

    @patch("utils.load._get_sheets_service")
    def test_calls_sheets_api(self, mock_get_service, sample_df):
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        # Chain: service.spreadsheets().values().clear().execute()
        mock_sheets = mock_service.spreadsheets.return_value
        mock_values = mock_sheets.values.return_value
        mock_values.clear.return_value.execute.return_value = {}
        mock_values.update.return_value.execute.return_value = {}

        load_to_google_sheets(
            sample_df,
            credentials_path="fake-creds.json",
            spreadsheet_id="fake-id",
            sheet_name="Sheet1",
        )

        mock_values.clear.assert_called_once()
        mock_values.update.assert_called_once()

    @patch("utils.load._get_sheets_service")
    def test_raises_on_api_error(self, mock_get_service, sample_df):
        mock_get_service.side_effect = Exception("Auth failed")
        with pytest.raises(Exception, match="Auth failed"):
            load_to_google_sheets(
                sample_df,
                credentials_path="fake-creds.json",
                spreadsheet_id="fake-id",
            )
