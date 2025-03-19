import shutil
import os
import pandas as pd
from openpyxl import load_workbook

# SCENARIO GENERATORS
# In this script a variety of scenario generator functions are defined to
# facilitate scenario definitions.

########################################################################################################################
########################################################################################################################
########################################################################################################################
#############################################----us_szenarios----#######################################################
########################################################################################################################
########################################################################################################################
########################################################################################################################


# base
def scenario_base(data, data_urbsextensionv1):
    if "process" in data:
        pro = data["process"]
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                pro.loc[(stf, "EU27", "Wind (onshore)"), "inst-cap"] = 0
                pro.loc[(stf, "EU27", "Wind (offshore)"), "inst-cap"] = 0

            else:
                pro.loc[(stf, "EU27", "Wind (onshore)"), "cap-up"] = 0
                pro.loc[(stf, "EU27", "Wind (offshore)"), "cap-up"] = 0

    print(data["process"])

    return data, data_urbsextensionv1


def scenario_base_nocap(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    if not data:
        print("Warning: param_dict is empty.")
        return (
            data,
            param_dict,
            importcost_dict,
            instalable_capacity_dict,
            eu_primary_cost_dict,
            eu_secondary_cost_dict,
            dcr_dict,
            stocklvl_dict,
            stocklvl_dict,
        )

    if "process" in data:
        pro = data["process"]
        for stf in data["global_prop"].index.levels[0].tolist():
            pro.loc[(stf, "EU27", "Coal Plant"), "cap-up"] = 999999  # Value for cap up
            pro.loc[(stf, "EU27", "Coal Lignite"), "cap-up"] = (
                999999  # Value for cap up
            )
            pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "cap-up"] = (
                999999  # Value for cap up
            )
    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
    )


########################################################################################################################


# normal fossil fuel and delayed CO2 pricing
def scenario_1(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    if not data:
        print("Warning: param_dict is empty.")
        return (
            data,
            param_dict,
            importcost_dict,
            instalable_capacity_dict,
            eu_primary_cost_dict,
            eu_secondary_cost_dict,
            dcr_dict,
            stocklvl_dict,
        )
    elif "commodity" in data:
        co = data["commodity"]
        for stf in data["global_prop"].index.levels[0].tolist():
            # Check if the year (stf) is before 2030
            if stf < 2030:
                # Set CO2 price to 0 for years before 2030

                # SEB_ https://tradingeconomics.com/commodity/carbon ==> 60-70 EUR/tCO2

                co.loc[(stf, "EU27", "CO2", "Env"), "price"] = (
                    70  # aktueller Marktwert nehmen
                )
            else:
                # Keep the existing values for 2030 and later years
                co.loc[(stf, "EU27", "CO2", "Env"), "price"] = co.loc[
                    (stf, "EU27", "CO2", "Env"), "price"
                ]

        return (
            data,
            param_dict,
            importcost_dict,
            instalable_capacity_dict,
            eu_primary_cost_dict,
            eu_secondary_cost_dict,
            dcr_dict,
            stocklvl_dict,
        )
    else:
        print("Warning: 'commodity' not found in data.")


########################################################################################################################


# high fossil fuel and CO2 prices
def scenario_2(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    if not data:
        print("Warning: data is empty.")
        return (
            data,
            param_dict,
            importcost_dict,
            instalable_capacity_dict,
            eu_primary_cost_dict,
            eu_secondary_cost_dict,
            dcr_dict,
            stocklvl_dict,
        )
    elif "commodity" in data:
        co = data["commodity"]
        fossil_fuels = ["Lignite", "Gas", "Coal", "Nuclear Fuel"]
        for stf in data["global_prop"].index.levels[0].tolist():
            # SEB_ Wenn wir ein "High CO2 Price Szenario" haben, dann sollte dort der Preis
            # schon zwischen 200 und 350 EUR/tCO2 sein.

            co.loc[(stf, "EU27", "CO2", "Env"), "price"] = 250
            for fuel in fossil_fuels:
                co.loc[(stf, "EU27", fuel, "Stock"), "price"] *= 1.5
        return (
            data,
            param_dict,
            importcost_dict,
            instalable_capacity_dict,
            eu_primary_cost_dict,
            eu_secondary_cost_dict,
            dcr_dict,
            stocklvl_dict,
        )
    else:
        print("Warning: 'commodity' not found in data.")


########################################################################################################################

# No Significant CO2 Price Increase

# SEB_ Ich würde hier vielleicht eher von "No Significant CO2 Price Increase" sprechen...
# also zum Beispiel den CO2 Preis bis 2050 auf 65 EUR/tCO2 setzen


def scenario_3(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    if not data:
        print("Warning: data is empty.")
        return (
            data,
            param_dict,
            importcost_dict,
            instalable_capacity_dict,
            eu_primary_cost_dict,
            eu_secondary_cost_dict,
            dcr_dict,
            stocklvl_dict,
        )
    elif "commodity" in data:
        co = data["commodity"]
        for stf in data["global_prop"].index.levels[0].tolist():
            co.loc[(stf, "EU27", "CO2", "Env"), "price"] = 65  # set co2 price to 0
        return (
            data,
            param_dict,
            importcost_dict,
            instalable_capacity_dict,
            eu_primary_cost_dict,
            eu_secondary_cost_dict,
            dcr_dict,
            stocklvl_dict,
        )
    else:
        print("Warning: 'commodity' not found in data.")


########################################################################################################################

# Favorable CCS Market Conditions

# SEB_ Ich würde hier vielleicht eher von "Favorable CCS Market Conditions" sprechen...


def scenario_4(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    if not data:
        print("One or more dictionaries are empty. Returning original data.")
        return (
            data,
            param_dict,
            importcost_dict,
            instalable_capacity_dict,
            eu_primary_cost_dict,
            eu_secondary_cost_dict,
            dcr_dict,
            stocklvl_dict,
        )

    if "processes" in data:
        pro = data["processes"]
        for stf in data["global_prop"].index.levels[0].tolist():
            # SEB_ Warum geht CCS für COAL ab 2029 und für Gas erst ab 2033?
            # Kannst du alle Technologien einfach ab 2035 machen bitte...Eventuell ab 2030 mit 0.9 der Investitionskosten
            # und dann ab 2035 mit 0.75 (so wie ich unten schreibe)

            if stf >= 2030:
                # SEB_ Auf welchen Wert ist 'cap-up' ursprünglich gesetzt, also bevor du den Wert auf 9999 setzt? Max: aktuell disabled
                # Welche Einheit hat der Wert 9999, sind das GW? Max: MW
                pro.loc[(stf, "EU27", "Coal CCUS"), "cap-up"] = 999999
                pro.loc[(stf, "EU27", "Coal CCUS"), "inv-cost"] *= 0.9
                pro.loc[(stf, "EU27", "Coal Lignite CCUS"), "cap-up"] = 999999
                pro.loc[(stf, "EU27", "Coal Lignite CCUS"), "inv-cost"] *= 0.9
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "cap-up"] = 999999
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "inv-cost"] *= 0.9
            if stf >= 2035:
                # SEB_ Ich würde da noch etwas stärker die Investitionskosten reduzieren, vielleicht so 0.75
                pro.loc[(stf, "EU27", "Coal CCUS"), "cap-up"] = 999999
                pro.loc[(stf, "EU27", "Coal CCUS"), "inv-cost"] *= 0.75
                pro.loc[(stf, "EU27", "Coal Lignite CCUS"), "cap-up"] = 999999
                pro.loc[(stf, "EU27", "Coal Lignite CCUS"), "inv-cost"] *= 0.75
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "cap-up"] = 999999
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "inv-cost"] *= 0.75

    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
        stocklvl_dict,
    )


