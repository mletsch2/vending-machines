import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

# 🔹 Streamlit App Title
st.set_page_config(page_title="Vending Machine Dashboard", layout="wide")

# ✅ Apply Custom Styling for White Background & Light Gray Outlines
st.markdown("""
    <style>
        body {
            background-color: white;
        }
        .block-container {
            padding: 2rem;
            background-color: white;
            border: 1px solid lightgray;
            border-radius: 8px;
        }
        .stDataFrame {
            border: 1px solid lightgray;
            border-radius: 5px;
            padding: 5px;
        }
        .stButton button {
            background-color: #f0f0f0;
            color: black;
            border-radius: 5px;
        }
    </style>
""", unsafe_allow_html=True)

# ✅ Step 1: Load Google Credentials from Streamlit Secrets
try:
    creds_info = st.secrets["google"]
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(creds_info, scopes=scope)
    client = gspread.authorize(creds)
except Exception:
    st.error("🚨 Google authentication failed!")
    st.stop()

# ✅ Step 2: Connect to Google Sheets
SHEET_ID = st.secrets["google"]["SHEET_ID"]
SHEET_NAME = "Vending Data"  # Update if your sheet has a different name

try:
    sheet = client.open_by_key(SHEET_ID)
    worksheet = sheet.worksheet(SHEET_NAME)
except Exception:
    st.error("🚨 Error accessing Google Sheets!")
    st.stop()

# ✅ Step 3: Load Data from Google Sheets
try:
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    df["ready_to_fill"] = df["total_items"] <= df["threshold"]
except Exception:
    st.error("🚨 Error loading data from Google Sheets!")
    st.stop()

# ✅ Step 4: Display Machines That Need Refilling (Moved to Top)
st.subheader("⚠️ Machines That Need Refilling")
low_stock_machines = df[df["ready_to_fill"]]
if not low_stock_machines.empty:
    st.write(low_stock_machines)
    st.warning("⚠️ Some machines are below the refill threshold!")
else:
    st.success("✅ All machines have sufficient stock!")

# ✅ Step 5: Refill a Machine (Moved Below "Machines That Need Refilling")
st.subheader("🔄 Refill a Machine")
machine_to_refill = st.selectbox("Select a machine", df["location"])
new_stock = st.number_input("Enter new total stock:", min_value=0, max_value=500, step=1)
if st.button("Update Stock"):
    df.loc[df["location"] == machine_to_refill, "total_items"] = new_stock
    df["ready_to_fill"] = df["total_items"] <= df["threshold"]
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())  # ✅ Update Google Sheets
    st.success(f"✅ {machine_to_refill} updated to {new_stock} items!")

# ✅ Step 6: Add a New Machine (Moved Below "Refill a Machine")
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

# ✅ Step 7: Display All Vending Machine Stock (Moved Below "Add a New Machine")
st.subheader("📋 Vending Machine Stock Levels")
st.dataframe(df)

# ✅ Step 8: Summary Information (Moved Below Everything)
st.subheader("📊 Vending Machine Summary")
st.write(f"**Total Locations:** {df.shape[0]}")
st.write(f"**Total Items in Stock:** {df['total_items'].sum()}")
st.write(f"**Machines Needing Refill:** {len(low_stock_machines)}")

st.caption("📌 Changes are automatically saved to Google Sheets.")