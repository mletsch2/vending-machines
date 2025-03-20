import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

# 🔹 Streamlit App Title
st.title("Health-E Vend")

# ✅ Step 1: Load Google Credentials from Streamlit Secrets
try:
    creds_info = st.secrets["google"]
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(creds_info, scopes=scope)
    client = gspread.authorize(creds)
except Exception as e:
    st.error(f"🚨 Google authentication failed: {e}")
    st.stop()

# ✅ Step 2: Connect to Google Sheets
SHEET_ID = st.secrets["google"]["SHEET_ID"]
SHEET_NAME = "Vending Data"

try:
    sheet = client.open_by_key(SHEET_ID)
    worksheet = sheet.worksheet(SHEET_NAME)
except Exception as e:
    st.error(f"🚨 Error accessing Google Sheets: {e}")
    st.stop()

# ✅ Step 3: Load Data from Google Sheets
try:
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    df["ready_to_fill"] = df["total_items"] <= df["threshold"]
except Exception as e:
    st.error(f"🚨 Error loading data from Google Sheets: {e}")
    st.stop()

# ✅ Machines That Need Refilling (Uncollapsed)
st.subheader("⚠️ Machines That Need Refilling")
low_stock_machines = df[df["ready_to_fill"]]
if not low_stock_machines.empty:
    st.write(low_stock_machines)
    st.warning("⚠️ Some machines are below the refill threshold!")
else:
    st.success("✅ All machines have sufficient stock!")

# ✅ Update Stock & Thresholds (Collapsed)
with st.expander("🔄 Update Stock & Thresholds"):
    st.subheader("Refill a Machine")
    machine_to_refill = st.selectbox("Select a machine", df["location"])
    new_stock = st.number_input("Enter new total stock:", min_value=0, max_value=500, step=1)
    if st.button("Update Stock"):
        df.loc[df["location"] == machine_to_refill, "total_items"] = new_stock
        df["ready_to_fill"] = df["total_items"] <= df["threshold"]
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())
        st.success(f"✅ {machine_to_refill} updated to {new_stock} items!")

    st.subheader("⚙️ Adjust Refill Threshold")
    machine_to_edit = st.selectbox("Select machine to edit threshold", df["location"])
    new_threshold = st.number_input("Enter new threshold:", min_value=0, max_value=500, step=1)
    if st.button("Update Threshold"):
        df.loc[df["location"] == machine_to_edit, "threshold"] = new_threshold
        df["ready_to_fill"] = df["total_items"] <= df["threshold"]
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())
        st.success(f"✅ {machine_to_edit} threshold updated to {new_threshold}!")

# ✅ Add a New Machine (Collapsed)
with st.expander("➕ Add a New Machine"):
    new_machine = st.text_input("Enter new machine location")
    new_total = st.number_input("Initial stock:", min_value=0, max_value=500, step=1)
    new_thresh = st.number_input("Set refill threshold:", min_value=0, max_value=500, step=1)
    if st.button("Add Machine"):
        new_row = pd.DataFrame({"location": [new_machine], "total_items": [new_total], "threshold": [new_thresh]})
        df = pd.concat([df, new_row], ignore_index=True)
        df["ready_to_fill"] = df["total_items"] <= df["threshold"]
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())
        st.success(f"✅ {new_machine} added with {new_total} items and a threshold of {new_thresh}!")

# ✅ Vending Machine Stock Levels (Collapsed)
with st.expander("📋 Vending Machine Stock Levels"):
    st.dataframe(df)

# ✅ Machine Stats (Uncollapsed)
st.subheader("📊 Machine Stats")
total_machines = len(df)
total_items = df["total_items"].sum()
total_refill_needed = len(low_stock_machines)
st.write(f"**Total Machines:** {total_machines}")
st.write(f"**Total Items in Stock:** {total_items}")
st.write(f"**Machines Needing Refill:** {total_refill_needed}")

st.caption("📌 Changes are automatically saved to Google Sheets.")