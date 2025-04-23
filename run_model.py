import os
import shutil
import argparse
import urbs
from datetime import date
import pandas as pd


def read_carry_over_from_excel(result_path, scenario_name, window_start):
    """Extract carry-over values from the result Excel of the previous window."""
    filepath = os.path.join(result_path, f"{scenario_name}.xlsx")

    # Read relevant sheets (update sheet names if needed!)
    cap_sheet = pd.read_excel(filepath, sheet_name="extension_total_caps")
    stock_sheet = pd.read_excel(filepath, sheet_name="extension_only_caps")
    dec_sheet = pd.read_excel(filepath, sheet_name="decom")
    total_CO2_sheet = pd.read_excel(filepath, sheet_name="total_co2")

    # Forward-fill the stf column to propagate the year across rows that have NaN
    cap_sheet["stf"] = cap_sheet["stf"].fillna(method="ffill")
    stock_sheet["stf"] = stock_sheet["stf"].fillna(method="ffill")
    dec_sheet["stf"] = dec_sheet["stf"].fillna(method="ffill")
    cap_sheet["sit"] = cap_sheet["sit"].fillna(method="ffill")
    stock_sheet["location"] = stock_sheet["location"].fillna(method="ffill")
    dec_sheet["location"] = dec_sheet["location"].fillna(method="ffill")

    # Extract only the last timestep
    last_timestep = window_start - 1

    cap_last = cap_sheet[cap_sheet["stf"] == last_timestep]
    stock_last = stock_sheet[stock_sheet["stf"] == last_timestep]
    dec_last = dec_sheet[dec_sheet["stf"] == last_timestep]

    # Debugging: Check if the filtering gives the expected results
    print(f"Last timestep: {last_timestep}")
    print(f"Rows in cap sheet for last timestep:\n{cap_last}")
    print(f"Rows in stock sheet for last timestep:\n{stock_last}")
    print(f"Rows in dec sheet for last timestep:\n{dec_last}")

    installed_capacity = {
        (row["sit"], row["pro"]): row["cap_pro"] for _, row in cap_last.iterrows()
    }
    stocklevel = {
        (row["location"], row["tech"]): row["capacity_ext_stock"]
        for _, row in stock_last.iterrows()
    }
    decomissions = {
        (row["location"], row["tech"]): row["capacity_dec"]
        for _, row in dec_last.iterrows()
    }
    total_co2 = total_CO2_sheet["Total_CO2"].iloc[0]

    # Return the extracted data in the correct format
    return {
        "Installed_Capacity_Q_s": installed_capacity,
        "Existing_Stock_Q_stock": stocklevel,
        "capacity_dec_start": decomissions,
        "Total_CO2_Emissions": total_co2,
    }


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


def run_rolling_horizon(window_length=5):
    for scenario_name, scenario in scenarios:
        total_years = 27
        windows = [
            (2024 + i, 2024 + i + window_length - 1)
            for i in range(0, total_years, window_length)
        ]

        for i, (window_start, window_end) in enumerate(windows):
            print(
                f"\nRunning window {i + 1}/{len(windows)}: {window_start}-{window_end}"
            )
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


# Execute selected mode
if args.mode == "perfect":
    print("Running in perfect foresight mode")
    run_perfect_foresight()
else:
    print(f"Running in rolling horizon mode (window={args.window} years)")
    run_rolling_horizon(window_length=args.window)

print("\nSimulation completed successfully!")
