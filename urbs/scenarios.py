import pandas as pd
def scenario_min_min_min(data, data_urbsextensionv1):
    import pandas as pd

    # Process updates
    if "process" in data:
        pro = data["process"]
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                pro.loc[(stf, "EU27", "Biomass Plant"), "inst-cap"] = 20420
                pro.loc[(stf, "EU27", "Coal Plant"), "inst-cap"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "inst-cap"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "inst-cap"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "inst-cap"] = 56670
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 9999999
            else:
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 9999999
                pro.loc[(stf, "EU27", "Coal Plant"), "cap-up"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "cap-up"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "cap-up"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0

    # Commodity updates
    if "commodity" in data:
        co = data["commodity"]

        # Piped Gas logic
        base_value = 319200000
        yearly_decrease_factor = 0.95948  # Test with stable Gas supply

        # CO2 prices per year (€/t)
        co2_prices = {}

        # Linear interpolation from 65 in 2024 to 75 in 2030
        for stf in range(2024, 2031):
            co2_prices[stf] = 65 + (stf - 2024) * (75 - 65) / (2030 - 2024)

        # Fixed values from 2031 onward
        fixed_co2_prices = {
            2031: 81.3,
            2032: 87.6,
            2033: 93.9,
            2034: 100.2,
            2035: 106.5,
            2036: 112.8,
            2037: 119.1,
            2038: 125.4,
            2039: 131.7,
            2040: 138,
            2041: 228.5,
            2042: 364.25,
            2043: 466.0625,
            2044: 500,
            2045: 600,
            2046: 750,
            2047: 900,
            2048: 1000,
            2049: 1000,
            2050: 1000,
        }
        co2_prices.update(fixed_co2_prices)

        for stf in data["global_prop"].index.levels[0].tolist():
            # Piped Gas max
            if stf == 2024:
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value
            else:
                year_diff = stf - 2024
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value * (
                    yearly_decrease_factor**year_diff
                )

            # CO2 price update
            if stf in co2_prices:
                co.loc[(stf, "EU27", "CO2", "Env"), "price"] = co2_prices[stf]
                print(f"Year {stf}: CO2 price set to {co2_prices[stf]:.2f} €/t")
    if "supim" in data:
        supim = data["supim"]
        for t in data["global_prop"].index.levels[0].tolist():
            if t > 0:
                supim.loc[t, ("EU27", "Hydro")] = 0.3375
                # print("SUPIM:", supim)
    # Process-commodity ratios
    if "process-commodity" in data:
        proco = data["process-commodity"]
        for stf in data["global_prop"].index.levels[0].tolist():
            proco.loc[(stf, "Gas Plant (CCGT)", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT)", "CO2", "Out"), "ratio"] = 0.205
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "CO2", "Out"), "ratio"] = 0.0205
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "LNG", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "CO2", "Out"), "ratio"] = 0.231

    # Recycling cost updates
    if "recyclingcost_dict" in data_urbsextensionv1:
        recyclingcost = data_urbsextensionv1["recyclingcost_dict"]
        technologies = ["solarPV", "windon", "windoff", "Batteries"]
        location = "EU27"
        new_costs = {
            "solarPV": 838.7,
            "windon": 4673.4,
            "windoff": 5563.4,
            "Batteries": 1344.3,
        }
        for stf in range(2024, 2051):
            for tech in technologies:
                key = (stf, location, tech)
                if key in recyclingcost:
                    recyclingcost[key] = new_costs[tech]

    return data, data_urbsextensionv1


def scenario_min_min_avg(data, data_urbsextensionv1):
    import pandas as pd

    # Process updates
    if "process" in data:
        pro = data["process"]
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                pro.loc[(stf, "EU27", "Biomass Plant"), "inst-cap"] = 20420
                pro.loc[(stf, "EU27", "Coal Plant"), "inst-cap"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "inst-cap"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "inst-cap"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "inst-cap"] = 56670
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
            else:
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
                pro.loc[(stf, "EU27", "Coal Plant"), "cap-up"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "cap-up"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "cap-up"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0

    # Commodity updates
    if "commodity" in data:
        co = data["commodity"]
        base_value = 319200000
        yearly_decrease_factor = 0.95948
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value
            else:
                year_diff = stf - 2024
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value * (
                    yearly_decrease_factor**year_diff
                )

    # Process-commodity ratios
    if "process-commodity" in data:
        proco = data["process-commodity"]
        for stf in data["global_prop"].index.levels[0].tolist():
            proco.loc[(stf, "Gas Plant (CCGT)", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT)", "CO2", "Out"), "ratio"] = 0.205
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "CO2", "Out"), "ratio"] = 0.0205
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "LNG", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "CO2", "Out"), "ratio"] = 0.231

    # Recycling cost updates
    if "recyclingcost_dict" in data_urbsextensionv1:
        recyclingcost = data_urbsextensionv1["recyclingcost_dict"]
        technologies = ["solarPV", "windon", "windoff", "Batteries"]
        location = "EU27"
        new_costs = {
            "solarPV": 838.7,
            "windon": 4673.4,
            "windoff": 5563.4,
            "Batteries": 2016.45,
        }
        for stf in range(2024, 2051):
            for tech in technologies:
                key = (stf, location, tech)
                if key in recyclingcost:
                    recyclingcost[key] = new_costs[tech]

    return data, data_urbsextensionv1


def scenario_min_min_high(data, data_urbsextensionv1):
    import pandas as pd

    # Process updates
    if "process" in data:
        pro = data["process"]
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                pro.loc[(stf, "EU27", "Biomass Plant"), "inst-cap"] = 20420
                pro.loc[(stf, "EU27", "Coal Plant"), "inst-cap"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "inst-cap"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "inst-cap"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "inst-cap"] = 56670
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
            else:
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
                pro.loc[(stf, "EU27", "Coal Plant"), "cap-up"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "cap-up"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "cap-up"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0

    # Commodity updates
    if "commodity" in data:
        co = data["commodity"]
        base_value = 319200000
        yearly_decrease_factor = 0.95948
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value
            else:
                year_diff = stf - 2024
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value * (
                    yearly_decrease_factor**year_diff
                )

    # Process-commodity ratios
    if "process-commodity" in data:
        proco = data["process-commodity"]
        for stf in data["global_prop"].index.levels[0].tolist():
            proco.loc[(stf, "Gas Plant (CCGT)", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT)", "CO2", "Out"), "ratio"] = 0.205
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "CO2", "Out"), "ratio"] = 0.0205
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "LNG", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "CO2", "Out"), "ratio"] = 0.231

    # Recycling cost updates
    if "recyclingcost_dict" in data_urbsextensionv1:
        recyclingcost = data_urbsextensionv1["recyclingcost_dict"]
        technologies = ["solarPV", "windon", "windoff", "Batteries"]
        location = "EU27"
        new_costs = {
            "solarPV": 838.7,
            "windon": 4673.4,
            "windoff": 5563.4,
            "Batteries": 2688.6,
        }
        for stf in range(2024, 2051):
            for tech in technologies:
                key = (stf, location, tech)
                if key in recyclingcost:
                    recyclingcost[key] = new_costs[tech]

    return data, data_urbsextensionv1


