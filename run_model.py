import os
import shutil
import argparse
import urbs
from datetime import date
import pandas as pd
from collections import defaultdict
# from urbs_auto_plotting import plot_from_excel


def read_carry_over_from_excel(result_path, scenario_name):
    """
    Extract carry-over values for all years in the result Excel.
    Returns a nested dict: {year: {carryover_type: {index: value}}}
    """
    filepath = os.path.join(result_path, f"{scenario_name}.xlsx")

    cap_sheet = pd.read_excel(filepath, sheet_name="extension_total_caps")
    stock_sheet = pd.read_excel(filepath, sheet_name="extension_only_caps")
    detailed_cap_sheet = pd.read_excel(filepath, sheet_name="extension_only_caps")
    dec_sheet = pd.read_excel(filepath, sheet_name="decom")
    secondary_cap = pd.read_excel(filepath, sheet_name="secondary_cap_sum")
    scrap_sheet = pd.read_excel(filepath, sheet_name="scrap")
    balance_sheet = pd.read_excel(filepath, sheet_name="extension_balance")
    e_pro_in_sheet = pd.read_excel(filepath, sheet_name="e_pro_in")
    cost_sheet = pd.read_excel(filepath, sheet_name="extension_cost")
    co2_sheet = pd.read_excel(filepath, sheet_name="us_co2")
    pricereduction_sec_sheet = pd.read_excel(filepath, sheet_name="pricereduction_sec")

    # Forward fill to clean up NaNs
    for df in [
        cap_sheet,
        stock_sheet,
        dec_sheet,
        detailed_cap_sheet,
        secondary_cap,
        pricereduction_sec_sheet,
        scrap_sheet,
    ]:
        df["stf"] = df["stf"].fillna(method="ffill")
        if "location" in df.columns:
            df["location"] = df["location"].fillna(method="ffill")
        if "sit" in df.columns:
            df["sit"] = df["sit"].fillna(method="ffill")

    cap_components = [
        "capacity_ext_imported",
        "capacity_ext_stockout",
        "capacity_ext_euprimary",
        "capacity_ext_eusecondary",
        "capacity_ext_stock",
        "capacity_ext_stock_imported",
        "newly_added_capacity",
    ]
    carryovers = {}

    all_years = sorted(set(cap_sheet["stf"].dropna().unique()))

    # Group CO2 by year, sit, and process
    co2_grouped = co2_sheet.groupby(["stf", "sit", "pro"], as_index=False)[
        "value"
    ].sum()
    balance_grouped = balance_sheet.groupby(["Stf", "Site", "Process"], as_index=False)[
        "Value"
    ].sum()
    e_pro_in_grouped = e_pro_in_sheet.groupby(
        ["stf", "sit", "pro", "com"], as_index=False
    )["e_pro_in"].sum()

    # Group costs by year and process
    cost_grouped = cost_sheet.groupby(["stf", "pro"], as_index=False)[
        "Total_Cost"
    ].sum()

    for year in all_years:
        cap_year = cap_sheet[cap_sheet["stf"] == year]
        stock_year = stock_sheet[stock_sheet["stf"] == year]
        dec_year = dec_sheet[dec_sheet["stf"] == year]
        sec_year = secondary_cap[secondary_cap["stf"] == year]

        co2_year = co2_grouped[co2_grouped["stf"] == year]
        cost_year = cost_grouped[cost_grouped["stf"] == year]
        scrap_year = scrap_sheet[scrap_sheet["stf"] == year]
        balance_year = balance_grouped[balance_grouped["Stf"] == year]
        e_pro_in_year = e_pro_in_grouped[e_pro_in_grouped["stf"] == year]
        detail_year = detailed_cap_sheet[detailed_cap_sheet["stf"] == year]
        pricereduction_sec_year = pricereduction_sec_sheet[
            pricereduction_sec_sheet["stf"] == year
        ]

        carryovers[int(year)] = {
            "Installed_Capacity_Q_s": {
                (row["sit"], row["pro"]): row["cap_pro"]
                for _, row in cap_year.iterrows()
            },
            "Existing_Stock_Q_stock": {
                (row["location"], row["tech"]): row["capacity_ext_stock"]
                for _, row in stock_year.iterrows()
            },
            "capacity_dec_start": {
                (row["location"], row["tech"]): row["capacity_dec"]
                for _, row in dec_year.iterrows()
            },
            "Total Cap Sec": {
                (row["location"], row["tech"]): row["cumulative"]
                for _, row in sec_year.iterrows()
            },
            "CO2_emissions": {
                (row["sit"], row["pro"]): row["value"] for _, row in co2_year.iterrows()
            },
            "Total_Cost": {
                row["pro"]: row["Total_Cost"] for _, row in cost_year.iterrows()
            },
            "Total_Scrap": {
                (row["location"], row["tech"]): row["capacity_scrap_total"]
                for _, row in scrap_year.iterrows()
            },
            "Pricereduction": {
                (row["location"], row["tech"]): row["pricereduction_sec"]
                for _, row in pricereduction_sec_year.iterrows()
            },
            "Balance": {
                (row["Site"], row["Process"]): row["Value"]
                for _, row in balance_year.iterrows()
            },
            "Commodities_Demand": {
                (row["sit"], row["pro"], row["com"]): row["e_pro_in"]
                for _, row in e_pro_in_year.iterrows()
            },
            # New breakdown fields from detailed_cap
            "capacity_ext_imported": {
                (row["location"], row["tech"]): row["capacity_ext_imported"]
                for _, row in detail_year.iterrows()
            },
            "capacity_ext_stockout": {
                (row["location"], row["tech"]): row["capacity_ext_stockout"]
                for _, row in detail_year.iterrows()
            },
            "capacity_ext_euprimary": {
                (row["location"], row["tech"]): row["capacity_ext_euprimary"]
                for _, row in detail_year.iterrows()
            },
            "capacity_ext_eusecondary": {
                (row["location"], row["tech"]): row["capacity_ext_eusecondary"]
                for _, row in detail_year.iterrows()
            },
            "capacity_ext_stock_imported": {
                (row["location"], row["tech"]): row["capacity_ext_stock_imported"]
                for _, row in detail_year.iterrows()
            },
            "newly_added_capacity": {
                (row["location"], row["tech"]): row["newly_added_capacity"]
                for _, row in detail_year.iterrows()
            },
        }

    return carryovers  # dict of year → carryover types


