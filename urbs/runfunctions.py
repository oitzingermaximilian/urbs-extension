import os
import pyomo.environ
from pyomo.opt.base import SolverFactory
from datetime import datetime, date
from .model import create_model
from .report import *
from .plot import *
from .input import *
from .validation import *
from .saveload import *
from pyomo.opt.results import TerminationCondition, SolverStatus  # Correct import
import gurobipy as gp
from collections import defaultdict
import pyomo.environ as pyomo
import pandas as pd
import numpy as np

# Import bilinear constraint detection
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# from detect_bilinear_constraints import analyze_model_bilinearity


def prepare_result_directory(result_name):
    """create a time stamped directory within the result folder.

    Args:
        result_name: user specified result name

    Returns:
        a subfolder in the result folder

    """
    # timestamp for result directory
    now = datetime.now().strftime("%Y%m%dT%H%M")

    # create result directory if not existent
    result_dir = os.path.join("result", "{}-{}".format(result_name, now))
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)

    return result_dir


def setup_solver(optim, logfile="solver.log"):
    """ """
    if optim.name == "gurobi":
        optim.set_options("logfile={}".format(logfile))
        # ✅ SET BINARY TOLERANCE TO MINIMUM ALLOWED for exact binary values
        optim.set_options(
            "IntFeasTol=1e-09"
        )  # Minimum allowed integer feasibility tolerance
        optim.set_options("FeasibilityTol=1e-09")  # General feasibility tolerance
        optim.set_options("OptimalityTol=1e-09")  # Optimality tolerance
        optim.set_options("MIPGap=0")  # Set MIP gap to 0 for exact solutions
        print("✅ Gurobi binary tolerance set to minimum (1e-09) for exact BD values")
    elif optim.name == "glpk":
        # reference with list of options
        # execute 'glpsol --help'
        optim.set_options("log={}".format(logfile))
        # ✅ SET BINARY TOLERANCE TO 0 for GLPK
        optim.set_options("--mipgap 0")  # Set MIP gap to 0
        print("✅ GLPK binary tolerance set to 0 for exact BD values")
        # optim.set_options("tmlim=7200")  # seconds
        # optim.set_options("mipgap=.0005")
    elif optim.name == "cplex":
        optim.set_options("log={}".format(logfile))
        # ✅ SET BINARY TOLERANCE TO 0 for CPLEX
        optim.set_options("mip tolerances integrality 0")
        optim.set_options("mip tolerances mipgap 0")
        print("✅ CPLEX binary tolerance set to 0 for exact BD values")
    else:
        print(
            "Warning from setup_solver: no options set for solver '{}'!".format(
                optim.name
            )
        )
    return optim