def scenario_min_avg_min(data, data_urbsextensionv1):
    import pandas as pd

    # Process updates
    if "process" in data:
        pro = data["process"]
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                pro.loc[(stf, "EU27", "Biomass Plant"), "inst-cap"] = 20420
                pro.loc[(stf, "EU27", "Coal Plant"), "inst-cap"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "inst-cap"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "inst-cap"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "inst-cap"] = 56670
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
            else:
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
                pro.loc[(stf, "EU27", "Coal Plant"), "cap-up"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "cap-up"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "cap-up"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0

    # Commodity updates
    if "commodity" in data:
        co = data["commodity"]
        base_value = 319200000
        yearly_decrease_factor = 0.95948
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value
            else:
                year_diff = stf - 2024
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value * (
                    yearly_decrease_factor**year_diff
                )

    # Process-commodity ratios
    if "process-commodity" in data:
        proco = data["process-commodity"]
        for stf in data["global_prop"].index.levels[0].tolist():
            proco.loc[(stf, "Gas Plant (CCGT)", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT)", "CO2", "Out"), "ratio"] = 0.205
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "CO2", "Out"), "ratio"] = 0.0205
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "LNG", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "CO2", "Out"), "ratio"] = 0.231

    # Recycling cost updates
    if "recyclingcost_dict" in data_urbsextensionv1:
        recyclingcost = data_urbsextensionv1["recyclingcost_dict"]
        technologies = ["solarPV", "windon", "windoff", "Batteries"]
        location = "EU27"
        new_costs = {
            "solarPV": 838.7,
            "windon": 7010.1,
            "windoff": 8345.15,
            "Batteries": 1344.3,
        }
        for stf in range(2024, 2051):
            for tech in technologies:
                key = (stf, location, tech)
                if key in recyclingcost:
                    recyclingcost[key] = new_costs[tech]

    return data, data_urbsextensionv1


def scenario_min_avg_avg(data, data_urbsextensionv1):
    import pandas as pd

    # Process updates
    if "process" in data:
        pro = data["process"]
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                pro.loc[(stf, "EU27", "Biomass Plant"), "inst-cap"] = 20420
                pro.loc[(stf, "EU27", "Coal Plant"), "inst-cap"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "inst-cap"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "inst-cap"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "inst-cap"] = 56670
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
            else:
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
                pro.loc[(stf, "EU27", "Coal Plant"), "cap-up"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "cap-up"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "cap-up"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0

    # Commodity updates
    if "commodity" in data:
        co = data["commodity"]
        base_value = 319200000
        yearly_decrease_factor = 0.95948
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value
            else:
                year_diff = stf - 2024
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value * (
                    yearly_decrease_factor**year_diff
                )

    # Process-commodity ratios
    if "process-commodity" in data:
        proco = data["process-commodity"]
        for stf in data["global_prop"].index.levels[0].tolist():
            proco.loc[(stf, "Gas Plant (CCGT)", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT)", "CO2", "Out"), "ratio"] = 0.205
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "CO2", "Out"), "ratio"] = 0.0205
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "LNG", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "CO2", "Out"), "ratio"] = 0.231

    # Recycling cost updates
    if "recyclingcost_dict" in data_urbsextensionv1:
        recyclingcost = data_urbsextensionv1["recyclingcost_dict"]
        technologies = ["solarPV", "windon", "windoff", "Batteries"]
        location = "EU27"
        new_costs = {
            "solarPV": 838.7,
            "windon": 7010.1,
            "windoff": 8345.15,
            "Batteries": 2016.45,
        }
        for stf in range(2024, 2051):
            for tech in technologies:
                key = (stf, location, tech)
                if key in recyclingcost:
                    recyclingcost[key] = new_costs[tech]

    return data, data_urbsextensionv1


def scenario_min_avg_high(data, data_urbsextensionv1):
    import pandas as pd

    # Process updates
    if "process" in data:
        pro = data["process"]
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                pro.loc[(stf, "EU27", "Biomass Plant"), "inst-cap"] = 20420
                pro.loc[(stf, "EU27", "Coal Plant"), "inst-cap"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "inst-cap"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "inst-cap"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "inst-cap"] = 56670
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
            else:
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
                pro.loc[(stf, "EU27", "Coal Plant"), "cap-up"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "cap-up"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "cap-up"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0

    # Commodity updates
    if "commodity" in data:
        co = data["commodity"]
        base_value = 319200000
        yearly_decrease_factor = 0.95948
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value
            else:
                year_diff = stf - 2024
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value * (
                    yearly_decrease_factor**year_diff
                )

    # Process-commodity ratios
    if "process-commodity" in data:
        proco = data["process-commodity"]
        for stf in data["global_prop"].index.levels[0].tolist():
            proco.loc[(stf, "Gas Plant (CCGT)", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT)", "CO2", "Out"), "ratio"] = 0.205
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "CO2", "Out"), "ratio"] = 0.0205
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "LNG", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "CO2", "Out"), "ratio"] = 0.231

    # Recycling cost updates
    if "recyclingcost_dict" in data_urbsextensionv1:
        recyclingcost = data_urbsextensionv1["recyclingcost_dict"]
        technologies = ["solarPV", "windon", "windoff", "Batteries"]
        location = "EU27"
        new_costs = {
            "solarPV": 838.7,
            "windon": 7010.1,
            "windoff": 8345.15,
            "Batteries": 2688.6,
        }
        for stf in range(2024, 2051):
            for tech in technologies:
                key = (stf, location, tech)
                if key in recyclingcost:
                    recyclingcost[key] = new_costs[tech]

    return data, data_urbsextensionv1


def scenario_min_high_min(data, data_urbsextensionv1):
    import pandas as pd

    # Process updates
    if "process" in data:
        pro = data["process"]
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                pro.loc[(stf, "EU27", "Biomass Plant"), "inst-cap"] = 20420
                pro.loc[(stf, "EU27", "Coal Plant"), "inst-cap"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "inst-cap"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "inst-cap"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "inst-cap"] = 56670
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
            else:
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
                pro.loc[(stf, "EU27", "Coal Plant"), "cap-up"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "cap-up"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "cap-up"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0

    # Commodity updates
    if "commodity" in data:
        co = data["commodity"]
        base_value = 319200000
        yearly_decrease_factor = 0.95948
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value
            else:
                year_diff = stf - 2024
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value * (
                    yearly_decrease_factor**year_diff
                )

    # Process-commodity ratios
    if "process-commodity" in data:
        proco = data["process-commodity"]
        for stf in data["global_prop"].index.levels[0].tolist():
            proco.loc[(stf, "Gas Plant (CCGT)", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT)", "CO2", "Out"), "ratio"] = 0.205
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "CO2", "Out"), "ratio"] = 0.0205
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "LNG", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "CO2", "Out"), "ratio"] = 0.231

    # Recycling cost updates
    if "recyclingcost_dict" in data_urbsextensionv1:
        recyclingcost = data_urbsextensionv1["recyclingcost_dict"]
        technologies = ["solarPV", "windon", "windoff", "Batteries"]
        location = "EU27"
        new_costs = {
            "solarPV": 838.7,
            "windon": 9346.8,
            "windoff": 11126.8,
            "Batteries": 1344.3,
        }
        for stf in range(2024, 2051):
            for tech in technologies:
                key = (stf, location, tech)
                if key in recyclingcost:
                    recyclingcost[key] = new_costs[tech]

    return data, data_urbsextensionv1


