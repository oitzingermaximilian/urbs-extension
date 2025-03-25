import math
import pyomo.core as pyomo
from datetime import datetime
from .features import *
from .input import *
from urbs.extension.scrap import apply_scrap_constraints
from urbs.extension.lr_remanufacturing import apply_rm_constraints
from urbs.extension.lr_manufacturing import apply_m_constraints
from urbs.extension.stockpile import apply_stockpiling_constraints
from urbs.extension.balance_converter import apply_balance_constraints
from urbs.extension.costs import apply_costs_constraints


def create_model(
    data, data_urbsextensionv1, dt=8760, timesteps=None, objective="cost", dual=None
):
    """Create a pyomo ConcreteModel urbs object from given input data.

    Args:
        - data: a dict of up to 12
        - dt: timestep duration in hours (default: 1)
        - timesteps: optional list of timesteps, default: demand timeseries
        - objective: Either "cost" or "CO2" for choice of objective function,
          default: "cost"
        - dual: set True to add dual variables to model output
          (marginally slower), default: True

    Returns:
        a pyomo ConcreteModel object
    """

    # Optional
    if not timesteps:
        timesteps = data["demand"].index.tolist()

    m = pyomo_model_prep(data, timesteps)  # preparing pyomo model
    m.name = "urbs"
    m.created = datetime.now().strftime("%Y%m%dT%H%M")
    m._data = data

    # Parameters

    # weight = length of year (hours) / length of simulation (hours)
    # weight scales costs and emissions from length of simulation to a full
    # year, making comparisons among cost types (invest is annualized, fixed
    # costs are annual by default, variable costs are scaled by weight) and
    # among different simulation durations meaningful.
    m.weight = pyomo.Param(
        within=pyomo.Reals,
        initialize=float(8760) / ((len(m.timesteps) - 1) * dt),
        doc="Pre-factor for variable costs and emissions for an annual result",
    )

    # dt = spacing between timesteps. Required for storage equation that
    # converts between energy (storage content, e_sto_con) and power (all other
    # quantities that start with "e_")
    m.dt = pyomo.Param(
        within=pyomo.Reals,
        initialize=730,
        doc="Time step duration (in hours), default: 1",
    )

    # import objective function information
    m.obj = pyomo.Param(
        within=pyomo.Any,
        initialize=objective,
        doc='Specification of minimized quantity, default: "cost"',
    )

    # Sets
    # ====
    # Syntax: m.{name} = Set({domain}, initialize={values})
    # where name: set name
    #       domain: set domain for tuple sets, a cartesian set product
    #       values: set values, a list or array of element tuples

    # generate ordered time step sets
    m.t = pyomo.Set(
        within=pyomo.Reals, initialize=m.timesteps, ordered=True, doc="Set of timesteps"
    )
    # m.t = pyomo.Set(initialize=range(0, 2), ordered=True, doc='Set of timesteps')
    # modelled (i.e. excluding init time step for storage) time steps
    m.tm = pyomo.Set(
        within=m.t,
        initialize=range(1, 13),
        ordered=True,
        doc="Set of modelled timesteps",
    )

    # Support timeframes (e.g. 2020, 2030...)
    indexlist = []
    for key in m.commodity_dict["price"]:
        # Convert the first element of the key to an integer
        year = int(key[0])
        if year not in indexlist:
            indexlist.append(year)

    # Create the Pyomo set
    m.stf = pyomo.Set(
        within=pyomo.Integers,  # Changed to Integers
        initialize=indexlist,
        ordered=True,
        doc="Set of modeled support timeframes (e.g. years)",
    )

    # site (e.g. north, middle, south...)

    indexlist = list()
    for key in m.commodity_dict["price"]:
        if key[1] not in indexlist:
            indexlist.append(key[1])
    m.sit = pyomo.Set(initialize=indexlist, doc="Set of sites")

    # commodity (e.g. solar, wind, coal...)
    indexlist = list()
    for key in m.commodity_dict["price"]:
        if key[2] not in indexlist:
            indexlist.append(key[2])
    m.com = pyomo.Set(initialize=indexlist, doc="Set of commodities")

    # commodity type (i.e. SupIm, Demand, Stock, Env)
    indexlist = list()
    for key in m.commodity_dict["price"]:
        if key[3] not in indexlist:
            indexlist.append(key[3])
    m.com_type = pyomo.Set(initialize=indexlist, doc="Set of commodity types")

    # process (e.g. Wind turbine, Gas plant, Photovoltaics...)
    indexlist = list()
    for key in m.process_dict["inv-cost"]:
        if key[2] not in indexlist:
            indexlist.append(key[2])
    m.pro = pyomo.Set(initialize=indexlist, doc="Set of conversion processes")

    # cost_type
    m.cost_type = pyomo.Set(
        initialize=m.cost_type_list, doc="Set of cost types (hard-coded)"
    )

    ###############################################
    # universal sets and params for extension v1.0#
    ###############################################

    # Excel read in
    base_params = data_urbsextensionv1["base_params"]
    # hard coded cost_types
    m.cost_type_new = pyomo.Set(
        initialize=m.cost_new_list, doc="Set of cost types (hard-coded)"
    )
    # Base sheet read in
    m.timesteps_ext = pyomo.Set(initialize=range(1, 13), doc="Timesteps")
    m.y0 = pyomo.Param(initialize=base_params["y0"])  # Initial year
    m.y_end = pyomo.Param(initialize=base_params["y_end"])  # End year
    m.hours = pyomo.Param(
        m.timesteps_ext, initialize=base_params["hours"]
    )  # Hours per year
    # locations sheet read in
    m.location = pyomo.Set(
        initialize=data_urbsextensionv1["locations_list"]
    )  # sites to be modelled

    # Extract all unique technologies across all locations
    all_techs = set()
    for loc in data_urbsextensionv1["technologies"]:
        all_techs.update(data_urbsextensionv1["technologies"][loc].keys())

    # Define the technology set
    m.tech = pyomo.Set(initialize=all_techs)

    #
    # Helper function to initialize parameters with default values
    def initialize_param(param_name, default_value=0):
        return {
            (loc, t): data_urbsextensionv1["technologies"]
            .get(loc, {})
            .get(t, {})
            .get(param_name, default_value)
            for loc in m.location
            for t in m.tech
        }

    # Define parameters using the helper function
    m.n = pyomo.Param(
        m.location,
        m.tech,
        initialize=initialize_param("n turnover stockpile", default_value=0),
    )  # Turnover of stockpile
    m.l = pyomo.Param(
        m.location, m.tech, initialize=initialize_param("l", default_value=0)
    )

    m.Installed_Capacity_Q_s = pyomo.Param(
        m.location,
        m.tech,
        initialize=initialize_param("InitialCapacity", default_value=0),
    )  # Initial installed capacity MW
    m.Existing_Stock_Q_stock = pyomo.Param(
        m.location,
        m.tech,
        initialize=initialize_param("InitialStockpile", default_value=0),
    )  # Initial stocked capacity
    m.FT = pyomo.Param(
        m.location, m.tech, initialize=initialize_param("FT", default_value=0)
    )  # Factor
    m.anti_dumping_index = pyomo.Param(
        m.location,
        m.tech,
        initialize=initialize_param("anti duping Index", default_value=0),
    )  # Anti-dumping index
    m.deltaQ_EUprimary = pyomo.Param(
        m.location,
        m.tech,
        initialize=initialize_param("dQ EU Primary", default_value=0),
    )  # ΔQ EU Primary
    m.deltaQ_EUsecondary = pyomo.Param(
        m.location,
        m.tech,
        initialize=initialize_param("dQ EU Secondary", default_value=0),
    )  # ΔQ EU Secondary
    m.IR_EU_primary = pyomo.Param(
        m.location,
        m.tech,
        initialize=initialize_param("IR EU Primary", default_value=0),
    )  # IR EU Primary
    m.IR_EU_secondary = pyomo.Param(
        m.location,
        m.tech,
        initialize=initialize_param("IR EU Secondary", default_value=0),
    )  # IR EU Secondary
    m.DR_primary = pyomo.Param(
        m.location, m.tech, initialize=initialize_param("DR Primary", default_value=0)
    )  # DR Primary
    m.DR_secondary = pyomo.Param(
        m.location, m.tech, initialize=initialize_param("DR Secondary", default_value=0)
    )  # DR Secondary
    m.STORAGECOST = pyomo.Param(
        m.location, m.tech, initialize=initialize_param("Storagecost", default_value=0)
    )
    m.logisticcost = pyomo.Param(
        m.location, m.tech, initialize=initialize_param("logisticcost", default_value=0)
    )

    # cost sheet read in
    m.IMPORTCOST = pyomo.Param(
        m.stf, m.location, m.tech, initialize=data_urbsextensionv1["importcost_dict"]
    )
    m.EU_primary_costs = pyomo.Param(
        m.stf,
        m.location,
        m.tech,
        initialize=data_urbsextensionv1["manufacturingcost_dict"],
    )
    m.EU_secondary_costs = pyomo.Param(
        m.stf,
        m.location,
        m.tech,
        initialize=data_urbsextensionv1["remanufacturingcost_dict"],
    )

    # instalable_capacity_sheet read in
    m.Q_ext_new = pyomo.Param(
        m.stf,
        m.location,
        m.tech,
        initialize=data_urbsextensionv1["installable_capacity_dict"],
    )
    # DCR sheet read in
    m.DCR_solar = pyomo.Param(
        m.stf, m.location, m.tech, initialize=data_urbsextensionv1["dcr_dict"]
    )  # DCR Solar
    # stocklvl sheet read in
    m.min_stocklvl = pyomo.Param(
        m.stf, m.location, m.tech, initialize=data_urbsextensionv1["stocklvl_dict"]
    )
    # loadfactors sheet read in
    # Capacity to Balance with loadfactor and h/a
    m.lf_solar = pyomo.Param(
        m.timesteps_ext,
        m.stf,
        m.location,
        m.tech,
        initialize=data_urbsextensionv1["loadfactors_dict"],
    )  # lf Solar

    ########################################
    # dynamic feedback loop EEM sets and params#     13. January 2025
    ########################################

    # -------EU-Primary-------# ToDo enable if needed
    # index set for n (=steps of linearization)
    # m.nsteps_pri = pyomo.Set(initialize=range(0, 7))
    # param def for price reduction
    # m.P_pri = pyomo.Param(m.nsteps_pri, initialize={0: 0, 1: 172444.8, 2: 246826.8
    #    , 3: 279008.4, 4: 292974, 5: 299046, 6: 301656.96})
    # m.capacityperstep_pri = pyomo.Param(m.nsteps_pri, initialize={0: 0, 1: 100, 2: 1000, 3: 10000, 4: 100000, 5:1000000, 6:10000000})
    # param for gamma
    # m.gamma_pri = pyomo.Param(initialize=1e10)

    # -------EU-Secondary-------#
    # index set for n (=steps of linearization)
    m.nsteps_sec = pyomo.Set(initialize=range(0, 7))
    # param def for price reduction

    # m.P_sec = pyomo.Param(m.nsteps_sec, initialize={
    #    0: 0,
    #    1: 13593.82044,
    #    2: 26741.2835,
    #    3: 39457.04547,
    #    4: 51755.28139,
    #    5: 63649.70086,
    #    6: 75153.56332
    # })
    # 2 LR 2%
    # m.P_sec = pyomo.Param(m.nsteps_sec, initialize={
    #    0: 0,
    #    1: 26872.52452,
    #    2: 52000.76746,
    #    3: 75497.94923,
    #    4: 97469.94116,
    #    5: 118015.7425,
    #    6: 137227.9266
    # })

    # 3 LR 5%
    # m.P_sec = pyomo.Param(m.nsteps_sec, initialize={
    #  0: 0,
    # 1: 64859.87772,
    # 2: 119558.3938,
    # 3: 165687.4918,
    # 4: 204589.7114,
    # 5: 237397.2614,
    # 6: 265064.9716
    # })

    # 4 LR 10%
    # m.P_sec = pyomo.Param(m.nsteps_sec, initialize={
    #    0: 0,
    #    1: 122259.1475,
    #    2: 208413.7077,
    #    3: 269125.7967,
    #    4: 311908.8802,
    #    5: 342057.6079,
    #    6: 363303.0561
    # })

    # 5 LR 25%
    # m.P_sec = pyomo.Param(m.nsteps_sec, initialize={
    #    0: 0,
    #    1: 254792.7496,
    #    2: 352775.4865,
    #    3: 390455.5883,
    #    4: 404945.7946,
    #    5: 410518.1277,
    #    6: 412661.0161
    # })
    # EEM6 LR 2.5%
    variation_6 = {
        0: 0,
        1: 33395.02122,
        2: 64096.25634,
        3: 92320.99775,
        4: 118269.0101,
        5: 142123.9441,
        6: 164054.6365,
    }
    # EEM7 LR 3%
    variation_7 = {
        0: 0,
        1: 39840.31305,
        2: 75846.68759,
        3: 108388.0736,
        4: 137797.9162,
        5: 164377.572,
        6: 188399.3973,
    }
    # EEM8 LR 3.5%
    variation_8 = {
        0: 0,
        1: 46208.92298,
        2: 87260.20208,
        3: 123729.5116,
        4: 156128.2716,
        5: 184910.8195,
        6: 210480.7816,
    }
    # EEM9 LR 4%
    variation_9 = {
        0: 0,
        1: 52501.37307,
        2: 98344.78919,
        3: 138374.5766,
        4: 173327.9901,
        5: 203848.7895,
        6: 230499.0966,
    }
    # EEM10 LR 4.5%
    variation_10 = {
        0: 0,
        1: 58718.18454,
        2: 109108.2889,
        3: 152351.496,
        4: 189461.4601,
        5: 221308.0674,
        6: 248637.827,
    }
    # EEM11 LR 3.75%
    variation_11 = {
        0: 0,
        1: 49364.63541,
        2: 92843.11808,
        3: 131137.3026,
        4: 164865.3556,
        5: 194571.7345,
        6: 220735.9768,
    }
    # EEM12 LR 3.6%
    variation_12 = {
        0: 0,
        1: 47473.48909,
        2: 89503.18068,
        3: 126713.3165,
        4: 159656.5562,
        5: 188822.1859,
        6: 214643.3852,
    }
    # EEM13 LR 3.7%
    variation_13 = {
        0: 0,
        1: 48735.01299,
        2: 91733.06585,
        3: 129669.4987,
        4: 163140.1525,
        5: 192670.7272,
        6: 218725.0388,
    }
    # EEM14 LR 3.55%
    # Define variation_14 correctly for each (nsteps_sec, tech) combination.
    # Assuming wind is added to m.tech and further locations
    # P_sec initialization (price reduction)
    variation_14_updated = {
        (n, tech, loc): value if tech == "solarPV" else 0
        for n, value in {
            0: 0,
            1: 46841.69972,
            2: 88383.54549,
            3: 125225.1836,
            4: 157898.4141,
            5: 186874.8668,
            6: 212572.8099,
        }.items()
        for tech in m.tech
        for loc in m.location
    }

    # Initialize m.P_sec
    m.P_sec = pyomo.Param(
        m.nsteps_sec, m.tech, m.location, initialize=variation_14_updated
    )

    # param def for Capacity needed to reach next step
    # Initialize the dictionary with values for capacityperstep_sec
    capacity_init_values = {}

    # Loop over all nsteps_sec, location, and tech
    for n in m.nsteps_sec:
        for loc in m.location:
            for tech in m.tech:
                if tech == "solarPV":
                    # Use the predefined capacity values for solarPV (or any logic you want for tech)
                    capacity_init_values[(n, loc, tech)] = {
                        0: 0,
                        1: 100,
                        2: 1000,
                        3: 10000,
                        4: 100000,
                        5: 1000000,
                        6: 10000000,
                    }.get(n, 0)  # Default to 0 for other steps
                else:
                    # For other technologies (like wind), set the default to 0
                    capacity_init_values[(n, loc, tech)] = 0
    print(capacity_init_values)

    # Now initialize the Param with the dictionary
    m.capacityperstep_sec = pyomo.Param(
        m.nsteps_sec, m.location, m.tech, initialize=capacity_init_values
    )

    # Initialize m.capacityperstep_sec
    m.capacityperstep_sec = pyomo.Param(
        m.nsteps_sec, m.location, m.tech, initialize=capacity_init_values
    )

    # param for gamma
    m.gamma_sec = pyomo.Param(initialize=1e10)

    ##########----------end EEM Addition-----------###############
    ##########----------    urbs-scrap  -----------###############
    m.f_scrap = pyomo.Param(
        m.location,
        m.tech,
        initialize=initialize_param("scrap", default_value=0),
        doc="tons per MW",
    )
    m.f_mining = pyomo.Param(
        m.location,
        m.tech,
        initialize=initialize_param("mining", default_value=0),
        doc="tons per MW",
    )
    m.f_recycling = pyomo.Param(
        m.location,
        m.tech,
        initialize=initialize_param("recycling_efficiency", default_value=0),
        doc="recycling efficiency in %",
    )
    m.f_scrap_rec = pyomo.Param(
        m.stf,
        m.location,
        m.tech,
        initialize=data_urbsextensionv1["recyclingcost_dict"],
        doc="cost for recycling in EUR/ton",
    )
    m.f_increase = pyomo.Param(
        m.location,
        m.tech,
        initialize=initialize_param("IR_recycling", default_value=0),
        doc="Fraction of increase in production",
    )
    m.capacity_dec_start = pyomo.Param(
        m.location,
        m.tech,
        initialize=initialize_param("Initial_decommisions", default_value=0),
        doc="initial decommisions",
    )

    ##########----------end urbs-scrap  -----------###############
    # tuple sets
    m.sit_tuples = pyomo.Set(
        within=m.stf * m.sit,
        initialize=tuple(m.site_dict["area"].keys()),
        doc="Combinations of support timeframes and sites",
    )
    m.com_tuples = pyomo.Set(
        within=m.stf * m.sit * m.com * m.com_type,
        initialize=tuple(m.commodity_dict["price"].keys()),
        doc="Combinations of defined commodities, e.g. (2018,Mid,Elec,Demand)",
    )
    m.pro_tuples = pyomo.Set(
        within=m.stf * m.sit * m.pro,
        initialize=tuple(m.process_dict["inv-cost"].keys()),
        doc="Combinations of possible processes, e.g. (2018,North,Coal plant)",
    )
    m.com_stock = pyomo.Set(
        within=m.com,
        initialize=commodity_subset(m.com_tuples, "Stock"),
        doc="Commodities that can be purchased at some site(s)",
    )
    if m.mode["int"]:
        # tuples for operational status of technologies
        m.operational_pro_tuples = pyomo.Set(
            within=m.sit * m.pro * m.stf * m.stf,
            initialize=[
                (sit, pro, stf, stf_later)
                for (sit, pro, stf, stf_later) in op_pro_tuples(m.pro_tuples, m)
            ],
            doc="Processes that are still operational through stf_later"
            "(and the relevant years following), if built in stf"
            "in stf.",
        )

        # tuples for rest lifetime of installed capacities of technologies
        m.inst_pro_tuples = pyomo.Set(
            within=m.sit * m.pro * m.stf,
            initialize=[(sit, pro, stf) for (sit, pro, stf) in inst_pro_tuples(m)],
            doc="Installed processes that are still operational through stf",
        )

    # commodity type subsets
    m.com_supim = pyomo.Set(
        within=m.com,
        initialize=commodity_subset(m.com_tuples, "SupIm"),
        doc="Commodities that have intermittent (timeseries) input",
    )
    m.com_demand = pyomo.Set(
        within=m.com,
        initialize=commodity_subset(m.com_tuples, "Demand"),
        doc="Commodities that have a demand (implies timeseries)",
    )
    m.com_env = pyomo.Set(
        within=m.com,
        initialize=commodity_subset(m.com_tuples, "Env"),
        doc="Commodities that (might) have a maximum creation limit",
    )

    # process tuples for area rule
    m.pro_area_tuples = pyomo.Set(
        within=m.stf * m.sit * m.pro,
        initialize=tuple(m.proc_area_dict.keys()),
        doc="Processes and Sites with area Restriction",
    )

    # process input/output
    m.pro_input_tuples = pyomo.Set(
        within=m.stf * m.sit * m.pro * m.com,
        initialize=[
            (stf, site, process, commodity)
            for (stf, site, process) in m.pro_tuples
            for (s, pro, commodity) in tuple(m.r_in_dict.keys())
            if process == pro and s == stf
        ],
        doc="Commodities consumed by process by site,e.g. (2020,Mid,PV,Solar)",
    )
    m.pro_output_tuples = pyomo.Set(
        within=m.stf * m.sit * m.pro * m.com,
        initialize=[
            (stf, site, process, commodity)
            for (stf, site, process) in m.pro_tuples
            for (s, pro, commodity) in tuple(m.r_out_dict.keys())
            if process == pro and s == stf
        ],
        doc="Commodities produced by process by site, e.g. (2020,Mid,PV,Elec)",
    )

    # process tuples for maximum gradient feature
    m.pro_maxgrad_tuples = pyomo.Set(
        within=m.stf * m.sit * m.pro,
        initialize=[
            (stf, sit, pro)
            for (stf, sit, pro) in m.pro_tuples
            if m.process_dict["max-grad"][stf, sit, pro] < 1.0 / dt
        ],
        doc="Processes with maximum gradient smaller than timestep length",
    )

    # process tuples for partial feature
    m.pro_partial_tuples = pyomo.Set(
        within=m.stf * m.sit * m.pro,
        initialize=[
            (stf, site, process)
            for (stf, site, process) in m.pro_tuples
            for (s, pro, _) in tuple(m.r_in_min_fraction_dict.keys())
            if process == pro and s == stf
        ],
        doc="Processes with partial input",
    )

    m.pro_partial_input_tuples = pyomo.Set(
        within=m.stf * m.sit * m.pro * m.com,
        initialize=[
            (stf, site, process, commodity)
            for (stf, site, process) in m.pro_partial_tuples
            for (s, pro, commodity) in tuple(m.r_in_min_fraction_dict.keys())
            if process == pro and s == stf
        ],
        doc="Commodities with partial input ratio,e.g. (2020,Mid,Coal PP,Coal)",
    )

    m.pro_partial_output_tuples = pyomo.Set(
        within=m.stf * m.sit * m.pro * m.com,
        initialize=[
            (stf, site, process, commodity)
            for (stf, site, process) in m.pro_partial_tuples
            for (s, pro, commodity) in tuple(m.r_out_min_fraction_dict.keys())
            if process == pro and s == stf
        ],
        doc="Commodities with partial input ratio, e.g. (Mid,Coal PP,CO2)",
    )

    # Variables

    # costs
    m.costs = pyomo.Var(m.cost_type, within=pyomo.Reals, doc="Costs by type (EUR/a)")

    m.process_costs = pyomo.Var(
        m.pro_tuples,
        m.cost_type,
        within=pyomo.Reals,
        doc="Costs by type and site (EUR/a)",
    )
    # commodity
    m.e_co_stock = pyomo.Var(
        m.tm,
        m.com_tuples,
        within=pyomo.NonNegativeReals,
        doc="Use of stock commodity source (MW) per timestep",
    )

    # process
    m.cap_pro_new = pyomo.Var(
        m.pro_tuples, within=pyomo.NonNegativeReals, doc="New process capacity (MW)"
    )

    # process capacity as expression object
    # (variable if expansion is possible, else static)
    m.cap_pro = pyomo.Expression(
        m.pro_tuples, rule=def_process_capacity_rule, doc="Total process capacity (MW)"
    )

    m.tau_pro = pyomo.Var(
        m.t,
        m.pro_tuples,
        within=pyomo.NonNegativeReals,
        doc="Power flow (MW) through process",
    )
    m.e_pro_in = pyomo.Var(
        m.tm,
        m.pro_input_tuples,
        within=pyomo.NonNegativeReals,
        doc="Power flow of commodity into process (MW) per timestep",
    )
    m.e_pro_out = pyomo.Var(
        m.tm,
        m.pro_output_tuples,
        within=pyomo.NonNegativeReals,
        doc="Power flow out of process (MW) per timestep",
    )

    ########################################
    #       dynamic feedback loop vars     #     13. January 2025
    ########################################
    # -------EU-Primary-------#
    # m.pricereduction_pri = pyomo.Var(m.stf, domain=pyomo.NonNegativeReals)
    # m.BD_pri = pyomo.Var(m.stf, m.nsteps_pri, domain=pyomo.Binary)

    # -------EU-Secondary-------#
    # pricereduction_sec (price reduction variable)
    m.pricereduction_sec = pyomo.Var(
        m.stf, m.location, m.tech, domain=pyomo.NonNegativeReals
    )
    # BD_sec (binary decision variable for BD)
    m.BD_sec = pyomo.Var(m.stf, m.location, m.tech, m.nsteps_sec, domain=pyomo.Binary)

    ################################
    # Variables used for urbs_ext#
    ################################

    # capacity variables (MW) ext as extension for certain processes
    m.capacity_ext = pyomo.Var(m.stf, m.location, m.tech, domain=pyomo.NonNegativeReals)
    m.capacity_ext_new = pyomo.Var(
        m.stf, m.location, m.tech, domain=pyomo.NonNegativeReals
    )
    m.capacity_ext_imported = pyomo.Var(
        m.stf, m.location, m.tech, domain=pyomo.NonNegativeReals
    )
    m.capacity_ext_stockout = pyomo.Var(
        m.stf, m.location, m.tech, domain=pyomo.NonNegativeReals
    )
    m.capacity_ext_euprimary = pyomo.Var(
        m.stf, m.location, m.tech, domain=pyomo.NonNegativeReals
    )
    m.capacity_ext_eusecondary = pyomo.Var(
        m.stf, m.location, m.tech, domain=pyomo.NonNegativeReals
    )
    m.capacity_ext_stock = pyomo.Var(
        m.stf, m.location, m.tech, domain=pyomo.NonNegativeReals
    )
    m.capacity_ext_stock_imported = pyomo.Var(
        m.stf, m.location, m.tech, domain=pyomo.NonNegativeReals
    )

    m.sum_outofstock = pyomo.Var(
        m.stf, m.location, m.tech, domain=pyomo.NonNegativeReals
    )
    m.sum_stock = pyomo.Var(m.stf, m.location, m.tech, domain=pyomo.NonNegativeReals)
    m.anti_dumping_measures = pyomo.Var(
        m.stf, m.location, m.tech, domain=pyomo.NonNegativeReals
    )

    # balance Variables (MWh) : only used for results & res_vertex_rule
    m.balance_ext = pyomo.Var(
        m.timesteps_ext, m.stf, m.location, m.tech, within=pyomo.NonNegativeReals
    )  # --> res_vertex_rule
    m.balance_import_ext = pyomo.Var(
        m.timesteps_ext, m.stf, m.location, m.tech, within=pyomo.NonNegativeReals
    )
    m.balance_outofstock_ext = pyomo.Var(
        m.timesteps_ext, m.stf, m.location, m.tech, within=pyomo.NonNegativeReals
    )
    m.balance_EU_primary_ext = pyomo.Var(
        m.timesteps_ext, m.stf, m.location, m.tech, within=pyomo.NonNegativeReals
    )
    m.balance_EU_secondary_ext = pyomo.Var(
        m.timesteps_ext, m.stf, m.location, m.tech, within=pyomo.NonNegativeReals
    )

    # cost Variables (€/MW): main objective Function --> minimize cost
    m.costs_new = pyomo.Var(m.cost_type_new, domain=pyomo.NonNegativeReals)
    m.costs_ext_import = pyomo.Var(
        m.stf, m.location, m.tech, within=pyomo.NonNegativeReals
    )
    m.costs_ext_storage = pyomo.Var(
        m.stf, m.location, m.tech, within=pyomo.NonNegativeReals
    )
    m.costs_EU_primary = pyomo.Var(
        m.stf, m.location, m.tech, within=pyomo.NonNegativeReals
    )
    m.costs_EU_secondary = pyomo.Var(
        m.stf, m.location, m.tech, within=pyomo.NonNegativeReals
    )
    ##########----------    urbs-scrap  -----------###############
    m.capacity_dec = pyomo.Var(m.stf, m.location, m.tech, domain=pyomo.NonNegativeReals)
    m.capacity_scrap_dec = pyomo.Var(
        m.stf, m.location, m.tech, domain=pyomo.NonNegativeReals
    )
    m.capacity_scrap_rec = pyomo.Var(
        m.stf, m.location, m.tech, domain=pyomo.NonNegativeReals
    )
    m.capacity_scrap_total = pyomo.Var(
        m.stf, m.location, m.tech, domain=pyomo.NonNegativeReals
    )
    m.cost_scrap = pyomo.Var(m.stf, m.location, m.tech, domain=pyomo.NonNegativeReals)
    ##########----------end urbs-scrap  -----------###############
    if m.mode["tra"]:
        if m.mode["dpf"]:
            m = add_transmission_dc(m)
        else:
            m = add_transmission(m)
    if m.mode["sto"]:
        m = add_storage(m)
    if m.mode["dsm"]:
        m = add_dsm(m)
    if m.mode["bsp"]:
        m = add_buy_sell_price(m)
    if m.mode["tve"]:
        m = add_time_variable_efficiency(m)
    else:
        m.pro_timevar_output_tuples = pyomo.Set(
            within=m.stf * m.sit * m.pro * m.com,
            doc="empty set needed for (partial) process output",
        )

    # Equation declarations
    # equation bodies are defined in separate functions, referred to here by
    # their name in the "rule" keyword.
    # Constraints for Scenarios ToDo ENABLE IF NEEDED
    # m.net_zero_industrialactbenchmark_a = pyomo.Constraint(m.stf, m.location, m.tech, rule=net_zero_industrialactbenchmark_rule_a)
    # m.net_zero_industrialactbenchmark_b = pyomo.Constraint(m.stf, rule=net_zero_industrialactbenchmark_rule_b)
    # m.best_estimate_TYNDP2030 = pyomo.Constraint(m.stf, rule=best_estimate_TYNDP2030_rule)
    # m.best_estimate_TYNDP2040 = pyomo.Constraint(m.stf, rule=best_estimate_TYNDP2040_rule)
    # m.best_estimate_TYNDP2050 = pyomo.Constraint(m.stf, rule=best_estimate_TYNDP2050_rule)
    # m.minimum_stock_level = pyomo.Constraint(m.stf, rule=minimum_stock_level_rule)

    ########################################################################################################################
    """
    This Section is used to read in certain packages and features coded to modify the basic urbs model. 
    It links the basic urbs model with our own Constraints and passes these Constraints to the model "m"
    """

    apply_stockpiling_constraints(m)

    # apply_m_constraints(m)

    apply_rm_constraints(m)

    apply_scrap_constraints(m)

    # apply_m_constraints(m)

    apply_balance_constraints(m)

    apply_costs_constraints(m)

    ########################################################################################################################
    # commodity constraints default
    m.res_vertex = pyomo.Constraint(
        m.tm,
        m.com_tuples,
        rule=res_vertex_rule,
        doc="storage + transmission + process + source + buy - sell == demand",
    )
    m.res_stock_step = pyomo.Constraint(
        m.tm,
        m.com_tuples,
        rule=res_stock_step_rule,
        doc="stock commodity input per step <= commodity.maxperstep",
    )
    m.res_stock_total = pyomo.Constraint(
        m.com_tuples,
        rule=res_stock_total_rule,
        doc="total stock commodity input <= commodity.max",
    )
    m.res_env_step = pyomo.Constraint(
        m.tm,
        m.com_tuples,
        rule=res_env_step_rule,
        doc="environmental output per step <= commodity.maxperstep",
    )
    m.res_env_total = pyomo.Constraint(
        m.com_tuples,
        rule=res_env_total_rule,
        doc="total environmental commodity output <= commodity.max",
    )

    # process
    m.def_process_input = pyomo.Constraint(
        m.tm,
        m.pro_input_tuples - m.pro_partial_input_tuples,
        rule=def_process_input_rule,
        doc="process input = process throughput * input ratio",
    )
    m.def_process_output = pyomo.Constraint(
        m.tm,
        (
            m.pro_output_tuples
            - m.pro_partial_output_tuples
            - m.pro_timevar_output_tuples
        ),
        rule=def_process_output_rule,
        doc="process output = process throughput * output ratio",
    )
    m.def_intermittent_supply = pyomo.Constraint(
        m.tm,
        m.pro_input_tuples,
        rule=def_intermittent_supply_rule,
        doc="process output = process capacity * supim timeseries",
    )
    m.res_process_throughput_by_capacity = pyomo.Constraint(
        m.tm,
        m.pro_tuples,
        rule=res_process_throughput_by_capacity_rule,
        doc="process throughput <= total process capacity",
    )
    m.res_process_maxgrad_lower = pyomo.Constraint(
        m.tm,
        m.pro_maxgrad_tuples,
        rule=res_process_maxgrad_lower_rule,
        doc="throughput may not decrease faster than maximal gradient",
    )
    m.res_process_maxgrad_upper = pyomo.Constraint(
        m.tm,
        m.pro_maxgrad_tuples,
        rule=res_process_maxgrad_upper_rule,
        doc="throughput may not increase faster than maximal gradient",
    )
    m.res_process_capacity = pyomo.Constraint(
        m.pro_tuples,
        rule=res_process_capacity_rule,
        doc="process.cap-lo <= total process capacity <= process.cap-up",
    )

    m.res_area = pyomo.Constraint(
        m.sit_tuples, rule=res_area_rule, doc="used process area <= total process area"
    )

    m.res_throughput_by_capacity_min = pyomo.Constraint(
        m.tm,
        m.pro_partial_tuples,
        rule=res_throughput_by_capacity_min_rule,
        doc="cap_pro * min-fraction <= tau_pro",
    )
    m.def_partial_process_input = pyomo.Constraint(
        m.tm,
        m.pro_partial_input_tuples,
        rule=def_partial_process_input_rule,
        doc="e_pro_in = "
        " cap_pro * min_fraction * (r - R) / (1 - min_fraction)"
        " + tau_pro * (R - min_fraction * r) / (1 - min_fraction)",
    )
    m.def_partial_process_output = pyomo.Constraint(
        m.tm,
        (
            m.pro_partial_output_tuples
            - (m.pro_partial_output_tuples & m.pro_timevar_output_tuples)
        ),
        rule=def_partial_process_output_rule,
        doc="e_pro_out = "
        " cap_pro * min_fraction * (r - R) / (1 - min_fraction)"
        " + tau_pro * (R - min_fraction * r) / (1 - min_fraction)",
    )

    # if m.mode['int']:
    #    m.res_global_co2_limit = pyomo.Constraint(
    #        m.stf
    #        ,
    #        rule=res_global_co2_limit_rule,
    #        doc='total co2 commodity output <= global.prop CO2 limit')

    # costs
    m.def_costs = pyomo.Constraint(
        m.cost_type, rule=def_costs_rule, doc="main cost function by cost type"
    )

    # specific cost calculation allows to identify individual contributors to the cost function.
    m.def_specific_process_costs = pyomo.Constraint(
        m.pro_tuples,
        m.cost_type,
        rule=def_specific_process_costs_rule,
        doc="main cost function of processes by cost type by process and stf",
    )

    # objective and global constraints
    if m.obj.value == "cost":
        m.res_global_co2_limit = pyomo.Constraint(
            m.stf,
            rule=res_global_co2_limit_rule,
            doc="total co2 commodity output <= Global CO2 limit",
        )

        if m.mode["int"]:
            m.res_global_co2_budget = pyomo.Constraint(
                rule=res_global_co2_budget_rule,
                doc="total co2 commodity output <= global.prop CO2 budget",
            )

            m.res_global_cost_limit = pyomo.Constraint(
                m.stf,
                rule=res_global_cost_limit_rule,
                doc="total costs <= Global cost limit",
            )

        m.objective_function = pyomo.Objective(
            rule=cost_rule,
            sense=pyomo.minimize,
            doc="minimize(cost = sum of all cost types)",
        )

    elif m.obj.value == "CO2":
        m.res_global_cost_limit = pyomo.Constraint(
            m.stf,
            rule=res_global_cost_limit_rule,
            doc="total costs <= Global cost limit",
        )

        if m.mode["int"]:
            m.res_global_cost_budget = pyomo.Constraint(
                rule=res_global_cost_budget_rule,
                doc="total costs <= global.prop Cost budget",
            )
            m.res_global_co2_limit = pyomo.Constraint(
                m.stf,
                rule=res_global_co2_limit_rule,
                doc="total co2 commodity output <= Global CO2 limit",
            )

        m.objective_function = pyomo.Objective(
            rule=co2_rule, sense=pyomo.minimize, doc="minimize total CO2 emissions"
        )

    else:
        raise NotImplementedError(
            "Non-implemented objective quantity. Set "
            "either 'cost' or 'CO2' as the objective in "
            "runme.py!"
        )

    if dual:
        m.dual = pyomo.Suffix(direction=pyomo.Suffix.IMPORT)

    return m


