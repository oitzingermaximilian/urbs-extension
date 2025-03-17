import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches as mpatches

plt.rcParams["font.family"] = "serif"
plt.rcParams["font.serif"] = "Times New Roman"

# Set the directory where the results are located
result_dir = "result/urbs-rerun-20241205T1823"  # Adjust this path as needed

# balance plots
for filename in os.listdir(result_dir):
    if filename.startswith("scenario_") and filename.endswith(".xlsx"):
        file_path = os.path.join(result_dir, filename)
        try:
            df = pd.read_excel(file_path, sheet_name="us_balance")
            # Extract unique years (Stf column)
            years = df["Stf"].unique()

            # Define the energy sources (categories)
            carriers = [
                "Biomass Plant",
                "Wind (onshore)",
                "Wind (offshore)",
                "Nuclear Plant",
                "Hydro (run-of-river)",
                "Hydro (reservoir)",
                "Gas Plant (CCGT)",
                "Coal Plant",
                "Coal Lignite CCUS",
                "Coal Lignite",
                "Coal CCUS",
                "Gas Plant (CCGT) CCUS",
                "Solar",
            ]

            # Initialize empty DataFrames for each year (to store energy demand by carrier)
            energy_dem_y = pd.DataFrame(index=carriers, columns=years)
            # Fill the DataFrame with the values from your dataset
            for year in years:
                temp_df = df[df["Stf"] == year]
                for carrier in carriers:
                    energy_dem_y.loc[carrier, year] = pd.to_numeric(
                        temp_df[temp_df["Process"] == carrier]["Value"], errors="coerce"
                    ).sum()

            # Convert the data into TWh for plotting and handle NaNs
            energy_dem_plot = energy_dem_y / 1e6  # Convert to TWh
            energy_dem_plot = energy_dem_plot.apply(
                pd.to_numeric, errors="coerce"
            )  # Ensure all values are numeric
            energy_dem_plot.fillna(0, inplace=True)  # Replace NaN values with 0

            # Generate the stackplot
            fig, ax = plt.subplots(figsize=(10, 6))

            # Prepare the data for stackplot
            x = years
            y = energy_dem_plot.values  # Values to be stacked
            # Define colors for each energy source
            colors = {
                "Biomass Plant": "#FFB347",  # Pastel blue for biomass
                "Wind (onshore)": "#77DD77",  # Pastel green for onshore wind
                "Wind (offshore)": "#006400",  # Dark green for offshore wind
                "Nuclear Plant": "#FFB6C1",  # Light pastel pink for nuclear
                "Hydro (run-of-river)": "#A0C4E1",  # Light pastel blue for run-of-river hydro
                "Hydro (reservoir)": "#74B3D6",  # Slightly darker pastel blue for reservoir hydro
                "Solar": "#FDFD96",  # Pastel yellow for solar
                "Gas Plant (CCGT)": "#FF6961",  # Light red for gas
                "Coal Plant": "#B0B0B0",  # Light grey for coal plant
                "Coal Lignite": "#808080",  # Dark grey for coal lignite
                "Gas Plant (CCGT) CCUS": "black",
                "Coal CCUS": "black",
                "Coal Lignite CCUS": "black",
            }
            # Stackplot for each carrier

            ax.stackplot(
                x,
                y,
                labels=carriers,
                colors=[colors[carrier] for carrier in carriers],
                alpha=0.8,
            )

            # Set grid, labels, and limits
            ax.grid(which="major", axis="y", color="#758D99", alpha=0.4, zorder=1)
            ax.set_ylabel("Energy produced in TWh", fontsize=17)
            ax.set_ylim([0, 7000])
            ax.set_yticklabels(ax.get_yticks(), fontsize=15)

            # Set ticks for all years (including unlabeled ones)
            ax.set_xticks(years)  # Set ticks for every year

            # Label specific years, keeping other years unlabeled
            ax.set_xticklabels(
                [
                    str(year) if year in [2025, 2030, 2035, 2040, 2045, 2050] else ""
                    for year in years
                ],
                fontsize=17,
            )

            # Customize tick appearance
            ax.tick_params(
                axis="x", which="major", length=5
            )  # Short ticks for all years
            ax.tick_params(
                axis="x", which="minor", length=3
            )  # Even smaller ticks for any minor ones (optional)

            # Add a legend for the stackplot above the plot
            ax.legend(
                loc="lower center",
                facecolor="White",
                fontsize=12,
                framealpha=0.8,
                ncol=3,
                borderpad=0.75,
                edgecolor="black",
                bbox_to_anchor=(0.5, 1.05),
            )
            plt.tight_layout()

            # Save the plot
            output_file = os.path.join(result_dir, f"total_balance_{filename}.png")
            plt.tight_layout()  # Adjust layout to make room for labels
            plt.savefig(output_file)
            print(f"Saved balance plot as: {output_file}")
            plt.clf()  # Clear the figure
        except Exception as e:
            print(f"Error processing file {filename}: {e}")