def scenario_min_high_avg(data, data_urbsextensionv1):
    import pandas as pd

    # Process updates
    if "process" in data:
        pro = data["process"]
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                pro.loc[(stf, "EU27", "Biomass Plant"), "inst-cap"] = 20420
                pro.loc[(stf, "EU27", "Coal Plant"), "inst-cap"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "inst-cap"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "inst-cap"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "inst-cap"] = 56670
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
            else:
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
                pro.loc[(stf, "EU27", "Coal Plant"), "cap-up"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "cap-up"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "cap-up"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0

    # Commodity updates
    if "commodity" in data:
        co = data["commodity"]
        base_value = 319200000
        yearly_decrease_factor = 0.95948
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value
            else:
                year_diff = stf - 2024
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value * (
                    yearly_decrease_factor**year_diff
                )

    # Process-commodity ratios
    if "process-commodity" in data:
        proco = data["process-commodity"]
        for stf in data["global_prop"].index.levels[0].tolist():
            proco.loc[(stf, "Gas Plant (CCGT)", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT)", "CO2", "Out"), "ratio"] = 0.205
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "CO2", "Out"), "ratio"] = 0.0205
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "LNG", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "CO2", "Out"), "ratio"] = 0.231

    # Recycling cost updates
    if "recyclingcost_dict" in data_urbsextensionv1:
        recyclingcost = data_urbsextensionv1["recyclingcost_dict"]
        technologies = ["solarPV", "windon", "windoff", "Batteries"]
        location = "EU27"
        new_costs = {
            "solarPV": 838.7,
            "windon": 9346.8,
            "windoff": 11126.8,
            "Batteries": 2016.45,
        }
        for stf in range(2024, 2051):
            for tech in technologies:
                key = (stf, location, tech)
                if key in recyclingcost:
                    recyclingcost[key] = new_costs[tech]

    return data, data_urbsextensionv1


def scenario_min_high_high(data, data_urbsextensionv1):
    import pandas as pd

    # Process updates
    if "process" in data:
        pro = data["process"]
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                pro.loc[(stf, "EU27", "Biomass Plant"), "inst-cap"] = 20420
                pro.loc[(stf, "EU27", "Coal Plant"), "inst-cap"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "inst-cap"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "inst-cap"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "inst-cap"] = 56670
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
            else:
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
                pro.loc[(stf, "EU27", "Coal Plant"), "cap-up"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "cap-up"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "cap-up"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0

    # Commodity updates
    if "commodity" in data:
        co = data["commodity"]
        base_value = 319200000
        yearly_decrease_factor = 0.95948
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value
            else:
                year_diff = stf - 2024
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value * (
                    yearly_decrease_factor**year_diff
                )

    # Process-commodity ratios
    if "process-commodity" in data:
        proco = data["process-commodity"]
        for stf in data["global_prop"].index.levels[0].tolist():
            proco.loc[(stf, "Gas Plant (CCGT)", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT)", "CO2", "Out"), "ratio"] = 0.205
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "CO2", "Out"), "ratio"] = 0.0205
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "LNG", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "CO2", "Out"), "ratio"] = 0.231

    # Recycling cost updates
    if "recyclingcost_dict" in data_urbsextensionv1:
        recyclingcost = data_urbsextensionv1["recyclingcost_dict"]
        technologies = ["solarPV", "windon", "windoff", "Batteries"]
        location = "EU27"
        new_costs = {
            "solarPV": 838.7,
            "windon": 9346.8,
            "windoff": 11126.8,
            "Batteries": 2688.6,
        }
        for stf in range(2024, 2051):
            for tech in technologies:
                key = (stf, location, tech)
                if key in recyclingcost:
                    recyclingcost[key] = new_costs[tech]

    return data, data_urbsextensionv1


def scenario_avg_min_min(data, data_urbsextensionv1):
    import pandas as pd

    # Process updates
    if "process" in data:
        pro = data["process"]
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                pro.loc[(stf, "EU27", "Biomass Plant"), "inst-cap"] = 20420
                pro.loc[(stf, "EU27", "Coal Plant"), "inst-cap"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "inst-cap"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "inst-cap"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "inst-cap"] = 56670
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
            else:
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
                pro.loc[(stf, "EU27", "Coal Plant"), "cap-up"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "cap-up"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "cap-up"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0

    # Commodity updates
    if "commodity" in data:
        co = data["commodity"]
        base_value = 319200000
        yearly_decrease_factor = 0.95948
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value
            else:
                year_diff = stf - 2024
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value * (
                    yearly_decrease_factor**year_diff
                )

    # Process-commodity ratios
    if "process-commodity" in data:
        proco = data["process-commodity"]
        for stf in data["global_prop"].index.levels[0].tolist():
            proco.loc[(stf, "Gas Plant (CCGT)", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT)", "CO2", "Out"), "ratio"] = 0.205
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "CO2", "Out"), "ratio"] = 0.0205
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "LNG", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "CO2", "Out"), "ratio"] = 0.231

    # Recycling cost updates
    if "recyclingcost_dict" in data_urbsextensionv1:
        recyclingcost = data_urbsextensionv1["recyclingcost_dict"]
        technologies = ["solarPV", "windon", "windoff", "Batteries"]
        location = "EU27"
        new_costs = {
            "solarPV": 1258.05,
            "windon": 4673.4,
            "windoff": 5563.4,
            "Batteries": 1344.3,
        }
        for stf in range(2024, 2051):
            for tech in technologies:
                key = (stf, location, tech)
                if key in recyclingcost:
                    recyclingcost[key] = new_costs[tech]

    return data, data_urbsextensionv1


def scenario_avg_min_avg(data, data_urbsextensionv1):
    import pandas as pd

    # Process updates
    if "process" in data:
        pro = data["process"]
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                pro.loc[(stf, "EU27", "Biomass Plant"), "inst-cap"] = 20420
                pro.loc[(stf, "EU27", "Coal Plant"), "inst-cap"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "inst-cap"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "inst-cap"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "inst-cap"] = 56670
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
            else:
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
                pro.loc[(stf, "EU27", "Coal Plant"), "cap-up"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "cap-up"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "cap-up"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0

    # Commodity updates
    if "commodity" in data:
        co = data["commodity"]
        base_value = 319200000
        yearly_decrease_factor = 0.95948
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value
            else:
                year_diff = stf - 2024
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value * (
                    yearly_decrease_factor**year_diff
                )

    # Process-commodity ratios
    if "process-commodity" in data:
        proco = data["process-commodity"]
        for stf in data["global_prop"].index.levels[0].tolist():
            proco.loc[(stf, "Gas Plant (CCGT)", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT)", "CO2", "Out"), "ratio"] = 0.205
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "CO2", "Out"), "ratio"] = 0.0205
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "LNG", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "CO2", "Out"), "ratio"] = 0.231

    # Recycling cost updates
    if "recyclingcost_dict" in data_urbsextensionv1:
        recyclingcost = data_urbsextensionv1["recyclingcost_dict"]
        technologies = ["solarPV", "windon", "windoff", "Batteries"]
        location = "EU27"
        new_costs = {
            "solarPV": 1258.05,
            "windon": 4673.4,
            "windoff": 5563.4,
            "Batteries": 2016.45,
        }
        for stf in range(2024, 2051):
            for tech in technologies:
                key = (stf, location, tech)
                if key in recyclingcost:
                    recyclingcost[key] = new_costs[tech]

    return data, data_urbsextensionv1