# commodity


# vertex equation: calculate balance for given commodity and site;
# contains implicit constraints for process activity, import/export and
# storage activity (calculated by function commodity_balance);
# contains implicit constraint for stock commodity source term
def res_vertex_rule(m, tm, stf, sit, com, com_type):
    # environmental or supim commodities don't have this constraint (yet)
    if com in m.com_env:
        return pyomo.Constraint.Skip
    if com in m.com_supim:
        return pyomo.Constraint.Skip

    # helper function commodity_balance calculates balance from input to
    # and output from processes, storage and transmission.
    # if power_surplus > 0: production/storage/imports create net positive
    #                       amount of commodity com
    # if power_surplus < 0: production/storage/exports consume a net
    #                       amount of the commodity com
    power_surplus = -commodity_balance(m, tm, stf, sit, com)

    # Add extra modelled capacity contribution to power surplus for "Elec"
    if com == "Elec":
        # Filter balance_ext for the current timestep, year, and site
        for tech in m.tech:
            if (tm, stf, sit, tech) in m.balance_ext:
                power_surplus += m.balance_ext[tm, stf, sit, tech]

    print(power_surplus)
    # if com is a stock commodity, the commodity source term e_co_stock
    # can supply a possibly negative power_surplus
    if com in m.com_stock:
        power_surplus += m.e_co_stock[tm, stf, sit, com, com_type]

    # if Buy and sell prices are enabled
    if m.mode["bsp"]:
        power_surplus += bsp_surplus(m, tm, stf, sit, com, com_type)

    # if com is a demand commodity, the power_surplus is reduced by the
    # demand value; no scaling by m.dt or m.weight is needed here, as this
    # constraint is about power (MW), not energy (MWh)
    if com in m.com_demand:
        try:
            # Get the demand value
            demand_value = m.demand_dict[(sit, com)][(stf, tm)]

            # Subtract demand from power surplus
            power_surplus -= demand_value
            # print(power_surplus)
        except KeyError:
            pass

    if m.mode["dsm"]:
        power_surplus += dsm_surplus(m, tm, stf, sit, com)

    return power_surplus == 0


