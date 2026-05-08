from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
import json

url = "https://kb56.tw/foodpanda-coupon/"

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36')

driver = webdriver.Chrome(options=chrome_options)

try:
    driver.get(url)
    WebDriverWait(driver, 30).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    html_content = driver.page_source
finally:
    driver.quit()

soup = BeautifulSoup(html_content, "html.parser")

coupon_date = soup.find(
    class_="kb56-date-box").text.split("：")[1].split(" ")
coupon_name = soup.find(
    class_="entry-title").text.split("【")[0] + " " + " ".join(coupon_date[0:4])

coupon_dict = {coupon_name: {}}
coupon_md = f"\n### {coupon_name}\n"

for table in soup.find_all("table"):
    tbody = table.find("tbody")
    if not tbody:
        continue

    heading = table.find_previous(["h2", "h3", "h4"])
    category_title = heading.text.strip() if heading else "其他"

    thead = table.find("thead")
    headers = [th.text.strip() for th in thead.find_all(["th", "td"])] if thead else []

    category_data = []
    for row in tbody.find_all("tr"):
        cells = row.find_all("td")
        if not cells:
            continue
        if any("kb56.tw" in cell.text for cell in cells):
            continue

        cell_texts = [cell.text.strip().replace("(點擊複製)", "").replace("(點擊前往)", "").strip() for cell in cells]
        if headers and len(headers) == len(cell_texts):
            row_dict = dict(zip(headers, cell_texts))
        else:
            row_dict = {f"col_{i}": v for i, v in enumerate(cell_texts)}
        category_data.append(row_dict)

    if not category_data:
        continue

    coupon_dict[coupon_name][category_title] = category_data

    col_keys = headers if headers else list(category_data[0].keys())
    coupon_md += f"\n#### {category_title}\n"
    coupon_md += "| " + " | ".join(col_keys) + " |\n"
    coupon_md += "| " + " | ".join(["---"] * len(col_keys)) + " |\n"
    for row_dict in category_data:
        cells = [v or "無" for v in row_dict.values()]
        coupon_md += "| " + " | ".join(cells) + " |\n"

json_string = json.dumps(coupon_dict, indent=4, ensure_ascii=False)

with open("coupon-json/foodpanda-coupon.json", "w", encoding="utf-8") as f:
    f.write(json_string)

with open("asset/md/foodpanda-table.md", "w", encoding="utf-8") as f:
    f.write(coupon_md)