def scenario_avg_min_high(data, data_urbsextensionv1):
    import pandas as pd

    # Process updates
    if "process" in data:
        pro = data["process"]
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                pro.loc[(stf, "EU27", "Biomass Plant"), "inst-cap"] = 20420
                pro.loc[(stf, "EU27", "Coal Plant"), "inst-cap"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "inst-cap"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "inst-cap"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "inst-cap"] = 56670
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
            else:
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
                pro.loc[(stf, "EU27", "Coal Plant"), "cap-up"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "cap-up"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "cap-up"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0

    # Commodity updates
    if "commodity" in data:
        co = data["commodity"]
        base_value = 319200000
        yearly_decrease_factor = 0.95948
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value
            else:
                year_diff = stf - 2024
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value * (
                    yearly_decrease_factor**year_diff
                )

    # Process-commodity ratios
    if "process-commodity" in data:
        proco = data["process-commodity"]
        for stf in data["global_prop"].index.levels[0].tolist():
            proco.loc[(stf, "Gas Plant (CCGT)", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT)", "CO2", "Out"), "ratio"] = 0.205
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "CO2", "Out"), "ratio"] = 0.0205
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "LNG", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "CO2", "Out"), "ratio"] = 0.231

    # Recycling cost updates
    if "recyclingcost_dict" in data_urbsextensionv1:
        recyclingcost = data_urbsextensionv1["recyclingcost_dict"]
        technologies = ["solarPV", "windon", "windoff", "Batteries"]
        location = "EU27"
        new_costs = {
            "solarPV": 1258.05,
            "windon": 4673.4,
            "windoff": 5563.4,
            "Batteries": 2688.6,
        }
        for stf in range(2024, 2051):
            for tech in technologies:
                key = (stf, location, tech)
                if key in recyclingcost:
                    recyclingcost[key] = new_costs[tech]

    return data, data_urbsextensionv1


def scenario_avg_avg_min(data, data_urbsextensionv1):
    import pandas as pd

    # Process updates
    if "process" in data:
        pro = data["process"]
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                pro.loc[(stf, "EU27", "Biomass Plant"), "inst-cap"] = 20420
                pro.loc[(stf, "EU27", "Coal Plant"), "inst-cap"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "inst-cap"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "inst-cap"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "inst-cap"] = 56670
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
            else:
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
                pro.loc[(stf, "EU27", "Coal Plant"), "cap-up"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "cap-up"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "cap-up"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0

    # Commodity updates
    if "commodity" in data:
        co = data["commodity"]
        base_value = 319200000
        yearly_decrease_factor = 0.95948
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value
            else:
                year_diff = stf - 2024
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value * (
                    yearly_decrease_factor**year_diff
                )

    # Process-commodity ratios
    if "process-commodity" in data:
        proco = data["process-commodity"]
        for stf in data["global_prop"].index.levels[0].tolist():
            proco.loc[(stf, "Gas Plant (CCGT)", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT)", "CO2", "Out"), "ratio"] = 0.205
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "CO2", "Out"), "ratio"] = 0.0205
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "LNG", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "CO2", "Out"), "ratio"] = 0.231

    # Recycling cost updates
    if "recyclingcost_dict" in data_urbsextensionv1:
        recyclingcost = data_urbsextensionv1["recyclingcost_dict"]
        technologies = ["solarPV", "windon", "windoff", "Batteries"]
        location = "EU27"
        new_costs = {
            "solarPV": 1258.05,
            "windon": 7010.1,
            "windoff": 8345.15,
            "Batteries": 1344.3,
        }
        for stf in range(2024, 2051):
            for tech in technologies:
                key = (stf, location, tech)
                if key in recyclingcost:
                    recyclingcost[key] = new_costs[tech]

    return data, data_urbsextensionv1


def scenario_avg_avg_avg(data, data_urbsextensionv1):
    import pandas as pd

    # Process updates
    if "process" in data:
        pro = data["process"]
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                pro.loc[(stf, "EU27", "Biomass Plant"), "inst-cap"] = 20420
                pro.loc[(stf, "EU27", "Coal Plant"), "inst-cap"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "inst-cap"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "inst-cap"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "inst-cap"] = 56670
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
            else:
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
                pro.loc[(stf, "EU27", "Coal Plant"), "cap-up"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "cap-up"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "cap-up"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0

    # Commodity updates
    if "commodity" in data:
        co = data["commodity"]
        base_value = 319200000
        yearly_decrease_factor = 0.95948
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value
            else:
                year_diff = stf - 2024
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value * (
                    yearly_decrease_factor**year_diff
                )

    # Process-commodity ratios
    if "process-commodity" in data:
        proco = data["process-commodity"]
        for stf in data["global_prop"].index.levels[0].tolist():
            proco.loc[(stf, "Gas Plant (CCGT)", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT)", "CO2", "Out"), "ratio"] = 0.205
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "CO2", "Out"), "ratio"] = 0.0205
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "LNG", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "CO2", "Out"), "ratio"] = 0.231

    # Recycling cost updates
    if "recyclingcost_dict" in data_urbsextensionv1:
        recyclingcost = data_urbsextensionv1["recyclingcost_dict"]
        technologies = ["solarPV", "windon", "windoff", "Batteries"]
        location = "EU27"
        new_costs = {
            "solarPV": 1258.05,
            "windon": 7010.1,
            "windoff": 8345.15,
            "Batteries": 2016.45,
        }
        for stf in range(2024, 2051):
            for tech in technologies:
                key = (stf, location, tech)
                if key in recyclingcost:
                    recyclingcost[key] = new_costs[tech]

    return data, data_urbsextensionv1


def scenario_avg_avg_high(data, data_urbsextensionv1):
    import pandas as pd

    # Process updates
    if "process" in data:
        pro = data["process"]
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                pro.loc[(stf, "EU27", "Biomass Plant"), "inst-cap"] = 20420
                pro.loc[(stf, "EU27", "Coal Plant"), "inst-cap"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "inst-cap"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "inst-cap"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "inst-cap"] = 56670
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
            else:
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
                pro.loc[(stf, "EU27", "Coal Plant"), "cap-up"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "cap-up"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "cap-up"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0

    # Commodity updates
    if "commodity" in data:
        co = data["commodity"]
        base_value = 319200000
        yearly_decrease_factor = 0.95948
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value
            else:
                year_diff = stf - 2024
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value * (
                    yearly_decrease_factor**year_diff
                )

    # Process-commodity ratios
    if "process-commodity" in data:
        proco = data["process-commodity"]
        for stf in data["global_prop"].index.levels[0].tolist():
            proco.loc[(stf, "Gas Plant (CCGT)", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT)", "CO2", "Out"), "ratio"] = 0.205
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "CO2", "Out"), "ratio"] = 0.0205
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "LNG", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "CO2", "Out"), "ratio"] = 0.231

    # Recycling cost updates
    if "recyclingcost_dict" in data_urbsextensionv1:
        recyclingcost = data_urbsextensionv1["recyclingcost_dict"]
        technologies = ["solarPV", "windon", "windoff", "Batteries"]
        location = "EU27"
        new_costs = {
            "solarPV": 1258.05,
            "windon": 7010.1,
            "windoff": 8345.15,
            "Batteries": 2688.6,
        }
        for stf in range(2024, 2051):
            for tech in technologies:
                key = (stf, location, tech)
                if key in recyclingcost:
                    recyclingcost[key] = new_costs[tech]

    return data, data_urbsextensionv1