# stock commodity purchase == commodity consumption, according to
# commodity_balance of current (time step, site, commodity);
# limit stock commodity use per time step


def res_stock_step_rule(m, tm, stf, sit, com, com_type):
    if com not in m.com_stock:
        return pyomo.Constraint.Skip
    else:
        return (
            m.e_co_stock[tm, stf, sit, com, com_type]
            <= m.dt * m.commodity_dict["maxperhour"][(stf, sit, com, com_type)]
        )


# limit stock commodity use in total (scaled to annual consumption, thanks
# to m.weight)
def res_stock_total_rule(m, stf, sit, com, com_type):
    if com not in m.com_stock:
        return pyomo.Constraint.Skip
    else:
        # calculate total consumption of commodity com
        total_consumption = 0
        for tm in m.tm:
            total_consumption += m.e_co_stock[tm, stf, sit, com, com_type]
        total_consumption *= m.weight
        return total_consumption <= m.commodity_dict["max"][(stf, sit, com, com_type)]


# environmental commodity creation == - commodity_balance of that commodity
# used for modelling emissions (e.g. CO2) or other end-of-pipe results of
# any process activity;
# limit environmental commodity output per time step
def res_env_step_rule(m, tm, stf, sit, com, com_type):
    if com not in m.com_env:
        return pyomo.Constraint.Skip
    else:
        environmental_output = -commodity_balance(m, tm, stf, sit, com)
        return (
            environmental_output
            <= m.dt * m.commodity_dict["maxperhour"][(stf, sit, com, com_type)]
        )


