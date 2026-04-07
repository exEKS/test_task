"""Shared brain.com.ua product extraction (BeautifulSoup, Selenium, Playwright)."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def configure_utf8_stdio() -> None:
    """Force UTF-8 encoding on stdout/stderr (Windows)."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except (OSError, ValueError, AttributeError):
                pass


def parse_specifications_from_soup(soup: Any) -> dict[str, str] | None:
    """Parse specification table rows from the product page HTML."""
    specs: dict[str, str] = {}
    try:
        items = soup.select(".br-pd-char-item, .br-pr-chr-item")
        for item in items:
            try:
                inner = item.find("div")
                if not inner:
                    continue
                for row in inner.find_all("div", recursive=False):
                    try:
                        spans = row.find_all("span", recursive=False)
                        if len(spans) >= 2:
                            key = spans[0].get_text(strip=True)
                            val = spans[1].get_text(" ", strip=True)
                            if key:
                                specs[key] = val
                    except (AttributeError, TypeError):
                        continue
            except (AttributeError, TypeError):
                continue
    except (AttributeError, TypeError):
        pass
    return specs if specs else None


def _price_from_ld_json_soup(soup: Any) -> str | None:
    try:
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                raw = script.string or script.get_text() or ""
                if not raw.strip():
                    continue
                data = json.loads(raw)
                candidates: list[Any] = data if isinstance(data, list) else [data]
                for obj in candidates:
                    if not isinstance(obj, dict):
                        continue
                    offers = obj.get("offers")
                    if isinstance(offers, dict) and offers.get("price") is not None:
                        return str(offers["price"]).strip()
                    if isinstance(offers, list):
                        for off in offers:
                            if isinstance(off, dict) and off.get("price") is not None:
                                return str(off["price"]).strip()
            except (json.JSONDecodeError, TypeError, AttributeError, KeyError):
                continue
    except (AttributeError, TypeError):
        pass
    return None


def extract_title_from_soup(soup: Any) -> str | None:
    for sel in ("h1.br-pd-title", "h1.main-title"):
        try:
            h = soup.select_one(sel)
            if h:
                t = h.get_text(strip=True)
                if t:
                    return t
        except (AttributeError, TypeError):
            pass
    try:
        h = soup.find("h1")
        if h:
            t = h.get_text(strip=True)
            if t:
                return t
    except (AttributeError, TypeError):
        pass
    return None


def extract_product_code_from_soup(soup: Any) -> str | None:
    for sel in (
        "span.br-pd-code-n",
        '[class*="br-pd-code-n"]',
        ".br-pr-code-val",
        "#product_code .br-pr-code-val",
    ):
        try:
            el = soup.select_one(sel)
            if el:
                t = el.get_text(strip=True)
                if t:
                    return t
        except (AttributeError, TypeError):
            continue
    try:
        for span in soup.find_all("span"):
            try:
                text = span.get_text(strip=True)
                if text in ("Код товару:", "Код товару", "Артикул"):
                    sib = span.find_next_sibling()
                    if sib:
                        t = sib.get_text(strip=True)
                        if t:
                            return t
            except (AttributeError, TypeError):
                continue
    except (AttributeError, TypeError):
        pass
    return None


def extract_regular_price_from_soup(soup: Any) -> str | None:
    try:
        m = soup.find("meta", attrs={"itemprop": "price"})
        if m and m.get("content"):
            c = (m.get("content") or "").strip()
            if c:
                return c
    except (AttributeError, TypeError, KeyError):
        pass
    try:
        d = soup.select_one("div.br-pr-c-main")
        if d:
            t = d.get_text(strip=True)
            if t:
                return t
    except (AttributeError, TypeError):
        pass
    try:
        d = soup.select_one(".br-pp-price")
        if d:
            parts: list[str] = []
            for sp in d.find_all("span", recursive=False):
                try:
                    cls = sp.get("class") or []
                    if "hidden" in cls or "data_io" in cls:
                        continue
                    t = sp.get_text(strip=True)
                    if t:
                        parts.append(t)
                except (AttributeError, TypeError):
                    continue
            if parts:
                return " ".join(parts).strip()
    except (AttributeError, TypeError):
        pass
    try:
        wrap = soup.select_one(".product-content-wrapper[data-price]")
        if wrap and wrap.get("data-price"):
            return str(wrap["data-price"]).strip()
    except (AttributeError, TypeError, KeyError):
        pass
    return _price_from_ld_json_soup(soup)


