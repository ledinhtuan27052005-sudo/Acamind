from app.services.web_scraper import scrape_url
import sys

print('Scraping 1...')
try:
    res1 = scrape_url('https://isp.vass.gov.vn/tin-vien-han-lam-khxh-viet-nam/sinh-vien-hoc-vien-bao-chi-va-tuyen-truyen-trai-nghiem-thuc-tien-tai-khong-gian-trung-bay-dong-chay-577541', 500)
    print("SUCCESS 1:", res1['title'])
    print(res1['content'][:200])
except Exception as e:
    print("FAILED 1:", e)

print('Scraping 2...')
try:
    res2 = scrape_url('https://isp.vass.gov.vn/tin-vien-han-lam-khxh-viet-nam/ra-mat-mo-hinh-bua-an-trua-noi-bo-tai-nha-da-nang-bua-trua-vui-ve-ket-noi-dong-nghiep-577537', 500)
    print("SUCCESS 2:", res2['title'])
    print(res2['content'][:200])
except Exception as e:
    print("FAILED 2:", e)