# limit environmental commodity output in total (scaled to annual
# emissions, thanks to m.weight)
def res_env_total_rule(m, stf, sit, com, com_type):
    if com not in m.com_env:
        return pyomo.Constraint.Skip
    else:
        # calculate total creation of environmental commodity com
        env_output_sum = 0
        for tm in m.tm:
            env_output_sum += -commodity_balance(m, tm, stf, sit, com)
        env_output_sum *= m.weight
        return env_output_sum <= m.commodity_dict["max"][(stf, sit, com, com_type)]


# process


# process capacity (for m.cap_pro Expression)
def def_process_capacity_rule(m, stf, sit, pro):
    if m.mode["int"]:
        if (sit, pro, stf) in m.inst_pro_tuples:
            if (sit, pro, min(m.stf)) in m.pro_const_cap_dict:
                cap_pro = m.process_dict["inst-cap"][(stf, sit, pro)]
            else:
                cap_pro = (
                    sum(
                        m.cap_pro_new[stf_built, sit, pro]
                        for stf_built in m.stf
                        if (sit, pro, stf_built, stf) in m.operational_pro_tuples
                    )
                    + m.process_dict["inst-cap"][(min(m.stf), sit, pro)]
                )
        else:
            cap_pro = sum(
                m.cap_pro_new[stf_built, sit, pro]
                for stf_built in m.stf
                if (sit, pro, stf_built, stf) in m.operational_pro_tuples
            )
    else:
        if (sit, pro, stf) in m.pro_const_cap_dict:
            cap_pro = m.process_dict["inst-cap"][(stf, sit, pro)]
        else:
            cap_pro = (
                m.cap_pro_new[stf, sit, pro]
                + m.process_dict["inst-cap"][(stf, sit, pro)]
            )
    return cap_pro


