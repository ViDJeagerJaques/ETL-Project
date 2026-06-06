import re
import requests
from bs4 import BeautifulSoup
import time


BASE_URL = "https://fashion-studio.dicoding.dev"


def get_page(url, retries=3, delay=2):
    """Fetch a single page with retry mechanism."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/114.0.0.0 Safari/537.36"
        )
    }
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"[Attempt {attempt + 1}] Error fetching {url}: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
    return None


def parse_products(html):
    """Parse product data from a page's HTML."""
    soup = BeautifulSoup(html, "html.parser")
    products = []

    product_cards = soup.find_all("div", class_="collection-card")

    for card in product_cards:
        try:
            # Title
            title_tag = card.find("h3", class_="product-title")
            title = title_tag.get_text(strip=True) if title_tag else None

            # Price — two different HTML structures
            price_tag = card.find("span", class_="price")
            if price_tag:
                price = price_tag.get_text(strip=True)
            else:
                unavailable_tag = card.find("p", class_="price-unavailable")
                price = unavailable_tag.get_text(strip=True) if unavailable_tag else None

            # Rating
            rating_tag = card.find("p", string=lambda t: t and "Rating:" in t)
            rating = rating_tag.get_text(strip=True) if rating_tag else None

            # Colors
            colors_tag = card.find("p", string=lambda t: t and "Colors" in t)
            colors = colors_tag.get_text(strip=True) if colors_tag else None

            # Size
            size_tag = card.find("p", string=lambda t: t and "Size:" in t)
            size = size_tag.get_text(strip=True) if size_tag else None

            # Gender
            gender_tag = card.find("p", string=lambda t: t and "Gender:" in t)
            gender = gender_tag.get_text(strip=True) if gender_tag else None

            products.append({
                "title": title,
                "price": price,
                "rating": rating,
                "colors": colors,
                "size": size,
                "gender": gender,
            })
        except Exception as e:
            print(f"Error parsing product card: {e}")
            continue

    return products


def get_total_pages(html):
    """Extract total number of pages from pagination."""
    soup = BeautifulSoup(html, "html.parser")

    
    page_info = soup.find(string=re.compile(r"\d+\s+of\s+\d+"))
    if page_info:
        match = re.search(r"\d+\s+of\s+(\d+)", page_info)
        if match:
            return int(match.group(1))

   
    all_links = soup.find_all("a", href=re.compile(r"/page\d+"))
    page_numbers = []
    for link in all_links:
        match = re.search(r"/page(\d+)", link.get("href", ""))
        if match:
            page_numbers.append(int(match.group(1)))
    if page_numbers:
        return max(page_numbers)

    
    pagination = soup.find("div", class_="pagination-container")
    if pagination:
        for link in pagination.find_all("a"):
            text = link.get_text(strip=True)
            if text.isdigit():
                page_numbers.append(int(text))
        if page_numbers:
            return max(page_numbers)

    return 1


def extract_all_products():
    """Extract all products across all pages."""
    print("Starting extraction...")

    first_page_html = get_page(BASE_URL)
    if not first_page_html:
        raise ConnectionError("Failed to fetch the first page.")

    total_pages = get_total_pages(first_page_html)
    print(f"Total pages found: {total_pages}")

    all_products = parse_products(first_page_html)
    print(f"Page 1: {len(all_products)} products extracted.")

    for page in range(2, total_pages + 1):
        url = f"{BASE_URL}/page{page}"
        html = get_page(url)
        if html:
            products = parse_products(html)
            all_products.extend(products)
            print(f"Page {page}: {len(products)} products extracted.")
        else:
            print(f"Page {page}: Failed to fetch, skipping.")
        time.sleep(1)

    print(f"Extraction complete. Total products: {len(all_products)}")
    return all_products