def run_scenario(
    input_files,
    Solver,
    timesteps,
    scenario,
    result_dir,
    dt,
    objective,
    plot_tuples=None,
    plot_sites_name=None,
    plot_periods=None,
    report_tuples=None,
    report_sites_name=None,
    initial_conditions=None,
    window_start=None,
    window_end=None,
    indexlist=None,
    windows=None,
    window_length=None,
):
    """run an urbs model for given input, time steps and scenario

    Args:
        - input_files: filenames of input Excel spreadsheets
        - Solver: the user specified solver
        - timesteps: a list of timesteps, e.g. range(0,8761)
        - scenario: a scenario function that modifies the input data dict
        - result_dir: directory name for result spreadsheet and plots
        - dt: length of each time step (unit: hours)
        - objective: objective function chosen (either "cost" or "CO2")
        - plot_tuples: (optional) list of plot tuples (c.f. urbs.result_figures)
        - plot_sites_name: (optional) dict of names for sites in plot_tuples
        - plot_periods: (optional) dict of plot periods
          (c.f. urbs.result_figures)
        - report_tuples: (optional) list of (sit, com) tuples
          (c.f. urbs.report)
        - report_sites_name: (optional) dict of names for sites in
          report_tuples
        - initial_conditions: Optional dictionary of initial conditions for carry-over values.

    Returns:
        the urbs model instance
    """

    # sets a modeled year for non-intertemporal problems
    # (necessary for consitency)
    year = date.today().year

    # scenario name, read and modify data for scenario
    sce = scenario.__name__
    data = read_input(input_files, year)

    # print(f"\n--- Debugging run_scenario ---")  # Commented out to reduce terminal output
    # print(f"window_start: {window_start}, window_end: {window_end}")  # Commented out to reduce terminal output
    # print(f"indexlist: {indexlist}")  # Commented out to reduce terminal output
    # print("--------------------------\n")  # Commented out to reduce terminal output

    ### --------start of urbs-extensionv1.0 input data addition-------- ###

    def process_cost_sheet(cost_sheet):
        """Processes cost data into structured dictionaries indexed by (year, location, process)."""
        importcost_dict = {}  # Dictionary to store import costs
        manufacturingcost_dict = {}  # Dictionary to store manufacturing costs
        remanufacturingcost_dict = {}  # Dictionary to store remanufacturing costs
        recyclingcost_dict = {}
        o_and_m_dict = {}  # Dictionary to store o&m costs

        # Extract the 'Stf' column (year)
        years = cost_sheet[
            "Stf"
        ].unique()  # Extract the unique years from the 'stf' column

        # Iterate through the columns of the cost sheet (skip the 'stf' column)
        for col in cost_sheet.columns:
            # Skip the 'stf' column since it's already handled
            if col == "Stf":
                continue

            # Split the column name into costtype, location, and process
            parts = col.split("_")
            if len(parts) < 3:
                continue  # Skip columns that don't follow the "costtype_location_process" format

            costtype = parts[0]  # Extract the cost type (e.g., "import")
            location = parts[1]  # Extract the location (e.g., "EU27")
            process = "_".join(parts[2:])  # Extract the process (e.g., "solarPV")

            # Iterate over the rows (years) for each column and map them to (year, location, process)
            for year, value in zip(cost_sheet["Stf"], cost_sheet[col]):
                if year not in years:
                    continue  # Skip invalid years if any

                # Construct a key as (year, location, process)
                key = (year, location, process)

                # Distribute values to respective dictionaries based on cost type
                if costtype == "import":
                    importcost_dict[key] = value
                elif costtype == "manufacturing":
                    manufacturingcost_dict[key] = value
                elif costtype == "remanufacturing":
                    remanufacturingcost_dict[key] = value
                elif costtype == "recycling":
                    recyclingcost_dict[key] = value
                elif costtype == "oandm":
                    o_and_m_dict[key] = value

        return (
            importcost_dict,
            manufacturingcost_dict,
            remanufacturingcost_dict,
            recyclingcost_dict,
            o_and_m_dict,
        )

    def process_technology_sheet(technologies_data):
        """Processes technology data into a structured dictionary indexed by location and technology."""
        technologies_dict = {}  # Dictionary to store technologies by location

        # Drop rows where 'Technologies' column is NaN (if any)
        technologies_data = technologies_data.dropna(subset=["Technologies"])

        # Iterate through each row of the technologies sheet
        for _, row in technologies_data.iterrows():
            # Extract the full technology name (Location.Tech)
            tech_full_name = row["Technologies"]

            # Split it into location and technology
            try:
                location, tech_name = tech_full_name.split(
                    ".", 1
                )  # Split at the first dot
            except ValueError:
                print(f"Skipping invalid entry: {tech_full_name}")
                continue  # Skip if there's no dot (invalid entry)

            # Extract other attributes for the technology
            tech_attributes = row.drop("Technologies").dropna().to_dict()

            # Add to the dictionary, grouped by location and then technology
            if location not in technologies_dict:
                technologies_dict[location] = {}

            technologies_dict[location][tech_name] = (
                tech_attributes  # Store attributes under location -> technology
            )

        return technologies_dict

    def process_installable_capacity_sheet(sheet_data):
        """Processes the installable capacity data into a dictionary indexed by (year, location, technology)."""
        installable_capacity_dict = {}

        # Set 'Stf' (year column) as the index
        sheet_data = sheet_data.set_index("Stf")

        # Iterate over the columns (technologies and locations)
        for col in sheet_data.columns:
            # Each column is in the form 'technology.location' (e.g., 'solarPV.EU27')
            parts = col.split("_")
            if len(parts) < 2:
                continue  # Skip columns that don't match the expected format (i.e., 'tech.location')

            tech = parts[1]  # Extract technology (e.g., "solarPV")
            location = parts[0]  # Extract location (e.g., "EU27")

            # Iterate over the rows (years) for each column
            for year, value in sheet_data[col].items():
                # Store the value in the dictionary as (year, location, technology) : capacity value
                installable_capacity_dict[(year, location, tech)] = value

        return installable_capacity_dict

    def process_dcr_sheet(sheet_data):
        """Processes the DCR (depreciation cost rate) data into a dictionary indexed by (year, location, technology)."""
        dcr_dict = {}

        # Set 'Stf' (year column) as the index
        sheet_data = sheet_data.set_index("Stf")

        # Iterate over the columns (technologies and locations)
        for col in sheet_data.columns:
            # Each column is in the form 'technology.location' (e.g., 'solarPV.EU27')
            parts = col.split("_")
            if len(parts) < 2:
                continue  # Skip columns that don't match the expected format (i.e., 'tech.location')

            tech = parts[1]  # Extract technology (e.g., "solarPV")
            location = parts[0]  # Extract location (e.g., "EU27")

            # Iterate over the rows (years) for each column
            for year, value in sheet_data[col].items():
                # Store the value in the dictionary as (year, location, technology) : dcr value
                dcr_dict[(year, location, tech)] = value

        return dcr_dict

    def process_stocklvl_sheet(sheet_data):
        """Processes the stock level data into a dictionary indexed by (year, location, technology)."""
        stocklvl_dict = {}

        # Set 'Stf' (year column) as the index
        sheet_data = sheet_data.set_index("Stf")

        # Iterate over the columns (technologies and locations)
        for col in sheet_data.columns:
            # Each column is in the form 'technology.location' (e.g., 'solarPV.EU27')
            parts = col.split("_")
            if len(parts) < 2:
                continue  # Skip columns that don't match the expected format (i.e., 'tech.location')

            tech = parts[1]  # Extract technology (e.g., "solarPV")
            location = parts[0]  # Extract location (e.g., "EU27")

            # Iterate over the rows (years) for each column
            for year, value in sheet_data[col].items():
                # Store the value in the dictionary as (year, location, technology) : stock level value
                stocklvl_dict[(year, location, tech)] = value

        return stocklvl_dict

    def process_loadfactors_sheet(sheet_data):
        """
        Processes load factor data into a dictionary indexed by
        (timestep, location, technology).

        Assumes the CSV has:
          - column 't' for timesteps
          - other columns in the form 'location_technology' (e.g., 'EU27_solarPV')
        """
        loadfactors_dict = {}

        # Ensure 't' exists
        if "t" not in sheet_data.columns:
            raise ValueError("Sheet must contain 't' column for timesteps")

        # Set 't' as index
        sheet_data = sheet_data.set_index("t")

        # Iterate over location_tech columns
        for col in sheet_data.columns:
            parts = col.split("_")
            if len(parts) < 2:
                continue  # skip invalid columns

            location, tech = parts[0], parts[1]

            # Fill dictionary for all timesteps
            for timestep, value in sheet_data[col].items():
                loadfactors_dict[(timestep, location, tech)] = value

        return loadfactors_dict

    def process_gas_block_sheet(sheet_data):
        """
        Reads gas blocks with yearly variation.
        Returns:
            - set of all block names
            - block_limits dict keyed by (stf, block_name)
            - block_prices dict keyed by (stf, block_name)
        """
        block_limits = {}
        block_prices = {}
        required_cols = ["stf", "block", "limit", "price"]
        for col in required_cols:
            if col not in sheet_data.columns:
                raise ValueError(f"Gas block sheet must have column '{col}'")

        sheet_data["stf"] = sheet_data["stf"].ffill().astype(int)
        block_names = set(sheet_data["block"].astype(str).unique())
        for _, row in sheet_data.iterrows():
            stf = row["stf"]
            block = str(row["block"])
            block_limits[(stf, block)] = float(row["limit"])
            block_prices[(stf, block)] = float(row["price"])

        print(block_limits)
        return block_names, block_limits, block_prices

    def load_data_from_excel(file_path):
        """Loads data from Excel and processes all relevant sheets."""
        # Read all sheets
        base_data = pd.read_excel(file_path, sheet_name="Base")
        cost_sheet = pd.read_excel(file_path, sheet_name="cost_sheet")
        locations_data = pd.read_excel(file_path, sheet_name="locations")
        loadfactors_data = pd.read_excel(file_path, sheet_name="loadfactors")
        technologies_data = pd.read_excel(file_path, sheet_name="Technologies")
        dcr_data = pd.read_excel(file_path, sheet_name="dcr")
        stocklvl_data = pd.read_excel(file_path, sheet_name="stocklvl")
        installable_capacity_data = pd.read_excel(
            file_path, sheet_name="installable_capacity"
        )
        gas_block_data = pd.read_excel(file_path, sheet_name="gas_block")
        # Process lng_blocks sheet
        block_names, block_limits_dict, block_price_dict = process_gas_block_sheet(
            gas_block_data
        )

        # Process Technologies sheet
        technologies_dict = process_technology_sheet(technologies_data)
        # Process the structured sheets
        stocklvl_dict = process_stocklvl_sheet(stocklvl_data)
        dcr_dict = process_dcr_sheet(dcr_data)
        installable_capacity_dict = process_installable_capacity_sheet(
            installable_capacity_data
        )
        loadfactors_dict = process_loadfactors_sheet(loadfactors_data)
        # Extract base parameters from the Base sheet
        base_params = {
            "y0": int(
                base_data.loc[base_data["Param"] == "Start Year y0", "Value"].values[0]
            ),
            "y_end": int(
                base_data.loc[base_data["Param"] == "End Year yn", "Value"].values[0]
            ),
            "hours": int(
                base_data.loc[base_data["Param"] == "hours per year", "Value"].values[0]
            ),
        }

        # Process the locations sheet: Extract non-empty values from the "Locations" column
        locations_list = locations_data.iloc[:, 0].dropna().tolist()
        # print(locations_list)

        # Process the cost sheet into import, manufacturing, and remanufacturing cost dicts
        (
            importcost_dict,
            manufacturingcost_dict,
            remanufacturingcost_dict,
            recyclingcost_dict,
            o_and_m_dict,
        ) = process_cost_sheet(cost_sheet)

        # Now we create the 'data_urbsextensionv1' dictionary to return all data
        data_urbsextensionv1 = {
            "base_params": base_params,
            "importcost_dict": importcost_dict,
            "manufacturingcost_dict": manufacturingcost_dict,
            "remanufacturingcost_dict": remanufacturingcost_dict,
            "recyclingcost_dict": recyclingcost_dict,
            "o_and_m_dict": o_and_m_dict,
            "locations_list": locations_list,
            "loadfactors_dict": loadfactors_dict,
            "technologies": technologies_dict,  # techs stored as dict
            "dcr_dict": dcr_dict,
            "stocklvl_dict": stocklvl_dict,
            "installable_capacity_dict": installable_capacity_dict,
            # LNG block info
            "block_limits": block_limits_dict,
            "block_price": block_price_dict,
            "block_names": block_names,
        }

        return data_urbsextensionv1

    # Load the data from the Excel file
    data_urbsextensionv1 = load_data_from_excel(
        "Input_urbsextensionv1.xlsx"
    )  # Replace with your actual file path
    # print("Technologies Dictionary:", data_urbsextensionv1["technologies"])
    # print(
    #    "Instalable Capacity Dictionary:",
    #    data_urbsextensionv1["installable_capacity_dict"],
    # )

    ### --------end of urbs-extensionv1.0 input data addition-------- ###

    data, data_urbsextensionv1 = scenario(data, data_urbsextensionv1.copy())

    # print("DATA-extension:", data_urbsextensionv1)
    validate_input(data)
    validate_dc_objective(data, objective)

    if window_start is not None and window_end is not None:
        print(f"Filtering data for the window {window_start}–{window_end}")
        data = slice_data_for_window(data, window_start, window_end, initial_conditions)
        data_urbsextensionv1 = sliced_dataurbsextensionv1(
            data_urbsextensionv1, window_start, window_end, initial_conditions
        )

        # print(initial_conditions)

    # create model
    prob = create_model(
        data,
        data_urbsextensionv1,
        dt,
        timesteps,
        objective,
        initial_conditions=initial_conditions,
        window_start=window_start,
        window_end=window_end,
        indexlist=indexlist,
    )

    # refresh time stamp string and create filename for logfile
    log_filename = os.path.join(result_dir, "{}.log").format(sce)

    # solve model and read results
    optim = SolverFactory("gurobi")  # cplex, glpk, gurobi, ...
    # optim.options['NumericFocus'] = 3
    # optim.options['ScaleFlag'] = 1
    optim = setup_solver(optim, logfile=log_filename)
    result = optim.solve(prob, tee=True)
    # assert str(result.solver.termination_condition) == "optimal"

    # solver debug

    # Check solver termination condition
    if str(result.solver.termination_condition) != "optimal":
        print(f"Solver termination condition: {result.solver.termination_condition}")

        if (
            result.solver.termination_condition
            == TerminationCondition.infeasibleOrUnbounded
        ):
            print(
                "Model is either infeasible or unbounded. Proceeding with IIS analysis..."
            )

            # Export the Pyomo model to an LP file
            lp_file_path = os.path.abspath("model.lp")
            prob.write(lp_file_path, io_options={"symbolic_solver_labels": True})
            print(f"Pyomo model written to LP file: {lp_file_path}")

            # Load the LP file into a Gurobi model
            try:
                gurobi_model = gp.read(lp_file_path)
                print("Gurobi model loaded successfully.")

                # Compute the IIS
                gurobi_model.computeIIS()

                # Write the IIS to a file
                iis_file_path = os.path.abspath("model_iis.ilp")
                gurobi_model.write(iis_file_path)
                print(f"IIS written to file: {iis_file_path}")

                # Optionally, print the IIS to the console
                print("\nConflicting constraints in the IIS:")
                for c in gurobi_model.getConstrs():
                    if c.IISConstr:
                        print(
                            f"Constraint '{c.ConstrName}': {gurobi_model.getRow(c)} {c.Sense} {c.RHS}"
                        )

                for v in gurobi_model.getVars():
                    if v.IISLB:
                        print(
                            f"Variable '{v.VarName}' has a conflicting lower bound: {v.LB}"
                        )
                    if v.IISUB:
                        print(
                            f"Variable '{v.VarName}' has a conflicting upper bound: {v.UB}"
                        )
            except Exception as e:
                print(f"Error computing IIS: {e}")
        else:
            print("Model termination condition:", result.solver.termination_condition)
    else:
        print("Model is feasible and solved to optimality.")

    # save problem solution (and input data) to HDF5 file
    save(prob, os.path.join(result_dir, "{}.h5".format(sce)))

    # write report to spreadsheet
    report(
        prob,
        os.path.join(result_dir, "{}.xlsx").format(sce),
        report_tuples=report_tuples,
        report_sites_name=report_sites_name,
    )

    # result plots
    result_figures(
        prob,
        os.path.join(result_dir, "{}".format(sce)),
        timesteps,
        plot_title_prefix=sce.replace("_", " "),
        plot_tuples=plot_tuples,
        plot_sites_name=plot_sites_name,
        periods=plot_periods,
        figure_size=(24, 9),
    )

    return prob