########################################################################################################################
# TODO DISABLE!!!
# low investement into CCUS technology

# SEB_ Dieses Szenario können wir streichen...das brauchen wir nicht!
# Kannst du mir nur erklären, was du dir bei dem =*4 von unten gedacht hast?
# Max: Durch geringere investition wird die technologie nicht so stark erforscht und wird nicht so effizient


def scenario_5(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    if not data:
        print("One or more dictionaries are empty. Returning original data.")
        return (
            data,
            param_dict,
            importcost_dict,
            instalable_capacity_dict,
            eu_primary_cost_dict,
            eu_secondary_cost_dict,
            dcr_dict,
            stocklvl_dict,
        )

    if "processes" in data:
        pro = data["processes"]
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf >= 2029:
                pro.loc[(stf, "EU27", "Coal CCUS"), "cap-up"] = 999999
                pro.loc[(stf, "EU27", "Coal CCUS"), "inv-cost"] *= 1.1
                pro.loc[(stf, "EU27", "Coal Lignite CCUS"), "cap-up"] = 999999
                pro.loc[(stf, "EU27", "Coal Lignite CCUS"), "inv-cost"] *= 1.1
            if stf >= 2033:
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "cap-up"] = 999999
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "inv-cost"] *= 1.1
    if "process_commodity" in data:
        proco = data["process_commodity"]
        for stf in data["global_prop"].index.levels[0].tolist():
            proco.loc[(stf, "Coal CCUS", "CO2", "Out"), "ratio"] *= 4
            proco.loc[(stf, "Coal Lignite CCUS", "CO2", "Out"), "ratio"] *= 4
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "CO2", "Out"), "ratio"] *= 4
    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
        stocklvl_dict,
    )


########################################################################################################################

# phase out of fossil fuels with anticipated target years


def scenario_6(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    if not data:
        print("Warning: param_dict is empty.")
        return (
            data,
            param_dict,
            importcost_dict,
            instalable_capacity_dict,
            eu_primary_cost_dict,
            eu_secondary_cost_dict,
            dcr_dict,
            stocklvl_dict,
        )
    elif "process" in data:
        pro = data["process"]
        for stf in data["global_prop"].index.levels[0].tolist():
            print(stf)
            if "lifetime" in pro.columns:  # Check for the specific timeframe
                try:
                    # Modify the process lifetimes as per the scenario

                    # SEB_ Was hast du sonst für Lifetimes angenommen? Max: geplanter Phase Out aus dieser Technologie RePowerEu
                    # Hat das einen speziellen Grund, dass es 10, 5, und 9 Jahre sind? Max: siehe oben

                    pro.loc[(stf, "EU27", "Coal Plant"), "lifetime"] = (
                        10  # new phaseout years 2024 + value
                    )
                    pro.loc[(stf, "EU27", "Coal Lignite"), "lifetime"] = (
                        5  # new phaseout years 2024 + value
                    )
                    pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "lifetime"] = (
                        9  # new phaseout years 2024 + value
                    )
                except KeyError as e:
                    print(
                        f"Warning: KeyError for {e}. The process might not exist for 2024."
                    )
            else:
                # If the row is not for 2024, we simply skip it.
                print(f"Skipping year {stf} as it's not 2024.")

        return (
            data,
            param_dict,
            importcost_dict,
            instalable_capacity_dict,
            eu_primary_cost_dict,
            eu_secondary_cost_dict,
            dcr_dict,
        )
    else:
        print("Warning: 'process' not found in data.")


########################################################################################################################

# delayed fossil fuel phaseout same as scenario 6


# SEB_ Sollte "Delayed" nicht dann eher 15, 10, und 10 zum Beispiel sein?
# Max: guter Input, wurde angepasst
def scenario_7(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    if not data:
        print("Warning: param_dict is empty.")
        return (
            data,
            param_dict,
            importcost_dict,
            instalable_capacity_dict,
            eu_primary_cost_dict,
            eu_secondary_cost_dict,
            dcr_dict,
            stocklvl_dict,
        )
    elif "process" in data:
        pro = data["process"]
        for stf in data["global_prop"].index.levels[0].tolist():
            print(stf)
            if "lifetime" in pro.columns:  # Check for the specific timeframe
                try:
                    # Modify the process lifetimes as per the scenario
                    pro.loc[(stf, "EU27", "Coal Plant"), "lifetime"] = (
                        5  # new phaseout years 2024 + value 2030
                    )
                    pro.loc[(stf, "EU27", "Coal Lignite"), "lifetime"] = (
                        5  # new phaseout years 2024 + value 2030
                    )
                    pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "lifetime"] = (
                        10  # new phaseout years 2024 + value  2033
                    )
                except KeyError as e:
                    print(
                        f"Warning: KeyError for {e}. The process might not exist for 2024."
                    )
            else:
                # If the row is not for 2024, we simply skip it.
                print(f"Skipping year {stf} as it's not 2024.")

        return (
            data,
            param_dict,
            importcost_dict,
            instalable_capacity_dict,
            eu_primary_cost_dict,
            eu_secondary_cost_dict,
            dcr_dict,
            stocklvl_dict,
        )
    else:
        print("Warning: 'process' not found in data.")


########################################################################################################################


# CCUS instead of normal fossil power plants after phase out
def scenario_8(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    if not data:
        print("One or more dictionaries are empty. Returning original data.")
        return (
            data,
            param_dict,
            importcost_dict,
            instalable_capacity_dict,
            eu_primary_cost_dict,
            eu_secondary_cost_dict,
            dcr_dict,
            stocklvl_dict,
        )

    if "processes" in data:
        pro = data["processes"]
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf >= 2029:
                pro.loc[(stf, "EU27", "Coal CCUS"), "cap-up"] = 999999
                pro.loc[(stf, "EU27", "Coal Lignite CCUS"), "cap-up"] = 999999
            if stf >= 2033:
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "cap-up"] = 999999

    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
        stocklvl_dict,
    )


