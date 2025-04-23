import pandas as pd
from .input import get_input
from .output import get_constants, get_timeseries
from .util import is_string


def report(instance, filename, report_tuples=None, report_sites_name={}):
    """Write result summary to a spreadsheet file

    Args:
        - instance: a urbs model instance;
        - filename: Excel spreadsheet filename, will be overwritten if exists;
        - report_tuples: (optional) list of (sit, com) tuples for which to
          create detailed timeseries sheets;
        - report_sites_name: (optional) dict of names for created timeseries
          sheets
    """

    # default to all demand (sit, com) tuples if none are specified
    if report_tuples is None:
        report_tuples = get_input(instance, "demand").columns

    (
        costs,
        cpro,
        ctra,
        csto,
        cext,
        updated_cpro,
        cost_df_combined,
        capacity_ext_total,
        df_co2,
        combined_balance,
        decisionvalues_pri,
        decisionvalues_sec,
        scrapdf,
        decomdf,
        inst_processes_time,
        df_total_co2,
    ) = get_constants(instance)

    # create spreadsheet writer object
    with pd.ExcelWriter(filename) as writer:
        #################################################################################
        # dynamic feedback loop reports
        decisionvalues_pri.to_excel(writer, sheet_name="us_BDpri_values")
        decisionvalues_sec.to_excel(writer, sheet_name="us_BDsec_values")

        # urbs-ext reports
        cext.to_excel(writer, sheet_name="extension_only_caps")
        cost_df_combined.to_excel(writer, sheet_name="extension_cost")
        updated_cpro.to_excel(writer, sheet_name="extension_total_caps")
        combined_balance.to_excel(writer, sheet_name="extension_balance", index=False)
        df_co2.to_excel(writer, sheet_name="us_co2", index=False)
        capacity_ext_total.to_excel(writer, sheet_name="extension_only_totalcapacity")
        scrapdf.to_excel(writer, sheet_name="scrap")
        decomdf.to_excel(writer, sheet_name="decom")
        inst_processes_time.to_excel(writer, sheet_name="inst_process")
        df_total_co2.to_excel(writer, sheet_name="total_co2")

        #################################################################################

        # write constants to spreadsheet
        costs.to_frame().to_excel(writer, sheet_name="Costs")
        cpro.to_excel(writer, sheet_name="Process caps")
        ctra.to_excel(writer, sheet_name="Transmission caps")
        csto.to_excel(writer, sheet_name="Storage caps")

        # initialize timeseries tableaus
        energies = []
        timeseries = {}
        help_ts = {}

        # collect timeseries data
        for stf, sit, com in report_tuples:
            # wrap single site name in 1-element list for consistent behavior
            if is_string(sit):
                help_sit = [sit]
            else:
                help_sit = sit
                sit = tuple(sit)

            # check existence of predefined names, else define them
            try:
                report_sites_name[sit]
            except BaseException:
                report_sites_name[sit] = str(sit)

            for lv in help_sit:
                (created, consumed, stored, imported, exported, dsm, voltage_angle) = (
                    get_timeseries(instance, stf, com, lv)
                )

                overprod = pd.DataFrame(
                    columns=["Overproduction"],
                    data=created.sum(axis=1)
                    - consumed.sum(axis=1)
                    + imported.sum(axis=1)
                    - exported.sum(axis=1)
                    + stored["Retrieved"]
                    - stored["Stored"],
                )

                tableau = pd.concat(
                    [
                        created,
                        consumed,
                        stored,
                        imported,
                        exported,
                        overprod,
                        dsm,
                        voltage_angle,
                    ],
                    axis=1,
                    keys=[
                        "Created",
                        "Consumed",
                        "Storage",
                        "Import from",
                        "Export to",
                        "Balance",
                        "DSM",
                        "Voltage Angle",
                    ],
                )
                help_ts[(stf, lv, com)] = tableau.copy()

                # timeseries sums
                help_sums = pd.concat(
                    [
                        created.sum(),
                        consumed.sum(),
                        stored.sum().drop("Level"),
                        imported.sum(),
                        exported.sum(),
                        overprod.sum(),
                        dsm.sum(),
                    ],
                    axis=0,
                    keys=[
                        "Created",
                        "Consumed",
                        "Storage",
                        "Import",
                        "Export",
                        "Balance",
                        "DSM",
                    ],
                )
                try:
                    timeseries[(stf, report_sites_name[sit], com)] = timeseries[
                        (stf, report_sites_name[sit], com)
                    ].add(help_ts[(stf, lv, com)], axis=1, fill_value=0)
                    sums = sums.add(help_sums, fill_value=0)
                except BaseException:
                    timeseries[(stf, report_sites_name[sit], com)] = help_ts[
                        (stf, lv, com)
                    ]
                    sums = help_sums

            # timeseries sums
            sums = pd.concat(
                [
                    created.sum(),
                    consumed.sum(),
                    stored.sum().drop("Level"),
                    imported.sum(),
                    exported.sum(),
                    overprod.sum(),
                    dsm.sum(),
                ],
                axis=0,
                keys=[
                    "Created",
                    "Consumed",
                    "Storage",
                    "Import",
                    "Export",
                    "Balance",
                    "DSM",
                ],
            )
            energies.append(sums.to_frame("{}.{}.{}".format(stf, sit, com)))

        # write timeseries data (if any)
        if timeseries:
            # concatenate Commodity sums
            energy = pd.concat(energies, axis=1).fillna(0)
            energy.to_excel(writer, sheet_name="Commodity sums")

            # write timeseries to individual sheets
            for stf, sit, com in report_tuples:
                if isinstance(sit, list):
                    sit = tuple(sit)
                # sheet names cannot be longer than 31 characters...
                sheet_name = "{}.{}.{} timeseries".format(
                    stf, report_sites_name[sit], com
                )[:31]
                timeseries[(stf, report_sites_name[sit], com)].to_excel(
                    writer, sheet_name=sheet_name
                )
