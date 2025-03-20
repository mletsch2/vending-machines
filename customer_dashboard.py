import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

# 🔹 Streamlit App Title (Centered)
st.markdown("<h1 style='text-align: center;'>Health-E Vend</h1>", unsafe_allow_html=True)

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
SHEET_NAME = st.secrets["google"]["SHEET_NAME"]

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

# ✅ Machines That Need Refilling (Centered Header)
st.markdown("<h2 style='text-align: center;'>Machines That Need Refilling</h2>", unsafe_allow_html=True)
low_stock_machines = df[df["ready_to_fill"]]
if not low_stock_machines.empty:
    st.write(low_stock_machines)
    st.warning("⚠️ Some machines are below the refill threshold!")
else:
    st.success("✅ All machines have sufficient stock!")

# ✅ Update Stock & Thresholds (Collapsible)
with st.expander("🔄 Update Stock & Thresholds"):
    st.subheader("Refill a Machine")
    machine_to_refill = st.selectbox("Select a machine", df["location"])
    new_stock = st.number_input("Enter new total stock:", min_value=0, max_value=500, step=1)
    if st.button("Update Stock"):
        df.loc[df["location"] == machine_to_refill, "total_items"] = new_stock
        df["ready_to_fill"] = df["total_items"] <= df["threshold"]
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())  # ✅ Update Google Sheets
        st.success(f"✅ {machine_to_refill} updated to {new_stock} items!")

    st.subheader("Adjust Refill Threshold")
    machine_to_edit = st.selectbox("Select machine to edit threshold", df["location"])
    new_threshold = st.number_input("Enter new threshold:", min_value=0, max_value=500, step=1)
    if st.button("Update Threshold"):
        df.loc[df["location"] == machine_to_edit, "threshold"] = new_threshold
        df["ready_to_fill"] = df["total_items"] <= df["threshold"]
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())  # ✅ Update Google Sheets
        st.success(f"✅ {machine_to_edit} threshold updated to {new_threshold}!")

# ✅ Add a New Machine (Collapsible)
with st.expander("➕ Add a New Machine"):
    new_machine = st.text_input("Enter new machine location")
    new_total = st.number_input("Initial stock:", min_value=0, max_value=500, step=1)
    new_thresh = st.number_input("Set refill threshold:", min_value=0, max_value=500, step=1)
    if st.button("Add Machine"):
        new_row = pd.DataFrame({"location": [new_machine], "total_items": [new_total], "threshold": [new_thresh]})
        df = pd.concat([df, new_row], ignore_index=True)
        df["ready_to_fill"] = df["total_items"] <= df["threshold"]
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())  # ✅ Update Google Sheets
        st.success(f"✅ {new_machine} added with {new_total} items and a threshold of {new_thresh}!")

# ✅ Vending Machine Stock Levels (Collapsible)
with st.expander("📋 Vending Machine Stock Levels"):
    st.dataframe(df)

# ✅ Machine Stats (Centered Header)
st.markdown("<h2 style='text-align: center;'>Machine Stats</h2>", unsafe_allow_html=True)
total_locations = df["location"].nunique()
total_items = df["total_items"].sum()
machines_needing_refill = df["ready_to_fill"].sum()

st.write(f"**Total Locations:** {total_locations}")
st.write(f"**Total Items in Stock:** {total_items}")
st.write(f"**Machines That Need Refills:** {machines_needing_refill}")

st.caption("📌 Changes are automatically saved to Google Sheets.")