########################################################################################################################


# meeting expansion plans for REPowerEU
def scenario_9(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    # SEB_ Wie stellst du sicher, dass REPowerEU plan erreicht wird hier? Max: wird bereits im TYNDP Scenario base mehr oder weniger bedacht
    # Base ist erfüllt RePowerEU schon

    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
        stocklvl_dict,
    )


########################################################################################################################


# high tolerance for RES expansion
def scenario_10(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    if not data or not instalable_capacity_dict:
        print("One or more dictionaries are empty. Returning original data.")
        return (
            data,
            param_dict,
            importcost_dict,
            instalable_capacity_dict,
            eu_primary_cost_dict,
            eu_secondary_cost_dict,
            dcr_dict,
        )

    if "process" in data:
        pro = data["process"]
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf <= 2030.0:
                pro.loc[(stf, "EU27", "Wind (onshore)"), "cap-up"] = (
                    379885  # Value for cap up
                )
                pro.loc[(stf, "EU27", "Wind (offshore)"), "cap-up"] = (
                    240293  # Value for cap up
                )
                pro.loc[(stf, "EU27", "Hydro (run-of-river)"), "cap-up"] = (
                    50000  # Value for cap up
                )
                pro.loc[(stf, "EU27", "Hydro (reservoir)"), "cap-up"] = (
                    80000  # Value for cap up
                )
            elif stf <= 2040.0:
                pro.loc[(stf, "EU27", "Wind (onshore)"), "cap-up"] = (
                    620169  # Value for cap up
                )
                pro.loc[(stf, "EU27", "Wind (offshore)"), "cap-up"] = (
                    458034  # Value for cap up
                )
                pro.loc[(stf, "EU27", "Hydro (run-of-river)"), "cap-up"] = (
                    80000  # Value for cap up
                )
                pro.loc[(stf, "EU27", "Hydro (reservoir)"), "cap-up"] = (
                    110000  # Value for cap up
                )
            else:
                pro.loc[(stf, "EU27", "Wind (onshore)"), "cap-up"] = (
                    799440  # Value for cap up
                )
                pro.loc[(stf, "EU27", "Wind (offshore)"), "cap-up"] = (
                    675796  # Value for cap up
                )
                pro.loc[(stf, "EU27", "Hydro (run-of-river)"), "cap-up"] = (
                    110000  # Value for cap up
                )
                pro.loc[(stf, "EU27", "Hydro (reservoir)"), "cap-up"] = (
                    140000  # Value for cap up
                )

    if "Instalable Capacity" in instalable_capacity_dict:
        for year, cap in instalable_capacity_dict.items():
            try:
                year_int = int(year)
                if year_int >= 2024:
                    new_cap = float(cap) * 1.1  # Factor by how much
                    instalable_capacity_dict[year] = new_cap
            except ValueError:
                print(f"Warning: Non-numeric year '{year}' found. Skipping.")
        print("Updated eu_primary_cost_dict:", instalable_capacity_dict)

    # Return the updated dictionaries/data
    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
    )


########################################################################################################################


# low tolerance for RES expansion
def scenario_11(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    if not data or not instalable_capacity_dict:
        print("One or more dictionaries are empty. Returning original data.")
        return (
            data,
            param_dict,
            importcost_dict,
            instalable_capacity_dict,
            eu_primary_cost_dict,
            eu_secondary_cost_dict,
            dcr_dict,
            stocklvl_dict,
        )

    if "process" in data:
        pro = data["process"]
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf <= 2030.0:
                pro.loc[(stf, "EU27", "Wind (onshore)"), "cap-up"] = (
                    299697  # Value for cap up
                )
                pro.loc[(stf, "EU27", "Wind (offshore)"), "cap-up"] = (
                    100989  # Value for cap up
                )
                pro.loc[(stf, "EU27", "Hydro (run-of-river)"), "cap-up"] = (
                    46710  # Value for cap up
                )
                pro.loc[(stf, "EU27", "Hydro (reservoir)"), "cap-up"] = (
                    59840  # Value for cap up
                )
            elif stf <= 2040.0:
                pro.loc[(stf, "EU27", "Wind (onshore)"), "cap-up"] = (
                    377767  # Value for cap up
                )
                pro.loc[(stf, "EU27", "Wind (offshore)"), "cap-up"] = (
                    269420  # Value for cap up
                )
                pro.loc[(stf, "EU27", "Hydro (run-of-river)"), "cap-up"] = (
                    46710  # Value for cap up
                )
                pro.loc[(stf, "EU27", "Hydro (reservoir)"), "cap-up"] = (
                    59840  # Value for cap up
                )
            else:
                pro.loc[(stf, "EU27", "Wind (onshore)"), "cap-up"] = (
                    414687  # Value for cap up
                )
                pro.loc[(stf, "EU27", "Wind (offshore)"), "cap-up"] = (
                    377545  # Value for cap up
                )
                pro.loc[(stf, "EU27", "Hydro (run-of-river)"), "cap-up"] = (
                    46710  # Value for cap up
                )
                pro.loc[(stf, "EU27", "Hydro (reservoir)"), "cap-up"] = (
                    59840  # Value for cap up
                )

    if "Instalable Capacity" in instalable_capacity_dict:
        for year, cap in instalable_capacity_dict.items():
            try:
                year_int = int(year)
                if year_int >= 2024:
                    new_cap = float(cap) * 0.8  # Factor by how much
                    instalable_capacity_dict[year] = new_cap
            except ValueError:
                print(f"Warning: Non-numeric year '{year}' found. Skipping.")
        print("Updated eu_primary_cost_dict:", instalable_capacity_dict)

        # Return the updated dictionaries/data
    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
    )


########################################################################################################################

# high importcost due to importtolls on solar modules


# SEB_ Faktor 3 scheint mir schon sehr hoch, machen wir eher Faktor 2... Max: erledigt
# und wie genau funktioniert das dann mit den (1) Updated Costs und (2) Anti Dumping Index?
# ab dem jahr 2035 wird dann der hinterlegte price im Input file * 2 genommen. Beim ADI ab startjahr dann
# max: erledigt
def scenario_12(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    if not importcost_dict or not param_dict:
        print("Warning: importcost_dict is empty.")
        return (
            data,
            param_dict,
            importcost_dict,
            instalable_capacity_dict,
            eu_primary_cost_dict,
            eu_secondary_cost_dict,
            dcr_dict,
            stocklvl_dict,
        )
    for year, cost in importcost_dict.items():
        try:
            year_int = int(year)
            if year_int >= 2035:  # year where importcost suddenly rises
                new_cost = float(cost) * 2  # Factor by how much
                importcost_dict[year] = new_cost
        except ValueError:
            print(f"Warning: Non-numeric year '{year}' found. Skipping.")

    if "anti dumping Index" in param_dict:
        current_value = float(param_dict["anti dumping Index"])
        new_value = current_value + 0.05  # add 5% startwert 0
        param_dict["anti dumping Index"] = new_value
        print("anti dumping Index updated.")
    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
        stocklvl_dict,
    )