# capacity plots
for filename in os.listdir(result_dir):
    if filename.startswith("scenario_") and filename.endswith(".xlsx"):
        file_path = os.path.join(result_dir, filename)
        try:
            df = pd.read_excel(file_path, sheet_name="us_capacity")
            print(f"Processing file: {filename}")

            # Fill missing site values
            if df["Site"].notna().any():
                site_value = df["Site"].dropna().iloc[0]
                df["Site"].fillna(site_value, inplace=True)

            # Fill missing Stf values and ensure it's float
            df["Stf"].fillna(method="ffill", inplace=True)
            df["Stf"] = df["Stf"].astype(float)  # Ensure 'Stf' is float

            # Initial solar capacity to be added (260,000 MW = 260 GW)
            initial_capacity_mw = 260000  # TODO change that to good code
            years = df["Stf"].unique()
            initial_capacity_df = pd.DataFrame(
                {
                    "Stf": years,
                    "Process": ["capacity_solar_initial"] * len(years),
                    "Total": [initial_capacity_mw] * len(years),
                }
            )
            df_combined = pd.concat([df, initial_capacity_df], ignore_index=True)
            solar_mask = df_combined["Process"].str.startswith("capacity_solar_")
            solar_data = df_combined[solar_mask]
            solar_sum = solar_data.groupby("Stf")["Total"].sum().reset_index()
            solar_sum["Process"] = "Solar"  # Assign a common name for solar capacities
            df_combined_no_solar = df_combined[~solar_mask]
            df_combined_final = pd.concat(
                [df_combined_no_solar, solar_sum], ignore_index=True
            )

            df_pivot = df_combined_final.pivot_table(
                index="Stf",
                columns="Process",
                values="Total",
                aggfunc="sum",
                fill_value=0,
            )

            df_pivot_gw = df_pivot / 1e3  # MW to GW
            df_plot = df_pivot_gw[
                [
                    col
                    for col in df_pivot_gw.columns
                    if not col.startswith("capacity_solar_")
                ]
            ]

            colors = {
                "Biomass Plant": "#FFB347",  # Pastel blue for biomass
                "Wind (onshore)": "#77DD77",  # Pastel green for onshore wind
                "Wind (offshore)": "#006400",  # Dark green for offshore wind
                "Nuclear Plant": "#FFB6C1",  # Light pastel pink for nuclear
                "Hydro (run-of-river)": "#A0C4E1",  # Light pastel blue for run-of-river hydro
                "Hydro (reservoir)": "#74B3D6",  # Slightly darker pastel blue for reservoir hydro
                "Solar": "#FDFD96",  # Pastel yellow for solar
                "Gas Plant (CCGT)": "#FF6961",  # Light red for gas
                "Coal Plant": "#B0B0B0",  # Light grey for coal plant
                "Coal Lignite": "#808080",  # Dark grey for coal lignite
                "Gas Plant (CCGT) CCUS": "black",
                "Coal CCUS": "black",
                "Coal Lignite CCUS": "black",
            }

            ax = df_plot.plot(
                kind="bar",
                stacked=True,
                figsize=(10, 6),
                color=[colors.get(col, "#D3D3D3") for col in df_plot.columns],
            )

            years_of_interest = [2024, 2030, 2035, 2040, 2045, 2050]

            ax.set_xticks(range(len(df_plot.index)))  # Set ticks for all years
            ax.set_xticklabels(
                [
                    int(year) if year in years_of_interest else ""
                    for year in df_plot.index
                ],
                rotation=0,
                fontsize=12,
            )

            ax.grid(which="major", axis="y", color="#758D99", alpha=0.4, zorder=1)
            ax.set_ylabel("Total Capacity Installed in GW", fontsize=17)

            ax.set_ylim([0, 4000])
            ax.set_yticklabels(ax.get_yticks(), fontsize=15)
            ax.set_xlabel("")

            ax.tick_params(
                axis="x", which="major", length=5
            )  # Short ticks for all years
            ax.tick_params(
                axis="x", which="minor", length=3
            )  # Even smaller ticks for any minor ones (optional)

            ax.legend(
                loc="lower center",
                facecolor="White",
                fontsize=12,
                framealpha=0.8,
                ncol=3,
                borderpad=0.75,
                edgecolor="black",
                bbox_to_anchor=(0.5, 1.05),
            )
            plt.tight_layout()

            plt.xlim(-0.5, len(df_plot.index) - 0.5)
            plt.ylim(bottom=0)

            output_file = os.path.join(result_dir, f"us_capacity_all_{filename}.png")
            plt.tight_layout()
            plt.savefig(output_file)
            print(f"Saved stacked bar plot as: {output_file}")
            plt.clf()  # Clear the current figure

            # next plot solar caps

            df_solar = df[
                df["Process"].str.startswith("capacity_solar_")
                | (df["Process"] == "Solar Stock")
            ]
            initial_capacity_df = pd.DataFrame(
                {
                    "Stf": years,
                    "Process": ["initial_solar_capacity"] * len(years),
                    "Total": [initial_capacity_mw] * len(years),
                }
            )

            df_solar = pd.concat([df_solar, initial_capacity_df], ignore_index=True)
            df_solar_pivot = df_solar.pivot_table(
                index="Stf",
                columns="Process",
                values="Total",
                aggfunc="sum",
                fill_value=0,
            )
            df_solar_pivot_gw = df_solar_pivot / 1e3
            df_solar_pivot_gw = df_solar_pivot_gw[
                ["initial_solar_capacity"]
                + [
                    col
                    for col in df_solar_pivot_gw.columns
                    if col != "initial_solar_capacity"
                ]
            ]
            nicer_names = {
                "initial_solar_capacity": "Initial Solar Capacity",
                "capacity_solar_euprimary": "Solar Capacity EU Primary",
                "capacity_solar_eusecondary": "Solar Capacity EU Secondary",
                "capacity_solar_imported": "Solar Capacity Imported",
                "capacity_solar_stock": "Stock Capacity",
                "capacity_solar_stockout": "Solar Capacity from Stock",
            }
            df_solar_pivot_gw.rename(columns=nicer_names, inplace=True)
            custom_colors = [
                "#FFB74D",  # Warm Yellow-Orange
                "grey",
                "#FFE4B5",
                "yellow",
                "#FFD700",
                "#FFAB91",  # Light Coral
            ]

            ax_solar = df_solar_pivot_gw.plot(
                kind="bar", stacked=True, figsize=(10, 6), color=custom_colors
            )
            plt.title(f"Solar Capacities by Year", fontsize=16)
            plt.ylabel("Total Capacity (GW)", fontsize=16)
            plt.xlabel("")

            years_of_interest = [2024, 2030, 2035, 2040, 2045, 2050]
            ax_solar.set_xticks(
                range(len(df_solar_pivot.index))
            )  # Set ticks for all years
            ax_solar.set_xticklabels(
                [
                    int(year) if year in years_of_interest else ""
                    for year in df_solar_pivot.index
                ],
                rotation=0,
                fontsize=12,
            )

            ax_solar.tick_params(axis="x", which="major", length=5)
            ax_solar.tick_params(axis="x", which="minor", length=3)
            ax_solar.tick_params(axis="x", labelsize=12, width=1)
            ax_solar.tick_params(axis="y", labelsize=12, width=1)
            ax_solar.grid(
                which="major",
                axis="y",
                color="lightgrey",
                linestyle="--",
                linewidth=0.5,
                alpha=0.7,
            )

            plt.xlim(-0.5, len(df_solar_pivot.index) - 0.5)
            plt.ylim(bottom=0)

            output_file_solar = os.path.join(
                result_dir, f"us_capacity_solar_{filename}.png"
            )
            plt.tight_layout()
            plt.savefig(output_file_solar)
            print(f"Saved solar capacities plot as: {output_file_solar}")
            plt.clf()
            # pie chart solar capacities

            solar_totals = df_solar_pivot_gw.sum()
            labels = [nicer_names.get(col, col) for col in solar_totals.index]
            colors = custom_colors

            plt.figure(figsize=(8, 8))
            plt.pie(
                solar_totals,
                labels=labels,
                colors=colors,
                autopct="%1.1f%%",
                startangle=140,
                wedgeprops={"edgecolor": "gray"},
            )

            plt.title("Distribution of Solar Capacities", fontsize=16)

            plt.axis("equal")

            output_file_solar_pie = os.path.join(
                result_dir, f"solar_capacity_pie_{filename}.png"
            )
            plt.tight_layout()
            plt.savefig(output_file_solar_pie)
            print(f"Saved solar capacity pie chart as: {output_file_solar_pie}")
            plt.clf()

            # new plot solar stock capacity

            df_solar = df[df["Process"] == "Solar Stock"]
            df_solar_pivot = df_solar.pivot_table(
                index="Stf",
                columns="Process",
                values="Total",
                aggfunc="sum",
                fill_value=0,
            )
            df_solar_pivot_gw = df_solar_pivot / 1e3
            custom_colors = [
                "#FDFD96",  # yellow
            ]

            ax_solar = df_solar_pivot_gw.plot(
                kind="bar", stacked=True, figsize=(10, 6), color=custom_colors
            )
            plt.title(f"Solar Stock Capacities per Year", fontsize=16)
            plt.ylabel("Total Capacity (GW)", fontsize=16)
            plt.xlabel("")

            years_of_interest = [2024, 2030, 2035, 2040, 2045, 2050]
            ax_solar.set_xticks(
                range(len(df_solar_pivot.index))
            )  # Set ticks for all years
            ax_solar.set_xticklabels(
                [
                    int(year) if year in years_of_interest else ""
                    for year in df_solar_pivot.index
                ],
                rotation=0,
                fontsize=12,
            )

            ax_solar.tick_params(axis="x", which="major", length=5)
            ax_solar.tick_params(axis="x", which="minor", length=3)
            ax_solar.tick_params(axis="x", labelsize=12, width=1)
            ax_solar.tick_params(axis="y", labelsize=12, width=1)
            ax_solar.grid(
                which="major",
                axis="y",
                color="lightgrey",
                linestyle="--",
                linewidth=0.5,
                alpha=0.7,
            )

            plt.xlim(-0.5, len(df_solar_pivot.index) - 0.5)
            plt.ylim(bottom=0)

            output_file_solar = os.path.join(
                result_dir, f"us_capacity_solarstock_{filename}.png"
            )
            plt.tight_layout()
            plt.savefig(output_file_solar)
            print(f"Saved solar capacities plot as: {output_file_solar}")
            plt.clf()

        except Exception as e:
            print(f"Error processing file {filename}: {e}")