# process input power == process throughput * input ratio


def def_process_input_rule(m, tm, stf, sit, pro, com):
    return (
        m.e_pro_in[tm, stf, sit, pro, com]
        == m.tau_pro[tm, stf, sit, pro] * m.r_in_dict[(stf, pro, com)]
    )


# process output power = process throughput * output ratio
def def_process_output_rule(m, tm, stf, sit, pro, com):
    ergebnis = m.tau_pro[tm, stf, sit, pro] * m.r_out_dict[(stf, pro, com)]
    # print(ergebnis)
    return m.e_pro_out[tm, stf, sit, pro, com] == ergebnis


# process input (for supim commodity) = process capacity * timeseries
def def_intermittent_supply_rule(m, tm, stf, sit, pro, coin):
    if coin in m.com_supim:
        return (
            m.e_pro_in[tm, stf, sit, pro, coin]
            == m.cap_pro[stf, sit, pro] * m.supim_dict[(sit, coin)][(stf, tm)] * m.dt
        )
    else:
        return pyomo.Constraint.Skip


# process throughput <= process capacity
def res_process_throughput_by_capacity_rule(m, tm, stf, sit, pro):
    result = m.dt * m.cap_pro[stf, sit, pro]
    # print(result)
    return m.tau_pro[tm, stf, sit, pro] <= result


