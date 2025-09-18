import pandas as pd
import pytz

# === Parameters ===
input_file = r"C:\Users\maxoi\OneDrive\Desktop\time_series_60min.csv"
renewables_output_file = "EU27_hourly_renewables_raw_2019.csv"
year = 2019

# EU27 ENTSO-E country codes
eu27_codes = [
    "AT","BE","BG","CY","CZ","DE","DK","EE","ES","FI","FR","GR",
    "HR","HU","IE","IT","LT","LU","LV","MT","NL","PL","PT","RO","SE","SI","SK"
]

# === 1. Read CSV ===
df = pd.read_csv(input_file)

# === 2. Convert timestamp column to datetime and tz-naive ===
df["cet_cest_timestamp"] = pd.to_datetime(df["cet_cest_timestamp"], utc=True, errors="coerce")
df["cet_cest_timestamp"] = df["cet_cest_timestamp"].dt.tz_convert(None)

# === 3. Filter for the given year ===
start = pd.Timestamp(f"{year}-01-01 00:00:00")
end = pd.Timestamp(f"{year}-12-31 23:00:00")
mask = (df["cet_cest_timestamp"] >= start) & (df["cet_cest_timestamp"] <= end)
df_year = df.loc[mask]

# -----------------------------
# Extract EU27 renewable columns
# -----------------------------
renewables_cols = []
for code in eu27_codes:
    for kind in ["solar_generation_actual", "wind_onshore_generation_actual", "wind_offshore_generation_actual"]:
        col_name = f"{code}_{kind}"
        if col_name in df_year.columns:
            renewables_cols.append(col_name)

# Keep timestamp + filtered columns
selected_cols = ["cet_cest_timestamp"] + renewables_cols
df_renew = df_year[selected_cols]

# Optional: rename timestamp column
df_renew = df_renew.rename(columns={"cet_cest_timestamp": "timestamp"})

# Fill NaNs with 0
df_renew = df_renew.fillna(0)

# Save raw renewables CSV
df_renew.to_csv(renewables_output_file, index=False)

print(f"Done! Saved {renewables_output_file} with all EU27 country renewable columns for {year}.")

# === Parameters ===
input_file = "EU27_hourly_renewables_raw_2019.csv"  # raw per-country CSV
output_file = "EU27_hourly_renewables_2019.csv"     # summed CSV

# Installed capacities 2019 (MW)
installed_capacity = {
    "Solar": 98236,
    "WindOnshore": 156776,
    "WindOffshore": 10000
}

# === 1. Load raw renewables CSV ===
df = pd.read_csv(input_file)

# === 2. Identify columns by type ===
solar_cols = [c for c in df.columns if "solar_generation_actual" in c]
wind_on_cols = [c for c in df.columns if "wind_onshore_generation_actual" in c]
wind_off_cols = [c for c in df.columns if "wind_offshore_generation_actual" in c]

# === 3. Sum over all countries for each type ===
df_summed = pd.DataFrame()
df_summed["t"] = range(len(df) +1)  # optional: index for model
df_summed["EU27.Solar"] = [0] + df[solar_cols].sum(axis=1).tolist()
df_summed["EU27.WindOnshore"] =[0]+ df[wind_on_cols].sum(axis=1).tolist()
df_summed["EU27.WindOffshore"] =[0]+ df[wind_off_cols].sum(axis=1).tolist()

# === 5. Compute hourly load factors ===
df_summed["EU27.Solar"] = df_summed["EU27.Solar"] / installed_capacity["Solar"]
df_summed["EU27.WindOnshore"] = df_summed["EU27.WindOnshore"] / installed_capacity["WindOnshore"]
df_summed["EU27.WindOffshore"] = df_summed["EU27.WindOffshore"] / installed_capacity["WindOffshore"]

# === 6. Save to CSV ===
df_summed.to_csv(output_file, index=False)

print(f"Done! Saved {output_file} with summed EU27 hourly renewables and load factors for 2019.")