########################################################################################################################

# subsidees on eu manufacturing in order to achieve independence from China

# SEB_ Würde hier etwas stärker unterstützen, zum Beispiel 0.75 (statt 0.9) Max: erledigt


def scenario_13(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    if not eu_primary_cost_dict or not param_dict:
        print("Warning: importcost_dict is empty.")
        return (
            data,
            param_dict,
            importcost_dict,
            instalable_capacity_dict,
            eu_primary_cost_dict,
            eu_secondary_cost_dict,
            dcr_dict,
            stocklvl_dict,
        )
    for year, cost in eu_primary_cost_dict.items():
        try:
            year_int = int(year)
            if year_int >= 2024:  # year where manufacturing gets cheaper
                new_cost = float(cost) * 0.75  # Factor by how much
                importcost_dict[year] = new_cost
        except ValueError:
            print(f"Warning: Non-numeric year '{year}' found. Skipping.")

    if "anti dumping Index" in param_dict:
        current_value = float(param_dict["anti dumping Index"])
        new_value = current_value + 0.05  # add 5%
        param_dict["anti dumping Index"] = new_value
        print("anti dumping Index updated.")
    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
    )


########################################################################################################################

# complete importstop on solar modules from China due to sanctions


def scenario_14(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    if not importcost_dict:
        print("Warning: importcost_dict is empty.")
        return (
            data,
            param_dict,
            importcost_dict,
            instalable_capacity_dict,
            eu_primary_cost_dict,
            eu_secondary_cost_dict,
            dcr_dict,
            stocklvl_dict,
        )
    for year, cost in importcost_dict.items():
        try:
            year_int = int(year)
            if year_int >= 2035:  # sudden import stop
                new_cost = float(cost) * 9999999999999  # Factor by how much
                importcost_dict[year] = new_cost
        except ValueError:
            print(f"Warning: Non-numeric year '{year}' found. Skipping.")
    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
        stocklvl_dict,
    )


########################################################################################################################

# high investements and development for domestic production and recycling

# SEB_ Heißt das, IR von 5%, das ist zu Gering...Würde eher 0.5 (also 50%) machen...
# Max: erledigt


def scenario_15(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    if not param_dict or not eu_primary_cost_dict or not eu_secondary_cost_dict:
        print("One or more dictionaries are empty. Returning original data.")
        return (
            data,
            param_dict,
            importcost_dict,
            instalable_capacity_dict,
            eu_primary_cost_dict,
            eu_secondary_cost_dict,
            dcr_dict,
            stocklvl_dict,
        )

    # Check if 'commodity' exists in the data and modify it
    if "IR EU Primary" in param_dict:
        current_value = float(param_dict["IR EU Primary"])
        new_value = current_value + 0.1  # add 5% current IR: 0,3741
        param_dict["IR EU Primary"] = new_value
        print("IR EU updated.")

    # Check if param_dict exists and modify it if needed
    if "IR EU Secondary" in param_dict:
        current_value = float(param_dict["IR EU Secondary"])
        new_value = current_value + 0.1  # add 5% current IR: 0,3888
        param_dict["IR EU Secondary"] = new_value
        print("IR secondary updated.")

    if "anti dumping Index" in param_dict:
        current_value = float(param_dict["anti dumping Index"])
        new_value = current_value + 0.05  # add 5%
        param_dict["anti dumping Index"] = new_value
        print("anti dumping Index updated.")

    # SEB_ machen wir da eher 2030 statt 2024 jeweils
    # Max: erledigt

    # Modify the eu_primary_cost_dict if applicable
    if eu_primary_cost_dict:
        for year, cost in eu_primary_cost_dict.items():
            try:
                year_int = int(year)
                if year_int >= 2030:  # year where manufacturing gets cheaper
                    new_cost = float(cost) * 0.6  # Factor by how much
                    eu_primary_cost_dict[year] = new_cost
            except ValueError:
                print(f"Warning: Non-numeric year '{year}' found. Skipping.")
        print("Updated eu_primary_cost_dict:", eu_primary_cost_dict)
    # modify eu secondary cost
    if eu_secondary_cost_dict:
        for year, cost in eu_secondary_cost_dict.items():
            try:
                year_int = int(year)
                if year_int >= 2030:  # year where manufacturing gets cheaper
                    new_cost = float(cost) * 0.8  # Factor by how much
                    eu_secondary_cost_dict[year] = new_cost
            except ValueError:
                print(f"Warning: Non-numeric year '{year}' found. Skipping.")
        print("Updated eu_secondary_cost_dict:", eu_secondary_cost_dict)
    # Return the updated dictionaries/data
    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
        stocklvl_dict,
    )


########################################################################################################################

# high volatility for domestic production and recycling

# SEB_ Hier sollten wir aus meiner Sicht IR und DR auf eher hohe Werte (zum Beispiel IR auf 0.5 und DR auf 0.35) setzen
# Max: DR aktuell auf 0.8 im Base, habe iuch gleichung falsch verstanden?


def scenario_16(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    if not param_dict:
        print("One or more dictionaries are empty. Returning original data.")
        return (
            data,
            param_dict,
            importcost_dict,
            instalable_capacity_dict,
            eu_primary_cost_dict,
            eu_secondary_cost_dict,
            dcr_dict,
            stocklvl_dict,
        )

    # Check if 'commodity' exists in the data and modify it
    if "DR Primary" in param_dict:
        current_value = float(param_dict["DR Primary"])
        new_value = 0.35  # new DR value
        param_dict["DR Primary"] = new_value
        print("DR updated.")

    # Check if param_dict exists and modify it if needed
    if "DR Secondary" in param_dict:
        current_value = float(param_dict["DR Secondary"])
        new_value = 0.35  # new DR value
        param_dict["DR Secondary"] = new_value
        print("DR updated.")

    if "IR EU Primary" in param_dict:
        current_value = float(param_dict["IR EU Primary"])
        new_value = 0.5
        param_dict["IR EU Primary"] = new_value
        print("IR EU updated.")

    # Check if param_dict exists and modify it if needed
    if "IR EU Secondary" in param_dict:
        current_value = float(param_dict["IR EU Secondary"])
        new_value = 0.5
        param_dict["IR EU Secondary"] = new_value
        print("IR secondary updated.")

    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
        stocklvl_dict,
    )


########################################################################################################################

# low volatility for domestic production and recycling

# SEB_ Hier sollten dann eher kleinerer Werte drinnen stehen (z.B. jeweils 0.2, statt 0.9)
# Max: erledigt


