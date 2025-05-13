import pandas as pd
from .input import get_input
from .pyomoio import get_entity, get_entities
from .util import is_string


def get_constants(instance):
    """Return summary DataFrames for important variables

    Usage:
        costs, cpro, ctra, csto = get_constants(instance)

    Args:
        instance: an urbs model instance

    Returns:
        (costs, cpro, ctra, csto) tuple

    Example:
        >>> import pyomo.environ
        >>> from pyomo.opt.base import SolverFactory
        >>> data = read_excel('mimo-example.xlsx')
        >>> prob = create_model(data, range(1,25))
        >>> optim = SolverFactory('glpk')
        >>> result = optim.solve(prob)
        >>> cap_pro = get_constants(prob)[1]['Total']
        >>> cap_pro.xs('Wind park', level='Process').apply(int)
        Site
        Mid      13000
        North    23258
        South        0
        Name: Total, dtype: int64
    """

    costs = get_entity(instance, "costs")
    cpro = get_entities(instance, ["cap_pro", "cap_pro_new"])
    # print("cpro", cpro)
    ctra = get_entities(instance, ["cap_tra", "cap_tra_new"])
    csto = get_entities(
        instance, ["cap_sto_c", "cap_sto_c_new", "cap_sto_p", "cap_sto_p_new"]
    )
    inst_processes_time = get_entities(instance, ["inst_pro_tuples"])

    ##########################################################################
    #                                                                        #
    # Handling of extra report df for better Display of Results and Plotting #
    #                                                                        #
    ##########################################################################
    ####gather BD df to see if it works 13. january 2025
    decisionvalues_pri = get_entity(instance, "BD_pri")
    # print(decisionvalues_pri)
    decisionvalues_sec = get_entity(instance, "BD_sec")
    # print(decisionvalues_sec)
    pricereduction_sec = get_entity(instance, "pricereduction_sec")
    #print(pricereduction_sec)
    capacityprimary = get_entity(instance, "capacity_ext_euprimary")
    # print(capacityprimary)
    # Print the values of BD
    # print("Decision variable values for BD:")
    # for stf in m.stf:
    #    for n in m.nsteps:
    #        print(f"BD[{stf}, {n}] = {m.BD[stf, n].value}")

    ####Gather all relevant urbs-ext df's

    process_cost = get_entity(instance, "process_costs")
    # print("process cost", process_cost)
    ext_costs = get_entity(instance, "costs_new")
    # print("ext_cost", ext_costs)
    cext = get_entities(
        instance,
        [
            "capacity_ext_imported",
            "capacity_ext_stockout",
            "capacity_ext_euprimary",
            "capacity_ext_eusecondary",
            "capacity_ext_stock",
            "capacity_ext_stock_imported",
        ],
    )
    # print("cext", cext)
    secondary_cap_df = get_entities(instance, ["capacity_ext_eusecondary"])
    secondary_cap_df.sort_values("stf").groupby(
        ["location", "tech"], as_index=False
    ).last()
    # Compute cumulative sum per (location, tech)
    secondary_cap_df["cumulative"] = secondary_cap_df.groupby(["location", "tech"])[
        "capacity_ext_eusecondary"
    ].cumsum()
    print(secondary_cap_df)

    bext = get_entity(instance, "balance_ext")
    # print("bext", bext)
    yearly_cost_ext = get_entities(
        instance,
        [
            "costs_ext_import",
            "costs_ext_storage",
            "costs_EU_primary",
            "costs_EU_secondary",
        ],
    )
    # print("yearly ext cost", yearly_cost_ext)
    capacity_ext_total = get_entity(instance, "capacity_ext")
    # print("capacity ext total", capacity_ext_total)
    e_pro_out_df = get_entity(instance, "e_pro_out")
    e_pro_in_df = get_entity(instance, "e_pro_in")
    df_e_pro_in_grouped = (
        e_pro_in_df.groupby(["stf", "sit", "pro", "com"]).sum().reset_index()
    )

    # print("e pro out df", e_pro_out_df)
    scrapdf = get_entity(instance, "capacity_scrap_total")
    decomdf = get_entity(instance, "capacity_dec")

    #####Process df's to be used in report sheets

    ####us_co2
    e_pro_out_co2 = e_pro_out_df.loc[
        e_pro_out_df.index.get_level_values("com") == "CO2"
    ]
    co2_df = e_pro_out_co2.reset_index()
    co2_df.columns = [
        "tm",
        "stf",
        "sit",
        "pro",
        "com",
        "value",
    ]  # Rename last column for clarity
    grouped_co2 = co2_df.groupby(["stf", "sit", "pro"], as_index=False)["value"].sum()
    grouped_co2 = grouped_co2.sort_values(by=["stf", "sit", "pro"])

    ####extension_balance
    # Filter e_pro_out_df for 'Elec'
    e_pro_out_elec = {
        key: value for key, value in e_pro_out_df.items() if key[-1] == "Elec"
    }

    # Convert to DataFrame
    df_Elec = pd.DataFrame(list(e_pro_out_elec.items()), columns=["Index", "Value"])
    df_Elec["Timestep"] = df_Elec["Index"].apply(
        lambda x: x[0]
    )  # Extract timestep from the MultiIndex
    df_Elec["Stf"] = df_Elec["Index"].apply(
        lambda x: int(x[1])
    )  # Extract year from the MultiIndex
    df_Elec["Site"] = df_Elec["Index"].apply(
        lambda x: x[2]
    )  # Extract site from the MultiIndex
    df_Elec["Process"] = df_Elec["Index"].apply(
        lambda x: x[3]
    )  # Extract process from the MultiIndex

    # Drop the 'Elec' column (not needed in the final DataFrame)
    df_Elec = df_Elec.drop(columns=["Index"])

    # Process bext data
    df_bext = pd.DataFrame(bext.items(), columns=["Index", "balance_ext"])
    df_bext["Timestep"] = df_bext["Index"].apply(
        lambda x: x[0]
    )  # Extract timestep from the Index
    df_bext["Stf"] = df_bext["Index"].apply(
        lambda x: x[1]
    )  # Extract year from the Index
    df_bext["Site"] = df_bext["Index"].apply(
        lambda x: x[2]
    )  # Extract site from the Index
    df_bext["Process"] = df_bext["Index"].apply(
        lambda x: x[3]
    )  # Extract technology from the Index

    # Drop the 'Index' column (not needed in the final DataFrame)
    df_bext = df_bext.drop(columns=["Index"])

    # Create ext_process DataFrame dynamically
    ext_process_list = []
    for timestep in df_bext["Timestep"].unique():
        for year in df_bext[df_bext["Timestep"] == timestep]["Stf"].unique():
            for site in df_bext[
                (df_bext["Timestep"] == timestep) & (df_bext["Stf"] == year)
            ]["Site"].unique():
                for tech in df_bext[
                    (df_bext["Timestep"] == timestep)
                    & (df_bext["Stf"] == year)
                    & (df_bext["Site"] == site)
                ]["Process"].unique():
                    ext_process_list.append(
                        {
                            "Value": df_bext[
                                (df_bext["Timestep"] == timestep)
                                & (df_bext["Stf"] == year)
                                & (df_bext["Site"] == site)
                                & (df_bext["Process"] == tech)
                            ]["balance_ext"].values[0],
                            "Timestep": timestep,
                            "Stf": year,
                            "Site": site,
                            "Process": tech,
                        }
                    )

    ext_process = pd.DataFrame(ext_process_list)

    # Combine the data
    combined_balance = pd.concat([df_Elec, ext_process], ignore_index=True)

    # Group by 'Stf' (year)

    combined_balance = (
        combined_balance.groupby(["Stf", "Site", "Process"]).sum().reset_index()
    )
    combined_balance = combined_balance.drop(columns=["Timestep"])
    # Display the final DataFrame
    # print(combined_balance)

    ####extension_cost
    df_process = pd.DataFrame(process_cost)
    df_process_reset = df_process.reset_index()
    cost_types_to_sum = ["Invest", "Fixed", "Variable", "Fuel", "Environmental"]
    df_process_summed = (
        df_process_reset[df_process_reset["cost_type"].isin(cost_types_to_sum)]
        .groupby(["stf", "pro"])["process_costs"]
        .sum()
        .reset_index()
    )
    df_process_summed.rename(columns={"process_costs": "Total_Cost"}, inplace=True)

    df_ext_melted = yearly_cost_ext.reset_index().melt(
        id_vars=["stf", "location", "tech"],
        var_name="cost_type",
        value_name="Total_Cost",
    )

    df_ext_melted["pro"] = df_ext_melted["tech"] + "_" + df_ext_melted["cost_type"]

    cost_types_ext = [
        "costs_ext_import",
        "costs_ext_storage",
        "costs_EU_primary",
        "costs_EU_secondary",
    ]
    df_ext_melted_filtered = df_ext_melted[
        df_ext_melted["cost_type"].isin(cost_types_ext)
    ]

    cost_df_combined = pd.concat(
        [df_process_summed, df_ext_melted_filtered[["stf", "pro", "Total_Cost"]]],
        ignore_index=True,
    )
    cost_df_combined = round(
        cost_df_combined.groupby(["stf", "pro"])["Total_Cost"].sum().reset_index(), 2
    )

    ####extension_capacity
    # Extract total capacity from capacity_ext_total
    total_capacity = capacity_ext_total.reset_index()[
        ["stf", "location", "tech", "capacity_ext"]
    ]
    # Calculate newly added capacity from cext by summing relevant columns
    cext["newly_added_capacity"] = cext[
        [
            "capacity_ext_imported",
            "capacity_ext_stockout",
            "capacity_ext_euprimary",
            "capacity_ext_eusecondary",
        ]
    ].sum(axis=1)
    new_capacity = cext.reset_index()[
        ["stf", "location", "tech", "newly_added_capacity"]
    ]
    # Merge total capacity and newly added capacity on 'stf', 'location', and 'tech'
    merged_capacity = pd.merge(
        total_capacity, new_capacity, on=["stf", "location", "tech"], how="left"
    )
    merged_capacity["newly_added_capacity"] = merged_capacity[
        "newly_added_capacity"
    ].fillna(0)
    # Rename columns to match cpro structure and set index
    merged_capacity = merged_capacity.rename(
        columns={
            "stf": "stf",
            "location": "sit",
            "tech": "pro",
            "capacity_ext": "cap_pro",
            "newly_added_capacity": "cap_pro_new",
        }
    )
    merged_capacity = merged_capacity.set_index(["stf", "sit", "pro"])
    # Identify rows in merged_capacity not in cpro and concatenate them
    new_rows = merged_capacity[~merged_capacity.index.isin(cpro.index)]
    updated_cpro = pd.concat([cpro, new_rows]).sort_index()
    # Display the final updated dataframe
    # print(updated_cpro)
    ########################################################################################################################

    if not ctra.empty:
        ctra.index.names = ["Stf", "Site In", "Site Out", "Transmission", "Commodity"]
        ctra.columns = ["Total", "New"]
        ctra.sort_index(inplace=True)
    if not csto.empty:
        csto.index.names = ["Stf", "Site", "Storage", "Commodity"]
        csto.columns = ["C Total", "C New", "P Total", "P New"]
        csto.sort_index(inplace=True)

    #### Process df's to be used in report sheets

    ext_costs = ext_costs.rename("costs")
    combined_costs_df = pd.concat([costs, ext_costs], ignore_index=False)

    return (
        costs,
        cpro,
        ctra,
        csto,
        cext,
        updated_cpro,
        cost_df_combined,
        capacity_ext_total,
        grouped_co2,
        combined_balance,
        decisionvalues_pri,
        decisionvalues_sec,
        scrapdf,
        decomdf,
        inst_processes_time,
        secondary_cap_df,
        df_e_pro_in_grouped,
        pricereduction_sec
    )


