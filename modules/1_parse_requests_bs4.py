"""Fetch one product URL with requests/BeautifulSoup and upsert Product."""

from load_django import *
from parser_app.models import Product

import requests
from bs4 import BeautifulSoup
from pprint import pprint

from braincom_extract import build_product_dict_from_soup, configure_utf8_stdio, save_parser_output

configure_utf8_stdio()

URL = (
    "https://brain.com.ua/ukr/"
    "Mobilniy_telefon_Apple_iPhone_16_Pro_Max_256GB_Black_Titanium-p1145443.html"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:126.0) "
        "Gecko/20100101 Firefox/126.0"
    ),
    "Accept-Language": "uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7",
}

response = requests.get(URL, headers=HEADERS, timeout=20)
response.raise_for_status()
response.encoding = response.apparent_encoding or "utf-8"

soup = BeautifulSoup(response.text, "html.parser")
product = build_product_dict_from_soup(soup)

pprint(product)
output_path = save_parser_output(product, "requests_bs4")
print(f"[*] JSON saved: {output_path}")

defaults = {
    "full_title": product.get("title"),
    "color": product.get("color"),
    "storage": product.get("storage"),
    "manufacturer": product.get("manufacturer"),
    "regular_price": product.get("regular_price"),
    "sale_price": product.get("sale_price"),
    "photos": product.get("photos"),
    "reviews_count": product.get("reviews_count"),
    "screen_diagonal": product.get("screen_diagonal"),
    "screen_resolution": product.get("screen_resolution"),
    "specifications": product.get("specifications"),
}

obj, created = Product.objects.get_or_create(
    product_code=product.get("product_code"),
    parser_type="requests_bs4",
    defaults=defaults,
)

if created:
    print(f"\n[DB] New product saved: {obj}")
else:
    for field, value in defaults.items():
        setattr(obj, field, value)
    obj.save()
    print(f"\n[DB] Existing product updated: {obj}")
