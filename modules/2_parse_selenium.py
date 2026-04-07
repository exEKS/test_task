"""Search brain.com.ua with Selenium, open first suggestion, scrape fields, upsert Product."""

from load_django import *
from parser_app.models import Product

import time
from pprint import pprint
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from braincom_extract import configure_utf8_stdio, save_parser_output

configure_utf8_stdio()

BASE_URL = "https://brain.com.ua/ukr/"
SEARCH_QUERY = "Apple iPhone 15 128GB Black"

options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1920,1080")
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 20)

driver.get(BASE_URL)

wait.until(EC.presence_of_element_located(
    (By.XPATH, "//input[@class='quick-search-input' and not(ancestor::*[@style='display:none'])]")
))

try:
    inputs = driver.find_elements(By.XPATH, "//input[@class='quick-search-input']")
    search_input = next((el for el in inputs if el.is_displayed()), None)
    if not search_input:
        raise RuntimeError("Visible search input not found")

    driver.execute_script("arguments[0].scrollIntoView(true);", search_input)
    search_input.click()

    actions = ActionChains(driver)
    for char in SEARCH_QUERY:
        actions.send_keys(char)
        actions.pause(0.08)
    actions.perform()

    print(f"[*] Typed: {SEARCH_QUERY}")

except Exception as e:
    print(f"[!] Input error: {e}")
    driver.quit()
    raise

try:
    search_btn = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[@class='search-button-first-form']")
    ))
    search_btn.click()
    print("[*] Clicked search button")

except TimeoutException:
    print("[!] Search button not found, continuing without click")

time.sleep(2.5)

try:
    first_result = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//a[contains(@href, '-p') and substring(@href, string-length(@href) - 4) = '.html']")
    ))
    href = first_result.get_attribute("href")
    print(f"[*] Found product: {href}")
    first_result.click()

except TimeoutException:
    print("[!] Dropdown did not appear. Saving debug HTML...")
    with open("debug_selenium_timeout.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    driver.quit()
    raise

try:
    wait.until(EC.presence_of_element_located((By.XPATH, "//h1")))
except TimeoutException:
    pass

print(f"[*] Product page: {driver.current_url}")

product = {}

try:
    product["title"] = driver.find_element(
        By.XPATH, "//h1[@class='br-pd-title'] | //h1[@class='main-title'] | //h1"
    ).text.strip()
except Exception:
    product["title"] = None

try:
    product["product_code"] = driver.find_element(
        By.XPATH, "//span[contains(@class,'br-pd-code-n')] | //*[@class='br-pr-code-val']"
    ).text.strip()
except Exception:
    product["product_code"] = None

if not product["product_code"]:
    try:
        product["product_code"] = driver.find_element(
            By.XPATH, "//span[contains(text(),'Код товару')]/following-sibling::*[1]"
        ).text.strip()
    except Exception:
        pass

try:
    product["regular_price"] = driver.find_element(
        By.XPATH, "//meta[@itemprop='price']"
    ).get_attribute("content")
except Exception:
    product["regular_price"] = None

if not product["regular_price"]:
    try:
        product["regular_price"] = driver.find_element(
            By.XPATH, "//div[@class='br-pr-c-main']"
        ).text.strip()
    except Exception:
        product["regular_price"] = None

try:
    product["sale_price"] = driver.find_element(
        By.XPATH, "//*[contains(@class,'price-old') or contains(@class,'br-pr-c-old')]"
    ).text.strip()
    if len(product["sale_price"]) > 80:
        product["sale_price"] = None
except Exception:
    product["sale_price"] = None

try:
    reviews_el = driver.find_element(
        By.XPATH, "//a[contains(@class,'reviews-count')]//span"
    )
    raw = reviews_el.text.strip()
    product["reviews_count"] = int(raw) if raw.isdigit() else None
except Exception:
    product["reviews_count"] = None

try:
    imgs = driver.find_elements(
        By.XPATH, "//*[contains(@class,'br-pic-block') or contains(@class,'product-gallery')]//img"
    )
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
    rows = driver.find_elements(
        By.XPATH,
        "//*[contains(@class,'br-pd-char-item') or contains(@class,'br-pr-chr-item')]//div/div"
    )
    for row in rows:
        try:
            spans = row.find_elements(By.XPATH, "./span")
            if len(spans) >= 2:
                key = spans[0].text.strip()
                val = spans[1].text.strip()
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

pprint(product)
output_path = save_parser_output(product, "selenium")
print(f"[*] JSON saved: {output_path}")
driver.quit()

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
    parser_type="selenium",
    defaults=defaults,
)

if created:
    print(f"\n[DB] New product saved: {obj}")
else:
    for field, value in defaults.items():
        setattr(obj, field, value)
    obj.save()
    print(f"\n[DB] Existing product updated: {obj}")
