import streamlit as st
import gspread
import pandas as pd
import matplotlib.pyplot as plt
from google.oauth2.service_account import Credentials

# 🎨 Custom Styling
st.markdown(
    """
    <style>
        .main {background-color: #f8f9fa;}
        div[data-testid="stMetric"] > label { font-size: 18px; font-weight: bold; }
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
    st.success("✅ Google authentication successful!")
except Exception as e:
    st.error(f"🚨 Google authentication failed: {e}")
    st.stop()

# ✅ Step 2: Connect to Google Sheets
SHEET_ID = st.secrets["google"]["SHEET_ID"]
SHEET_NAME = "Vending Data"

try:
    sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
    st.success(f"✅ Connected to Google Sheet: {SHEET_NAME}")
except Exception as e:
    st.error(f"🚨 Error accessing Google Sheets: {e}")
    st.stop()

# ✅ Step 3: Load Data
try:
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    df["ready_to_fill"] = df["total_items"] <= df["threshold"]

    # 📊 Display Key Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("📍 Locations", len(df))
    col2.metric("🛒 Total Items", df["total_items"].sum())
    col3.metric("⚠️ Needs Refill", df["ready_to_fill"].sum())

    # 📋 Styled Data Table
    st.subheader("📋 Vending Machine Stock Levels")
    st.dataframe(df.style.applymap(lambda x: "background-color: #ffcccc" if x else "", subset=["ready_to_fill"]))
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

# ⚠️ **Machines That Need Refilling**
st.subheader("⚠️ Machines That Need Refilling")
low_stock_machines = df[df["ready_to_fill"]]
if not low_stock_machines.empty:
    st.write(low_stock_machines)
    st.warning("⚠️ Some machines need refilling!")
else:
    st.success("✅ All machines have sufficient stock!")

# 📊 **Inventory Chart**
st.subheader("📊 Inventory Levels Chart")
fig, ax = plt.subplots()
ax.bar(df["location"], df["total_items"], color="#4285F4", label="Total Items")
ax.axhline(y=df["threshold"].mean(), color="red", linestyle="--", label="Avg Threshold")
ax.set_xlabel("Location")
ax.set_ylabel("Total Items")
ax.set_title("Inventory Levels by Location")
ax.legend()
st.pyplot(fig)

st.caption("📌 Changes are automatically saved to Google Sheets.")