def extract_sale_price_from_soup(soup: Any) -> str | None:
    try:
        d = soup.select_one(".price-old, .br-pr-c-old, .product-price__old")
        if d:
            t = d.get_text(strip=True)
            if t and len(t) <= 80:
                return t
    except (AttributeError, TypeError):
        pass
    return None


def extract_reviews_count_from_soup(soup: Any) -> int | None:
    try:
        el = soup.select_one("a.reviews-count span")
        if el:
            raw = el.get_text(strip=True)
            if raw.isdigit():
                return int(raw)
    except (AttributeError, TypeError, ValueError):
        pass
    try:
        el = soup.select_one(".rating-count, .reviews-count")
        if el:
            raw = el.get_text(strip=True)
            digits = "".join(filter(str.isdigit, raw))
            if digits:
                return int(digits)
    except (AttributeError, TypeError, ValueError):
        pass
    return None


def extract_photos_from_soup(soup: Any) -> list[str] | None:
    urls: list[str] = []
    try:
        block = soup.select_one(".br-pic-block, .product-gallery")
        scope = block if block else soup
        for img in scope.find_all("img"):
            try:
                src = img.get("data-src") or img.get("data-observe-src") or img.get("src")
                if src and isinstance(src, str) and src.startswith("http"):
                    urls.append(src)
            except (AttributeError, TypeError):
                continue
    except (AttributeError, TypeError):
        pass
    return urls if urls else None


def _get_spec(specs: dict[str, str], keys: list[str]) -> str | None:
    for needle in keys:
        try:
            nl = needle.lower()
            for spec_key, spec_val in specs.items():
                if nl in spec_key.lower():
                    return spec_val
        except Exception:
            continue
    return None


def build_product_dict_from_soup(soup: Any) -> dict[str, Any]:
    """Build a flat product dict from BeautifulSoup of a product page."""
    specs_dict: dict[str, str] = parse_specifications_from_soup(soup) or {}
    product: dict[str, Any] = {}
    for field, fn in [
        ("title", lambda: extract_title_from_soup(soup)),
        ("product_code", lambda: extract_product_code_from_soup(soup)),
        ("regular_price", lambda: extract_regular_price_from_soup(soup)),
        ("sale_price", lambda: extract_sale_price_from_soup(soup)),
        ("reviews_count", lambda: extract_reviews_count_from_soup(soup)),
        ("photos", lambda: extract_photos_from_soup(soup)),
        ("specifications", lambda: parse_specifications_from_soup(soup)),
        ("color", lambda: _get_spec(specs_dict, ["колір", "цвет", "color"])),
        ("storage", lambda: _get_spec(specs_dict, ["пам'ять", "память", "storage", "ємність", "вбудована пам"])),
        ("manufacturer", lambda: _get_spec(specs_dict, ["виробник", "производитель", "manufacturer", "бренд"])),
        ("screen_diagonal", lambda: _get_spec(specs_dict, ["діагональ", "диагональ", "diagonal"])),
        ("screen_resolution", lambda: _get_spec(specs_dict, ["роздільна", "разреш", "resolution"])),
    ]:
        try:
            product[field] = fn()
        except Exception:
            product[field] = None
    return product


def _selenium_meta_content(driver: Any, selector: str) -> str | None:
    from selenium.webdriver.common.by import By
    from selenium.common.exceptions import NoSuchElementException
    try:
        el = driver.find_element(By.CSS_SELECTOR, selector)
        c = el.get_attribute("content")
        if c and c.strip():
            return c.strip()
    except (NoSuchElementException, Exception):
        pass
    return None


