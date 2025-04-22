import os
import shutil
import argparse
import urbs
from datetime import date
import pandas as pd

def read_carry_over_from_excel(result_path, scenario_name):
    """Extract carry-over values from the result Excel of the previous window."""
    filepath = os.path.join(result_path, f"{scenario_name}.xlsx")

    # Read relevant sheets (update sheet names if needed!)
    cap_sheet = pd.read_excel(filepath, sheet_name="extension_total_caps")
    stock_sheet = pd.read_excel(filepath, sheet_name="Stock_Capacity")
    dec_sheet = pd.read_excel(filepath, sheet_name="decom")

    # Extract only the last timestep
    last_timestep = cap_sheet['stf'].max()

    cap_last = cap_sheet[cap_sheet['stf'] == last_timestep]
    stock_last = stock_sheet[stock_sheet['stf'] == last_timestep]
    dec_last = dec_sheet[dec_sheet['stf'] == last_timestep]

    # Transform into dictionary format
    cap_dict = {(row['sit'], row['pro']): row['cap_pro'] for _, row in cap_last.iterrows()}
    stock_dict = {(row['location'], row['tech']): row['capacity_ext_stock'] for _, row in stock_last.iterrows()}
    dec_dict = {(row['location'], row['tech']): row['capacity_dec'] for _, row in dec_last.iterrows()}

    return {
        'Installed_Capacity_Q_s': cap_dict,
        'Existing_Stock_Q_stock': stock_dict,
        'capacity_dec_start': dec_dict,
        # optionally add 'cap_pro' if it's also stored
    }


# Add command-line argument parsing
parser = argparse.ArgumentParser(description='Run URBS model in different optimization modes.')
parser.add_argument('--mode', choices=['perfect', 'rolling'], default='perfect',
                   help='Optimization mode: "perfect" (default) or "rolling" horizon')
parser.add_argument('--window', type=int, default=5,
                   help='Rolling horizon window length in years (default: 5)')
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
    urbs.scenario_base
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
    for scenario in scenarios:
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
    """Rolling horizon implementation"""
    for scenario in scenarios:
        total_years = 27  # 2024–2050
        windows = [(2024 + i, 2024 + i + window_length - 1) for i in range(0, total_years, window_length)]

        # Initialize carry-over variables
        carry_over = {
            'Installed_Capacity_Q_s': {},
            'Existing_Stock_Q_stock': {},
            'capacity_dec_start': {},
            'cap_pro': {}
        }

        # Define locations and technologies (replace with actual model data)
        locations = ["EU27"]  # Example; replace with actual locations TODO fix hardcode
        technologies = ["solarPV", "windon", "windoff"]  # Example; replace with actual technologies TODO fix hardcode
        techs = ['Biomass Plant', 'Coal CCUS', 'Coal Lignite', 'Coal Lignite CCUS', 'Coal Plant', 'Gas Plant (CCGT)', 'Gas Plant (CCGT) CCUS', 'Hydro (reservoir)', 'Hydro (run-of-river)', 'Nuclear Plant', 'Wind (offshore)', 'Wind (onshore)'] # TODO fix hardcode

        for i, (window_start, window_end) in enumerate(windows):
            print(f"\nRunning window {i + 1}/{len(windows)}: {window_start}-{window_end}")

            # Create the result directory for the current window
            window_result_dir = os.path.join(result_dir, f"window_{window_start}_{window_end}")
            os.makedirs(window_result_dir, exist_ok=True)

            # Generate the indexlist for the current rolling horizon window
            indexlist = list(range(window_start, window_end + 1))
            print(f"Rolling horizon: {window_start} - {window_end}")
            print(f"Indexlist (stf): {indexlist}")

            # Define timesteps for the current window
            window_start_timestep = (window_start - 2024) * 12  # Assuming monthly timesteps starting at 2024
            window_end_timestep = (window_end - 2024 + 1) * 12
            timesteps = range(window_start_timestep, window_end_timestep)

            # Apply carry-over initial conditions
            if i > 0:
                prev_window_start, prev_window_end = windows[i - 1]
                prev_result_dir = os.path.join(result_dir, f"window_{prev_window_start}_{prev_window_end}")
                initial_conditions = read_carry_over_from_excel(prev_result_dir, scenario)
                print(initial_conditions)
            else:
                initial_conditions = None

            # Pass rolling horizon parameters to urbs.run_scenario
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
                window_start=window_start,  # Pass window start
                window_end=window_end,      # Pass window end
                indexlist=indexlist,         # Pass indexlist for stf filtering
            )

            # Debugging output
            print(type(prob))
            print(dir(prob))
            prob.stf.initialize = list(range(window_start, window_end + 1))
            print(f"Updated stf for Rolling Horizon: {list(prob.stf)}")  # Debugging output
            prob.y0 = window_start

            # Extract results for carry-over
            last_year = window_end
            carry_over['cap_pro'] = {
                (sit, pro): prob.process_dict["inst-cap"][(last_year, sit, pro)].value
                for sit in locations
                for pro in techs
                if (sit, pro, last_year) in prob.pro_const_cap_dict
            }

            carry_over = {
                'Installed_Capacity_Q_s': {
                    (loc, tech): prob.capacity_ext[last_year, loc, tech].value
                    for loc in locations
                    for tech in technologies
                },
                'Existing_Stock_Q_stock': {
                    (loc, tech): prob.capacity_ext_stock[last_year, loc, tech].value
                    for loc in locations
                    for tech in technologies
                },
                'capacity_dec_start': {
                    (loc, tech): prob.capacity_dec[last_year, loc, tech].value
                    for loc in locations
                    for tech in technologies
                }
            }


# Execute selected mode
if args.mode == 'perfect':
    print("Running in perfect foresight mode")
    run_perfect_foresight()
else:
    print(f"Running in rolling horizon mode (window={args.window} years)")
    run_rolling_horizon(window_length=args.window)

print("\nSimulation completed successfully!")