def slice_data_for_window(data, window_start, window_end, initial_conditions):
    """
    Slice the input data dictionary for the specified rolling horizon window.
    Ensure rows outside the `window_start` and `window_end` range are removed.
    Handle cases where only specific columns (e.g., `cap-up`) have values.
    """
    sliced_data = {}

    for key, value in data.items():
        print(f"\nProcessing key: {key}")
        if isinstance(value, pd.DataFrame):
            if "support_timeframe" in value.index.names:
                # Sort the MultiIndex to avoid UnsortedIndexError
                value = value.sort_index()

                # Slicing by index
                print("Slicing by index...")
                sliced_df = value.loc[window_start:window_end]
            else:
                print(
                    f"Warning: `support_timeframe` not found in index for '{key}'. Skipping slicing."
                )
                sliced_data[key] = value
                continue

            # Special handling for `process`: drop rows with only `cap-up` containing values
            if key == "process":
                sliced_df = sliced_df[
                    sliced_df.drop(columns=["cap-up"], errors="ignore")
                    .notna()
                    .any(axis=1)
                ]
                print(sliced_df.index.get_level_values("Process"))
                tech_to_update = [
                    "Biomass Plant",
                    "Coal CCUS",
                    "Coal Lignite",
                    "Coal Lignite CCUS",
                    "Coal Plant",
                    "Gas Plant (CCGT)",
                    "Gas Plant (CCGT) CCUS",
                    "Hydro (reservoir)",
                    "Hydro (run-of-river)",
                    "Nuclear Plant",
                    "Gas Plant (CCGT) LNG",
                ]

                hardcoded_lifetimes = {
                    "Biomass Plant": 25,
                    "Coal CCUS": 40,
                    "Coal Lignite": 5,
                    "Coal Lignite CCUS": 40,
                    "Coal Plant": 5,
                    "Gas Plant (CCGT)": 25,
                    "Gas Plant (CCGT) CCUS": 25,
                    "Hydro (reservoir)": 50,
                    "Hydro (run-of-river)": 50,
                    "Nuclear Plant": 60,
                    "Gas Plant (CCGT) LNG": 25,
                }

                hardcoded_cap_init = {
                    "Biomass Plant": 20420,
                    "Gas Plant (CCGT)": 132230,
                    "Gas Plant (CCGT) LNG": 56670,
                }

                # Define the very first model year for lifetime offset
                first_model_year = 2024  # ← Adjust this if needed
                elapsed_years = 5  # TODO change for different rolling window

                if initial_conditions is not None:
                    # Filter initial_conditions to only include relevant technologies
                    filtered_installed_capacity = {
                        tech: initial_conditions["Installed_Capacity_Q_s"].get(
                            ("EU27", tech), 0
                        )
                        for tech in tech_to_update
                    }
                    print(
                        "filtered_installed_capacity (before adjustment):",
                        filtered_installed_capacity,
                    )

                    # Adjust capacities based on degradation for the 3 hardcoded techs
                    for tech in hardcoded_cap_init:
                        if tech in filtered_installed_capacity:
                            original_capacity = filtered_installed_capacity[tech]

                            if (
                                window_start == 2029
                            ):  # Subtract half of hardcoded capacity
                                degradation_amount = hardcoded_cap_init[tech] * 0.5
                                filtered_installed_capacity[tech] = (
                                    original_capacity - degradation_amount
                                )
                                print(
                                    f"2029 - {tech}: {original_capacity} - {degradation_amount} = {filtered_installed_capacity[tech]}"
                                )

                            elif (
                                window_start == 2034
                            ):  # Subtract all hardcoded capacity (full degradation)
                                degradation_amount = hardcoded_cap_init[tech]
                                filtered_installed_capacity[tech] = (
                                    original_capacity * 0.5
                                ) - degradation_amount
                                print(
                                    f"2034 - {tech}: {original_capacity} - {degradation_amount} = {filtered_installed_capacity[tech]}"
                                )

                            # Ensure capacity doesn't go negative
                            if filtered_installed_capacity[tech] < 0:
                                print(
                                    f"Warning: {tech} capacity went negative, setting to 0"
                                )
                                filtered_installed_capacity[tech] = 0

                    print(
                        "filtered_installed_capacity (after adjustment):",
                        filtered_installed_capacity,
                    )

                    for tech, capacity in filtered_installed_capacity.items():
                        tech_key = (
                            f"EU27.{tech}"  # Construct the key for the technology
                        )

                        # Check if the technology exists in the 'process' dataframe index for the window_start year
                        if tech in sliced_df.index.get_level_values("Process"):
                            # Filter the rows for the specific window_start year and the specific technology
                            rows_to_update = sliced_df.loc[
                                (
                                    sliced_df.index.get_level_values(
                                        "support_timeframe"
                                    )
                                    == window_start
                                )
                                & (sliced_df.index.get_level_values("Process") == tech)
                            ]

                            # If no rows for the technology at window_start, create them
                            if rows_to_update.empty:
                                print(
                                    f"No rows found for {tech_key} at year {window_start}. Creating a new row..."
                                )
                                # Create a new row for the missing tech at the window_start year
                                new_row = pd.DataFrame(
                                    {
                                        "inst-cap": [capacity]
                                    },  # Set the inst-cap value from adjusted filtered_installed_capacity
                                    index=pd.MultiIndex.from_tuples(
                                        [(window_start, "EU27", tech)],
                                        names=["support_timeframe", "Site", "Process"],
                                    ),
                                )
                                # Add this row to the sliced_df DataFrame
                                sliced_df = pd.concat([sliced_df, new_row])

                            # Now update the 'inst-cap' column for the filtered rows (if found)
                            sliced_df.loc[rows_to_update.index, "inst-cap"] = capacity
                            print(
                                f"Updated {tech_key} inst-cap to {capacity} for {window_start}"
                            )  # Debugging statement
                        else:
                            print(
                                f"{tech_key} not found in the 'process' DataFrame."
                            )  # Debugging statement

                    for tech, base_lifetime in hardcoded_lifetimes.items():
                        tech_key = f"EU27.{tech}"
                        adjusted_lifetime = max(base_lifetime - elapsed_years, 0)

                        if tech in sliced_df.index.get_level_values("Process"):
                            lifetime_rows = sliced_df.loc[
                                (
                                    sliced_df.index.get_level_values(
                                        "support_timeframe"
                                    )
                                    == window_start
                                )
                                & (sliced_df.index.get_level_values("Process") == tech)
                            ]

                            if lifetime_rows.empty:
                                new_lifetime_row = pd.DataFrame(
                                    {"lifetime": [adjusted_lifetime]},
                                    index=pd.MultiIndex.from_tuples(
                                        [(window_start, "EU27", tech)],
                                        names=["support_timeframe", "Site", "Process"],
                                    ),
                                )
                                sliced_df = pd.concat([sliced_df, new_lifetime_row])
                                print(
                                    f"Added lifetime for {tech_key} at {window_start}: {adjusted_lifetime}"
                                )
                            else:
                                sliced_df.loc[lifetime_rows.index, "lifetime"] = (
                                    adjusted_lifetime
                                )
                                print(
                                    f"Updated lifetime for {tech_key} at {window_start}: {adjusted_lifetime}"
                                )

                    non_first_years = (
                        sliced_df.index.get_level_values("support_timeframe")
                        != window_start
                    )
                    cols_to_clean = ["inst-cap", "lifetime"]

                    for col in cols_to_clean:
                        if col in sliced_df.columns:
                            sliced_df.loc[non_first_years, col] = np.nan

                    required_cols = [
                        "area-per-cap"
                    ]  # Add other required columns here if needed
                    cols_to_keep = [
                        col
                        for col in sliced_df.columns
                        if col in required_cols or not sliced_df[col].isna().all()
                    ]
                    sliced_df = sliced_df[cols_to_keep]
            # Assign weight = 1 for the last year in the rolling horizon if missing
            if key == "global_prop":  # Adjust this key if needed
                co2_limit_mask = (
                    sliced_df.index.get_level_values("support_timeframe").isin(
                        range(window_start, window_end + 1)
                    )
                ) & (sliced_df.index.get_level_values("Property") == "CO2 limit")

                if co2_limit_mask.any():
                    sliced_df.loc[co2_limit_mask, "value"] = float(
                        "inf"
                    )  # or 9999999999 or any other large number
                    print(f"Set CO2 limit to inf for years {window_start}–{window_end}")

                # Add Discount Rate = 0.03 for window_start year
                if (
                    "Discount rate" not in sliced_df.index.get_level_values("Property")
                ) and (
                    window_start
                    in sliced_df.index.get_level_values("support_timeframe")
                ):
                    # Create a new row for 'Discount Rate' at the window_start year
                    new_discount_row = pd.DataFrame(
                        {"value": [0.03]},  # Set Discount Rate to 0.03
                        index=pd.MultiIndex.from_tuples(
                            [(window_start, "Discount rate")],
                            names=sliced_df.index.names,
                        ),
                    )
                    # Append the new Discount Rate row to the DataFrame
                    sliced_df = pd.concat([sliced_df, new_discount_row])
                # Add CO2 budget = infinity for window_start year
                if (
                    "CO2 budget" not in sliced_df.index.get_level_values("Property")
                ) and (
                    window_start
                    in sliced_df.index.get_level_values("support_timeframe")
                ):
                    # Create a new row for 'CO2 budget' at the window_start year
                    new_co2_budget_row = pd.DataFrame(
                        {
                            "value": [float("inf")]
                        },  # Set CO2 budget to infinity as string
                        index=pd.MultiIndex.from_tuples(
                            [(window_start, "CO2 budget")],
                            names=sliced_df.index.names,
                        ),
                    )
                    # Append the new CO2 budget row to the DataFrame
                    sliced_df = pd.concat([sliced_df, new_co2_budget_row])

            elif key == "commodity":
                # Get scenario-specific prices
                scenario_prices = read_scenario_prices(window_start)

                # Update Piped Gas prices
                for year, price in scenario_prices["piped_gas"].items():
                    if window_start <= year <= window_end:
                        gas_mask = (
                            (
                                sliced_df.index.get_level_values("support_timeframe")
                                == year
                            )
                            & (sliced_df.index.get_level_values("Site") == "EU27")
                            & (
                                sliced_df.index.get_level_values("Commodity")
                                == "Piped Gas"
                            )
                            & (sliced_df.index.get_level_values("Type") == "Stock")
                        )
                        if gas_mask.any():
                            sliced_df.loc[gas_mask, "price"] = price
                            # Keep existing max and maxperhour values
                            print(f"Updated Piped Gas price for {year} to {price}")
                        else:
                            # Create new row if it doesn't exist, with max=319200000 for Piped Gas
                            new_gas_row = pd.DataFrame(
                                {
                                    "price": [price],
                                    "max": [
                                        319200000.0
                                    ],  # Specific max value for Piped Gas
                                    "maxperhour": [float("inf")],
                                },
                                index=pd.MultiIndex.from_tuples(
                                    [(year, "EU27", "Piped Gas", "Stock")],
                                    names=[
                                        "support_timeframe",
                                        "Site",
                                        "Commodity",
                                        "Type",
                                    ],
                                ),
                            )
                            sliced_df = pd.concat([sliced_df, new_gas_row])
                            print(
                                f"Added new Piped Gas price entry for {year}: {price}"
                            )
            # Debug: Print the resulting DataFrame for verification
            print(f"Sliced DataFrame for '{key}':\n{sliced_df}")

            # Add the sliced DataFrame back to the dictionary
            sliced_data[key] = sliced_df
        else:
            # If the value is not a DataFrame, keep it as is
            sliced_data[key] = value

    return sliced_data


