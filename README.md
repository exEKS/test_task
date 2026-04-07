# braincom_project (test_task)

brain.com.ua parsers (requests, Selenium, Playwright) and a Django app that stores `Product` rows in PostgreSQL.

## Layout

- `braincom_project/` — Django settings and URLs
- `parser_app/` — `Product` model and admin
- `modules/` — standalone scripts (`load_django.py`, parsers, `export_csv.py`)
- `run_all.py` — runs all three parsers in order

## Setup

```bash
pip install -r requirements.txt
playwright install chromium
```

Create database `braincom_db` (or set `POSTGRES_*` env vars). Then:

```bash
python manage.py migrate
python manage.py createsuperuser
```

## Parsers

From project root:

```bash
python run_all.py
```

Or from `modules/`:

```bash
python 1_parse_requests_bs4.py
python 2_parse_selenium.py
python 3_parse_playwright.py
python export_csv.py
```

JSON snapshots go to `modules/outputs/` (gitignored). Admin UI: `/admin/` after `python manage.py runserver`.