def get_timeseries(instance, stf, com, sites, timesteps=None):
    """Return DataFrames of all timeseries referring to given commodity

    Usage:
        created, consumed, stored, imported, exported,
        dsm = get_timeseries(instance, commodity, sites, timesteps)

    Args:
        - instance: a urbs model instance
        - com: a commodity name
        - sites: a site name or list of site names
        - timesteps: optional list of timesteps, default: all modelled
          timesteps

    Returns:
        a tuple of (created, consumed, storage, imported, exported, dsm) with
        DataFrames timeseries. These are:

        - created: timeseries of commodity creation, including stock source
        - consumed: timeseries of commodity consumption, including demand
        - storage: timeseries of commodity storage (level, stored, retrieved)
        - imported: timeseries of commodity import
        - exported: timeseries of commodity export
        - dsm: timeseries of demand-side management
    """
    if timesteps is None:
        # default to all simulated timesteps
        timesteps = sorted(get_entity(instance, "tm").index)
    else:
        timesteps = sorted(timesteps)  # implicit: convert range to list

    if is_string(sites):
        # wrap single site name into list
        sites = [sites]

    # DEMAND
    # default to zeros if commodity has no demand, get timeseries
    try:
        # select relevant timesteps (=rows)
        # select commodity (xs), then the sites from remaining simple columns
        # and sum all together to form a Series
        demand = (
            pd.DataFrame.from_dict(get_input(instance, "demand_dict"))
            .loc[stf]
            .loc[timesteps]
            .xs(com, axis=1, level=1)[sites]
            .sum(axis=1)
        )
    except KeyError:
        demand = pd.Series(0, index=timesteps)
    demand.name = "Demand"

    # STOCK
    eco = get_entity(instance, "e_co_stock")
    try:
        eco = eco.xs((stf, com, "Stock"), level=["stf", "com", "com_type"])
        stock = eco.unstack()[sites].sum(axis=1)
    except KeyError:
        stock = pd.Series(0, index=timesteps)
    stock.name = "Stock"

    # PROCESS
    created = get_entity(instance, "e_pro_out")

    try:
        created = created.xs((stf, com), level=["stf", "com"]).loc[timesteps]
        created = created.unstack(level="sit")[sites].fillna(0).sum(axis=1)
        created = created.unstack(level="pro")
        created = drop_all_zero_columns(created)

    except KeyError:
        created = pd.DataFrame(index=timesteps[1:])

    consumed = get_entity(instance, "e_pro_in")
    try:
        consumed = consumed.xs((stf, com), level=["stf", "com"]).loc[timesteps]
        consumed = consumed.unstack(level="sit")[sites].fillna(0).sum(axis=1)
        consumed = consumed.unstack(level="pro")
        consumed = drop_all_zero_columns(consumed)
    except KeyError:
        consumed = pd.DataFrame(index=timesteps[1:])

    # TRANSMISSION
    other_sites = (
        get_input(instance, "site")
        .xs(stf, level="support_timeframe")
        .index.difference(sites)
    )

    # if commodity is transportable
    try:
        df_transmission = get_input(instance, "transmission")
        if com in set(df_transmission.index.get_level_values("Commodity")):
            imported = get_entity(instance, "e_tra_out")
            # avoid negative value import for DCPF transmissions
            if instance.mode["dpf"]:
                # -0.01 to avoid numerical errors such as -0
                minus_imported = imported[(imported < -0.01)]
                minus_imported = -1 * minus_imported.swaplevel("sit", "sit_")
                imported = imported[imported >= 0]
                imported = pd.concat([imported, minus_imported])
            imported = imported.loc[timesteps].xs((stf, com), level=["stf", "com"])
            imported = imported.unstack(level="tra").sum(axis=1)
            imported = imported.unstack(level="sit_")[sites].fillna(0).sum(axis=1)
            imported = imported.unstack(level="sit")

            internal_import = imported[sites].sum(axis=1)  # ...from sites
            if instance.mode["dpf"]:
                imported = imported[
                    [x for x in other_sites if x in imported.keys()]
                ]  # ...to existing other_sites
            else:
                imported = imported[other_sites]  # ...from other_sites
            imported = drop_all_zero_columns(imported.fillna(0))

            exported = get_entity(instance, "e_tra_in")
            # avoid negative value export for DCPF transmissions
            if instance.mode["dpf"]:
                # -0.01 to avoid numerical errors such as -0
                minus_exported = exported[(exported < -0.01)]
                minus_exported = -1 * minus_exported.swaplevel("sit", "sit_")
                exported = exported[exported >= 0]
                exported = pd.concat([exported, minus_exported])
            exported = exported.loc[timesteps].xs((stf, com), level=["stf", "com"])
            exported = exported.unstack(level="tra").sum(axis=1)
            exported = exported.unstack(level="sit")[sites].fillna(0).sum(axis=1)
            exported = exported.unstack(level="sit_")

            internal_export = exported[sites].sum(axis=1)  # ...to sites (internal)
            if instance.mode["dpf"]:
                exported = exported[
                    [x for x in other_sites if x in exported.keys()]
                ]  # ...to existing other_sites
            else:
                exported = exported[other_sites]  # ...to other_sites
            exported = drop_all_zero_columns(exported.fillna(0))
        else:
            imported = pd.DataFrame(index=timesteps)
            exported = pd.DataFrame(index=timesteps)
            internal_export = pd.Series(0, index=timesteps)
            internal_import = pd.Series(0, index=timesteps)

        # to be discussed: increase demand by internal transmission losses
        internal_transmission_losses = internal_export - internal_import
        demand = demand + internal_transmission_losses
    except KeyError:
        # imported and exported are empty
        imported = exported = pd.DataFrame(index=timesteps)

    # STORAGE
    # group storage energies by commodity
    # select all entries with desired commodity co
    stored = get_entities(instance, ["e_sto_con", "e_sto_in", "e_sto_out"])
    try:
        stored = stored.loc[timesteps].xs((stf, com), level=["stf", "com"])
        stored = stored.groupby(level=["t", "sit"]).sum()
        stored = stored.loc[(slice(None), sites), :].groupby("t").sum()
        stored.columns = ["Level", "Stored", "Retrieved"]
    except (KeyError, ValueError):
        stored = pd.DataFrame(
            0, index=timesteps, columns=["Level", "Stored", "Retrieved"]
        )

    # DEMAND SIDE MANAGEMENT (load shifting)
    dsmup = get_entity(instance, "dsm_up")
    dsmdo = get_entity(instance, "dsm_down")

    if dsmup.empty:
        # if no DSM happened, the demand is not modified (delta = 0)
        delta = pd.Series(0, index=timesteps)

    else:
        # DSM happened (dsmup implies that dsmdo must be non-zero, too)
        # so the demand will be modified by the difference of DSM up and
        # DSM down uses
        # for sit in m.dsm_site_tuples:
        try:
            # select commodity
            dsmup = dsmup.xs((stf, com), level=["stf", "com"])
            dsmdo = dsmdo.xs((stf, com), level=["stf", "com"])

            # select sites
            dsmup = dsmup.unstack()[sites].sum(axis=1)
            dsmdo = dsmdo.unstack()[sites].sum(axis=1)

            # convert dsmdo to Series by summing over the first time level
            dsmdo = dsmdo.unstack().sum(axis=0)
            dsmdo.index.names = ["t"]

            # derive secondary timeseries
            delta = dsmup - dsmdo
        except KeyError:
            delta = pd.Series(0, index=timesteps)

    shifted = demand + delta

    shifted.name = "Shifted"
    demand.name = "Unshifted"
    delta.name = "Delta"

    dsm = pd.concat((shifted, demand, delta), axis=1)

    # JOINS
    created = created.join(stock)  # show stock as created
    consumed = consumed.join(shifted.rename("Demand"))

    # VOLTAGE ANGLE of sites

    try:
        voltage_angle = get_entity(instance, "voltage_angle")
        voltage_angle = voltage_angle.xs(stf, level=["stf"]).loc[timesteps]
        voltage_angle = voltage_angle.unstack(level="sit")[sites]
    except (KeyError, AttributeError, TypeError):
        voltage_angle = pd.DataFrame(index=timesteps)
    voltage_angle.name = "Voltage Angle"

    return created, consumed, stored, imported, exported, dsm, voltage_angle


def drop_all_zero_columns(df):
    """Drop columns from DataFrame if they contain only zeros.

    Args:
        df: a DataFrame

    Returns:
        the DataFrame without columns that only contain zeros
    """
    return df.loc[:, (df != 0).any(axis=0)]
