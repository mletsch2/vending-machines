import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

# 🎨 Dark Mode Styling
st.markdown(
    """
    <style>
        body {background-color: #1e1e1e; color: #ffffff;}
        .main {background-color: #2a2a2a; padding: 20px; border-radius: 10px;}
        .stDataFrame {border-radius: 10px; background-color: #333333; color: #ffffff;}
        div[data-testid="stMetric"] > label { font-size: 18px; font-weight: bold; color: #dddddd; }
        .stExpander {border: 1px solid #444444; border-radius: 10px; background-color: #252525; color: #ffffff;}
        .warning {background-color: #ff4c4c; padding: 10px; border-radius: 8px; color: white; font-weight: bold;}
    </style>
    """,
    unsafe_allow_html=True,
)

# 🔹 Streamlit App Title
st.title("🥤 Vending Machine Dashboard")

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
    sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
except Exception as e:
    st.error(f"🚨 Error accessing Google Sheets: {e}")
    st.stop()

# ✅ Step 3: Load Data
try:
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    df["ready_to_fill"] = df["total_items"] <= df["threshold"]

    # ⚠️ **Machines That Need Refilling** - MOVED TO TOP
    st.subheader("⚠️ Machines That Need Refilling")
    low_stock_machines = df[df["ready_to_fill"]]
    if not low_stock_machines.empty:
        st.markdown('<div class="warning">⚠️ Some machines need refilling!</div>', unsafe_allow_html=True)
        st.write(low_stock_machines.style.set_properties(**{"background-color": "#ff4c4c", "color": "white"}))
    else:
        st.success("✅ All machines have sufficient stock!")

    # 📊 Display Key Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("📍 Locations", len(df))
    col2.metric("🛒 Total Items", df["total_items"].sum())
    col3.metric("⚠️ Needs Refill", df["ready_to_fill"].sum())

    # 📋 Styled Data Table - General Stock Levels
    st.subheader("📋 Vending Machine Stock Levels")
    st.dataframe(df.style.applymap(lambda x: "background-color: #ff4c4c" if x else "", subset=["ready_to_fill"]))

except Exception as e:
    st.error(f"🚨 Error loading data from Google Sheets: {e}")
    st.stop()

# 🔄 **Refill Section in Expander**
with st.expander("🔄 Update Stock & Thresholds", expanded=False):
    col1, col2 = st.columns(2)

    # Refill a Machine
    with col1:
        st.subheader("🔄 Refill a Machine")
        machine_to_refill = st.selectbox("Select a machine", df["location"])
        new_stock = st.number_input("Enter new total stock:", min_value=0, max_value=500, step=1)
        if st.button("Update Stock"):
            df.loc[df["location"] == machine_to_refill, "total_items"] = new_stock
            df["ready_to_fill"] = df["total_items"] <= df["threshold"]
            sheet.update([df.columns.values.tolist()] + df.values.tolist())  # ✅ Update Google Sheets
            st.success(f"✅ {machine_to_refill} updated to {new_stock} items!")

    # Adjust Refill Threshold
    with col2:
        st.subheader("⚙️ Adjust Refill Threshold")
        machine_to_edit = st.selectbox("Select machine to edit threshold", df["location"], key="edit_thresh")
        new_threshold = st.number_input("Enter new threshold:", min_value=0, max_value=500, step=1)
        if st.button("Update Threshold"):
            df.loc[df["location"] == machine_to_edit, "threshold"] = new_threshold
            df["ready_to_fill"] = df["total_items"] <= df["threshold"]
            sheet.update([df.columns.values.tolist()] + df.values.tolist())  # ✅ Update Google Sheets
            st.success(f"✅ {machine_to_edit} threshold updated to {new_threshold}!")

# ➕ **Add Machine Section**
with st.expander("➕ Add a New Machine", expanded=False):
    st.subheader("➕ Add a New Machine")
    new_machine = st.text_input("Enter new machine location")
    new_total = st.number_input("Initial stock:", min_value=0, max_value=500, step=1)
    new_thresh = st.number_input("Set refill threshold:", min_value=0, max_value=500, step=1)
    if st.button("Add Machine"):
        new_row = pd.DataFrame({"location": [new_machine], "total_items": [new_total], "threshold": [new_thresh]})
        df = pd.concat([df, new_row], ignore_index=True)
        df["ready_to_fill"] = df["total_items"] <= df["threshold"]
        sheet.update([df.columns.values.tolist()] + df.values.tolist())  # ✅ Update Google Sheets
        st.success(f"✅ {new_machine} added with {new_total} items and a threshold of {new_thresh}!")

st.caption("📌 Changes are automatically saved to Google Sheets.")