def scenario_17(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    if not param_dict:
        print("One or more dictionaries are empty. Returning original data.")
        return (
            data,
            param_dict,
            importcost_dict,
            instalable_capacity_dict,
            eu_primary_cost_dict,
            eu_secondary_cost_dict,
            dcr_dict,
            stocklvl_dict,
        )

    # Check if 'commodity' exists in the data and modify it
    if "DR Primary" in param_dict:
        current_value = float(param_dict["DR Primary"])
        new_value = 0.2  # new DR value
        param_dict["DR Primary"] = new_value
        print("DR updated.")

    # Check if param_dict exists and modify it if needed
    if "DR Secondary" in param_dict:
        current_value = float(param_dict["DR Secondary"])
        new_value = 0.2  # new DR value
        param_dict["DR Secondary"] = new_value
        print("DR updated.")

    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
        stocklvl_dict,
    )


########################################################################################################################


# diversify import countries
def scenario_18(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    if not importcost_dict:
        print("Warning: importcost_dict is empty.")
        return (
            data,
            param_dict,
            importcost_dict,
            instalable_capacity_dict,
            eu_primary_cost_dict,
            eu_secondary_cost_dict,
            dcr_dict,
            stocklvl_dict,
        )
    for year, cost in importcost_dict.items():
        try:
            year_int = int(year)
            if year_int >= 2024:
                new_cost = (
                    float(cost) + 50000
                )  # Value by how much importcost increase for diversified
                importcost_dict[year] = new_cost
        except ValueError:
            print(f"Warning: Non-numeric year '{year}' found. Skipping.")
    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
    )


########################################################################################################################


# slow and steady reduction of CO2 emissions
def scenario_19(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    if not data:
        print("Warning: data is empty.")
        return (
            data,
            param_dict,
            importcost_dict,
            instalable_capacity_dict,
            eu_primary_cost_dict,
            eu_secondary_cost_dict,
            dcr_dict,
            stocklvl_dict,
        )

    # Predefined CO2 limit values for years 2024–2050
    co2_limit_slow_steady = [
        482000000,
        465000000,
        448000000,
        431000000,
        414000000,
        397000000,
        380000000,
        363000000,
        346000000,
        329000000,
        312000000,
        295000000,
        278000000,
        261000000,
        244000000,
        227000000,
        210000000,
        193000000,
        176000000,
        159000000,
        142000000,
        125000000,
        108000000,
        91000000,
        74000000,
        57000000,
        40000000,
    ]

    if "global_prop" in data:
        global_prop = data["global_prop"]

        # Apply CO2 limits for each year in the range 2024–2050
        for idx, year in enumerate(range(2024, 2051)):
            if year in global_prop.index.levels[0].tolist():
                global_prop.loc[(year, "CO2 limit"), "value"] = co2_limit_slow_steady[
                    idx
                ]
            else:
                print(f"Year {year} is not found in global_prop index levels.")
    else:
        print("Warning: 'global_prop' not found in data.")
    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
    )


########################################################################################################################


# late and rapid reduction of CO2 emissions
def scenario_20(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    if not data:
        print("Warning: data is empty.")
        return (
            data,
            param_dict,
            importcost_dict,
            instalable_capacity_dict,
            eu_primary_cost_dict,
            eu_secondary_cost_dict,
            dcr_dict,
            stocklvl_dict,
        )

    # Predefined CO2 limit values for years 2024–2050
    co2_limit_late_rapid = [
        505000000,
        505000000,
        505000000,
        505000000,
        500000000,
        490000000,
        475000000,
        460000000,
        440000000,
        415000000,
        390000000,
        350000000,
        290000000,
        220000000,
        150000000,
        100000000,
        75000000,
        60000000,
        50000000,
        40000000,
        30000000,
        25000000,
        20000000,
        15000000,
        10000000,
        5000000,
        3000000,
    ]

    if "global_prop" in data:
        global_prop = data["global_prop"]

        # Apply CO2 limits for each year in the range 2024–2050
        for idx, year in enumerate(range(2024, 2051)):
            if year in global_prop.index.levels[0].tolist():
                global_prop.loc[(year, "CO2 limit"), "value"] = co2_limit_late_rapid[
                    idx
                ]
            else:
                print(f"Year {year} is not found in global_prop index levels.")
    else:
        print("Warning: 'global_prop' not found in data.")
    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
        stocklvl_dict,
    )


########################################################################################################################


# 100% decarbonization of energy sector
def scenario_21(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    if not data:
        print("Warning: data is empty.")
        return (
            data,
            param_dict,
            importcost_dict,
            instalable_capacity_dict,
            eu_primary_cost_dict,
            eu_secondary_cost_dict,
        )
    if "global_prop" in data:
        global_prop = data["global_prop"]
        for stf in global_prop.index.levels[0].tolist():
            if stf >= 2050:
                global_prop.loc[(stf, "CO2 limit"), "value"] = 0
            else:
                print(f"Skipping year {stf} as it's not 2024.")

    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
        stocklvl_dict,
    )


########################################################################################################################


# staying below 1.5 degrees
def scenario_22(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
    )


########################################################################################################################


# above 2 degrees
def scenario_23(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
    )


########################################################################################################################


# SEB_ das Szenario brauchen wir nicht...
# Max: alles klar TODO DISABLE
# abort all climate change measures since USA left Paris Climate Agreement
def scenario_24(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    if not data:
        print("Warning: data is empty.")
        return (
            data,
            param_dict,
            importcost_dict,
            instalable_capacity_dict,
            eu_primary_cost_dict,
            eu_secondary_cost_dict,
            dcr_dict,
        )
    if "commodity" in data:
        co = data["commodity"]
        for stf in data["global_prop"].index.levels[0].tolist():
            co.loc[(stf, "EU27", "CO2", "Env"), "price"] = 0  # set co2 price to 0
    if "global_prop" in data:
        global_prop = data["global_prop"]
        for stf in global_prop.index.levels[0].tolist():
            global_prop.loc[(stf, "CO2 limit"), "value"] = (
                999999999999999999999999999999
            )
            global_prop.loc[(stf, "CO2 budget"), "value"] = (
                999999999999999999999999999999
            )
    if "process" in data:
        pro = data["process"]
        for stf in data["global_prop"].index.levels[0].tolist():
            pro.loc[(stf, "EU27", "Coal Plant"), "cap-up"] = 9999999  # Value for cap up
            pro.loc[(stf, "EU27", "Coal Lignite"), "cap-up"] = (
                9999999  # Value for cap up
            )
            pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "cap-up"] = (
                9999999  # Value for cap up
            )

    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
    )


########################################################################################################################


