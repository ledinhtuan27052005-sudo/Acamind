import requests
import re

r = requests.get('http://localhost:3001/chat')
urls = re.findall(r'(/_next/static/[^"\'\s>]+)', r.text)
print(f"Total static assets found in HTML: {len(urls)}")

bad = []
for u in set(urls):
    full_url = 'http://localhost:3001' + u
    try:
        res = requests.get(full_url)
        if res.status_code != 200:
            bad.append((u, res.status_code))
    except Exception as e:
        bad.append((u, str(e)))

if not bad:
    print("ALL STATIC ASSETS (CSS + JS + WEBPACK) LOAD WITH 200 OK! PERFECT!")
else:
    print(f"Failed assets ({len(bad)}):", bad)