def scenario_avg_high_min(data, data_urbsextensionv1):
    import pandas as pd

    # Process updates
    if "process" in data:
        pro = data["process"]
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                pro.loc[(stf, "EU27", "Biomass Plant"), "inst-cap"] = 20420
                pro.loc[(stf, "EU27", "Coal Plant"), "inst-cap"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "inst-cap"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "inst-cap"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "inst-cap"] = 56670
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
            else:
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
                pro.loc[(stf, "EU27", "Coal Plant"), "cap-up"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "cap-up"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "cap-up"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0

    # Commodity updates
    if "commodity" in data:
        co = data["commodity"]
        base_value = 319200000
        yearly_decrease_factor = 0.95948
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value
            else:
                year_diff = stf - 2024
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value * (
                    yearly_decrease_factor**year_diff
                )

    # Process-commodity ratios
    if "process-commodity" in data:
        proco = data["process-commodity"]
        for stf in data["global_prop"].index.levels[0].tolist():
            proco.loc[(stf, "Gas Plant (CCGT)", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT)", "CO2", "Out"), "ratio"] = 0.205
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "CO2", "Out"), "ratio"] = 0.0205
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "LNG", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "CO2", "Out"), "ratio"] = 0.231

    # Recycling cost updates
    if "recyclingcost_dict" in data_urbsextensionv1:
        recyclingcost = data_urbsextensionv1["recyclingcost_dict"]
        technologies = ["solarPV", "windon", "windoff", "Batteries"]
        location = "EU27"
        new_costs = {
            "solarPV": 1258.05,
            "windon": 9346.8,
            "windoff": 11126.8,
            "Batteries": 1344.3,
        }
        for stf in range(2024, 2051):
            for tech in technologies:
                key = (stf, location, tech)
                if key in recyclingcost:
                    recyclingcost[key] = new_costs[tech]

    return data, data_urbsextensionv1


def scenario_avg_high_avg(data, data_urbsextensionv1):
    import pandas as pd

    # Process updates
    if "process" in data:
        pro = data["process"]
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                pro.loc[(stf, "EU27", "Biomass Plant"), "inst-cap"] = 20420
                pro.loc[(stf, "EU27", "Coal Plant"), "inst-cap"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "inst-cap"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "inst-cap"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "inst-cap"] = 56670
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
            else:
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
                pro.loc[(stf, "EU27", "Coal Plant"), "cap-up"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "cap-up"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "cap-up"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0

    # Commodity updates
    if "commodity" in data:
        co = data["commodity"]
        base_value = 319200000
        yearly_decrease_factor = 0.95948
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value
            else:
                year_diff = stf - 2024
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value * (
                    yearly_decrease_factor**year_diff
                )

    # Process-commodity ratios
    if "process-commodity" in data:
        proco = data["process-commodity"]
        for stf in data["global_prop"].index.levels[0].tolist():
            proco.loc[(stf, "Gas Plant (CCGT)", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT)", "CO2", "Out"), "ratio"] = 0.205
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "CO2", "Out"), "ratio"] = 0.0205
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "LNG", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "CO2", "Out"), "ratio"] = 0.231

    # Recycling cost updates
    if "recyclingcost_dict" in data_urbsextensionv1:
        recyclingcost = data_urbsextensionv1["recyclingcost_dict"]
        technologies = ["solarPV", "windon", "windoff", "Batteries"]
        location = "EU27"
        new_costs = {
            "solarPV": 1258.05,
            "windon": 9346.8,
            "windoff": 11126.8,
            "Batteries": 2016.45,
        }
        for stf in range(2024, 2051):
            for tech in technologies:
                key = (stf, location, tech)
                if key in recyclingcost:
                    recyclingcost[key] = new_costs[tech]

    return data, data_urbsextensionv1


def scenario_avg_high_high(data, data_urbsextensionv1):
    import pandas as pd

    # Process updates
    if "process" in data:
        pro = data["process"]
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                pro.loc[(stf, "EU27", "Biomass Plant"), "inst-cap"] = 20420
                pro.loc[(stf, "EU27", "Coal Plant"), "inst-cap"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "inst-cap"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "inst-cap"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "inst-cap"] = 56670
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
            else:
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
                pro.loc[(stf, "EU27", "Coal Plant"), "cap-up"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "cap-up"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "cap-up"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0

    # Commodity updates
    if "commodity" in data:
        co = data["commodity"]
        base_value = 319200000
        yearly_decrease_factor = 0.95948
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value
            else:
                year_diff = stf - 2024
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value * (
                    yearly_decrease_factor**year_diff
                )

    # Process-commodity ratios
    if "process-commodity" in data:
        proco = data["process-commodity"]
        for stf in data["global_prop"].index.levels[0].tolist():
            proco.loc[(stf, "Gas Plant (CCGT)", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT)", "CO2", "Out"), "ratio"] = 0.205
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "CO2", "Out"), "ratio"] = 0.0205
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "LNG", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "CO2", "Out"), "ratio"] = 0.231

    # Recycling cost updates
    if "recyclingcost_dict" in data_urbsextensionv1:
        recyclingcost = data_urbsextensionv1["recyclingcost_dict"]
        technologies = ["solarPV", "windon", "windoff", "Batteries"]
        location = "EU27"
        new_costs = {
            "solarPV": 1258.05,
            "windon": 9346.8,
            "windoff": 11126.8,
            "Batteries": 2688.6,
        }
        for stf in range(2024, 2051):
            for tech in technologies:
                key = (stf, location, tech)
                if key in recyclingcost:
                    recyclingcost[key] = new_costs[tech]

    return data, data_urbsextensionv1


