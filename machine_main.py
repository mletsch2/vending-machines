import pandas as pd
import os

# File to store machine data
FILE_PATH = "vending_machines.csv"

# Sample daily sales data (this would eventually be automated)
daily_sales = {
    "Location A": 50,
    "Location B": 20,
    "Location C": 15
}


# Function to load machine data
def load_data():
    if os.path.exists(FILE_PATH):
        return pd.read_csv(FILE_PATH)
    else:
        # If the file doesn't exist, create a default one
        data = pd.DataFrame({
            "location": ["Location A", "Location B", "Location C"],
            "total_items": [100, 120, 90],
            "threshold": [40, 50, 45]
        })
        data.to_csv(FILE_PATH, index=False)
        return data


# Function to update stock levels based on daily sales
def update_stock(data):
    for index, row in data.iterrows():
        location = row["location"]
        if location in daily_sales:
            data.at[index, "total_items"] -= daily_sales[location]  # Subtract sales
            if data.at[index, "total_items"] < 0:
                data.at[index, "total_items"] = 0  # Prevent negative stock
    return data


# Function to check which machines need refilling
def check_ready_to_fill(data):
    data["ready_to_fill"] = data["total_items"] <= data["threshold"]
    print("\nMachines that need refilling:")
    print(data[["location", "total_items", "threshold", "ready_to_fill"]])
    return data


# Function to refill a machine
def refill_machine(data):
    print("\nRefilling machines...")
    for index, row in data.iterrows():
        if row["ready_to_fill"]:  # If flagged for refill
            new_stock = int(input(f"Enter new total items for {row['location']}: "))
            data.at[index, "total_items"] = new_stock  # Update stock
            print(f"{row['location']} refilled to {new_stock} items.")
    return data


# Main program
def main():
    # Load machine data
    machine_data = load_data()

    # Update stock levels with daily sales
    machine_data = update_stock(machine_data)

    # Check which machines need refilling
    machine_data = check_ready_to_fill(machine_data)

    # Ask for refills if necessary
    if machine_data["ready_to_fill"].any():
        machine_data = refill_machine(machine_data)

    # Save updated data
    machine_data.to_csv(FILE_PATH, index=False)
    print("\nUpdated machine data saved!")


# Run the program
if __name__ == "__main__":
    main()