def _selenium_first_text(driver: Any, selectors: list[str]) -> str | None:
    from selenium.webdriver.common.by import By
    from selenium.common.exceptions import NoSuchElementException
    for css in selectors:
        try:
            el = driver.find_element(By.CSS_SELECTOR, css)
            t = el.text.strip()
            if t:
                return t
        except (NoSuchElementException, Exception):
            continue
    return None


def _selenium_price_from_ld_json(driver: Any) -> str | None:
    from selenium.webdriver.common.by import By
    try:
        scripts = driver.find_elements(By.CSS_SELECTOR, 'script[type="application/ld+json"]')
        for script in scripts:
            try:
                raw = script.get_attribute("innerHTML") or script.text or ""
                if not raw.strip():
                    continue
                data = json.loads(raw)
                items = data if isinstance(data, list) else [data]
                for obj in items:
                    if not isinstance(obj, dict):
                        continue
                    offers = obj.get("offers")
                    if isinstance(offers, dict) and offers.get("price") is not None:
                        return str(offers["price"]).strip()
                    if isinstance(offers, list):
                        for off in offers:
                            if isinstance(off, dict) and off.get("price") is not None:
                                return str(off["price"]).strip()
            except (json.JSONDecodeError, TypeError, AttributeError, KeyError):
                continue
    except Exception:
        pass
    return None


def build_product_dict_from_selenium(driver: Any) -> dict[str, Any]:
    """Build a flat product dict from a Selenium WebDriver on a product page."""
    from selenium.webdriver.common.by import By

    specs: dict[str, str] = {}
    try:
        items = driver.find_elements(By.CSS_SELECTOR, ".br-pd-char-item, .br-pr-chr-item")
        for item in items:
            try:
                inner = item.find_element(By.XPATH, "./div")
                for row in inner.find_elements(By.XPATH, "./div"):
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
                continue
    except Exception:
        pass

    product: dict[str, Any] = {}

    product["title"] = _selenium_first_text(driver, ["h1.br-pd-title", "h1.main-title", "h1"])

    product["product_code"] = _selenium_first_text(driver, [
        "span.br-pd-code-n", '[class*="br-pd-code-n"]',
        ".br-pr-code-val", "#product_code .br-pr-code-val",
    ])
    if not product.get("product_code"):
        try:
            labels = driver.find_elements(
                By.XPATH, "//span[contains(., 'Код товару') or contains(., 'Артикул')]"
            )
            for lab in labels:
                try:
                    sib = lab.find_element(By.XPATH, "following-sibling::*[1]")
                    t = sib.text.strip()
                    if t:
                        product["product_code"] = t
                        break
                except Exception:
                    continue
        except Exception:
            pass

    product["regular_price"] = _selenium_meta_content(driver, 'meta[itemprop="price"]')
    if not product.get("regular_price"):
        product["regular_price"] = _selenium_first_text(driver, ["div.br-pr-c-main"])
    if not product.get("regular_price"):
        try:
            el = driver.find_element(By.CSS_SELECTOR, ".br-pp-price")
            parts: list[str] = []
            for sp in el.find_elements(By.CSS_SELECTOR, ":scope > span"):
                try:
                    cls = sp.get_attribute("class") or ""
                    if "hidden" in cls or "data_io" in cls:
                        continue
                    t = sp.text.strip()
                    if t:
                        parts.append(t)
                except Exception:
                    continue
            if parts:
                product["regular_price"] = " ".join(parts)
        except Exception:
            pass
    if not product.get("regular_price"):
        try:
            el = driver.find_element(By.CSS_SELECTOR, ".product-content-wrapper[data-price]")
            dp = el.get_attribute("data-price")
            if dp and dp.strip():
                product["regular_price"] = dp.strip()
        except Exception:
            pass
    if not product.get("regular_price"):
        product["regular_price"] = _selenium_price_from_ld_json(driver)

    product["sale_price"] = _selenium_first_text(driver, [".price-old", ".br-pr-c-old", ".product-price__old"])
    if product.get("sale_price") and len(product["sale_price"]) > 80:
        product["sale_price"] = None

    product["reviews_count"] = None
    try:
        el = driver.find_element(By.CSS_SELECTOR, "a.reviews-count span")
        raw = el.text.strip()
        if raw.isdigit():
            product["reviews_count"] = int(raw)
    except Exception:
        try:
            el = driver.find_element(By.CSS_SELECTOR, ".rating-count, .reviews-count")
            digits = "".join(filter(str.isdigit, el.text.strip()))
            if digits:
                product["reviews_count"] = int(digits)
        except Exception:
            pass

    try:
        imgs = driver.find_elements(By.CSS_SELECTOR, ".br-pic-block img, .product-gallery img")
        urls: list[str] = []
        for img in imgs:
            try:
                src = (img.get_attribute("data-src")
                       or img.get_attribute("data-observe-src")
                       or img.get_attribute("src"))
                if src and src.startswith("http"):
                    urls.append(src)
            except Exception:
                continue
        product["photos"] = urls if urls else None
    except Exception:
        product["photos"] = None

    product["specifications"] = specs if specs else None
    product["color"] = _get_spec(specs, ["колір", "цвет", "color"])
    product["storage"] = _get_spec(specs, ["пам'ять", "память", "storage", "ємність", "вбудована пам"])
    product["manufacturer"] = _get_spec(specs, ["виробник", "производитель", "manufacturer", "бренд"])
    product["screen_diagonal"] = _get_spec(specs, ["діагональ", "диагональ", "diagonal"])
    product["screen_resolution"] = _get_spec(specs, ["роздільна", "разреш", "resolution"])

    return product


