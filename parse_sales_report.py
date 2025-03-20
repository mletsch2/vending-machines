import re
import pandas as pd
from bs4 import BeautifulSoup

# 🔹 Load the HTML file
with open("sales_report.html", "r", encoding="utf-8") as file:
    html_content = file.read()

# 🔹 Parse the HTML
soup = BeautifulSoup(html_content, "html.parser")

# 🔹 Extract all devices
device_data = []
devices = soup.find_all(string=re.compile(r"Device: VJ\d+"))  # Matches "Device: VJ..."
for device in devices:
    device_id = device.split(":")[-1].strip()
    location_tag = device.find_next(text=re.compile(r"Location:"))  # Find location name
    location = location_tag.split(":")[-1].strip() if location_tag else "Unknown"

    # 🔹 Count transactions (Each line like `42($1.00)` = **1 transaction**)
    transaction_count = 0
    details_section = device.find_all_next(text=re.compile(r"\d+\(\$\d+\.\d{2}\)"))  # Matches `42($1.00)`

    for detail in details_section:
        if "Two-Tier Pricing" not in detail:  # ✅ Exclude Two-Tier Pricing
            transaction_count += 1  # ✅ Each valid entry = **1 transaction**

    device_data.append({"Device": device_id, "Location": location, "Total Transactions": transaction_count})

# 🔹 Convert to DataFrame
df = pd.DataFrame(device_data)

# ✅ Display & Save Final Data
print(df)
df.to_csv("cleaned_sales_report.csv", index=False)