def write_carryovers_to_excel(all_initial_conditions, output_path):
    with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
        for var_name, data in all_initial_conditions.items():
            records = []
            for (year, key), (win_idx, value) in data.items():
                if isinstance(key, tuple):
                    record = {
                        "window_index": win_idx,
                        "year": year,
                        **{f"key_{i}": k for i, k in enumerate(key)},
                        "value": value,
                    }
                else:
                    record = {
                        "window_index": win_idx,
                        "year": year,
                        "key": key,
                        "value": value,
                    }
                records.append(record)

            df = pd.DataFrame(records)
            df.to_excel(writer, sheet_name=var_name[:31], index=False)


# Add command-line argument parsing
parser = argparse.ArgumentParser(
    description="Run URBS model in different optimization modes."
)
parser.add_argument(
    "--mode",
    choices=["perfect", "rolling"],
    default="perfect",
    help='Optimization mode: "perfect" (default) or "rolling" horizon',
)
parser.add_argument(
    "--window",
    type=int,
    default=5,
    help="Rolling horizon window length in years (default: 5)",
)
args = parser.parse_args()

# Original setup (unchanged)
input_files = "urbs_intertemporal_2050"
input_dir = "Input"
input_path = os.path.join(input_dir, input_files)

result_name = "urbs"
result_dir = urbs.prepare_result_directory(result_name)
year = date.today().year

# Copy input/run files to result directory
try:
    shutil.copytree(input_path, os.path.join(result_dir, input_dir))
except NotADirectoryError:
    shutil.copyfile(input_path, os.path.join(result_dir, input_files))
shutil.copy(__file__, result_dir)

# Configuration (unchanged)
objective = "cost"
solver = "gurobi"
(offset, length) = (0, 12)
timesteps = range(offset, offset + length + 1)
dt = 730

# Reporting/plotting setup (unchanged)
report_tuples = []
report_sites_name = {("EU27"): "All"}
plot_tuples = []
plot_sites_name = {("EU27"): "All"}
plot_periods = {"all": timesteps[1:]}
my_colors = {"EU27": (200, 230, 200)}
for country, color in my_colors.items():
    urbs.COLORS[country] = color

# select scenarios to be run
scenarios = [
    ("scenario_base", urbs.scenario_base)
    # urbs.scenario_base_minstock,
    # urbs.scenario_1,
    # urbs.scenario_2,
    # urbs.scenario_3,
    # urbs.scenario_4,
    # urbs.scenario_6,
    # urbs.scenario_7,
    # urbs.scenario_8,
    # urbs.scenario_10,
    # urbs.scenario_11,
    # urbs.scenario_12,
    # urbs.scenario_13,
    # urbs.scenario_14,
    # urbs.scenario_15,
    # urbs.scenario_16,
    # urbs.scenario_17,
    # urbs.scenario_18,
    # urbs.scenario_19,
    # urbs.scenario_20,
    ##urbs.scenario_21,
    # urbs.scenario_25,
    # urbs.scenario_26,
    # urbs.scenario_27,
    # urbs.scenario_28,
    # urbs.scenario_29,
    # urbs.scenario_30,
    # urbs.scenario_31,
    # urbs.scenario_32,
    # urbs.scenario_33,
    # urbs.scenario_34
    # urbs.scenario_35
    # urbs.scenario_36,
    # urbs.scenario_37
    # urbs.scenario_38
    # urbs.scenario_39
    # urbs.scenario_40
]


def run_perfect_foresight():
    """Original perfect foresight execution"""
    for scenario_name, scenario in scenarios:
        prob = urbs.run_scenario(
            input_path,
            solver,
            timesteps,
            scenario,
            result_dir,
            dt,
            objective,
            plot_tuples=plot_tuples,
            plot_sites_name=plot_sites_name,
            plot_periods=plot_periods,
            report_tuples=report_tuples,
            report_sites_name=report_sites_name,
        )