# cost plots
for filename in os.listdir(result_dir):
    if filename.startswith("scenario_") and filename.endswith(".xlsx"):
        file_path = os.path.join(result_dir, filename)
        try:
            df = pd.read_excel(file_path, sheet_name="us_cost")
            print(f"Processing file: {filename}")

            if df["pro"].notna().any():
                pro_value = df["pro"].dropna().iloc[0]
                df["pro"].fillna(pro_value, inplace=True)

            df["stf"].fillna(method="ffill", inplace=True)
            df["stf"] = df["stf"].astype(float)

            # Create pivot table
            df_pivot = df.pivot_table(
                index="stf",
                columns="pro",
                values="Total_Cost",
                aggfunc="sum",
                fill_value=0,
            )

            # Convert total costs to billion euros
            df_pivot /= 1e9  # Divide by 1 billion to convert to billion euros
            nicer_names = {
                "Biomass Plant": "Biomass Plant",
                "Coal CCUS": "Coal Plant CCUS",
                "Coal Lignite": "Coal Lignite",
                "Coal Lignite CCUS": "Coal Lignite CCUS",
                "Coal Plant": "Coal Plant",
                "Gas Plant (CCGT)": "Gas Plant (CCGT)",
                "Gas Plant (CCGT) CCUS": "Gas Plant (CCGT) CCUS",
                "Hydro (reservoir)": "Hydro (reservoir)",
                "Hydro (run-of-river)": "Hydro (run-of-river)",
                "Nuclear Plant": "Nuclear Plant",
                "Wind (offshore)": "Wind (offshore)",
                "Wind (onshore)": "Wind (onshore)",
                "costs_EU_primary": "Manufacturing Solar",
                "costs_EU_secondary": "Recycling Solar",
                "costs_solar_import": "Import Solar",
                "costs_solar_storage": "Storage Solar",
            }
            df_pivot.rename(columns=nicer_names, inplace=True)

            colors = {
                "Biomass Plant": "#FFB347",  # Pastel orange for biomass
                "Wind (onshore)": "#77DD77",  # Pastel green for onshore wind
                "Wind (offshore)": "#006400",  # Dark green for offshore wind
                "Nuclear Plant": "#FFB6C1",  # Light pastel pink for nuclear
                "Hydro (run-of-river)": "#A0C4E1",  # Light pastel blue for run-of-river hydro
                "Hydro (reservoir)": "#74B3D6",  # Slightly darker pastel blue for reservoir hydro
                "Gas Plant (CCGT)": "#FF6961",  # Light red for gas
                "Coal Plant": "#B0B0B0",  # Light grey for coal plant
                "Coal Lignite": "#808080",  # Dark grey for coal lignite
                "Gas Plant (CCGT) CCUS": "black",
                "Coal Plant CCUS": "black",
                "Coal Lignite CCUS": "black",
                # Dark grey for coal lignite
                # Distinguishable palette for Solar costs
                "Manufacturing Solar": "#FFFACD",  # Lemon chiffon (soft yellow) for manufacturing solar
                "Recycling Solar": "#FFE4B5",  # Moccasin (light yellow-orange) for recycling solar
                "Import Solar": "yellow",  # Cornsilk (pale yellow) for import solar
                "Storage Solar": "#FFD700",  # Gold (vibrant yellow) for storage solar
            }

            # Create the stacked bar plot
            # Create the stacked bar plot with custom colors
            ax = df_pivot.plot(
                kind="bar",
                stacked=True,
                figsize=(12, 7),
                color=[colors[col] for col in df_pivot.columns],
            )

            # Customize the plot
            plt.title("", fontsize=16)
            plt.ylabel("Total System Cost in Billion €", fontsize=16)
            plt.xlabel("")

            # Define the years for x-ticks
            years_of_interest = [2024, 2030, 2035, 2040, 2045, 2050]
            # Set ticks and labels for the x-axis
            ax.set_xticks(range(len(df_pivot.index)))  # Set ticks for all years
            ax.set_xticklabels(
                [
                    int(year) if year in years_of_interest else ""
                    for year in df_pivot.index
                ],
                rotation=0,
                fontsize=1,
            )
            ax.tick_params(
                axis="x", which="major", length=5
            )  # Short ticks for all years
            ax.tick_params(axis="x", which="minor", length=3)
            ax.tick_params(axis="x", labelsize=12, width=1)
            ax.tick_params(axis="y", labelsize=12, width=1)

            # Set grid
            ax.grid(which="major", axis="y", color="#758D99", alpha=0.4, zorder=1)

            # Adjust legend position above the title, and remove 'pro' label from the legend
            plt.legend(
                loc="lower center",
                facecolor="White",
                fontsize=12,
                framealpha=0.8,
                ncol=3,
                borderpad=0.75,
                edgecolor="black",
                bbox_to_anchor=(0.5, 1.05),
            )

            # Adjust layout and save the plot
            plt.tight_layout()  # Extra top space for legend and title
            output_file_stack = os.path.join(result_dir, f"barplot_cost_{filename}.png")
            plt.savefig(output_file_stack)  # Save the stack plot
            print(f"Saved stack plot as: {output_file_stack}")
            plt.clf()  # Clear the current figure

            if "Total_Cost" in df.columns:
                # Step 4: Group by year (assuming 'Year' is in 'stf') and sum total costs
                df_total_costs = df.groupby("stf")["Total_Cost"].sum().reset_index()

                # Scale costs to billion €
                df_total_costs["Total_Cost"] /= 1e9  # Convert to billion €

                # Step 5: Create a line plot for total costs over time
                plt.figure(figsize=(10, 6))
                plt.plot(
                    df_total_costs["stf"],
                    df_total_costs["Total_Cost"],
                    linestyle="-",
                    color="#006400",
                )

                # Step 6: Customize the line plot
                plt.title("", fontsize=16)
                plt.ylabel("Total System Cost in Billion €", fontsize=16)

                # Set ticks for specific years with empty labels for others
                specific_years = [2024, 2030, 2035, 2040, 2045, 2050]
                tick_labels = [
                    str(int(year)) if year in specific_years else ""
                    for year in df_total_costs["stf"]
                ]
                plt.xticks(df_total_costs["stf"], tick_labels)
                plt.tick_params(
                    axis="x", which="major", length=5
                )  # Short ticks for all years
                plt.tick_params(axis="x", which="minor", length=3)
                plt.tick_params(axis="x", labelsize=12, width=1)
                plt.tick_params(axis="y", labelsize=12, width=1)
                # Add grid
                plt.grid(which="major", axis="y", color="#758D99", alpha=0.4, zorder=1)

                # Set limits and ticks
                plt.xlim(
                    df_total_costs["stf"].min() - 1, df_total_costs["stf"].max() + 1
                )  # Set limits for x-axis
                plt.ylim(bottom=0)  # Set lower limit for y-axis

                # Save the plot
                output_file = os.path.join(result_dir, f"lineplot_costs_{filename}.png")
                plt.tight_layout()  # Adjust layout to make room for labels
                plt.savefig(output_file)
                print(f"Saved line plot as: {output_file}")

                plt.clf()  # Clear the figure

        except Exception as e:
            print(f"Error processing file {filename}: {e}")

# co2 plots
# for filename in os.listdir(result_dir):
#    if filename.startswith("scenario_") and filename.endswith(".xlsx"):
#        file_path = os.path.join(result_dir, filename)
#        try:
#            df = pd.read_excel(file_path, sheet_name="us_co2")