def res_process_maxgrad_lower_rule(m, t, stf, sit, pro):
    return (
        m.tau_pro[t - 1, stf, sit, pro]
        - m.cap_pro[stf, sit, pro] * m.process_dict["max-grad"][(stf, sit, pro)] * m.dt
        <= m.tau_pro[t, stf, sit, pro]
    )


def res_process_maxgrad_upper_rule(m, t, stf, sit, pro):
    return (
        m.tau_pro[t - 1, stf, sit, pro]
        + m.cap_pro[stf, sit, pro] * m.process_dict["max-grad"][(stf, sit, pro)] * m.dt
        >= m.tau_pro[t, stf, sit, pro]
    )


def res_throughput_by_capacity_min_rule(m, tm, stf, sit, pro):
    return (
        m.tau_pro[tm, stf, sit, pro]
        >= m.cap_pro[stf, sit, pro]
        * m.process_dict["min-fraction"][(stf, sit, pro)]
        * m.dt
    )


def def_partial_process_input_rule(m, tm, stf, sit, pro, coin):
    # input ratio at maximum operation point
    R = m.r_in_dict[(stf, pro, coin)]
    # input ratio at lowest operation point
    r = m.r_in_min_fraction_dict[stf, pro, coin]
    min_fraction = m.process_dict["min-fraction"][(stf, sit, pro)]

    online_factor = min_fraction * (r - R) / (1 - min_fraction)
    throughput_factor = (R - min_fraction * r) / (1 - min_fraction)

    return (
        m.e_pro_in[tm, stf, sit, pro, coin]
        == m.dt * m.cap_pro[stf, sit, pro] * online_factor
        + m.tau_pro[tm, stf, sit, pro] * throughput_factor
    )


