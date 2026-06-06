import pytest
from unittest.mock import patch, MagicMock
from utils.extract import get_page, parse_products, get_total_pages, extract_all_products


# ── Fixtures ──────────────────────────────────────────────────────────────────

SAMPLE_HTML_PAGE1 = """
<html>
<body>
  <div class="collection-card">
    <h3 class="product-title">Casual T-Shirt</h3>
    <span class="price">$19.99</span>
    <p>Rating: ⭐ 4.5 / 5</p>
    <p>3 Colors</p>
    <p>Size: M</p>
    <p>Gender: Men</p>
  </div>
  <div class="collection-card">
    <h3 class="product-title">Slim Pants</h3>
    <span class="price">$29.99</span>
    <p>Rating: ⭐ 3.8 / 5</p>
    <p>2 Colors</p>
    <p>Size: L</p>
    <p>Gender: Women</p>
  </div>
  <div class="pagination-container">
    <a class="page-link" href="/page1">1</a>
    <a class="page-link" href="/page2">2</a>
  </div>
</body>
</html>
"""

SAMPLE_HTML_UNAVAILABLE = """
<html>
<body>
  <div class="collection-card">
    <h3 class="product-title">Mystery Jacket</h3>
    <p class="price-unavailable">Price Unavailable</p>
    <p>Rating: ⭐ 4.0 / 5</p>
    <p>1 Colors</p>
    <p>Size: XL</p>
    <p>Gender: Unisex</p>
  </div>
</body>
</html>
"""


# get_page 

class TestGetPage:
    @patch("utils.extract.requests.get")
    def test_get_page_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = "<html>OK</html>"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = get_page("https://fashion-studio.dicoding.dev")
        assert result == "<html>OK</html>"
        mock_get.assert_called_once()

    @patch("utils.extract.requests.get")
    def test_get_page_failure_returns_none(self, mock_get):
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

        result = get_page("https://fashion-studio.dicoding.dev", retries=1, delay=0)
        assert result is None

    @patch("utils.extract.requests.get")
    def test_get_page_retries_on_failure(self, mock_get):
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError("fail")

        get_page("https://fashion-studio.dicoding.dev", retries=3, delay=0)
        assert mock_get.call_count == 3


# parse_products 

class TestParseProducts:
    def test_parse_products_normal(self):
        products = parse_products(SAMPLE_HTML_PAGE1)
        assert len(products) == 2
        assert products[0]["title"] == "Casual T-Shirt"
        assert products[0]["price"] == "$19.99"

    def test_parse_products_price_unavailable(self):
        products = parse_products(SAMPLE_HTML_UNAVAILABLE)
        assert len(products) == 1
        assert "Unavailable" in products[0]["price"]

    def test_parse_products_empty_html(self):
        products = parse_products("<html><body></body></html>")
        assert products == []

    def test_parse_products_returns_list(self):
        products = parse_products(SAMPLE_HTML_PAGE1)
        assert isinstance(products, list)
        for p in products:
            assert isinstance(p, dict)


# get_total_pages 

class TestGetTotalPages:
    def test_returns_correct_page_count(self):
        total = get_total_pages(SAMPLE_HTML_PAGE1)
        assert total == 2

    def test_returns_1_when_no_pagination(self):
        html = "<html><body><p>No pagination</p></body></html>"
        total = get_total_pages(html)
        assert total == 1


#  extract_all_products 

class TestExtractAllProducts:
    @patch("utils.extract.get_page")
    def test_extract_all_products_single_page(self, mock_get_page):
        mock_get_page.return_value = SAMPLE_HTML_PAGE1.replace(
            '<a class="page-link" href="/page2">2</a>', ""
        )
        products = extract_all_products()
        assert len(products) == 2

    @patch("utils.extract.time.sleep", return_value=None)
    @patch("utils.extract.get_page")
    def test_extract_all_products_multiple_pages(self, mock_get_page, mock_sleep):
        mock_get_page.side_effect = [SAMPLE_HTML_PAGE1, SAMPLE_HTML_PAGE1]
        products = extract_all_products()
        assert len(products) == 4  # 2 products × 2 pages

    @patch("utils.extract.get_page")
    def test_extract_raises_on_first_page_failure(self, mock_get_page):
        mock_get_page.return_value = None
        with pytest.raises(ConnectionError):
            extract_all_products()
