import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import os

# ✅ Load Streamlit secrets (Google creds + Sheet info)
creds_info = st.secrets["google"]
scope = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(creds_info, scopes=scope)
client = gspread.authorize(creds)

# ✅ Connect to Google Sheet
SHEET_ID = st.secrets["google"]["SHEET_ID"]
SHEET_NAME = st.secrets["google"]["SHEET_NAME"]
sheet = client.open_by_key(SHEET_ID)
worksheet = sheet.worksheet(SHEET_NAME)

# ✅ Load the uploaded sales report CSV
csv_path = "sales_report.csv"  # Must be uploaded via Streamlit file uploader

try:
    df = pd.read_csv(csv_path)

    # ✅ Remove any rows where "Details" column contains 'Two-Tier Pricing'
    df = df[~df['Details'].str.contains("Two-Tier Pricing", na=False)]

    # ✅ Count transactions per Location
    transaction_counts = df.groupby("Location").size().reset_index(name="transactions")

    # ✅ Load current sheet data
    sheet_df = pd.DataFrame(worksheet.get_all_records())

    # ✅ Merge transaction counts into sheet_df
    for _, row in transaction_counts.iterrows():
        location = row["Location"]
        transactions = row["transactions"]
        sheet_df.loc[sheet_df["location"] == location, "total_items"] -= transactions

    # ✅ Update Google Sheet
    worksheet.update([sheet_df.columns.values.tolist()] + sheet_df.values.tolist())
    print("✅ Google Sheet successfully updated!")

except Exception as e:
    print(f"🚨 Error processing sales report: {e}")