import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt  # ✅ Added Matplotlib for charting

# File where vending machine data is stored
FILE_PATH = "vending_machines.csv"


# Function to load and update machine data
def load_data():
    if os.path.exists(FILE_PATH):
        df = pd.read_csv(FILE_PATH)
    else:
        df = pd.DataFrame(columns=["location", "total_items", "threshold"])

    # ✅ Dynamically update "ready_to_fill" status
    df["ready_to_fill"] = df["total_items"] <= df["threshold"]

    return df


# Load data
df = load_data()

# Streamlit Dashboard UI
st.title("Vending Machine Manager 🥤")

# Display Machine Stock
st.subheader("📊 Current Stock Levels")
st.dataframe(df)


# ✅ **Fix: Ensure refill status updates after stock changes**
def update_csv():
    df["ready_to_fill"] = df["total_items"] <= df["threshold"]
    df.to_csv(FILE_PATH, index=False)


# Refill a Machine
st.subheader("🔄 Refill a Machine")
machine_to_refill = st.selectbox("Select a machine", df["location"])
new_stock = st.number_input("Enter new total stock:", min_value=0, max_value=500, step=1)
if st.button("Update Stock"):
    df.loc[df["location"] == machine_to_refill, "total_items"] = new_stock
    update_csv()  # ✅ Update the refill status
    st.success(f"✅ {machine_to_refill} updated to {new_stock} items!")

# Change Refill Threshold
st.subheader("⚙️ Adjust Refill Threshold")
machine_to_edit = st.selectbox("Select machine to edit threshold", df["location"])
new_threshold = st.number_input("Enter new threshold:", min_value=0, max_value=500, step=1)
if st.button("Update Threshold"):
    df.loc[df["location"] == machine_to_edit, "threshold"] = new_threshold
    update_csv()  # ✅ Update the refill status
    st.success(f"✅ {machine_to_edit} threshold updated to {new_threshold}!")

# Add a New Machine
st.subheader("➕ Add a New Machine")
new_machine = st.text_input("Enter new machine location")
new_total = st.number_input("Initial stock:", min_value=0, max_value=500, step=1)
new_thresh = st.number_input("Set refill threshold:", min_value=0, max_value=500, step=1)
if st.button("Add Machine"):
    new_row = pd.DataFrame({"location": [new_machine], "total_items": [new_total], "threshold": [new_thresh]})
    df = pd.concat([df, new_row], ignore_index=True)
    update_csv()  # ✅ Update the refill status
    st.success(f"✅ {new_machine} added with {new_total} items and a threshold of {new_thresh}!")

# ✅ **Recalculate refill status dynamically**
df["ready_to_fill"] = df["total_items"] <= df["threshold"]

# Display updated machine list
st.subheader("⚠️ Machines That Need Refilling")
low_stock_machines = df[df["ready_to_fill"]]
if not low_stock_machines.empty:
    st.write(low_stock_machines)
    st.warning("⚠️ Some machines are below the refill threshold!")
else:
    st.success("✅ All machines have sufficient stock!")

# ✅ **Enhanced Chart with Filters**
st.subheader("📉 Stock Levels by Machine")

# Add a filter dropdown for locations
selected_locations = st.multiselect("Filter by Location", df["location"].unique(), default=df["location"].unique())

# Filter the dataframe based on selection
filtered_df = df[df["location"].isin(selected_locations)]

# Create the chart
fig, ax = plt.subplots()
ax.bar(
    filtered_df["location"],
    filtered_df["total_items"],
    color=['green' if t >= th else 'red' for t, th in zip(filtered_df["total_items"], filtered_df["threshold"])]
)
ax.set_xlabel("Vending Machines")
ax.set_ylabel("Total Items Remaining")
ax.set_title("Vending Machine Stock Levels")

# Display the updated chart
st.pyplot(fig)

st.caption("📌 Changes are automatically saved.")