def run_myopic(window_length=5):
    #    for scenario_name, scenario in scenarios:
    total_years = 27
    windows = [
        (2024 + i, 2024 + i + window_length - 1)
        for i in range(0, total_years, window_length)
    ]

    for i, (window_start, window_end) in enumerate(windows):
        print(f"\nRunning window {i + 1}/{len(windows)}: {window_start}-{window_end}")
        window_result_dir = os.path.join(
            result_dir, f"window_{window_start}_{window_end}"
        )
        os.makedirs(window_result_dir, exist_ok=True)

        indexlist = list(range(window_start, window_end + 1))
        (offset, length) = (0, 12)
        timesteps = range(offset, offset + length + 1)

        # Load carry-over data from the previous window
        if i > 0:
            prev_window_start, prev_window_end = windows[i - 1]
            prev_result_dir = os.path.join(
                result_dir, f"window_{prev_window_start}_{prev_window_end}"
            )
            initial_conditions = read_carry_over_from_excel(
                prev_result_dir, scenario_name, window_start
            )
            print(initial_conditions)
        else:
            initial_conditions = None

        prob = urbs.run_scenario(
            input_path,
            solver,
            timesteps,
            scenario,
            window_result_dir,
            dt,
            objective,
            plot_tuples=plot_tuples,
            plot_sites_name=plot_sites_name,
            plot_periods={"all": timesteps},
            report_tuples=report_tuples,
            report_sites_name=report_sites_name,
            initial_conditions=initial_conditions,
            window_start=window_start,
            window_end=window_end,
            indexlist=indexlist,
        )

        print(dir(prob))


def run_rolling_horizon(start_year=2024, end_year=2050, step=9):
    all_carryovers = defaultdict(dict)

    for scenario_name, scenario in scenarios:
        windows = []
        current_start = start_year

        while current_start < end_year:
            windows.append((current_start, end_year))
            current_start += step

        for i, (window_start, window_end) in enumerate(windows):
            print(
                f"\nRunning window {i + 1}/{len(windows)}: {window_start}-{window_end}"
            )
            window_result_dir = os.path.join(
                result_dir, f"rolling_{window_start}_to_{window_end}"
            )
            os.makedirs(window_result_dir, exist_ok=True)

            indexlist = list(range(window_start, window_end + 1))
            timesteps = range(0, 13)

            # Load carry-over from previous window if not the first
            if i > 0:
                prev_window_start, _ = windows[i - 1]
                prev_result_dir = os.path.join(
                    result_dir, f"rolling_{prev_window_start}_to_{end_year}"
                )

                carryovers_by_year = read_carry_over_from_excel(
                    result_path=prev_result_dir, scenario_name=scenario_name
                )

                carry_year = window_start - 1
                if carry_year in carryovers_by_year:
                    initial_conditions = carryovers_by_year[carry_year]
                    print(
                        f"Loaded initial conditions from year {carry_year} in {prev_result_dir}"
                    )
                else:
                    print(f"No carryover data available for year {carry_year}")
                    initial_conditions = None
            else:
                initial_conditions = None

            prob = urbs.run_scenario(
                input_path,
                solver,
                timesteps,
                scenario,
                window_result_dir,
                dt,
                objective,
                plot_tuples=plot_tuples,
                plot_sites_name=plot_sites_name,
                plot_periods={"all": timesteps},
                report_tuples=report_tuples,
                report_sites_name=report_sites_name,
                initial_conditions=initial_conditions,
                window_start=window_start,
                window_end=window_end,
                indexlist=indexlist,
            )

            print(dir(prob))

            # Now, after the scenario has run, capture the carryover data from the results
            carryovers_for_window = read_carry_over_from_excel(
                result_path=window_result_dir, scenario_name=scenario_name
            )

            # You need to append the carryover data for this window to the `all_carryovers` dictionary
            for year, year_data in carryovers_for_window.items():
                for var_name, data_dict in year_data.items():
                    for key, value in data_dict.items():
                        all_carryovers[var_name][(year, key)] = (
                            i,
                            value,
                        )  # overwrite if exists

            # Optionally, you can print or inspect the carryovers to verify they are being collected
            print(
                f"Carryovers for window {window_start}-{window_end}: {carryovers_for_window}"
            )

            # Once all windows are processed, you can now save all carryovers to Excel
            # Make sure to pass `all_carryovers` to the write function
        output_filename = (
            f"result_{scenario_name}.xlsx"  # Include scenario name in the file name
        )
        output_file_path = os.path.join(result_dir, output_filename)
        write_carryovers_to_excel(all_carryovers, output_file_path)
        # plot_from_excel(output_file_path) #ToDo enable when final


# Execute selected mode
if args.mode == "perfect":
    print("Running in perfect foresight mode")
    run_perfect_foresight()
elif args.mode == "rolling":
    print("Running in rolling horizon mode")
    run_rolling_horizon(start_year=2024, end_year=2050, step=9)

else:
    print(f"Running in myopic mode (window={args.window} years)")
    run_myopic(window_length=args.window)

print("\nSimulation completed successfully!")
