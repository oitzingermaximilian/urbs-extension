import pandas as pd
import pytz

# === Parameters ===
input_file = r"C:\Users\maxoi\OneDrive\Desktop\time_series_60min.csv"  # CSV file path
output_file = "load_2019_filtered.csv"  # output CSV
year = 2019

# EU27 ENTSO-E country codes
eu27_codes = [
    "AT","BE","BG","CY","CZ","DE","DK","EE","ES","FI","FR","GR",
    "HR","HU","IE","IT","LT","LU","LV","MT","NL","PL","PT","RO","SE","SI","SK"
]

# === 1. Read CSV ===
df = pd.read_csv(input_file)

# === 2. Convert timestamp column to datetime (tz-aware) ===
df["cet_cest_timestamp"] = pd.to_datetime(df["cet_cest_timestamp"], errors="coerce")

# === 3. Define start and end timestamps for the year (tz-aware) ===
cet = pytz.FixedOffset(60)  # +0100 in minutes
start = pd.Timestamp(f"{year}-01-01 00:00:00", tz=cet)
end   = pd.Timestamp(f"{year}-12-31 23:00:00", tz=cet)

# === 4. Filter for the given year ===
mask = (df["cet_cest_timestamp"] >= start) & (df["cet_cest_timestamp"] <= end)
df_year = df.loc[mask]

# === 5. Keep only *_load_actual_entsoe_transparency columns ===
load_cols = [col for col in df_year.columns if col.endswith("_load_actual_entsoe_transparency")]

# === 6. Filter only main EU27 country columns (exclude sub-zones) ===
main_eu27_load_cols = [
    col for col in load_cols
    if any(col == f"{code}_load_actual_entsoe_transparency" for code in eu27_codes)
]

# === 7. Keep timestamp + main country columns ===
selected_cols = ["cet_cest_timestamp"] + main_eu27_load_cols
df_filtered = df_year[selected_cols]

# === 8. Flatten column names to country codes ===
column_mapping = {"cet_cest_timestamp": "timestamp"}
for col in main_eu27_load_cols:
    country_code = col.split("_")[0]  # e.g., "DE_load_actual_entsoe_transparency" -> "DE"
    column_mapping[col] = country_code
df_filtered = df_filtered.rename(columns=column_mapping)

# === 9. Compute EU27 hourly total load safely ===
existing_eu27_cols = [c for c in eu27_codes if c in df_filtered.columns]
df_filtered["EU27_total_load_MW"] = df_filtered[existing_eu27_cols].sum(axis=1)

# === 10. Save to CSV ===
df_filtered.to_csv(output_file, index=False)

print(f"Done! Saved {output_file} with hourly load data for {year} and main EU27 countries only.")



# Load the previously processed CSV
df = pd.read_csv("load_2019_filtered.csv")

# Create a new dataframe with the desired format
df_transformed = pd.DataFrame()
df_transformed["t"] = range(len(df) + 1)  # +1 to include t=0
df_transformed["EU27.Elec"] = [0] + df["EU27_total_load_MW"].tolist()  # prepend 0 for t=0

# Check the first few rows
print(df_transformed.head())

# Save to CSV
df_transformed.to_csv("EU27_hourly_for_model.csv", index=False)

# Load 2019 hourly EU27 demand
df = pd.read_csv("EU27_hourly_for_model.csv")  # columns: t, EU27.Elec

# Total 2019 annual demand in MWh
demand_2019 = 2619863479

# Projected annual demands 2024-2050 (in MWh)
projected_demands = [
    2491900000, 2625200000, 2758500000, 2891800000, 3025100000, 3158500000,
    3062837351, 3144100000, 3225400000, 3306700000, 3388000000, 3469300000,
    3550700000, 3632000000, 3713300000, 3794600000, 3534408544, 3650800000,
    3767200000, 3883600000, 4000000000, 4116400000, 4232800000, 4349200000,
    4465600000, 4582300000, 4062969513
]

# Corresponding years
years = list(range(2024, 2051))

# Create new dataframe for all years
df_all_years = pd.DataFrame()
df_all_years["t"] = df["t"]

# Scale 2019 hourly profile to each projection year
for year, proj_demand in zip(years, projected_demands):
    scaling_factor = proj_demand / demand_2019
    df_all_years[f"{year}_EU27.Elec"] = df["EU27.Elec"] * scaling_factor

# Save combined CSV
df_all_years.to_csv("EU27_hourly_scaled_all_years.csv", index=False)

print("Done! Saved EU27 hourly scaled profile for all projection years.")
