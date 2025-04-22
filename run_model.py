import os
import shutil
import argparse
import urbs
from datetime import date

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
    total_years = 26  # 2025-2050
    windows = [(2025 + i, 2025 + i + window_length)
               for i in range(0, total_years, window_length)]

    # Initialize carry-over variables
    carry_over = {
        'stockpile': 40,  # Initial stockpile (GW)
        'cumulative_rem': 0,  # Cumulative remanufacturing capacity
    }

    for i, (window_start, window_end) in enumerate(windows):
        print(f"\nRunning window {i + 1}/{len(windows)}: {window_start}-{window_end}")

        # Modify scenario with window-specific parameters
        window_scenario = scenarios[0].copy()  # Use a copy of the base scenario
        window_scenario['window'] = (window_start, window_end)
        window_scenario.update(carry_over)

        # Run the model for this window
        prob = urbs.run_scenario(
            input_path,
            solver,
            timesteps,
            window_scenario,
            os.path.join(result_dir, f"window_{window_start}_{window_end}"),
            dt,
            objective,
            plot_tuples=plot_tuples,
            plot_sites_name=plot_sites_name,
            plot_periods=plot_periods,
            report_tuples=report_tuples,
            report_sites_name=report_sites_name,
        )

        # Update carry-over variables for next window
        carry_over = {
            'stockpile': prob.get_stockpile_level(window_end),
            'cumulative_rem': carry_over['cumulative_rem'] +
                              prob.get_cumulative_rem_capacity(window_start, window_end),
        }


# Execute selected mode
if args.mode == 'perfect':
    print("Running in perfect foresight mode")
    run_perfect_foresight()
else:
    print(f"Running in rolling horizon mode (window={args.window} years)")
    run_rolling_horizon(window_length=args.window)

print("\nSimulation completed successfully!")