def scenario_high_min_min(data, data_urbsextensionv1):
    import pandas as pd

    # Process updates
    if "process" in data:
        pro = data["process"]
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                pro.loc[(stf, "EU27", "Biomass Plant"), "inst-cap"] = 20420
                pro.loc[(stf, "EU27", "Coal Plant"), "inst-cap"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "inst-cap"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "inst-cap"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "inst-cap"] = 56670
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
            else:
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
                pro.loc[(stf, "EU27", "Coal Plant"), "cap-up"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "cap-up"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "cap-up"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0

    # Commodity updates
    if "commodity" in data:
        co = data["commodity"]
        base_value = 319200000
        yearly_decrease_factor = 0.95948
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value
            else:
                year_diff = stf - 2024
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value * (
                    yearly_decrease_factor**year_diff
                )

    # Process-commodity ratios
    if "process-commodity" in data:
        proco = data["process-commodity"]
        for stf in data["global_prop"].index.levels[0].tolist():
            proco.loc[(stf, "Gas Plant (CCGT)", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT)", "CO2", "Out"), "ratio"] = 0.205
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "CO2", "Out"), "ratio"] = 0.0205
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "LNG", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "CO2", "Out"), "ratio"] = 0.231

    # Recycling cost updates
    if "recyclingcost_dict" in data_urbsextensionv1:
        recyclingcost = data_urbsextensionv1["recyclingcost_dict"]
        technologies = ["solarPV", "windon", "windoff", "Batteries"]
        location = "EU27"
        new_costs = {
            "solarPV": 1677.4,
            "windon": 4673.4,
            "windoff": 5563.4,
            "Batteries": 1344.3,
        }
        for stf in range(2024, 2051):
            for tech in technologies:
                key = (stf, location, tech)
                if key in recyclingcost:
                    recyclingcost[key] = new_costs[tech]

    return data, data_urbsextensionv1


def scenario_high_min_avg(data, data_urbsextensionv1):
    import pandas as pd

    # Process updates
    if "process" in data:
        pro = data["process"]
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                pro.loc[(stf, "EU27", "Biomass Plant"), "inst-cap"] = 20420
                pro.loc[(stf, "EU27", "Coal Plant"), "inst-cap"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "inst-cap"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "inst-cap"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "inst-cap"] = 56670
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
            else:
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
                pro.loc[(stf, "EU27", "Coal Plant"), "cap-up"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "cap-up"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "cap-up"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0

    # Commodity updates
    if "commodity" in data:
        co = data["commodity"]
        base_value = 319200000
        yearly_decrease_factor = 0.95948
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value
            else:
                year_diff = stf - 2024
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value * (
                    yearly_decrease_factor**year_diff
                )

    # Process-commodity ratios
    if "process-commodity" in data:
        proco = data["process-commodity"]
        for stf in data["global_prop"].index.levels[0].tolist():
            proco.loc[(stf, "Gas Plant (CCGT)", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT)", "CO2", "Out"), "ratio"] = 0.205
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "CO2", "Out"), "ratio"] = 0.0205
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "LNG", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "CO2", "Out"), "ratio"] = 0.231

    # Recycling cost updates
    if "recyclingcost_dict" in data_urbsextensionv1:
        recyclingcost = data_urbsextensionv1["recyclingcost_dict"]
        technologies = ["solarPV", "windon", "windoff", "Batteries"]
        location = "EU27"
        new_costs = {
            "solarPV": 1677.4,
            "windon": 4673.4,
            "windoff": 5563.4,
            "Batteries": 2016.45,
        }
        for stf in range(2024, 2051):
            for tech in technologies:
                key = (stf, location, tech)
                if key in recyclingcost:
                    recyclingcost[key] = new_costs[tech]

    return data, data_urbsextensionv1


def scenario_high_min_high(data, data_urbsextensionv1):
    import pandas as pd

    # Process updates
    if "process" in data:
        pro = data["process"]
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                pro.loc[(stf, "EU27", "Biomass Plant"), "inst-cap"] = 20420
                pro.loc[(stf, "EU27", "Coal Plant"), "inst-cap"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "inst-cap"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "inst-cap"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "inst-cap"] = 56670
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
            else:
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
                pro.loc[(stf, "EU27", "Coal Plant"), "cap-up"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "cap-up"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "cap-up"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0

    # Commodity updates
    if "commodity" in data:
        co = data["commodity"]
        base_value = 319200000
        yearly_decrease_factor = 0.95948
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value
            else:
                year_diff = stf - 2024
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value * (
                    yearly_decrease_factor**year_diff
                )

    # Process-commodity ratios
    if "process-commodity" in data:
        proco = data["process-commodity"]
        for stf in data["global_prop"].index.levels[0].tolist():
            proco.loc[(stf, "Gas Plant (CCGT)", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT)", "CO2", "Out"), "ratio"] = 0.205
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "CO2", "Out"), "ratio"] = 0.0205
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "LNG", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "CO2", "Out"), "ratio"] = 0.231

    # Recycling cost updates
    if "recyclingcost_dict" in data_urbsextensionv1:
        recyclingcost = data_urbsextensionv1["recyclingcost_dict"]
        technologies = ["solarPV", "windon", "windoff", "Batteries"]
        location = "EU27"
        new_costs = {
            "solarPV": 1677.4,
            "windon": 4673.4,
            "windoff": 5563.4,
            "Batteries": 2688.6,
        }
        for stf in range(2024, 2051):
            for tech in technologies:
                key = (stf, location, tech)
                if key in recyclingcost:
                    recyclingcost[key] = new_costs[tech]

    return data, data_urbsextensionv1


def scenario_high_avg_min(data, data_urbsextensionv1):
    import pandas as pd

    # Process updates
    if "process" in data:
        pro = data["process"]
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                pro.loc[(stf, "EU27", "Biomass Plant"), "inst-cap"] = 20420
                pro.loc[(stf, "EU27", "Coal Plant"), "inst-cap"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "inst-cap"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "inst-cap"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "inst-cap"] = 56670
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
            else:
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
                pro.loc[(stf, "EU27", "Coal Plant"), "cap-up"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "cap-up"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "cap-up"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0

    # Commodity updates
    if "commodity" in data:
        co = data["commodity"]
        base_value = 319200000
        yearly_decrease_factor = 0.95948
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value
            else:
                year_diff = stf - 2024
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value * (
                    yearly_decrease_factor**year_diff
                )

    # Process-commodity ratios
    if "process-commodity" in data:
        proco = data["process-commodity"]
        for stf in data["global_prop"].index.levels[0].tolist():
            proco.loc[(stf, "Gas Plant (CCGT)", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT)", "CO2", "Out"), "ratio"] = 0.205
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "CO2", "Out"), "ratio"] = 0.0205
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "LNG", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "CO2", "Out"), "ratio"] = 0.231

    # Recycling cost updates
    if "recyclingcost_dict" in data_urbsextensionv1:
        recyclingcost = data_urbsextensionv1["recyclingcost_dict"]
        technologies = ["solarPV", "windon", "windoff", "Batteries"]
        location = "EU27"
        new_costs = {
            "solarPV": 1677.4,
            "windon": 7010.1,
            "windoff": 8345.15,
            "Batteries": 1344.3,
        }
        for stf in range(2024, 2051):
            for tech in technologies:
                key = (stf, location, tech)
                if key in recyclingcost:
                    recyclingcost[key] = new_costs[tech]

    return data, data_urbsextensionv1


