import streamlit as st
import pandas as pd
import os

# File where vending machine data is stored
FILE_PATH = "vending_machines.csv"

# Function to load machine data
def load_data():
    if os.path.exists(FILE_PATH):
        return pd.read_csv(FILE_PATH)
    else:
        return pd.DataFrame(columns=["location", "total_items", "threshold"])

# Load data
df = load_data()

# Streamlit Dashboard UI
st.title("Vending Machine Manager 🥤")

# Display Machine Stock
st.subheader("📊 Current Stock Levels")
st.dataframe(df)

# Refill a Machine
st.subheader("🔄 Refill a Machine")
machine_to_refill = st.selectbox("Select a machine", df["location"])
new_stock = st.number_input("Enter new total stock:", min_value=0, max_value=500, step=1)
if st.button("Update Stock"):
    df.loc[df["location"] == machine_to_refill, "total_items"] = new_stock
    df.to_csv(FILE_PATH, index=False)
    st.success(f"✅ {machine_to_refill} updated to {new_stock} items!")

# Change Refill Threshold
st.subheader("⚙️ Adjust Refill Threshold")
machine_to_edit = st.selectbox("Select machine to edit threshold", df["location"])
new_threshold = st.number_input("Enter new threshold:", min_value=0, max_value=500, step=1)
if st.button("Update Threshold"):
    df.loc[df["location"] == machine_to_edit, "threshold"] = new_threshold
    df.to_csv(FILE_PATH, index=False)
    st.success(f"✅ {machine_to_edit} threshold updated to {new_threshold}!")

# Add a New Machine
st.subheader("➕ Add a New Machine")
new_machine = st.text_input("Enter new machine location")
new_total = st.number_input("Initial stock:", min_value=0, max_value=500, step=1)
new_thresh = st.number_input("Set refill threshold:", min_value=0, max_value=500, step=1)
if st.button("Add Machine"):
    new_row = pd.DataFrame({"location": [new_machine], "total_items": [new_total], "threshold": [new_thresh]})
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(FILE_PATH, index=False)
    st.success(f"✅ {new_machine} added with {new_total} items and a threshold of {new_thresh}!")

st.caption("📌 Changes are automatically saved.")