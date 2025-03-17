import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import matplotlib.pyplot as plt  # ✅ Matplotlib for charting

# ✅ Load Google Sheets
SHEET_ID = "1c-WgLrMW-teYTtW1OGiVqf9q-eGuUvfkSYDCuF9S2ok"
SHEET_NAME = "Sheet1"

# ✅ Google Authentication
CREDS_FILE = "config/service_account.json"  #
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file(CREDS_FILE, scopes=scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

# ✅ Function to Load Data from Google Sheets
def load_data():
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    df["ready_to_fill"] = df["total_items"] <= df["threshold"]
    return df

# ✅ Function to Update Google Sheets
def update_google_sheets(dataframe):
    sheet.clear()  # 🔹 Clears old data
    sheet.update([dataframe.columns.values.tolist()] + dataframe.values.tolist())

# Load data
df = load_data()

# ✅ Streamlit Dashboard UI
st.title("Vending Machine Manager 🥤")

# ✅ Show Machines That Need Refilling (At the Top)
st.subheader("⚠️ Machines That Need Refilling")
low_stock_machines = df[df["ready_to_fill"]]
if not low_stock_machines.empty:
    st.write(low_stock_machines)
    st.warning("⚠️ Some machines are below the refill threshold!")
else:
    st.success("✅ All machines have sufficient stock!")

# ✅ Display Machine Stock
st.subheader("📊 Current Stock Levels")
st.dataframe(df)

# ✅ Refill a Machine
st.subheader("🔄 Refill a Machine")
machine_to_refill = st.selectbox("Select a machine", df["location"])
new_stock = st.number_input("Enter new total stock:", min_value=0, max_value=500, step=1)
if st.button("Update Stock"):
    df.loc[df["location"] == machine_to_refill, "total_items"] = new_stock
    update_google_sheets(df)  # 🔹 Save to Google Sheets
    st.success(f"✅ {machine_to_refill} updated to {new_stock} items!")

# ✅ Change Refill Threshold
st.subheader("⚙️ Adjust Refill Threshold")
machine_to_edit = st.selectbox("Select machine to edit threshold", df["location"])
new_threshold = st.number_input("Enter new threshold:", min_value=0, max_value=500, step=1)
if st.button("Update Threshold"):
    df.loc[df["location"] == machine_to_edit, "threshold"] = new_threshold
    update_google_sheets(df)  # 🔹 Save to Google Sheets
    st.success(f"✅ {machine_to_edit} threshold updated to {new_threshold}!")

# ✅ Add a New Machine
st.subheader("➕ Add a New Machine")
new_machine = st.text_input("Enter new machine location")
new_total = st.number_input("Initial stock:", min_value=0, max_value=500, step=1)
new_thresh = st.number_input("Set refill threshold:", min_value=0, max_value=500, step=1)
if st.button("Add Machine"):
    new_row = pd.DataFrame({"location": [new_machine], "total_items": [new_total], "threshold": [new_thresh]})
    df = pd.concat([df, new_row], ignore_index=True)
    update_google_sheets(df)  # 🔹 Save to Google Sheets
    st.success(f"✅ {new_machine} added with {new_total} items and a threshold of {new_thresh}!")

# ✅ Enhanced Chart with Filters
st.subheader("📉 Stock Levels by Machine")

selected_locations = st.multiselect("Filter by Location", df["location"].unique(), default=df["location"].unique())
filtered_df = df[df["location"].isin(selected_locations)]

fig, ax = plt.subplots()
ax.bar(
    filtered_df["location"],
    filtered_df["total_items"],
    color=['green' if t >= th else 'red' for t, th in zip(filtered_df["total_items"], filtered_df["threshold"])]
)
ax.set_xlabel("Vending Machines")
ax.set_ylabel("Total Items Remaining")
ax.set_title("Vending Machine Stock Levels")

st.pyplot(fig)

st.caption("📌 Changes are automatically saved.")