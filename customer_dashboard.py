import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
import subprocess
import sys
import os

# Streamlit App Title
st.markdown("<h1 style='text-align: center;'>Health-E Vend</h1>", unsafe_allow_html=True)
st.divider()  # Optional: Adds a gray divider like before

# ✅ Load Google Credentials from Streamlit Secrets
try:
    creds_info = st.secrets["google"]
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(creds_info, scopes=scope)
    client = gspread.authorize(creds)
except Exception as e:
    st.error(f"🚨 Google authentication failed: {e}")
    st.stop()

# ✅ Connect to Google Sheets
SHEET_ID = st.secrets["google"]["SHEET_ID"]
SHEET_NAME = st.secrets["google"]["SHEET_NAME"]

try:
    sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
except Exception as e:
    st.error(f"🚨 Error accessing Google Sheets: {e}")
    st.stop()

# ✅ Load Data from Google Sheets
try:
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    df["ready_to_fill"] = df["total_items"] <= df["threshold"]
except Exception as e:
    st.error(f"🚨 Error loading data from Google Sheets: {e}")
    st.stop()

# ✅ Machines That Need Refilling (Always Visible)
st.markdown('<h3 style="text-align: center;">⚠️ Machines That Need Refilling</h3>', unsafe_allow_html=True)
low_stock_machines = df[df["ready_to_fill"]]
if not low_stock_machines.empty:
    st.write(low_stock_machines)
    st.warning("⚠️ Some machines are below the refill threshold!")
else:
    st.success("✅ All machines have sufficient stock!")

# ✅ Collapsible Section: Update Stock & Thresholds
with st.expander("🔄 Update Stock & Thresholds"):
    search_refill = st.text_input("Search for a machine:")
    filtered_machines = df[df["location"].str.contains(search_refill, case=False, na=False)]["location"].tolist()

    machine_to_refill = st.selectbox("Select a machine",
                                     options=filtered_machines if filtered_machines else ["No matches found"])

    new_stock = st.number_input("Enter new total stock:", min_value=0, max_value=500, step=1)
    if st.button("Update Stock") and machine_to_refill and machine_to_refill != "No matches found":
        df.loc[df["location"] == machine_to_refill, "total_items"] = new_stock
        df["ready_to_fill"] = df["total_items"] <= df["threshold"]
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())  # ✅ Update Google Sheets
        st.success(f"✅ {machine_to_refill} updated to {new_stock} items!")

    # ✅ Adjust Refill Threshold (Dropdown + Search Box)
    st.subheader("⚙️ Adjust Refill Threshold")

    search_threshold = st.text_input("Search for a machine to edit threshold:")
    filtered_machines_threshold = df[df["location"].str.contains(search_threshold, case=False, na=False)][
        "location"].tolist()

    machine_to_edit = st.selectbox("Select machine to edit threshold",
                                   options=filtered_machines_threshold if filtered_machines_threshold else [
                                       "No matches found"])

    new_threshold = st.number_input("Enter new threshold:", min_value=0, max_value=500, step=1)
    if st.button("Update Threshold") and machine_to_edit and machine_to_edit != "No matches found":
        df.loc[df["location"] == machine_to_edit, "threshold"] = new_threshold
        df["ready_to_fill"] = df["total_items"] <= df["threshold"]
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())  # ✅ Update Google Sheets
        st.success(f"✅ {machine_to_edit} threshold updated to {new_threshold}!")

# ✅ Collapsible Section: Add a New Machine
with st.expander("➕ Add a New Machine"):
    new_machine = st.text_input("Enter new machine location")
    new_total = st.number_input("Initial stock:", min_value=0, max_value=500, step=1)
    new_thresh = st.number_input("Set refill threshold:", min_value=0, max_value=500, step=1)
    if st.button("Add Machine"):
        new_row = pd.DataFrame({"location": [new_machine], "total_items": [new_total], "threshold": [new_thresh]})
        df = pd.concat([df, new_row], ignore_index=True)
        df["ready_to_fill"] = df["total_items"] <= df["threshold"]
        sheet.update([df.columns.values.tolist()] + df.values.tolist())
        st.success(f"✅ {new_machine} added with {new_total} items and a threshold of {new_thresh}!")

# ✅ Collapsible Section: Vending Machine Stock Levels
with st.expander("📋 Vending Machine Stock Levels"):
    st.dataframe(df)

# ✅ Centered Machine Stats
st.markdown("""
    <style>
        .machine-stats {
            text-align: center;
            font-size: 18px;
            font-weight: bold;
            background-color: rgba(255, 255, 255, 0.1);
            padding: 10px;
            border-radius: 10px;
            display: inline-block;
            width: 100%;
        }
        .machine-stats-table {
            margin: auto;
            border-collapse: collapse;
            width: 50%;
        }
        .machine-stats-table th, .machine-stats-table td {
            padding: 10px;
            text-align: center;
            border: 1px solid #ccc;
        }
    </style>
""", unsafe_allow_html=True)

# Calculate stats
total_machines = len(df)
total_items = df["total_items"].sum()
needs_refill = (df["ready_to_fill"]).sum()

st.markdown(f"""
    <div class="machine-stats">
        <h3>Machine Stats</h3>
        <table class="machine-stats-table">
            <tr><th>Locations</th><td>{total_machines}</td></tr>
            <tr><th>Items</th><td>{total_items}</td></tr>
            <tr><th>Needs Refill</th><td>{needs_refill}</td></tr>
        </table>
    </div>
""", unsafe_allow_html=True)

# 🔥 SALES REPORT PROCESSING FUNCTION 🔥

def process_sales_report(csv_path, worksheet):
    try:
        # Load CSV
        df = pd.read_csv(csv_path)

        # ✅ Convert Location column to lowercase to match Google Sheet
        df["Location"] = df["Location"].str.lower()

        # Count transactions, excluding any with 'Two-Tier Pricing'
        def count_valid_transactions(details):
            if pd.isna(details):
                return 0
            return sum(1 for item in details.split(",") if "Two-Tier Pricing" not in item)

        # Calculate total transactions per location
        df["Transaction Count"] = df["Details"].apply(count_valid_transactions)
        transaction_summary = df.groupby("Location")["Transaction Count"].sum().reset_index()

        # Load existing sheet into a DataFrame
        sheet_data = worksheet.get_all_records()
        sheet_df = pd.DataFrame(sheet_data)

        # ✅ Also make sure sheet column is lowercase to ensure match
        sheet_df["location"] = sheet_df["location"].str.lower()

        # Subtract transactions from current total_items
        for _, row in transaction_summary.iterrows():
            location = row["Location"]
            transactions = row["Transaction Count"]
            if location in sheet_df["location"].values:
                sheet_df.loc[sheet_df["location"] == location, "total_items"] -= transactions

        # Write updated data back to the sheet
        worksheet.update([sheet_df.columns.tolist()] + sheet_df.values.tolist())

        return True, "✅ Sales report processed and totals updated!"
    except Exception as e:
        return False, f"🚨 Error processing sales report: {e}"

# ✅ **Button to Process Sales Report**
st.subheader("📂 Process Sales Report")
uploaded_file = st.file_uploader("Upload daily sales report (CSV)", type=["csv"])
if uploaded_file is not None:
    if st.button("📤 Process Sales Report"):
        try:
            process_sales_report(uploaded_file)
            st.success("✅ Sales report processed and Google Sheet updated!")
        except Exception as e:
            st.error(f"🚨 Error processing sales report: {e}")
else:
    st.info("📥 Please upload a CSV sales report to begin processing.")