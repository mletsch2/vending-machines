import pandas as pd
import re

def parse_and_update(sheet):
    df = pd.read_csv("sales_report.csv")

    cleaned_data = []

    for index, row in df.iterrows():
        location = row.get("Location")
        details = str(row.get("Details", ""))

        if location and "Two-Tier Pricing" not in details:
            # Count how many individual items were sold in this row
            item_count = len([item for item in details.split(",") if "Two-Tier Pricing" not in item and item.strip()])
            if item_count > 0:
                cleaned_data.append((location.strip(), item_count))

    # Aggregate item counts by location
    location_sales = {}
    for location, count in cleaned_data:
        location_sales[location] = location_sales.get(location, 0) + count

    # Load the Google Sheet
    sheet_data = sheet.get_all_records()
    df_sheet = pd.DataFrame(sheet_data)

    # Update item counts
    for loc, sold in location_sales.items():
        df_sheet.loc[df_sheet["location"] == loc, "total_items"] -= sold

    # Push back to the sheet
    sheet.update([df_sheet.columns.values.tolist()] + df_sheet.values.tolist())

    return location_sales  # Optional: for display or logging