def scenario_high_avg_avg(data, data_urbsextensionv1):
    import pandas as pd

    # Process updates
    if "process" in data:
        pro = data["process"]
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                pro.loc[(stf, "EU27", "Biomass Plant"), "inst-cap"] = 20420
                pro.loc[(stf, "EU27", "Coal Plant"), "inst-cap"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "inst-cap"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "inst-cap"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "inst-cap"] = 56670
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
            else:
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
                pro.loc[(stf, "EU27", "Coal Plant"), "cap-up"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "cap-up"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "cap-up"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0

    # Commodity updates
    if "commodity" in data:
        co = data["commodity"]
        base_value = 319200000
        yearly_decrease_factor = 0.95948
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value
            else:
                year_diff = stf - 2024
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value * (
                    yearly_decrease_factor**year_diff
                )

    # Process-commodity ratios
    if "process-commodity" in data:
        proco = data["process-commodity"]
        for stf in data["global_prop"].index.levels[0].tolist():
            proco.loc[(stf, "Gas Plant (CCGT)", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT)", "CO2", "Out"), "ratio"] = 0.205
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "CO2", "Out"), "ratio"] = 0.0205
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "LNG", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "CO2", "Out"), "ratio"] = 0.231

    # Recycling cost updates
    if "recyclingcost_dict" in data_urbsextensionv1:
        recyclingcost = data_urbsextensionv1["recyclingcost_dict"]
        technologies = ["solarPV", "windon", "windoff", "Batteries"]
        location = "EU27"
        new_costs = {
            "solarPV": 1677.4,
            "windon": 7010.1,
            "windoff": 8345.15,
            "Batteries": 2016.45,
        }
        for stf in range(2024, 2051):
            for tech in technologies:
                key = (stf, location, tech)
                if key in recyclingcost:
                    recyclingcost[key] = new_costs[tech]

    return data, data_urbsextensionv1


def scenario_high_avg_high(data, data_urbsextensionv1):
    import pandas as pd

    # Process updates
    if "process" in data:
        pro = data["process"]
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                pro.loc[(stf, "EU27", "Biomass Plant"), "inst-cap"] = 20420
                pro.loc[(stf, "EU27", "Coal Plant"), "inst-cap"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "inst-cap"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "inst-cap"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "inst-cap"] = 56670
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
            else:
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
                pro.loc[(stf, "EU27", "Coal Plant"), "cap-up"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "cap-up"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "cap-up"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0

    # Commodity updates
    if "commodity" in data:
        co = data["commodity"]
        base_value = 319200000
        yearly_decrease_factor = 0.95948
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value
            else:
                year_diff = stf - 2024
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value * (
                    yearly_decrease_factor**year_diff
                )

    # Process-commodity ratios
    if "process-commodity" in data:
        proco = data["process-commodity"]
        for stf in data["global_prop"].index.levels[0].tolist():
            proco.loc[(stf, "Gas Plant (CCGT)", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT)", "CO2", "Out"), "ratio"] = 0.205
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "CO2", "Out"), "ratio"] = 0.0205
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "LNG", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "CO2", "Out"), "ratio"] = 0.231

    # Recycling cost updates
    if "recyclingcost_dict" in data_urbsextensionv1:
        recyclingcost = data_urbsextensionv1["recyclingcost_dict"]
        technologies = ["solarPV", "windon", "windoff", "Batteries"]
        location = "EU27"
        new_costs = {
            "solarPV": 1677.4,
            "windon": 7010.1,
            "windoff": 8345.15,
            "Batteries": 2688.6,
        }
        for stf in range(2024, 2051):
            for tech in technologies:
                key = (stf, location, tech)
                if key in recyclingcost:
                    recyclingcost[key] = new_costs[tech]

    return data, data_urbsextensionv1


def scenario_high_high_min(data, data_urbsextensionv1):
    import pandas as pd

    # Process updates
    if "process" in data:
        pro = data["process"]
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                pro.loc[(stf, "EU27", "Biomass Plant"), "inst-cap"] = 20420
                pro.loc[(stf, "EU27", "Coal Plant"), "inst-cap"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "inst-cap"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "inst-cap"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "inst-cap"] = 56670
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
            else:
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
                pro.loc[(stf, "EU27", "Coal Plant"), "cap-up"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "cap-up"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "cap-up"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0

    # Commodity updates
    if "commodity" in data:
        co = data["commodity"]
        base_value = 319200000
        yearly_decrease_factor = 0.95948
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value
            else:
                year_diff = stf - 2024
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value * (
                    yearly_decrease_factor**year_diff
                )

    # Process-commodity ratios
    if "process-commodity" in data:
        proco = data["process-commodity"]
        for stf in data["global_prop"].index.levels[0].tolist():
            proco.loc[(stf, "Gas Plant (CCGT)", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT)", "CO2", "Out"), "ratio"] = 0.205
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "CO2", "Out"), "ratio"] = 0.0205
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "LNG", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "CO2", "Out"), "ratio"] = 0.231

    # Recycling cost updates
    if "recyclingcost_dict" in data_urbsextensionv1:
        recyclingcost = data_urbsextensionv1["recyclingcost_dict"]
        technologies = ["solarPV", "windon", "windoff", "Batteries"]
        location = "EU27"
        new_costs = {
            "solarPV": 1677.4,
            "windon": 9346.8,
            "windoff": 11126.8,
            "Batteries": 1344.3,
        }
        for stf in range(2024, 2051):
            for tech in technologies:
                key = (stf, location, tech)
                if key in recyclingcost:
                    recyclingcost[key] = new_costs[tech]

    return data, data_urbsextensionv1


def scenario_high_high_avg(data, data_urbsextensionv1):
    import pandas as pd

    # Process updates
    if "process" in data:
        pro = data["process"]
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                pro.loc[(stf, "EU27", "Biomass Plant"), "inst-cap"] = 20420
                pro.loc[(stf, "EU27", "Coal Plant"), "inst-cap"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "inst-cap"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "inst-cap"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "inst-cap"] = 56670
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
            else:
                pro.loc[(stf, "EU27", "Biomass Plant"), "cap-up"] = 60000
                pro.loc[(stf, "EU27", "Coal Plant"), "cap-up"] = 53560
                pro.loc[(stf, "EU27", "Coal Lignite"), "cap-up"] = 43590
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "cap-up"] = 132230
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) LNG"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0

    # Commodity updates
    if "commodity" in data:
        co = data["commodity"]
        base_value = 319200000
        yearly_decrease_factor = 0.95948
        for stf in data["global_prop"].index.levels[0].tolist():
            if stf == 2024:
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value
            else:
                year_diff = stf - 2024
                co.loc[(stf, "EU27", "Piped Gas", "Stock"), "max"] = base_value * (
                    yearly_decrease_factor**year_diff
                )

    # Process-commodity ratios
    if "process-commodity" in data:
        proco = data["process-commodity"]
        for stf in data["global_prop"].index.levels[0].tolist():
            proco.loc[(stf, "Gas Plant (CCGT)", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT)", "CO2", "Out"), "ratio"] = 0.205
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "Piped Gas", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) CCUS", "CO2", "Out"), "ratio"] = 0.0205
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "LNG", "In"), "ratio"] = 1
            proco.loc[(stf, "Gas Plant (CCGT) LNG", "CO2", "Out"), "ratio"] = 0.231

    # Recycling cost updates
    if "recyclingcost_dict" in data_urbsextensionv1:
        recyclingcost = data_urbsextensionv1["recyclingcost_dict"]
        technologies = ["solarPV", "windon", "windoff", "Batteries"]
        location = "EU27"
        new_costs = {
            "solarPV": 1677.4,
            "windon": 9346.8,
            "windoff": 11126.8,
            "Batteries": 2016.45,
        }
        for stf in range(2024, 2051):
            for tech in technologies:
                key = (stf, location, tech)
                if key in recyclingcost:
                    recyclingcost[key] = new_costs[tech]

    return data, data_urbsextensionv1


