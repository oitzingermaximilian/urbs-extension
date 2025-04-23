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
        # reference with list of option names
        # http://www.gurobi.com/documentation/5.6/reference-manual/parameters
        optim.set_options("logfile={}".format(logfile))
        # optim.set_options("timelimit=7200")  # seconds
        # optim.set_options("mipgap=5e-4")  # default = 1e-4
    elif optim.name == "glpk":
        # reference with list of options
        # execute 'glpsol --help'
        optim.set_options("log={}".format(logfile))
        # optim.set_options("tmlim=7200")  # seconds
        # optim.set_options("mipgap=.0005")
    elif optim.name == "cplex":
        optim.set_options("log={}".format(logfile))
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

    print(f"\n--- Debugging run_scenario ---")
    print(f"window_start: {window_start}, window_end: {window_end}")
    print(f"indexlist: {indexlist}")
    print("--------------------------\n")

    ### --------start of urbs-extensionv1.0 input data addition-------- ###

    def process_cost_sheet(cost_sheet):
        """Processes cost data into structured dictionaries indexed by (year, location, process)."""
        importcost_dict = {}  # Dictionary to store import costs
        manufacturingcost_dict = {}  # Dictionary to store manufacturing costs
        remanufacturingcost_dict = {}  # Dictionary to store remanufacturing costs
        recyclingcost_dict = {}

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

        return (
            importcost_dict,
            manufacturingcost_dict,
            remanufacturingcost_dict,
            recyclingcost_dict,
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
        """Processes the load factors data into a dictionary indexed by (timestep, year, location, technology)."""
        loadfactors_dict = {}

        # Ensure the sheet data has the required columns
        if "Stf" not in sheet_data.columns or "timestep" not in sheet_data.columns:
            raise ValueError(
                "Sheet data must contain 'Stf' (year) and 'Timestep' columns."
            )

        # Set 'Stf' and 'Timestep' as the index
        sheet_data = sheet_data.set_index(["Stf", "timestep"])

        # Iterate over the columns (technologies and locations)
        for col in sheet_data.columns:
            # Each column is in the form 'location_technology' (e.g., 'EU27_solarPV')
            parts = col.split("_")
            if len(parts) < 2:
                continue  # Skip columns that don't match the expected format (i.e., 'location_tech')

            location = parts[0]  # Extract location (e.g., "EU27")
            tech = parts[1]  # Extract technology (e.g., "solarPV")

            # Iterate over the rows (years and timesteps) for each column
            for (year, timestep), value in sheet_data[col].items():
                # Store the value in the dictionary as (timestep, year, location, technology) : load factor value
                loadfactors_dict[(timestep, year, location, tech)] = value
        # print(loadfactors_dict)
        return loadfactors_dict

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
        ) = process_cost_sheet(cost_sheet)

        # Now we create the 'data_urbsextensionv1' dictionary to return all data
        data_urbsextensionv1 = {
            "base_params": base_params,
            "importcost_dict": importcost_dict,
            "manufacturingcost_dict": manufacturingcost_dict,
            "remanufacturingcost_dict": remanufacturingcost_dict,
            "recyclingcost_dict": recyclingcost_dict,
            "locations_list": locations_list,
            "loadfactors_dict": loadfactors_dict,
            "technologies": technologies_dict,  # techs stored as dict
            "dcr_dict": dcr_dict,
            "stocklvl_dict": stocklvl_dict,
            "installable_capacity_dict": installable_capacity_dict,
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

    # prob_filename = os.path.join(result_dir, 'model.lp')
    # prob.write(prob_filename, io_options={'symbolic_solver_labels':True})

    # refresh time stamp string and create filename for logfile
    log_filename = os.path.join(result_dir, "{}.log").format(sce)

    # solve model and read results
    optim = SolverFactory("gurobi")  # cplex, glpk, gurobi, ...
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
                    "Coal Plant CCUS",
                    "Coal Lignite",
                    "Coal Lignite CCUS",
                    "Coal Plant",
                    "Gas Plant (CCGT)",
                    "Gas Plant (CCGT) CCUS",
                    "Hydro (reservoir)",
                    "Hydro (run-of-river)",
                    "Nuclear Plant",
                    "Wind (offshore)",
                    "Wind (onshore)",
                ]

                hardcoded_lifetimes = {
                    "Biomass Plant": 25,
                    "Coal Plant CCUS": 40,
                    "Coal Lignite": 40,
                    "Coal Lignite CCUS": 40,
                    "Coal Plant": 40,
                    "Gas Plant (CCGT)": 25,
                    "Gas Plant (CCGT) CCUS": 25,
                    "Hydro (reservoir)": 50,
                    "Hydro (run-of-river)": 50,
                    "Nuclear Plant": 60,
                    "Wind (offshore)": 25,
                    "Wind (onshore)": 25,
                }

                # Define the very first model year for lifetime offset
                first_model_year = 2024  # ← Adjust this if needed
                elapsed_years = window_start - first_model_year
                if initial_conditions is not None:
                    # Filter initial_conditions to only include relevant technologies
                    filtered_installed_capacity = {
                        tech: initial_conditions["Installed_Capacity_Q_s"].get(
                            ("EU27", tech), 0
                        )
                        for tech in tech_to_update
                    }
                    print("filtered_installed_capacity", filtered_installed_capacity)
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
                                    },  # Set the inst-cap value from filtered_installed_capacity
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
                        adjusted_lifetime = max(base_lifetime - elapsed_years, 1)

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
            # Assign weight = 1 as a row for the last year in the rolling horizon
            if key == "global_prop":  # Adjust this key if needed
                co2_limit_mask = (
                    sliced_df.index.get_level_values("support_timeframe").isin(
                        range(window_start, window_end + 1)
                    )
                ) & (sliced_df.index.get_level_values("Property") == "CO2 limit")

                if co2_limit_mask.any():
                    sliced_df.loc[co2_limit_mask, "value"] = (
                        999999999999  # or 9999999999 or any other large number
                    )
                    print(f"Set CO2 limit to inf for years {window_start}–{window_end}")

                # Ensure Weight is added as a property for the last year (window_end)
                if ("Weight" not in sliced_df.index.get_level_values("Property")) and (
                    window_end in sliced_df.index.get_level_values("support_timeframe")
                ):
                    # Create a new row for 'Weight' at the window_end year
                    new_row = pd.DataFrame(
                        {"value": [1]},  # Set Weight to 1
                        index=pd.MultiIndex.from_tuples(
                            [(window_end, "Weight")], names=sliced_df.index.names
                        ),
                    )
                    # Append the new row to the DataFrame
                    sliced_df = pd.concat([sliced_df, new_row])
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
                    # Add Discount Rate = 0.03 for window_start year
                if (
                    "CO2 budget" not in sliced_df.index.get_level_values("Property")
                ) and (
                    window_start
                    in sliced_df.index.get_level_values("support_timeframe")
                ):
                    # Create a new row for 'CO2 budget' at the window_start year
                    new_co2_budget_row = pd.DataFrame(
                        {"value": [99999999999]},  # Set CO2 budget to 4,000,000,000
                        index=pd.MultiIndex.from_tuples(
                            [(window_start, "CO2 budget")],
                            names=sliced_df.index.names,
                        ),
                    )
                    # Append the new CO2 budget row to the DataFrame
                    sliced_df = pd.concat([sliced_df, new_co2_budget_row])
                    # Add CO2 budget = 4,000,000,000 for window_start year

            # Debug: Print the resulting DataFrame for verification
            print(f"Sliced DataFrame for '{key}':\n{sliced_df}")

            # Add the sliced DataFrame back to the dictionary
            sliced_data[key] = sliced_df
        else:
            # If the value is not a DataFrame, keep it as is
            sliced_data[key] = value

    return sliced_data


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

    tech_to_update = ["solarPV", "windoff", "windon"]  # List of technologies to update
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

                # Print the updates
                print(f"Updated {tech_key}:")
                print(f"  InitialCapacity: {current_capacity} -> {new_capacity}")
                print(f"  InitialStockpile: {current_stockpile} -> {new_stockpile}")
                print(
                    f"  Initial_decommisions: {current_decommission} -> {new_decommission}"
                )
            else:
                print(
                    f"Technology {tech_key} not found in data_urbsextensionv1['technologies']['EU27']."
                )

    # Filter each dictionary based on the rolling horizon window
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