def def_partial_process_output_rule(m, tm, stf, sit, pro, coo):
    # input ratio at maximum operation point
    R = m.r_out_dict[stf, pro, coo]
    # input ratio at lowest operation point
    r = m.r_out_min_fraction_dict[stf, pro, coo]
    min_fraction = m.process_dict["min-fraction"][(stf, sit, pro)]

    online_factor = min_fraction * (r - R) / (1 - min_fraction)
    throughput_factor = (R - min_fraction * r) / (1 - min_fraction)

    return (
        m.e_pro_out[tm, stf, sit, pro, coo]
        == m.dt * m.cap_pro[stf, sit, pro] * online_factor
        + m.tau_pro[tm, stf, sit, pro] * throughput_factor
    )


# lower bound <= process capacity <= upper bound
def res_process_capacity_rule(m, stf, sit, pro):
    return (
        m.process_dict["cap-lo"][stf, sit, pro],
        m.cap_pro[stf, sit, pro],
        m.process_dict["cap-up"][stf, sit, pro],
    )


# used process area <= maximal process area
def res_area_rule(m, stf, sit):
    if (
        m.site_dict["area"][stf, sit] >= 0
        and sum(
            m.process_dict["area-per-cap"][st, s, p]
            for (st, s, p) in m.pro_area_tuples
            if s == sit and st == stf
        )
        > 0
    ):
        total_area = sum(
            m.cap_pro[st, s, p] * m.process_dict["area-per-cap"][st, s, p]
            for (st, s, p) in m.pro_area_tuples
            if s == sit and st == stf
        )
        return total_area <= m.site_dict["area"][stf, sit]
    else:
        # Skip constraint, if area is not numeric
        return pyomo.Constraint.Skip


# total CO2 output <= Global CO2 limit
def res_global_co2_limit_rule(m, stf):
    if math.isinf(m.global_prop_dict["value"][stf, "CO2 limit"]):
        return pyomo.Constraint.Skip
    elif m.global_prop_dict["value"][stf, "CO2 limit"] >= 0:
        co2_output_sum = 0
        for tm in m.tm:
            for sit in m.sit:
                # minus because negative commodity_balance represents creation
                # of that commodity.
                co2_output_sum += -commodity_balance(m, tm, stf, sit, "CO2")

        # scaling to annual output (cf. definition of m.weight)
        co2_output_sum *= m.weight
        return co2_output_sum <= m.global_prop_dict["value"][stf, "CO2 limit"]
    else:
        return pyomo.Constraint.Skip


# CO2 output in entire period <= Global CO2 budget
def res_global_co2_budget_rule(m):
    if math.isinf(m.global_prop_dict["value"][min(m.stf_list), "CO2 budget"]):
        return pyomo.Constraint.Skip
    elif (m.global_prop_dict["value"][min(m.stf_list), "CO2 budget"]) >= 0:
        co2_output_sum = 0
        for stf in m.stf:
            for tm in m.tm:
                for sit in m.sit:
                    # minus because negative commodity_balance represents
                    # creation of that commodity.
                    co2_output_sum += (
                        -commodity_balance(m, tm, stf, sit, "CO2")
                        * m.weight
                        * stf_dist(stf, m)
                    )

        return co2_output_sum <= m.global_prop_dict["value"][min(m.stf), "CO2 budget"]
    else:
        return pyomo.Constraint.Skip


# total cost of one year <= Global cost limit
def res_global_cost_limit_rule(m, stf):
    if math.isinf(m.global_prop_dict["value"][stf, "Cost limit"]):
        return pyomo.Constraint.Skip
    elif m.global_prop_dict["value"][stf, "Cost limit"] >= 0:
        return (
            pyomo.summation(m.costs) <= m.global_prop_dict["value"][stf, "Cost limit"]
        )
    else:
        return pyomo.Constraint.Skip


# total cost in entire period <= Global cost budget
def res_global_cost_budget_rule(m):
    if math.isinf(m.global_prop_dict["value"][min(m.stf), "Cost budget"]):
        return pyomo.Constraint.Skip
    elif m.global_prop_dict["value"][min(m.stf), "Cost budget"] >= 0:
        return (
            pyomo.summation(m.costs)
            <= m.global_prop_dict["value"][min(m.stf), "Cost budget"]
        )
    else:
        return pyomo.Constraint.Skip


# Costs and emissions
def def_costs_rule(m, cost_type):
    # Calculate total costs by cost type.
    # Sums up process activity and capacity expansions
    # and sums them in the cost types that are specified in the set
    # m.cost_type. To change or add cost types, add/change entries
    # there and modify the if/elif cases in this function accordingly.
    # Cost types are
    #  - Investment costs for process power, storage power and
    #    storage capacity. They are multiplied by the investment
    #    factors. Rest values of units are subtracted.
    #  - Fixed costs for process power, storage power and storage
    #    capacity.
    #  - Variables costs for usage of processes, storage and transmission.
    #  - Fuel costs for stock commodity purchase.

    if cost_type == "Invest":
        cost = sum(
            m.cap_pro_new[p]
            * m.process_dict["inv-cost"][p]
            * m.process_dict["invcost-factor"][p]
            for p in m.pro_tuples
        )
        if m.mode["int"]:
            cost -= sum(
                m.cap_pro_new[p]
                * m.process_dict["inv-cost"][p]
                * m.process_dict["overpay-factor"][p]
                for p in m.pro_tuples
            )
            # print('Invest Cost',cost)
        if m.mode["tra"]:
            # transmission_cost is defined in transmission.py
            cost += transmission_cost(m, cost_type)
        if m.mode["sto"]:
            # storage_cost is defined in storage.py
            cost += storage_cost(m, cost_type)
        return m.costs[cost_type] == cost

    elif cost_type == "Fixed":
        cost = sum(
            m.cap_pro[p]
            * m.process_dict["fix-cost"][p]
            * m.process_dict["cost_factor"][p]
            for p in m.pro_tuples
        )
        if m.mode["tra"]:
            cost += transmission_cost(m, cost_type)
        if m.mode["sto"]:
            cost += storage_cost(m, cost_type)
        return m.costs[cost_type] == cost

    elif cost_type == "Variable":
        cost = sum(
            m.tau_pro[(tm,) + p]
            * m.weight
            * m.process_dict["var-cost"][p]
            * m.process_dict["cost_factor"][p]
            for tm in m.tm
            for p in m.pro_tuples
        )
        if m.mode["tra"]:
            cost += transmission_cost(m, cost_type)
        if m.mode["sto"]:
            cost += storage_cost(m, cost_type)
        return m.costs[cost_type] == cost

    elif cost_type == "Fuel":
        return m.costs[cost_type] == sum(
            m.e_co_stock[(tm,) + c]
            * m.weight
            * m.commodity_dict["price"][c]
            * m.commodity_dict["cost_factor"][c]
            for tm in m.tm
            for c in m.com_tuples
            if c[2] in m.com_stock
        )

    elif cost_type == "Environmental":
        return m.costs[cost_type] == sum(
            -commodity_balance(m, tm, stf, sit, com)
            * m.weight
            * m.commodity_dict["price"][(stf, sit, com, com_type)]
            * m.commodity_dict["cost_factor"][(stf, sit, com, com_type)]
            for tm in m.tm
            for stf, sit, com, com_type in m.com_tuples
            if com in m.com_env
        )

    # Revenue and Purchase costs defined in BuySellPrice.py
    elif cost_type == "Revenue":
        return m.costs[cost_type] == revenue_costs(m)

    elif cost_type == "Purchase":
        return m.costs[cost_type] == purchase_costs(m)

    else:
        raise NotImplementedError("Unknown cost type.")