# high electricity demand due to increasing electrification
def scenario_25(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    if not data:
        print("Warning: param_dict is empty.")
        return (
            data,
            param_dict,
            importcost_dict,
            instalable_capacity_dict,
            eu_primary_cost_dict,
            eu_secondary_cost_dict,
            dcr_dict,
        )
    elif "demand" in data:
        de = data["demand"]
        print(de.index)
        print(de.columns)
        for stf in de.index.levels[0].tolist():  # Iterate over support_timeframe
            for t in de.index.levels[1].tolist():  # Iterate over 't'
                # Try to print the value before modifying it
                print(
                    f"Before modification - Year {stf}, t={t}: {de.loc[(stf, t), ('EU27', 'Elec')]}"
                )
                # Increase the demand by 10% for the specific year and t
                de.loc[(stf, t), ("EU27", "Elec")] *= 1.1
                # Print the updated value
                print(
                    f"After modification - Year {stf}, t={t}: {de.loc[(stf, t), ('EU27', 'Elec')]}"
                )
        return (
            data,
            param_dict,
            importcost_dict,
            instalable_capacity_dict,
            eu_primary_cost_dict,
            eu_secondary_cost_dict,
            dcr_dict,
            stocklvl_dict,
        )
    else:
        print("Warning: 'demand' not found in data.")


########################################################################################################################


# technofriendly
def scenario_26(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    if (
        not data
        or not importcost_dict
        or not eu_primary_cost_dict
        or not eu_secondary_cost_dict
    ):
        print("Warning: importcost_dict is empty.")
        return (
            data,
            param_dict,
            importcost_dict,
            instalable_capacity_dict,
            eu_primary_cost_dict,
            eu_secondary_cost_dict,
            dcr_dict,
        )
    if importcost_dict:
        for year, cost in importcost_dict.items():
            try:
                year_int = int(year)
                if year_int >= 2024:
                    new_cost = float(cost) * 0.9  # Factor by how much
                    importcost_dict[year] = new_cost
            except ValueError:
                print(f"Warning: Non-numeric year '{year}' found. Skipping.")
        print("Updated importcost_dict:", importcost_dict)
        # Modify the eu_primary_cost_dict if applicable
    if eu_primary_cost_dict:
        for year, cost in eu_primary_cost_dict.items():
            try:
                year_int = int(year)
                if year_int >= 2024:
                    new_cost = float(cost) * 0.9
                    eu_primary_cost_dict[year] = new_cost
            except ValueError:
                print(f"Warning: Non-numeric year '{year}' found. Skipping.")
        print("Updated eu_primary_cost_dict:", eu_primary_cost_dict)
        # modify eu secondary cost
    if eu_secondary_cost_dict:
        for year, cost in eu_secondary_cost_dict.items():
            try:
                year_int = int(year)
                if year_int >= 2024:
                    new_cost = float(cost) * 0.9
                    eu_secondary_cost_dict[year] = new_cost
            except ValueError:
                print(f"Warning: Non-numeric year '{year}' found. Skipping.")
        print("Updated eu_secondary_cost_dict:", eu_secondary_cost_dict)
    if "processes" in data:
        pro = data["processes"]
        processes = [
            "Wind (onschore)",
            "Wind (offshore)",
            "Hydro (run-of-river)",
            "hydro (reservoir)",
            "Coal Plant",
            "Coal Lignite",
            "Gas Plant (CCGT)",
            "Nuclear Plant",
            "Biomass Plant",
        ]
        for stf in data["global_prop"].index.levels[0].tolist():
            for carrier in processes:
                co.loc[(stf, "EU27", carrier, "Env"), "inv-cost"] *= 0.9
                co.loc[(stf, "EU27", carrier, "Env"), "fix-cost"] *= 0.9
                co.loc[(stf, "EU27", carrier, "Env"), "var-cost"] *= 0.9

    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
        stocklvl_dict,
    )


########################################################################################################################


# global economical crisis
def scenario_27(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    if (
        not data
        or not importcost_dict
        or not eu_primary_cost_dict
        or not eu_secondary_cost_dict
    ):
        print("Warning: importcost_dict is empty.")
        return (
            data,
            param_dict,
            importcost_dict,
            instalable_capacity_dict,
            eu_primary_cost_dict,
            eu_secondary_cost_dict,
            dcr_dict,
            stocklvl_dict,
        )
    if importcost_dict:
        for year, cost in importcost_dict.items():
            try:
                year_int = int(year)
                if year_int >= 2024:
                    new_cost = float(cost) * 1.5  # Factor by how much
                    importcost_dict[year] = new_cost
            except ValueError:
                print(f"Warning: Non-numeric year '{year}' found. Skipping.")
        print("Updated importcost_dict:", importcost_dict)
        # Modify the eu_primary_cost_dict if applicable
    if eu_primary_cost_dict:
        for year, cost in eu_primary_cost_dict.items():
            try:
                year_int = int(year)
                if year_int >= 2024:
                    new_cost = float(cost) * 1.5
                    eu_primary_cost_dict[year] = new_cost
            except ValueError:
                print(f"Warning: Non-numeric year '{year}' found. Skipping.")
        print("Updated eu_primary_cost_dict:", eu_primary_cost_dict)
        # modify eu secondary cost
    if eu_secondary_cost_dict:
        for year, cost in eu_secondary_cost_dict.items():
            try:
                year_int = int(year)
                if year_int >= 2024:
                    new_cost = float(cost) * 1.5
                    eu_secondary_cost_dict[year] = new_cost
            except ValueError:
                print(f"Warning: Non-numeric year '{year}' found. Skipping.")
        print("Updated eu_secondary_cost_dict:", eu_secondary_cost_dict)
    if "processes" in data:
        pro = data["processes"]
        processes = [
            "Wind (onschore)",
            "Wind (offshore)",
            "Hydro (run-of-river)",
            "hydro (reservoir)",
            "Coal Plant",
            "Coal Lignite",
            "Gas Plant (CCGT)",
            "Nuclear Plant",
            "Biomass Plant",
        ]
        for stf in data["global_prop"].index.levels[0].tolist():
            for carrier in processes:
                pro.loc[(stf, "EU27", carrier, "Env"), "inv-cost"] *= 1.5
                pro.loc[(stf, "EU27", carrier, "Env"), "fix-cost"] *= 1.5
                pro.loc[(stf, "EU27", carrier, "Env"), "var-cost"] *= 1.5

    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
    )


# Rapid Solar Technology Advancement
def scenario_28(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
):
    if (
        not instalable_capacity_dict
        or not eu_primary_cost_dict
        or not eu_secondary_cost_dict
        or not param_dict
    ):
        print("Warning: Missing data for scenario 28.")
        return (
            data,
            param_dict,
            importcost_dict,
            instalable_capacity_dict,
            eu_primary_cost_dict,
            eu_secondary_cost_dict,
            dcr_dict,
        )

    # Reduce manufacturing and recycling costs
    if eu_primary_cost_dict:
        for year, cost in eu_primary_cost_dict.items():
            eu_primary_cost_dict[year] = float(cost) * 0.8  # Reduce costs by 20%
        print("Updated eu_primary_cost_dict:", eu_primary_cost_dict)

    if eu_secondary_cost_dict:
        for year, cost in eu_secondary_cost_dict.items():
            eu_secondary_cost_dict[year] = float(cost) * 0.8  # Reduce costs by 20%
        print("Updated eu_secondary_cost_dict:", eu_secondary_cost_dict)

    # Increase installable capacity
    if instalable_capacity_dict:
        for year, capacity in instalable_capacity_dict.items():
            instalable_capacity_dict[year] = (
                float(capacity) * 1.2
            )  # Increase capacity by 20%
        print("Updated instalable_capacity_dict:", instalable_capacity_dict)

    # if 'anti dumping Index' in param_dict:
    #    current_value = float(param_dict['anti dumping Index'])
    #    new_value = current_value - 0.05 # -5%
    #    param_dict['anti dumping Index'] = new_value
    #    print("anti dumping Index updated.")

    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
    )


