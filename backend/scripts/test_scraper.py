"""Quick test for the improved multi-strategy web scraper."""
import sys, os, io

# Fix Windows console encoding for Vietnamese
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import logging
logging.basicConfig(level=logging.INFO, format="  [%(levelname)s] %(message)s")

from app.services.web_scraper import scrape_url

test_urls = [
    "https://vnexpress.net/",
    "https://isp.vass.gov.vn/tin-vien-han-lam-khxh-viet-nam/sinh-vien-hoc-vien-bao-chi-va-tuyen-truyen-trai-nghiem-thuc-tien-tai-khong-gian-trung-bay-dong-chay-577541",
    "https://tuoitre.vn/",
]

for url in test_urls:
    print(f"\n{'='*60}")
    print(f"URL: {url[:80]}...")
    try:
        r = scrape_url(url, max_chars=500)
        print(f"  Title:   {r['title'][:80]}")
        print(f"  Method:  {r['source_method']}")
        print(f"  Chars:   {r['char_count']}")
        print(f"  Preview: {r['content'][:250]}...")
        print(f"  OK!")
    except Exception as e:
        print(f"  ERROR: {e}")
