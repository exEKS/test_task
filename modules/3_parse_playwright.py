"""Search brain.com.ua with Playwright, open first suggestion, scrape fields, upsert Product."""

from load_django import *
from parser_app.models import Product

from pprint import pprint
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from braincom_extract import configure_utf8_stdio, save_parser_output

configure_utf8_stdio()

BASE_URL = "https://brain.com.ua/ukr/"
SEARCH_QUERY = "Apple iPhone 15 128GB Black"

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1920, "height": 1080},
    )
    page = context.new_page()

    page.goto(BASE_URL, wait_until="domcontentloaded")

    try:
        search_field = page.locator("xpath=//input[@class='quick-search-input']").filter(visible=True).first
        search_field.wait_for(state="visible", timeout=10000)
        search_field.click()

        search_field.type(SEARCH_QUERY, delay=80)
        print(f"[*] Typed: {SEARCH_QUERY}")

    except PlaywrightTimeoutError as e:
        print(f"[!] Search input timeout: {e}")
        browser.close()
        raise
    except Exception as e:
        print(f"[!] Search input error: {e}")
        browser.close()
        raise

    try:
        search_btn = page.locator("xpath=//button[@class='search-button-first-form']").first
        search_btn.click(timeout=5000)
        print("[*] Clicked search button")
    except Exception:
        print("[!] Search button not found, continuing without click")

    page.wait_for_timeout(2500)

    try:
        first_link = page.locator(
            "xpath=//a[contains(@href, '-p') and substring(@href, string-length(@href) - 4) = '.html']"
        ).first
        first_link.wait_for(state="visible", timeout=15000)
        href = first_link.get_attribute("href")
        print(f"[*] Found product: {href}")
        first_link.click()

    except PlaywrightTimeoutError:
        print("[!] Dropdown did not appear. Saving debug info...")
        with open("debug_playwright_timeout.html", "w", encoding="utf-8") as f:
            f.write(page.content())
        page.screenshot(path="debug_playwright_timeout.png")
        browser.close()
        raise

    except Exception as e:
        print(f"[!] Click error: {e}")
        browser.close()
        raise

    try:
        page.wait_for_selector("xpath=//h1", timeout=20000)
    except PlaywrightTimeoutError:
        pass

    print(f"[*] Product page: {page.url}")

    product = {}

    try:
        product["title"] = page.locator(
            "xpath=//h1[@class='br-pd-title'] | //h1[@class='main-title'] | //h1"
        ).first.inner_text(timeout=5000).strip()
    except Exception:
        product["title"] = None

    try:
        product["product_code"] = page.locator(
            "xpath=//*[contains(@class,'br-pd-code-n')] | //*[@class='br-pr-code-val']"
        ).first.inner_text(timeout=3000).strip()
    except Exception:
        product["product_code"] = None

    if not product["product_code"]:
        try:
            product["product_code"] = page.locator(
                "xpath=//span[contains(text(),'Код товару')]/following-sibling::*[1]"
            ).first.inner_text(timeout=3000).strip()
        except Exception:
            pass

    try:
        product["regular_price"] = page.locator(
            "xpath=//meta[@itemprop='price']"
        ).first.get_attribute("content")
    except Exception:
        product["regular_price"] = None

    if not product["regular_price"]:
        try:
            product["regular_price"] = page.locator(
                "xpath=//div[@class='br-pr-c-main']"
            ).first.inner_text(timeout=3000).strip()
        except Exception:
            product["regular_price"] = None

    try:
        sale = page.locator(
            "xpath=//*[contains(@class,'price-old') or contains(@class,'br-pr-c-old')]"
        ).first.inner_text(timeout=3000).strip()
        product["sale_price"] = sale if len(sale) <= 80 else None
    except Exception:
        product["sale_price"] = None

    try:
        raw = page.locator(
            "xpath=//a[contains(@class,'reviews-count')]//span"
        ).first.inner_text(timeout=3000).strip()
        product["reviews_count"] = int(raw) if raw.isdigit() else None
    except Exception:
        product["reviews_count"] = None

    try:
        imgs = page.locator(
            "xpath=//*[contains(@class,'br-pic-block') or contains(@class,'product-gallery')]//img"
        ).all()
        urls = []
        for img in imgs:
            src = img.get_attribute("data-src") or img.get_attribute("data-observe-src") or img.get_attribute("src")
            if src and src.startswith("http"):
                urls.append(src)
        product["photos"] = urls if urls else None
    except Exception:
        product["photos"] = None

    specs = {}
    try:
        rows = page.locator(
            "xpath=//*[contains(@class,'br-pd-char-item') or contains(@class,'br-pr-chr-item')]//div/div"
        ).all()
        for row in rows:
            try:
                spans = row.locator("xpath=./span").all()
                if len(spans) >= 2:
                    key = spans[0].inner_text(timeout=1000).strip()
                    val = spans[1].inner_text(timeout=1000).strip()
                    if key:
                        specs[key] = val
            except Exception:
                continue
    except Exception:
        pass

    product["specifications"] = specs if specs else None

    def get_spec(specs, keys):
        for needle in keys:
            for k, v in specs.items():
                if needle.lower() in k.lower():
                    return v
        return None

    product["color"] = get_spec(specs, ["колір", "цвет", "color"])
    product["storage"] = get_spec(specs, ["пам'ять", "память", "storage", "ємність", "вбудована пам"])
    product["manufacturer"] = get_spec(specs, ["виробник", "производитель", "manufacturer", "бренд"])
    product["screen_diagonal"] = get_spec(specs, ["діагональ", "диагональ", "diagonal"])
    product["screen_resolution"] = get_spec(specs, ["роздільна", "разреш", "resolution"])

    browser.close()

pprint(product)
output_path = save_parser_output(product, "playwright")
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
    parser_type="playwright",
    defaults=defaults,
)

if created:
    print(f"\n[DB] New product saved: {obj}")
else:
    for field, value in defaults.items():
        setattr(obj, field, value)
    obj.save()
    print(f"\n[DB] Existing product updated: {obj}")