# Global Trade War on Solar Materials
def scenario_29(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
):
    if not importcost_dict or not instalable_capacity_dict or not eu_primary_cost_dict:
        print("Warning: Missing data for scenario 29.")
        return (
            data,
            param_dict,
            importcost_dict,
            instalable_capacity_dict,
            eu_primary_cost_dict,
            eu_secondary_cost_dict,
            dcr_dict,
        )

    # Increase import costs
    for year, cost in importcost_dict.items():
        importcost_dict[year] = float(cost) * 1.5  # Increase import costs by 50%
    print("Updated importcost_dict:", importcost_dict)

    # Reduce installable capacity
    for year, capacity in instalable_capacity_dict.items():
        instalable_capacity_dict[year] = float(capacity) * 0.8  # Reduce capacity by 20%
    print("Updated instalable_capacity_dict:", instalable_capacity_dict)

    # Increase primary production cost
    for year, cost in eu_primary_cost_dict.items():
        eu_primary_cost_dict[year] = float(cost) * 1.5
    print("Updated eu_primary_cost_dict:", importcost_dict)

    if "anti dumping Index" in param_dict:
        current_value = float(param_dict["anti dumping Index"])
        new_value = current_value + 0.2  # +20%
        param_dict["anti dumping Index"] = new_value

    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
    )


# Circular Economy Revolution in Solar Modules
def scenario_30(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
):
    if not eu_primary_cost_dict or not eu_secondary_cost_dict or not importcost_dict:
        print("Warning: Missing data for scenario 30.")
        return (
            data,
            param_dict,
            importcost_dict,
            instalable_capacity_dict,
            eu_primary_cost_dict,
            eu_secondary_cost_dict,
            dcr_dict,
        )
    base_year = 2024  # Set the base year
    annual_reduction_rate = 0.025  # 2% annual reduction
    # normal recycling costs initially, then reduce due to high learning rate
    for year, cost in eu_secondary_cost_dict.items():
        try:
            year_int = int(year)
            if year_int >= base_year:
                # Apply the exponential decrease formula
                reduction_factor = (1 - annual_reduction_rate) ** (year_int - base_year)
                new_cost = float(cost) * reduction_factor
                eu_secondary_cost_dict[year] = new_cost
        except ValueError:
            print(f"Warning: Non-numeric year '{year}' found. Skipping.")
    print("Updated eu_secondary_cost_dict:", eu_secondary_cost_dict)

    # Reduce on imports
    for year, cost in importcost_dict.items():
        importcost_dict[year] = (
            float(cost) * 0.9
        )  # Decrease import costs by 10% due to lower demand
    print("Updated importcost_dict:", importcost_dict)

    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
    )


# Solar Module Overcapacity Crisis
def scenario_31(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
):
    if not eu_primary_cost_dict or not eu_secondary_cost_dict or not importcost_dict:
        print("Warning: Missing data for scenario 4.")
        return (
            data,
            param_dict,
            importcost_dict,
            instalable_capacity_dict,
            eu_primary_cost_dict,
            eu_secondary_cost_dict,
            dcr_dict,
        )

    # Reduce costs due to overcapacity
    for year, cost in eu_primary_cost_dict.items():
        eu_primary_cost_dict[year] = (
            float(cost) * 0.7
        )  # Reduce manufacturing costs by 30%
    print("Updated eu_primary_cost_dict:", eu_primary_cost_dict)

    for year, cost in eu_secondary_cost_dict.items():
        eu_secondary_cost_dict[year] = (
            float(cost) * 1.3
        )  # Increase recycling costs by 30%
    print("Updated eu_secondary_cost_dict:", eu_secondary_cost_dict)

    # Increase volatility in production
    if "DR Primary" in param_dict:
        current_value = float(param_dict["DR Primary"])
        new_value = 0.5  # new DR value
        param_dict["DR Primary"] = new_value
        print("DR updated.")

    # Check if param_dict exists and modify it if needed
    if "DR Secondary" in param_dict:
        current_value = float(param_dict["DR Secondary"])
        new_value = 0.5  # new DR value
        param_dict["DR Secondary"] = new_value
        print("DR updated.")

    if "anti dumping Index" in param_dict:
        current_value = float(param_dict["anti dumping Index"])
        new_value = 0
        param_dict["anti dumping Index"] = new_value
        print("anti dumping Index updated.")

    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
    )


# enable TO-Constraint!!
def scenario_32(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    if not importcost_dict or not param_dict:
        print("Warning: importcost_dict is empty.")
        return (
            data,
            param_dict,
            importcost_dict,
            instalable_capacity_dict,
            eu_primary_cost_dict,
            eu_secondary_cost_dict,
            dcr_dict,
            stocklvl_dict,
        )
    for year, cost in importcost_dict.items():
        try:
            year_int = int(year)
            if year_int >= 2035:  # year where importcost suddenly rises
                new_cost = float(cost) * 2  # Factor by how much
                importcost_dict[year] = new_cost
        except ValueError:
            print(f"Warning: Non-numeric year '{year}' found. Skipping.")

    if "anti dumping Index" in param_dict:
        current_value = float(param_dict["anti dumping Index"])
        new_value = current_value + 0.05  # add 5% startwert 0
        param_dict["anti dumping Index"] = new_value
        print("anti dumping Index updated.")
    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
        stocklvl_dict,
    )


# enable TO-Constraint!!
def scenario_33(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    if not importcost_dict:
        print("Warning: importcost_dict is empty.")
        return (
            data,
            param_dict,
            importcost_dict,
            instalable_capacity_dict,
            eu_primary_cost_dict,
            eu_secondary_cost_dict,
            dcr_dict,
            stocklvl_dict,
        )
    for year, cost in importcost_dict.items():
        try:
            year_int = int(year)
            if year_int >= 2035:  # sudden import stop
                new_cost = float(cost) * 9999999999999  # Factor by how much
                importcost_dict[year] = new_cost
        except ValueError:
            print(f"Warning: Non-numeric year '{year}' found. Skipping.")

    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
        stocklvl_dict,
    )


