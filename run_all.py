"""Run parsers in order: requests_bs4, selenium, playwright. Run from project root."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _configure_stdio_utf8() -> None:
    """Force UTF-8 encoding on stdout/stderr (Windows)."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except (OSError, ValueError, AttributeError):
                pass


ROOT = Path(__file__).resolve().parent

SCRIPTS = [
    ROOT / "modules" / "1_parse_requests_bs4.py",
    ROOT / "modules" / "2_parse_selenium.py",
    ROOT / "modules" / "3_parse_playwright.py",
]


def main() -> int:
    _configure_stdio_utf8()
    for script in SCRIPTS:
        if not script.is_file():
            print(f"[!] Missing file: {script}", file=sys.stderr, flush=True)
            return 1
        rel = script.relative_to(ROOT)
        print(f"\n{'=' * 60}\n>>> {rel}\n{'=' * 60}", flush=True)
        r = subprocess.run([sys.executable, str(script)], cwd=str(ROOT))
        if r.returncode != 0:
            print(f"\n[!] Failed: {rel} (exit {r.returncode})", file=sys.stderr, flush=True)
            return r.returncode
    print(f"\n{'=' * 60}\n[*] All parsers finished.\n{'=' * 60}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