# Global variable to track cumulative secondary capacities
cumulative_secondary_caps = defaultdict(float)


def read_scenario_prices(window_start):
    """Read scenario-specific prices for the given window start year."""
    scenario_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "scenario_specific_data.xlsx"
    )
    print(f"\nReading scenario prices for window_start: {window_start}")
    print(f"Looking for file: {scenario_file}")

    try:
        # Read the separate price sheets
        import_prices = pd.read_excel(
            scenario_file, sheet_name="import_prices", index_col="Stf"
        )
        manufacturing_prices = pd.read_excel(
            scenario_file, sheet_name="manufacturing_prices", index_col="Stf"
        )
        piped_gas_prices = pd.read_excel(
            scenario_file, sheet_name="piped_gas_prices", index_col="Stf"
        )

        # Print available columns for debugging
        print("\nAvailable columns in each sheet:")
        print("Import prices columns:", import_prices.columns.tolist())
        print("Manufacturing prices columns:", manufacturing_prices.columns.tolist())
        print("Piped gas prices columns:", piped_gas_prices.columns.tolist())

        # Define the technologies we want to track
        technologies = ["solarPV", "windon", "windoff", "Batteries"]

        # Get the correct column names based on window_start
        gas_col = f"piped_gas_{window_start}"

        print(f"\nLooking for price columns for window_start {window_start}")

        result = {
            "tech_prices": {},
            "piped_gas": piped_gas_prices[gas_col].to_dict()
            if gas_col in piped_gas_prices
            else {},
        }

        # Process each technology's import and manufacturing prices
        for tech in technologies:
            import_col = f"import_EU27_{tech}_{window_start}"
            manufacturing_col = f"manufacturing_EU27_{tech}_{window_start}"

            result["tech_prices"][tech] = {
                "import": import_prices[import_col].to_dict()
                if import_col in import_prices
                else {},
                "manufacturing": manufacturing_prices[manufacturing_col].to_dict()
                if manufacturing_col in manufacturing_prices
                else {},
            }
            print(f"Processed prices for {tech}")
            print(f"  Import column: {import_col}")
            print(f"  Manufacturing column: {manufacturing_col}")

        return result

    except FileNotFoundError:
        print(f"Warning: Could not find scenario file: {scenario_file}")
        return {"tech_prices": {}, "lng": {}, "piped_gas": {}}
    except Exception as e:
        print(f"Error reading scenario prices: {str(e)}")
        return {"tech_prices": {}, "lng": {}, "piped_gas": {}}


