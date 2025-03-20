import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

# ✅ Set Streamlit Page Config for Centered Layout
st.set_page_config(page_title="Vending Machine Dashboard", layout="centered")

# ✅ Custom Styling for **FULL TRANSPARENCY**
st.markdown("""
    <style>
        body {
            background: none !important;  /* 🚀 Fully Transparent */
            color: white !important;  /* Ensure Text is Visible */
        }
        .block-container {
            background: none !important;  /* Remove Boxed Background */
            padding: 3rem;
            max-width: 800px;
            margin: auto;
        }
        .stDataFrame, .stTable {
            border: 1px solid #444;  /* Light gray border */
            border-radius: 5px;
            padding: 5px;
        }
        .stButton button {
            background-color: #222 !important;
            color: white !important;
            border-radius: 5px;
        }
    </style>
""", unsafe_allow_html=True)

# ✅ Step 1: Load Google Credentials (Hidden from UI)
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
SHEET_NAME = "Vending Data"

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

# ✅ Step 4: Machines That Need Refilling (TOP SECTION)
st.subheader("⚠️ Machines That Need Refilling")
low_stock_machines = df[df["ready_to_fill"]]
if not low_stock_machines.empty:
    st.write(low_stock_machines)
    st.warning("⚠️ Some machines are below the refill threshold!")
else:
    st.success("✅ All machines have sufficient stock!")

# ✅ Step 5: Collapsible Section for Refill & Thresholds
with st.expander("🔄 Update Stock & Thresholds", expanded=True):
    # ✅ **Refill a Machine**
    st.subheader("🛠️ Refill a Machine")
    machine_to_refill = st.selectbox("Select a machine", df["location"], help="Type to filter", index=None)
    new_stock = st.number_input("Enter new total stock:", min_value=0, max_value=500, step=1)
    if st.button("Update Stock"):
        df.loc[df["location"] == machine_to_refill, "total_items"] = new_stock
        df["ready_to_fill"] = df["total_items"] <= df["threshold"]
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())  # ✅ Update Google Sheets
        st.success(f"✅ {machine_to_refill} updated to {new_stock} items!")

    # ✅ **Change Refill Threshold**
    st.subheader("⚙️ Adjust Refill Threshold")
    machine_to_edit = st.selectbox("Select machine to edit threshold", df["location"], help="Type to filter", index=None)
    new_threshold = st.number_input("Enter new threshold:", min_value=0, max_value=500, step=1)
    if st.button("Update Threshold"):
        df.loc[df["location"] == machine_to_edit, "threshold"] = new_threshold
        df["ready_to_fill"] = df["total_items"] <= df["threshold"]
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())  # ✅ Update Google Sheets
        st.success(f"✅ {machine_to_edit} threshold updated to {new_threshold}!")

# ✅ Step 6: Add a New Machine
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

# ✅ Step 7: Vending Machine Stock Levels
st.subheader("📋 Vending Machine Stock Levels")
st.dataframe(df)

# ✅ Step 8: Summary Information
st.subheader("📊 Vending Machine Summary")
st.write(f"**Total Locations:** {df.shape[0]}")
st.write(f"**Total Items in Stock:** {df['total_items'].sum()}")
st.write(f"**Machines Needing Refill:** {len(low_stock_machines)}")

st.caption("📌 Changes are automatically saved to Google Sheets.")