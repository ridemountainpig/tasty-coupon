from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
import json
import time

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
    class_="post-modified-info").text.split("：")[1].split(" ")
coupon_name = soup.find(
    class_="entry-title").text.split("【")[0] + " " + " ".join(coupon_date[0: 4])

coupon_dict = {coupon_name: {}}
coupon_table_title = ["優惠內容", "優惠代碼", "優惠期間", "適用範圍"]
coupon_category = ["FP-subscription", "Promo-Food-FP", "Promo-restaurant-FP", "Promo-Fresh-FP"]

coupon_md = f"""
### {coupon_name}
| 優惠內容 | 優惠代碼 | 優惠期間 | 適用範圍 |
| --- | --- | --- | --- |
"""

for category in coupon_category:
    coupon_title = soup.find(id=category).text
    coupon_table = soup.find(id=category).find_next("tbody").find_all("tr")

    coupon_dict[coupon_name][coupon_title] = []
    temp_dict = {}
    temp_list = []

    for coupon in coupon_table:
        coupon_content = coupon.find_all("td")
        for i in range(len(coupon_content)):
            if "kb56.tw" in coupon_content[i].text:
                continue

            temp_dict[coupon_table_title[i % 4]] = coupon_content[i].text
            temp_list.append("```無```" if coupon_content[i].text == "" else f"```{coupon_content[i].text.replace('丨', '').strip()}```")
            if i != 0 and (i + 1) % 4 == 0:
                coupon_dict[coupon_name][coupon_title].append(temp_dict)
                temp_dict = {}

                temp_list[0] = f"**{coupon_title.replace('丨', '').replace(' ', '')}** : {temp_list[0]}"
                md_content = "|" + "|".join(temp_list) + "|\n"
                coupon_md += md_content
                temp_list = []

json_string = json.dumps(coupon_dict, indent=4, ensure_ascii=False)

with open("coupon-json/foodpanda-coupon.json", "w", encoding="utf-8") as f:
    f.write(json_string)

with open("asset/md/foodpanda-table.md", "w", encoding="utf-8") as f:
    f.write(coupon_md)
