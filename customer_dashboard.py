import streamlit as st
import gspread
import pandas as pd
import matplotlib.pyplot as plt
from google.oauth2.service_account import Credentials

# 🔹 Streamlit App Title
st.title("📊 Vending Machine Dashboard")

# ✅ Step 1: Load Google Credentials from Streamlit Secrets
try:
    creds_info = st.secrets["google"]
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(creds_info, scopes=scope)
    client = gspread.authorize(creds)
    st.write("✅ Google authentication successful!")
except Exception as e:
    st.error(f"🚨 Google authentication failed: {e}")
    st.stop()

# ✅ Step 2: Connect to Google Sheets
SHEET_ID = st.secrets["google"]["SHEET_ID"]
SHEET_NAME = "Vending Data"  # 🔹 Update this to match your actual sheet tab name

try:
    sheet = client.open_by_key(SHEET_ID)
    worksheet = sheet.worksheet(SHEET_NAME)
    st.write(f"✅ Connected to Google Sheet: {SHEET_NAME}")
except Exception as e:
    st.error(f"🚨 Error accessing Google Sheets: {e}")
    st.stop()

# ✅ Step 3: Display Machines That Need Refilling
st.subheader("⚠️ Machines That Need Refilling")
low_stock_machines = df[df["ready_to_fill"]]
if not low_stock_machines.empty:
    st.write(low_stock_machines)
    st.warning("⚠️ Some machines are below the refill threshold!")
else:
    st.success("✅ All machines have sufficient stock!")

# ✅ Step 4: Load Data from Google Sheets
try:
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    df["ready_to_fill"] = df["total_items"] <= df["threshold"]
    st.subheader("📋 Vending Machine Stock Levels")
    st.dataframe(df)
except Exception as e:
    st.error(f"🚨 Error loading data from Google Sheets: {e}")
    st.stop()

# ✅ Step 5: Refill a Machine
st.subheader("🔄 Refill a Machine")
machine_to_refill = st.selectbox("Select a machine", df["location"])
new_stock = st.number_input("Enter new total stock:", min_value=0, max_value=500, step=1)
if st.button("Update Stock"):
    df.loc[df["location"] == machine_to_refill, "total_items"] = new_stock
    df["ready_to_fill"] = df["total_items"] <= df["threshold"]
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())  # ✅ Update Google Sheets
    st.success(f"✅ {machine_to_refill} updated to {new_stock} items!")

# ✅ Step 6: Adjust Refill Threshold
st.subheader("⚙️ Adjust Refill Threshold")
machine_to_edit = st.selectbox("Select machine to edit threshold", df["location"])
new_threshold = st.number_input("Enter new threshold:", min_value=0, max_value=500, step=1)
if st.button("Update Threshold"):
    df.loc[df["location"] == machine_to_edit, "threshold"] = new_threshold
    df["ready_to_fill"] = df["total_items"] <= df["threshold"]
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())  # ✅ Update Google Sheets
    st.success(f"✅ {machine_to_edit} threshold updated to {new_threshold}!")

# ✅ Step 7: Add New Machine
st.subheader("➕ Add a New Machine")
new_machine = st.text_input("Enter new machine location")
new_total = st.number_input("Initial stock:", min_value=0, max_value=500, step=1)
new_thresh = st.number_input("Set refill threshold:", min_value=0, max_value=500, step=1)
if st.button("Add Machine"):
    new_row = pd.DataFrame({"location": [new_machine], "total_items": [new_total], "threshold": [new_thresh]})
    df = pd.concat([df, new_row], ignore_index=True)
    df["ready_to_fill"] = df["total_items"] <= df["threshold"]
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())  # ✅ Update Google Sheets
    st.success(f"✅ {new_machine} added with {new_total} items and a threshold of {new_thresh}!")

# ✅ Step 8: Plot Inventory Levels
st.subheader("📊 Inventory Levels Chart")
fig, ax = plt.subplots()
ax.bar(df["location"], df["total_items"], color="blue", label="Total Items")
ax.axhline(y=df["threshold"].mean(), color="red", linestyle="--", label="Average Threshold")
ax.set_xlabel("Location")
ax.set_ylabel("Total Items")
ax.set_title("Inventory Levels by Location")
ax.legend()
st.pyplot(fig)

st.caption("📌 Changes are automatically saved to Google Sheets.")