def scenario_34(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    print("SCENARIO 34 industrial act benchmark A")
    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
        stocklvl_dict,
    )


def scenario_35(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    print("SCENARIO 34 industrial act benchmark B")
    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
        stocklvl_dict,
    )


def scenario_36(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    if not importcost_dict:
        print("Warning: importcost_dict is empty.")
        return (
            data,
            param_dict,
            importcost_dict,
            instalable_capacity_dict,
            eu_primary_cost_dict,
            eu_secondary_cost_dict,
            dcr_dict,
            stocklvl_dict,
        )

    importcost_dict = {int(year): value for year, value in importcost_dict.items()}
    base_2030 = importcost_dict[2030]
    base_2040 = importcost_dict[2040]
    for year in range(2030, 2036):
        factor = 1 + ((year - 2030) / 5)  # Gradually increase to 2x in 2035
        importcost_dict[year] = base_2030 * factor
    for year in range(2036, 2041):
        factor = (2040 - year) / (2040 - 2035)  # Gradually return to base_2040
        importcost_dict[year] = base_2040 + (base_2030 * 2 - base_2040) * factor
    print("Updated importcost_dict:", importcost_dict)

    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
        stocklvl_dict,
    )


# enable TO-Constraint!!
def scenario_37(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    if not importcost_dict:
        print("Warning: importcost_dict is empty.")
        return (
            data,
            param_dict,
            importcost_dict,
            instalable_capacity_dict,
            eu_primary_cost_dict,
            eu_secondary_cost_dict,
            dcr_dict,
            stocklvl_dict,
        )

    importcost_dict = {int(year): value for year, value in importcost_dict.items()}
    base_2030 = importcost_dict[2030]
    base_2040 = importcost_dict[2040]
    for year in range(2030, 2036):
        factor = 1 + ((year - 2030) / 5)  # Gradually increase to 2x in 2035
        importcost_dict[year] = base_2030 * factor
    for year in range(2036, 2041):
        factor = (2040 - year) / (2040 - 2035)  # Gradually return to base_2040
        importcost_dict[year] = base_2040 + (base_2030 * 2 - base_2040) * factor
    print("Updated importcost_dict:", importcost_dict)

    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
        stocklvl_dict,
    )


def scenario_38(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    if not instalable_capacity_dict:
        print("Warning: instalable_capacity_dict is empty.")
        return (
            data,
            param_dict,
            importcost_dict,
            instalable_capacity_dict,
            eu_primary_cost_dict,
            eu_secondary_cost_dict,
            dcr_dict,
            stocklvl_dict,
        )

    years = list(range(2024, 2051))  # From 2024 to 2050 inclusive
    start_capacity_2024 = 56000  # in MW
    min_capacity_2040 = 40000  # in MW
    end_capacity_2050 = 60000  # in MW
    for year in range(2024, 2041):  # Includes 2040
        instalable_capacity_dict[year] = start_capacity_2024 + (
            min_capacity_2040 - start_capacity_2024
        ) * (year - 2024) / (2040 - 2024)

    for year in range(2040, 2051):  # Includes 2050
        instalable_capacity_dict[year] = min_capacity_2040 + (
            end_capacity_2050 - min_capacity_2040
        ) * (year - 2040) / (2050 - 2040)

    # Debugging: Print updated dictionary
    print("Updated instalable_capacity_dict:", instalable_capacity_dict)
    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
        stocklvl_dict,
    )


def scenario_39(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    if not instalable_capacity_dict:
        print("Warning: instalable_capacity_dict is empty.")
        return (
            data,
            param_dict,
            importcost_dict,
            instalable_capacity_dict,
            eu_primary_cost_dict,
            eu_secondary_cost_dict,
            dcr_dict,
            stocklvl_dict,
        )

    base_capacity_2024 = 56000  # in GW
    annual_increase_rate = 0.10  # 10% per year

    # Iterate through the years and calculate the capacity
    for year in sorted(instalable_capacity_dict.keys()):
        if year >= 2024:
            # Formula for exponential growth: value = initial * (1 + rate)^(year - start_year)
            instalable_capacity_dict[year] = base_capacity_2024 * (
                1 + annual_increase_rate
            ) ** (year - 2024)

    # Debugging: Print updated dictionary
    print("Updated instalable_capacity_dict:", instalable_capacity_dict)
    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
        stocklvl_dict,
    )


def scenario_40(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    print("RUNNING SCENARIO 40")
    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
        stocklvl_dict,
    )


def scenario_base_minstock(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    # do nothing
    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
        stocklvl_dict,
        stocklvl_dict,
    )


def scenario_eem_1(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    print("Running NZIA flex + TO for LR1")
    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
        stocklvl_dict,
    )


def scenario_eem_2(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    print("Running NZIA flex + TO for LR2")
    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
        stocklvl_dict,
    )


def scenario_eem_3(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    print("Running NZIA flex + TO for LR3")
    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
        stocklvl_dict,
    )


def scenario_eem_4(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    print("Running NZIA flex + TO for LR4")
    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
        stocklvl_dict,
    )


def scenario_eem_5(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    print("Running NZIA flex + TO for LR5")
    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
        stocklvl_dict,
    )


def scenario_eem_6(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    print("Running NZIA flex + TO for LR6")
    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
        stocklvl_dict,
    )


def scenario_eem_7(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    print("Running NZIA flex + TO for LR7")
    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
        stocklvl_dict,
    )


def scenario_eem_8(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    print("Running NZIA flex + TO for LR8")
    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
        stocklvl_dict,
    )


def scenario_eem_9(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    print("Running NZIA flex + TO for LR9")
    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
        stocklvl_dict,
    )


def scenario_eem_10(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    print("Running NZIA flex + TO for LR10")
    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
        stocklvl_dict,
    )


def scenario_eem_11(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    print("Running NZIA flex + TO for LR11")
    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
        stocklvl_dict,
    )


def scenario_eem_12(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    print("Running NZIA flex + TO for LR12")
    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
        stocklvl_dict,
    )


def scenario_eem_13(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    print("Running NZIA flex + TO for LR13")
    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
        stocklvl_dict,
    )


def scenario_eem_14(
    data,
    param_dict,
    importcost_dict,
    instalable_capacity_dict,
    eu_primary_cost_dict,
    eu_secondary_cost_dict,
    dcr_dict,
    stocklvl_dict,
):
    print("Running NZIA flex + TO for LR14")
    return (
        data,
        param_dict,
        importcost_dict,
        instalable_capacity_dict,
        eu_primary_cost_dict,
        eu_secondary_cost_dict,
        dcr_dict,
        stocklvl_dict,
    )
