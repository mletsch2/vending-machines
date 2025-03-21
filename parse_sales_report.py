import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# === STEP 1: PARSE RAW SALES REPORT ===
def parse_sales_report(csv_path):
    df = pd.read_csv(csv_path)

    cleaned_data = []

    for _, row in df.iterrows():
        location = row.get("Location")
        details = str(row.get("Details"))

        if "Two-Tier Pricing" in details or location is None:
            continue

        # Count actual items (based on how many item codes like 13($1.00) there are)
        item_count = details.count("(")

        if item_count > 0:
            cleaned_data.append({
                "location": location.strip(),
                "transactions": item_count
            })

    parsed_df = pd.DataFrame(cleaned_data)
    return parsed_df.groupby("location", as_index=False).sum()


# === STEP 2: UPDATE GOOGLE SHEET ===
def update_machine_stock(parsed_df):
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(st.secrets["google"], scopes=scope)
    client = gspread.authorize(creds)

    SHEET_ID = st.secrets["google"]["SHEET_ID"]
    SHEET_NAME = st.secrets["google"]["SHEET_NAME"]

    sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    for _, row in parsed_df.iterrows():
        location = row["location"]
        transactions = row["transactions"]

        if location in df["location"].values:
            current_stock = df.loc[df["location"] == location, "total_items"].values[0]
            updated_stock = max(0, current_stock - transactions)  # Ensure stock doesn’t go negative
            df.loc[df["location"] == location, "total_items"] = updated_stock

    # Update "ready_to_fill" status
    df["ready_to_fill"] = df["total_items"] <= df["threshold"]

    # Push updated data to Google Sheets
    sheet.update([df.columns.values.tolist()] + df.values.tolist())
    print("✅ Google Sheet successfully updated!")


if __name__ == "__main__":
    csv_path = "sales_report.csv"  # Name of the raw daily sales report
    parsed_df = parse_sales_report(csv_path)
    print(parsed_df)  # Optional: preview parsed data
    update_machine_stock(parsed_df)