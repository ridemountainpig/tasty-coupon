readme = """
![](./asset/image/tasty-coupon.png)

# Tasty Coupon

"""

with open("asset/md/ubereats-table.md", "r", encoding="utf-8") as f:
    readme += f.read()

with open("asset/md/foodpanda-table.md", "r", encoding="utf-8") as f:
    readme += f.read()

with open("README.md", "w", encoding="utf-8") as f:
    f.write(readme)