def _pw_first_text(page: Any, selectors: list[str]) -> str | None:
    for css in selectors:
        try:
            loc = page.locator(css)
            if loc.count() > 0:
                t = loc.first.inner_text(timeout=5000).strip()
                if t:
                    return t
        except Exception:
            continue
    return None


def _pw_meta_content(page: Any, selector: str) -> str | None:
    try:
        loc = page.locator(selector)
        if loc.count() > 0:
            c = loc.first.get_attribute("content")
            if c and c.strip():
                return c.strip()
    except Exception:
        pass
    return None


def _pw_price_from_ld_json(page: Any) -> str | None:
    try:
        scripts = page.locator('script[type="application/ld+json"]').all()
        for script in scripts:
            try:
                raw = script.inner_text()
                if not raw.strip():
                    continue
                data = json.loads(raw)
                items = data if isinstance(data, list) else [data]
                for obj in items:
                    if not isinstance(obj, dict):
                        continue
                    offers = obj.get("offers")
                    if isinstance(offers, dict) and offers.get("price") is not None:
                        return str(offers["price"]).strip()
                    if isinstance(offers, list):
                        for off in offers:
                            if isinstance(off, dict) and off.get("price") is not None:
                                return str(off["price"]).strip()
            except (json.JSONDecodeError, TypeError, AttributeError, KeyError):
                continue
    except Exception:
        pass
    return None