def sliced_dataurbsextensionv1(
    data_urbsextensionv1, window_start, window_end, initial_conditions
):
    """
    Update the DATA-extension dictionary for the current rolling horizon window.

    Args:
        data_urbsextensionv1 (dict): The original DATA-extension dictionary.
        window_start (int): Start year of the rolling horizon window.
        window_end (int): End year of the rolling horizon window.

    Returns:
        dict: The updated DATA-extension dictionary.
    """
    # Update the base_params to reflect the current rolling horizon window
    data_urbsextensionv1["base_params"]["y0"] = window_start
    data_urbsextensionv1["base_params"]["y_end"] = window_end

    # Calculate time period
    time_period = window_end - window_start

    tech_to_update = [
        "solarPV",
        "windoff",
        "windon",
        "Batteries",
    ]  # List of technologies to update
    print(data_urbsextensionv1["technologies"])

    # If initial_conditions is not None, then update the capacities, stockpiles, and decommissions
    if initial_conditions is not None:
        # Filter initial_conditions to only include relevant technologies

        filtered_installed_capacity = {
            tech: initial_conditions["Installed_Capacity_Q_s"].get(("EU27", tech), 0)
            for tech in tech_to_update
        }

        filtered_stockpile = {
            tech: initial_conditions["Existing_Stock_Q_stock"].get(("EU27", tech), 0)
            for tech in tech_to_update
        }

        filtered_capacity_dec_start = {
            tech: initial_conditions["capacity_dec_start"].get(("EU27", tech), 0)
            for tech in tech_to_update
        }

        filtered_cumulative_sec_start = {
            tech: initial_conditions["Total Cap Sec"].get(("EU27", tech), 0)
            for tech in tech_to_update
        }
        filtered_cumulativ_fac_start = {
            tech: initial_conditions["Total Cap Fac"].get(("EU27", tech), 0)
            for tech in tech_to_update
        }

        filtered_pricereduction_sec_start = {
            tech: initial_conditions["Pricereduction"].get(("EU27", tech), 0)
            for tech in tech_to_update
        }

        filtered_cap_prim_prior_start = {
            tech: initial_conditions["capacity_ext_euprimary"].get(("EU27", tech), 0)
            for tech in tech_to_update
        }

        filtered_cap_sec_prior_start = {
            tech: initial_conditions["capacity_facility_eusecondary"].get(
                ("EU27", tech), 0
            )
            for tech in tech_to_update
        }

        filtered_cap_scrao_total_start = {
            tech: initial_conditions["Total_Scrap"].get(("EU27", tech), 0)
            for tech in tech_to_update
        }

        # Update technologies_dict with filtered values
        for tech in tech_to_update:
            tech_key = tech
            # Access the technology's information within the 'EU27' dictionary
            if tech_key in data_urbsextensionv1["technologies"]["EU27"]:
                # Get current values before update
                current_capacity = data_urbsextensionv1["technologies"]["EU27"][
                    tech_key
                ].get("InitialCapacity", "Not Set")
                current_stockpile = data_urbsextensionv1["technologies"]["EU27"][
                    tech_key
                ].get("InitialStockpile", "Not Set")
                current_decommission = data_urbsextensionv1["technologies"]["EU27"][
                    tech_key
                ].get("Initial_decommisions", "Not Set")
                current_cumulative_sec = data_urbsextensionv1["technologies"]["EU27"][
                    tech_key
                ].get("Initial_secondary_cap", "Not Set")

                current_cumulative_fac = data_urbsextensionv1["technologies"]["EU27"][
                    tech_key
                ].get("total_facility_cap_initial", "Not Set")

                current_pricereduction_sec = data_urbsextensionv1["technologies"][
                    "EU27"
                ][tech_key].get("price_reduction_init", "Not Set")

                current_capacity_ext_euprimary = data_urbsextensionv1["technologies"][
                    "EU27"
                ][tech_key].get("last_prim_cap", "Not Set")
                current_capacity_ext_eusecondary = data_urbsextensionv1["technologies"][
                    "EU27"
                ][tech_key].get("last_sec_cap", "Not Set")

                current_scrap_total = data_urbsextensionv1["technologies"]["EU27"][
                    tech_key
                ].get("capacity_scrap_total", "Not Set")

                current_lifetime = data_urbsextensionv1["technologies"]["EU27"][
                    tech_key
                ].get("l", "Not Set")
                time_period = 5  # TODO change window size if intervall is changed
                new_lifetime = max(current_lifetime - time_period, 1)  # Ensure ≥1
                data_urbsextensionv1["technologies"]["EU27"][tech_key]["l"] = (
                    new_lifetime
                )

                # Update InitialCapacity
                new_capacity = filtered_installed_capacity.get(tech, 0)
                data_urbsextensionv1["technologies"]["EU27"][tech_key][
                    "InitialCapacity"
                ] = new_capacity

                # Update InitialStockpile
                new_stockpile = filtered_stockpile.get(tech, 0)
                data_urbsextensionv1["technologies"]["EU27"][tech_key][
                    "InitialStockpile"
                ] = new_stockpile

                # Update Initial_decommissions
                new_decommission = filtered_capacity_dec_start.get(tech, 0)
                data_urbsextensionv1["technologies"]["EU27"][tech_key][
                    "Initial_decommisions"
                ] = new_decommission

                new_cap_cumulative = filtered_cumulative_sec_start.get(tech, 0)
                data_urbsextensionv1["technologies"]["EU27"][tech_key][
                    "Initial_secondary_cap"
                ] = new_cap_cumulative

                new_fac_cumulative = filtered_cumulativ_fac_start.get(tech, 0)
                data_urbsextensionv1["technologies"]["EU27"][tech_key][
                    "total_facility_cap_initial"
                ] = new_fac_cumulative

                new_pricereduction = filtered_pricereduction_sec_start.get(tech, 0)
                data_urbsextensionv1["technologies"]["EU27"][tech_key][
                    "price_reduction_init"
                ] = new_pricereduction

                new_last_prim_cap = filtered_cap_prim_prior_start.get(tech, 0)
                data_urbsextensionv1["technologies"]["EU27"][tech_key][
                    "last_prim_cap"
                ] = new_last_prim_cap

                new_last_sec_cap = filtered_cap_sec_prior_start.get(tech, 0)
                data_urbsextensionv1["technologies"]["EU27"][tech_key][
                    "last_sec_cap"
                ] = new_last_sec_cap

                new_cap_scrap_total = filtered_cap_scrao_total_start.get(tech, 0)
                data_urbsextensionv1["technologies"]["EU27"][tech_key][
                    "capacity_scrap_total"
                ] = new_cap_scrap_total

                # Print the updates
                print(f"Updated {tech_key}:")
                print(f"  InitialCapacity: {current_capacity} -> {new_capacity}")
                print(f"  InitialStockpile: {current_stockpile} -> {new_stockpile}")
                print(
                    f"  Initial_decommisions: {current_decommission} -> {new_decommission}"
                )
                print(
                    f"  Initial_secondary_cap: {current_cumulative_sec} -> {new_cap_cumulative}"
                )
                print(
                    f"  Initial_secondary_fac: {current_cumulative_fac} -> {new_fac_cumulative}"
                )
                print(
                    f"  price_reduction_init: {current_pricereduction_sec} -> {new_pricereduction}"
                )
                print(
                    f"  last_prim_cap: {current_capacity_ext_euprimary} -> {new_last_prim_cap}"
                )
                print(
                    f"  last_sec_cap: {current_capacity_ext_eusecondary} -> {new_last_sec_cap}"
                )
                print(f"  scrap_total: {current_scrap_total} -> {new_cap_scrap_total}")

                print(f" lifetimes: {current_lifetime} -> {new_lifetime}")
            else:
                print(
                    f"Technology {tech_key} not found in data_urbsextensionv1['technologies']['EU27']."
                )

    # Read scenario-specific prices for this window
    scenario_prices = read_scenario_prices(window_start)

    # Debug print before updating
    print("\n=== Debug Costs Before Update ===")
    print("Window:", window_start, "to", window_end)

    # Update costs with scenario-specific prices
    print("\n=== Updating Costs ===")

    # Update technology prices (both import and manufacturing)
    for tech, prices in scenario_prices["tech_prices"].items():
        # Update import costs
        for year, import_price in prices["import"].items():
            if window_start <= year <= window_end:
                key = (year, "EU27", tech)
                old_price = data_urbsextensionv1["importcost_dict"].get(key, "not set")
                data_urbsextensionv1["importcost_dict"][key] = import_price
                print(
                    f"Updated {tech} import price for {year}: {old_price} -> {import_price}"
                )

        # Update manufacturing costs
        for year, manufacturing_price in prices["manufacturing"].items():
            if window_start <= year <= window_end:
                key = (year, "EU27", tech)
                old_price = data_urbsextensionv1["manufacturingcost_dict"].get(
                    key, "not set"
                )
                data_urbsextensionv1["manufacturingcost_dict"][key] = (
                    manufacturing_price
                )
                print(
                    f"Updated {tech} manufacturing price for {year}: {old_price} -> {manufacturing_price}"
                )

    print("\n=== Debug Costs After Update ===")
    print("Updated cost entries for this window:")
    print("\nImport costs:")
    for key, value in data_urbsextensionv1["importcost_dict"].items():
        if window_start <= key[0] <= window_end:
            print(f"  {key}: {value}")
    print("\nManufacturing costs:")
    for key, value in data_urbsextensionv1["manufacturingcost_dict"].items():
        if window_start <= key[0] <= window_end:
            print(f"  {key}: {value}")

    # Continue with existing filtering
    data_urbsextensionv1["importcost_dict"] = {
        key: value
        for key, value in data_urbsextensionv1["importcost_dict"].items()
        if window_start <= key[0] <= window_end
    }
    data_urbsextensionv1["manufacturingcost_dict"] = {
        key: value
        for key, value in data_urbsextensionv1["manufacturingcost_dict"].items()
        if window_start <= key[0] <= window_end
    }
    data_urbsextensionv1["remanufacturingcost_dict"] = {
        key: value
        for key, value in data_urbsextensionv1["remanufacturingcost_dict"].items()
        if window_start <= key[0] <= window_end
    }
    data_urbsextensionv1["recyclingcost_dict"] = {
        key: value
        for key, value in data_urbsextensionv1["recyclingcost_dict"].items()
        if window_start <= key[0] <= window_end
    }
    data_urbsextensionv1["o_and_m_dict"] = {
        key: value
        for key, value in data_urbsextensionv1["o_and_m_dict"].items()
        if window_start <= key[0] <= window_end
    }
    data_urbsextensionv1["loadfactors_dict"] = {
        key: value
        for key, value in data_urbsextensionv1["loadfactors_dict"].items()
        if window_start <= key[1] <= window_end
    }
    data_urbsextensionv1["dcr_dict"] = {
        key: value
        for key, value in data_urbsextensionv1["dcr_dict"].items()
        if window_start <= key[0] <= window_end
    }
    data_urbsextensionv1["stocklvl_dict"] = {
        key: value
        for key, value in data_urbsextensionv1["stocklvl_dict"].items()
        if window_start <= key[0] <= window_end
    }

    data_urbsextensionv1["installable_capacity_dict"] = {
        key: value
        for key, value in data_urbsextensionv1["installable_capacity_dict"].items()
        if window_start <= key[0] <= window_end
    }
    # Debug: Print updated data for verification
    print("\n--- Debugging sliced_dataurbsextensionv1 ---")
    print("Base Params (y0, y_end):", data_urbsextensionv1["base_params"])
    print("Sample importcost_dict entries:")
    for i, (k, v) in enumerate(data_urbsextensionv1["importcost_dict"].items()):
        print(f"  {k}: {v}")
        if i >= 4:  # Print only the first 5 entries
            break
    print("Sample manufacturingcost_dict entries:")
    for i, (k, v) in enumerate(data_urbsextensionv1["manufacturingcost_dict"].items()):
        print(f"  {k}: {v}")
        if i >= 4:
            break
    print("Sample remanufacturingcost_dict entries:")
    for i, (k, v) in enumerate(
        data_urbsextensionv1["remanufacturingcost_dict"].items()
    ):
        print(f"  {k}: {v}")
        if i >= 4:
            break
    print("Sample recyclingcost_dict entries:")
    for i, (k, v) in enumerate(data_urbsextensionv1["recyclingcost_dict"].items()):
        print(f"  {k}: {v}")
        if i >= 4:
            break
    print("Sample loadfactors_dict entries:")
    for i, (k, v) in enumerate(data_urbsextensionv1["loadfactors_dict"].items()):
        print(f"  {k}: {v}")
        if i >= 4:
            break
    print("Sample dcr_dict entries:")
    for i, (k, v) in enumerate(data_urbsextensionv1["dcr_dict"].items()):
        print(f"  {k}: {v}")
        if i >= 4:
            break
    print("Sample stocklvl_dict entries:")
    for i, (k, v) in enumerate(data_urbsextensionv1["stocklvl_dict"].items()):
        print(f"  {k}: {v}")
        if i >= 4:
            break
    print("Sample instalable capacity entries:")
    for i, (k, v) in enumerate(
        data_urbsextensionv1["installable_capacity_dict"].items()
    ):
        print(f"  {k}: {v}")
        if i >= 4:
            break
    print("--- End Debugging ---\n")

    # Return the updated data
    return data_urbsextensionv1