def def_specific_process_costs_rule(m, stf, sit, pro, cost_type):
    # Calculate total costs by cost type per process and stf. This allows to easily identify the biggest contributors to the cost functions.
    if cost_type == "Invest":
        cost_spec = (
            m.cap_pro_new[stf, sit, pro]
            * m.process_dict["inv-cost"][stf, sit, pro]
            * m.process_dict["invcost-factor"][stf, sit, pro]
        )

        if m.mode["int"]:
            # import pdb;pdb.set_trace()
            cost_spec -= (
                m.cap_pro_new[stf, sit, pro]
                * m.process_dict["inv-cost"][stf, sit, pro]
                * m.process_dict["overpay-factor"][stf, sit, pro]
            )

        return m.process_costs[stf, sit, pro, cost_type] == cost_spec

    elif cost_type == "Fixed":
        cost_spec = (
            m.cap_pro[stf, sit, pro]
            * m.process_dict["fix-cost"][stf, sit, pro]
            * m.process_dict["cost_factor"][stf, sit, pro]
        )

        return m.process_costs[stf, sit, pro, cost_type] == cost_spec

    elif cost_type == "Variable":
        cost_spec = sum(
            m.tau_pro[tm, stf, sit, pro]
            * m.weight
            * m.process_dict["var-cost"][stf, sit, pro]
            * m.process_dict["cost_factor"][stf, sit, pro]
            for tm in m.tm
        )

        return m.process_costs[stf, sit, pro, cost_type] == cost_spec

    elif cost_type == "Fuel":
        return m.process_costs[stf, sit, pro, cost_type] == sum(
            m.e_pro_in[(tm, st, si, pro, co)]
            * m.weight
            * m.commodity_dict["price"][st, si, co, co_type]
            * m.commodity_dict["cost_factor"][st, si, co, co_type]
            for tm in m.tm
            for (st, si, co, co_type) in m.com_tuples
            if st == stf
            if si == sit
            if ((stf, sit, pro, co) in m.pro_input_tuples) and co_type == "Stock"
        )

    elif cost_type == "Environmental":
        return m.process_costs[stf, sit, pro, cost_type] == sum(
            m.e_pro_out[(tm, st, si, pro, co)]
            * m.weight
            * m.commodity_dict["price"][st, si, co, co_type]
            * m.commodity_dict["cost_factor"][st, si, co, co_type]
            for tm in m.tm
            for (st, si, co, co_type) in m.com_tuples
            if st == stf
            if si == sit
            if ((stf, sit, pro, co) in m.pro_output_tuples) and co_type == "Env"
        )

    # Revenue and Purchase costs defined in BuySellPrice.py
    elif cost_type == "Revenue":
        return m.process_costs[stf, sit, pro, cost_type] == revenue_costs(m)

    elif cost_type == "Purchase":
        return m.process_costs[stf, sit, pro, cost_type] == purchase_costs(m)
    else:
        raise NotImplementedError("Unknown cost type.")


def cost_rule(m):  # urbs_solar Extention
    # Calculate total base costs from m.costs
    total_base_costs = pyomo.summation(m.costs)
    total_ext_costs = pyomo.summation(m.costs_new)
    # print("Total Base Costs:", total_base_costs)  # Print base costs for debugging
    # print("Total Urbs Solar Costs:", total_solar_costs)  # Print solar costs
    # Calculate the total combined costs
    total_costs = total_base_costs + total_ext_costs
    # print("Total Combined Costs (Base + Solar):", total_costs)  # Print total costs

    return total_costs


# CO2 output in entire period <= Global CO2 budget
def co2_rule(m):
    co2_output_sum = 0
    for stf in m.stf:
        for tm in m.tm:
            for sit in m.sit:
                # minus because negative commodity_balance represents
                # creation of that commodity.
                if m.mode["int"]:
                    co2_output_sum += (
                        -commodity_balance(m, tm, stf, sit, "CO2")
                        * m.weight
                        * stf_dist(stf, m)
                    )
                else:
                    co2_output_sum += (
                        -commodity_balance(m, tm, stf, sit, "CO2") * m.weight
                    )

    return co2_output_sum


##########################################################################################
#                                                                                        #
#  urbs_solar Additional functions and rules used to implement into existing urbs model  #
#                              25. September 2024                                        #
#                                                                                        #
##########################################################################################


def net_zero_industrialactbenchmark_rule_a(m, stf, location, tech):
    lhs = (
        m.capacity_ext_euprimary[stf, location, tech]
        + m.capacity_ext_eusecondary[stf, location, tech]
        + m.capacity_ext_stockout[stf, location, tech]
        - m.capacity_ext_stock_imported[stf, location, tech]
    )

    rhs = 0.4 * m.capacity_ext_new[stf, location, tech]

    # Print both sides for debugging
    print(
        f"Debug: STF = {stf}, Location = {location}, Tech = {tech}, LHS = {lhs}, RHS = {rhs}"
    )

    return lhs >= rhs


def net_zero_industrialactbenchmark_rule_b(m, stf, location, tech):
    lhs = (
        m.capacity_ext_euprimary[stf, location, tech]
        + m.capacity_ext_eusecondary[stf, location, tech]
    )

    rhs = 0.4 * m.capacity_ext_new[stf, location, tech]

    # Print both sides for debugging
    print(
        f"Debug: STF = {stf}, Location = {location}, Tech = {tech}, LHS = {lhs}, RHS = {rhs}"
    )

    return lhs >= rhs


# Addition made on 29th November:
def best_estimate_TYNDP2030_rule(m, stf, location, tech):
    lhs = sum(m.capacity_ext_new[stf, location, tech] for stf in m.stf if stf <= 2030)

    # Print the sum for debugging
    print(
        f"Debug: STF = {stf}, Location = {location}, Tech = {tech}, Total Solar Capacity for TYNDP2030 = {lhs}"
    )

    return lhs <= 558118


def best_estimate_TYNDP2040_rule(m, stf, location, tech):
    lhs = sum(m.capacity_ext_new[stf, location, tech] for stf in m.stf if stf <= 2040)

    # Print the sum for debugging
    print(
        f"Debug: STF = {stf}, Location = {location}, Tech = {tech}, Total Solar Capacity for TYNDP2040 = {lhs}"
    )

    return lhs <= 1177233


def best_estimate_TYNDP2050_rule(m, stf, location, tech):
    lhs = sum(m.capacity_ext_new[stf, location, tech] for stf in m.stf if stf <= 2050)

    # Print the sum for debugging
    print(
        f"Debug: STF = {stf}, Location = {location}, Tech = {tech}, Total Solar Capacity for TYNDP2050 = {lhs}"
    )

    return lhs <= 1753785


def minimum_stock_level_rule(m, stf, location, tech):
    lhs = m.min_stocklvl[stf, location, tech]
    rhs = m.capacity_ext_stock[stf, location, tech]

    # Debugging: Print the LHS and RHS values
    print(
        f"Debug: STF = {stf}, Location = {location}, Tech = {tech}, LHS = {lhs}, RHS = {rhs}"
    )

    return lhs <= rhs
