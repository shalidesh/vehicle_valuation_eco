import pandas as pd

# Read CSV
df = pd.read_csv("fast_moving_vehicles.csv")

# Function to convert "20-Sep" → "2020-09-01"
def convert_date(x):
    # split "20-Sep" into year and month
    year_part, month_part = x.split("-")
    year = 2000 + int(year_part)  # "20" → 2020
    month = pd.to_datetime(month_part, format="%b").month  # "Sep" → 9
    return f"{year:04d}-{month:02d}-01"

# Apply conversion
df["date"] = df["date"].apply(convert_date)

# Save back to CSV (optional)
df.to_csv("fast_moving_vehicles_2.csv", index=False)