def build_product_dict_from_playwright(page: Any) -> dict[str, Any]:
    """Build a flat product dict from a Playwright page on a product page."""
    specs: dict[str, str] = {}
    try:
        section = page.locator(".br-pd-char-item, .br-pr-chr-item")
        n = section.count()
        for i in range(n):
            item = section.nth(i)
            try:
                inner = item.locator("> div").first
                inner.wait_for(timeout=5000)
                rc = inner.locator("> div").count()
                for j in range(rc):
                    row = inner.locator("> div").nth(j)
                    try:
                        sc = row.locator("> span").count()
                        if sc >= 2:
                            key = row.locator("> span").nth(0).inner_text(timeout=2000).strip()
                            val = row.locator("> span").nth(1).inner_text(timeout=2000).strip()
                            if key:
                                specs[key] = val
                    except Exception:
                        continue
            except Exception:
                continue
    except Exception:
        pass

    product: dict[str, Any] = {}

    product["title"] = _pw_first_text(page, ["h1.br-pd-title", "h1.main-title", "h1"])

    product["product_code"] = _pw_first_text(page, [
        "span.br-pd-code-n", '[class*="br-pd-code-n"]',
        ".br-pr-code-val", "#product_code .br-pr-code-val",
    ])
    if not product.get("product_code"):
        try:
            loc = page.locator("xpath=//span[contains(., 'Код товару') or contains(., 'Артикул')]")
            if loc.count() > 0:
                sib = loc.first.locator("xpath=following-sibling::*[1]")
                if sib.count() > 0:
                    t = sib.first.inner_text(timeout=3000).strip()
                    if t:
                        product["product_code"] = t
        except Exception:
            pass

    product["regular_price"] = _pw_meta_content(page, 'meta[itemprop="price"]')
    if not product.get("regular_price"):
        product["regular_price"] = _pw_first_text(page, ["div.br-pr-c-main"])
    if not product.get("regular_price"):
        try:
            box = page.locator(".br-pp-price").first
            box.wait_for(timeout=3000)
            parts: list[str] = []
            n2 = box.locator(":scope > span").count()
            for j in range(n2):
                sp = box.locator(":scope > span").nth(j)
                cls = (sp.get_attribute("class") or "").lower()
                if "hidden" in cls or "data_io" in cls:
                    continue
                t = sp.inner_text(timeout=1000).strip()
                if t:
                    parts.append(t)
            if parts:
                product["regular_price"] = " ".join(parts)
        except Exception:
            pass
    if not product.get("regular_price"):
        try:
            wrap = page.locator(".product-content-wrapper[data-price]").first
            wrap.wait_for(timeout=3000)
            dp = wrap.get_attribute("data-price")
            if dp and dp.strip():
                product["regular_price"] = dp.strip()
        except Exception:
            pass
    if not product.get("regular_price"):
        product["regular_price"] = _pw_price_from_ld_json(page)

    product["sale_price"] = _pw_first_text(page, [".price-old", ".br-pr-c-old", ".product-price__old"])
    if product.get("sale_price") and len(product["sale_price"]) > 80:
        product["sale_price"] = None

    product["reviews_count"] = None
    try:
        loc = page.locator("a.reviews-count span")
        if loc.count() > 0:
            raw = loc.first.inner_text(timeout=3000).strip()
            if raw.isdigit():
                product["reviews_count"] = int(raw)
    except Exception:
        try:
            loc = page.locator(".rating-count, .reviews-count")
            if loc.count() > 0:
                digits = "".join(filter(str.isdigit, loc.first.inner_text(timeout=3000).strip()))
                if digits:
                    product["reviews_count"] = int(digits)
        except Exception:
            pass

    try:
        imgs = page.locator(".br-pic-block img, .product-gallery img").all()
        urls: list[str] = []
        for img in imgs:
            try:
                src = (img.get_attribute("data-src")
                       or img.get_attribute("data-observe-src")
                       or img.get_attribute("src"))
                if src and src.startswith("http"):
                    urls.append(src)
            except Exception:
                continue
        product["photos"] = urls if urls else None
    except Exception:
        product["photos"] = None

    product["specifications"] = specs if specs else None
    product["color"] = _get_spec(specs, ["колір", "цвет", "color"])
    product["storage"] = _get_spec(specs, ["пам'ять", "память", "storage", "ємність", "вбудована пам"])
    product["manufacturer"] = _get_spec(specs, ["виробник", "производитель", "manufacturer", "бренд"])
    product["screen_diagonal"] = _get_spec(specs, ["діагональ", "диагональ", "diagonal"])
    product["screen_resolution"] = _get_spec(specs, ["роздільна", "разреш", "resolution"])

    return product


def save_parser_output(product: dict[str, Any], parser_name: str) -> str:
    """Write parser result JSON under modules/outputs; return absolute path."""
    out_dir = Path(__file__).resolve().parent / "outputs"
    out_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = out_dir / f"{parser_name}_{stamp}.json"
    with out_file.open("w", encoding="utf-8") as f:
        json.dump(product, f, ensure_ascii=False, indent=2)
    return str(out_file)