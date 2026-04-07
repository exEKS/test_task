"""Export all Product rows to products.csv in the current working directory."""

from load_django import *
from parser_app.models import Product

import csv
import json

OUTPUT_FILE = "products.csv"

FIELDS = [
    "id",
    "parser_type",
    "product_code",
    "full_title",
    "manufacturer",
    "color",
    "storage",
    "regular_price",
    "sale_price",
    "reviews_count",
    "screen_diagonal",
    "screen_resolution",
    "photos",
    "specifications",
    "parsed_at",
]

products = Product.objects.all().order_by("id")

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=FIELDS)
    writer.writeheader()

    for p in products:
        writer.writerow({
            "id": p.id,
            "parser_type": p.parser_type,
            "product_code": p.product_code,
            "full_title": p.full_title,
            "manufacturer": p.manufacturer,
            "color": p.color,
            "storage": p.storage,
            "regular_price": p.regular_price,
            "sale_price": p.sale_price,
            "reviews_count": p.reviews_count,
            "screen_diagonal": p.screen_diagonal,
            "screen_resolution": p.screen_resolution,
            "photos": json.dumps(p.photos, ensure_ascii=False) if p.photos else "",
            "specifications": json.dumps(p.specifications, ensure_ascii=False) if p.specifications else "",
            "parsed_at": p.parsed_at.strftime("%Y-%m-%d %H:%M:%S") if p.parsed_at else "",
        })

print(f"[*] Exported {products.count()} records -> {OUTPUT_FILE}")