def scenario_high_high_high(data, data_urbsextensionv1):
    # Commodity updates
    if "commodity" in data:
        co = data["commodity"]
        # CO2 prices per year (€/t)
        co2_prices = {}
        # Linear interpolation from 65 in 2024 to 75 in 2030
        for stf in range(2024, 2051):
            # Set CO2 price to 0 €/t
            #co.loc[(stf, "EU27", "CO2", "Env"), "price"] = 0.0
            #print(f"Year {stf}: CO2 price set to 0 €/t")
            co2_prices[stf] = 65 + (stf - 2024) * (75 - 65) / (2030 - 2024)
        # Fixed values from 2031 onward
        fixed_co2_prices_seb = {
            2031: 81.3,
            2032: 87.6,
            2033: 93.9,
            2034: 100.2,
            2035: 106.5,
            2036: 112.8,
            2037: 119.1,
            2038: 125.4,
            2039: 131.7,
            2040: 138,
            2041: 228.5,
            2042: 364.25,
            2043: 466.0625,
            2044: 500,
            2045: 500,
            2046: 500,
            2047: 500,
            2048: 500,
            2049: 500,
            2050: 500,
        }

        fixed_co2_prices_tyndp = {
            2024: 65.0,
            2025: 74.6667,
            2026: 84.3333,
            2027: 94.0,
            2028: 103.6667,
            2029: 113.3333,
            2030: 113.4,
            2031: 115.9,
            2032: 118.4,
            2033: 120.9,
            2034: 123.4,
            2035: 125.9,
            2036: 128.4,
            2037: 130.9,
            2038: 133.4,
            2039: 135.9,
            2040: 147.0,
            2041: 149.1,
            2042: 151.2,
            2043: 153.3,
            2044: 155.4,
            2045: 157.5,
            2046: 159.6,
            2047: 161.7,
            2048: 163.8,
            2049: 165.9,
            2050: 168.0,
        }
        co2_prices.update(fixed_co2_prices_tyndp)
        for stf in data["global_prop"].index.levels[0].tolist():
            # CO2 price update
            if stf in co2_prices:
                co.loc[(stf, "EU27", "CO2", "Env"), "price"] = co2_prices[stf]


                #print(f"Year {stf}: CO2 price set to {co2_prices[stf]:.2f} €/t")
    if "demand" in data:
        demand = data["demand"]
        print("✅ Demand Columns", demand.columns)

        # === 1. Load the previously generated hourly scaled demand CSV ===
        df_all_years = pd.read_csv("EU27_hourly_scaled_all_years.csv")  # t, 2024_EU27.Elec, 2025_EU27.Elec, ...

        # === 2. Loop over years and timesteps and fill Pyomo demand DataFrame ===
        for year in range(2024, 2051):
            col_name = f"{year}_EU27.Elec"
            if col_name not in df_all_years.columns:
                raise ValueError(f"{col_name} not found in df_all_years!")

            for t, value in zip(df_all_years["t"], df_all_years[col_name]):
                # demand has MultiIndex (year, timestep) and MultiColumn (location, tech)
                demand.loc[(float(year), t), ("EU27", "Elec")] = value

        print("✅ Demand updated for EU27 Elec from 2024–2050 using hourly CSV")

    if "supim" in data:
        # Define number of hours in a non-leap year
        n_timesteps = 8760

        # Create supim_dict with one entry per hour
        supim_dict = {(t, "EU27", "Hydro"): 0.3375 for t in range(1, n_timesteps + 1)}

        supim_df = pd.DataFrame(index=range(0, n_timesteps + 1))
        supim_df[("EU27", "Hydro")] = 0.3375

        # Store back
        data["supim"] = supim_df
        data["supim_dict"] = supim_dict
                # print("SUPIM:", supim)
    # Recycling cost updates
    if "recyclingcost_dict" in data_urbsextensionv1:
        recyclingcost = data_urbsextensionv1["recyclingcost_dict"]
        technologies = ["solarPV", "windon", "windoff", "Batteries"]
        location = "EU27"
        new_costs = {
            "solarPV": 1677.4,
            "windon": 9346.8,
            "windoff": 11126.8,
            "Batteries": 2688.6,
        }
        for stf in range(2024, 2051):
            for tech in technologies:
                key = (stf, location, tech)
                if key in recyclingcost:
                    recyclingcost[key] = new_costs[tech]

    if "process" in data:
        pro = data["process"]
        for stf in data["global_prop"].index.levels[0].tolist():

            if stf >= 2029:
                pro.loc[(stf, "EU27", "Coal Plant"), "cap-up"] = 0
                pro.loc[(stf, "EU27", "Lignite Plant"), "cap-up"] = 0
                pro.loc[(stf, "EU27", "Lignite Plant CCUS"), "cap-up"] = 0
                pro.loc[(stf, "EU27", "Coal Plant CCUS"), "cap-up"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "cap-up"] = 0
            else:
                pro.loc[(stf, "EU27", "Lignite Plant CCUS"), "cap-up"] = 0
                pro.loc[(stf, "EU27", "Coal Plant CCUS"), "cap-up"] = 0
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "cap-up"] = 0
                pro.loc[(stf, "EU27", "Biomass Plant"), "inv-cost"] = 3487.6605 * 1000
                pro.loc[(stf, "EU27", "Biomass Plant"), "var-cost"] = 2.2255

                # Min-fractions (capacity factors)
                pro.loc[(stf, "EU27", "Coal Plant"), "min-fraction"] = 0.221
                pro.loc[(stf, "EU27", "Lignite Plant"), "min-fraction"] = 0.431
                pro.loc[(stf, "EU27", "Gas Plant (CCGT)"), "min-fraction"] = 0.207
                pro.loc[(stf, "EU27", "Other non-res"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Oil Plant"), "min-fraction"] = 0.053
                pro.loc[(stf, "EU27", "Coal Plant CCUS"), "min-fraction"] = 0.221
                pro.loc[(stf, "EU27", "Lignite Plant CCUS"), "min-fraction"] = 0.431
                pro.loc[(stf, "EU27", "Gas Plant (CCGT) CCUS"), "min-fraction"] = 0.207
                pro.loc[(stf, "EU27", "Nuclear Plant"), "min-fraction"] = 0.75
                pro.loc[(stf, "EU27", "Hydro (run-of-river)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Hydro (reservoir)"), "min-fraction"] = 0
                pro.loc[(stf, "EU27", "Biomass Plant"), "min-fraction"] = 0.513

    if "process_commodity" in data:
        proco = data["process_commodity"]

        # get the 2024 subset
        proco_2024 = proco.xs(2024, level="support_timeframe", drop_level=False)

        # repeat 2024 values for all support_timeframes
        for stf in data["global_prop"].index.levels[0].tolist():
            mask = proco.index.get_level_values("support_timeframe") == stf
            proco.loc[mask, ["ratio-min"]] = proco_2024["ratio"].values

        print("✅ All support_timeframes set to 2024 ratio values")

    return data, data_urbsextensionv1
