import re
import json
from pathlib import Path
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

url = "https://kb56.tw/foodpanda-coupon/"

chrome_options = Options()
chrome_options.add_argument('--headless=new')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

driver = None
try:
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(30)
    driver.get(url)
    WebDriverWait(driver, 30).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    html_content = driver.page_source
finally:
    if driver:
        driver.quit()

def sanitize_text(text: str) -> str:
    """ Clean and normalize whitespace in parsed text """
    if not text:
        return ""
    return re.sub(r'[\r\n\t]+', ' ', text).strip()

def escape_md(text: str) -> str:
    """ Escape pipe characters specifically for markdown table formatting """
    return text.replace('|', '&#124;')

soup = BeautifulSoup(html_content, "html.parser")

date_box = soup.find(class_="kb56-date-box")
entry_title = soup.find(class_="entry-title")

# Abort before touching existing files if the page layout changed
if not date_box or not entry_title or "：" not in date_box.text:
    raise RuntimeError("Coupon page is missing metadata")

coupon_date = date_box.text.split("：")[1].split(" ")
title_prefix = entry_title.text.split("【")[0]
coupon_name = f"{title_prefix} {' '.join(coupon_date[0:4])}".strip()

coupon_dict = {coupon_name: {}}
coupon_md = f"\n### {escape_md(coupon_name)}\n"

for table in soup.find_all("table"):
    tbody = table.find("tbody")
    if not tbody:
        continue

    heading = table.find_previous(["h2", "h3", "h4"])
    category_title = sanitize_text(heading.text) if heading else "其他"

    thead = table.find("thead")
    headers = [sanitize_text(th.text) for th in thead.find_all(["th", "td"])] if thead else []

    category_data = []
    for row in tbody.find_all("tr"):
        cells = row.find_all("td")
        if not cells:
            continue
        if any("kb56.tw" in cell.text for cell in cells):
            continue

        cell_texts = [
            sanitize_text(cell.text.replace("(點擊複製)", "").replace("(點擊前往)", ""))
            for cell in cells
        ]
        if headers and len(headers) == len(cell_texts):
            row_dict = dict(zip(headers, cell_texts))
        else:
            row_dict = {f"col_{i}": v for i, v in enumerate(cell_texts)}
        category_data.append(row_dict)

    if not category_data:
        continue

    coupon_dict[coupon_name][category_title] = category_data

    col_keys = [escape_md(k) for k in (headers if headers else list(category_data[0].keys()))]
    coupon_md += f"\n#### {escape_md(category_title)}\n"
    coupon_md += "| " + " | ".join(col_keys) + " |\n"
    coupon_md += "| " + " | ".join(["---"] * len(col_keys)) + " |\n"
    for row_dict in category_data:
        cells = [escape_md(v) if v else "無" for v in row_dict.values()]
        coupon_md += "| " + " | ".join(cells) + " |\n"

# Abort before overwriting existing files if no coupon rows were parsed
if not coupon_dict[coupon_name]:
    raise RuntimeError("Coupon page has no coupon data")

Path("coupon-json").mkdir(parents=True, exist_ok=True)
Path("asset/md").mkdir(parents=True, exist_ok=True)

json_string = json.dumps(coupon_dict, indent=4, ensure_ascii=False)

with open("coupon-json/foodpanda-coupon.json", "w", encoding="utf-8") as f:
    f.write(json_string)

with open("asset/md/foodpanda-table.md", "w", encoding="utf-8") as f:
    f.write(coupon_md)
