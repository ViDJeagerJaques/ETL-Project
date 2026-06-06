import pytest
import pandas as pd
from utils.transform import transform, EXCHANGE_RATE_USD_TO_IDR


#  Fixtures 

def make_valid_products():
    return [
        {
            "title": "Casual T-Shirt",
            "price": "$19.99",
            "rating": "Rating: ⭐ 4.5 / 5",
            "colors": "3 Colors",
            "size": "Size: M",
            "gender": "Gender: Men",
        },
        {
            "title": "Slim Pants",
            "price": "$29.99",
            "rating": "Rating: ⭐ 3.8 / 5",
            "colors": "2 Colors",
            "size": "Size: L",
            "gender": "Gender: Women",
        },
    ]


# Basic output 

class TestTransformOutput:
    def test_returns_dataframe(self):
        df = transform(make_valid_products())
        assert isinstance(df, pd.DataFrame)

    def test_correct_row_count(self):
        df = transform(make_valid_products())
        assert len(df) == 2

    def test_correct_columns(self):
        df = transform(make_valid_products())
        expected_cols = {"title", "price", "rating", "colors", "size", "gender"}
        assert expected_cols.issubset(set(df.columns))


# Price cleaning 

class TestTransformPrice:
    def test_price_converted_to_idr(self):
        df = transform(make_valid_products())
        expected = 19.99 * EXCHANGE_RATE_USD_TO_IDR
        assert abs(df.loc[0, "price"] - expected) < 0.01

    def test_price_unavailable_removed(self):
        products = make_valid_products() + [
            {
                "title": "Mystery Jacket",
                "price": "Price Unavailable",
                "rating": "Rating: ⭐ 4.0 / 5",
                "colors": "1 Colors",
                "size": "Size: XL",
                "gender": "Gender: Unisex",
            }
        ]
        df = transform(products)
        assert len(df) == 2  # unavailable row dropped

    def test_price_is_numeric(self):
        df = transform(make_valid_products())
        assert pd.api.types.is_numeric_dtype(df["price"])


#  Rating cleaning 

class TestTransformRating:
    def test_rating_extracted_as_float(self):
        df = transform(make_valid_products())
        assert df.loc[0, "rating"] == 4.5
        assert df.loc[1, "rating"] == 3.8

    def test_invalid_rating_removed(self):
        products = make_valid_products() + [
            {
                "title": "Bad Rating Product",
                "price": "$9.99",
                "rating": "Rating: ⭐ N/A / 5",
                "colors": "1 Colors",
                "size": "Size: S",
                "gender": "Gender: Men",
            }
        ]
        df = transform(products)
        assert len(df) == 2


#  Colors cleaning

class TestTransformColors:
    def test_colors_extracted_as_int(self):
        df = transform(make_valid_products())
        assert df.loc[0, "colors"] == 3
        assert pd.api.types.is_integer_dtype(df["colors"])


#  Size & Gender cleaning 

class TestTransformSizeGender:
    def test_size_stripped(self):
        df = transform(make_valid_products())
        assert df.loc[0, "size"] == "M"

    def test_gender_stripped(self):
        df = transform(make_valid_products())
        assert df.loc[0, "gender"] == "Men"


#  Duplicates & nulls 

class TestTransformDuplicatesNulls:
    def test_duplicates_removed(self):
        products = make_valid_products() * 3  # triple everything
        df = transform(products)
        assert len(df) == 2  # only unique rows remain

    def test_null_title_removed(self):
        products = make_valid_products() + [
            {
                "title": None,
                "price": "$9.99",
                "rating": "Rating: ⭐ 3.0 / 5",
                "colors": "1 Colors",
                "size": "Size: S",
                "gender": "Gender: Men",
            }
        ]
        df = transform(products)
        assert len(df) == 2

    def test_unknown_product_removed(self):
        products = make_valid_products() + [
            {
                "title": "Unknown Product",
                "price": "$9.99",
                "rating": "Rating: ⭐ 3.0 / 5",
                "colors": "1 Colors",
                "size": "Size: S",
                "gender": "Gender: Men",
            }
        ]
        df = transform(products)
        assert len(df) == 2

    def test_empty_input_returns_empty_df(self):
        df = transform([])
        assert df.empty
