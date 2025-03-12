import os
import shutil
import urbs
from datetime import date

input_files = 'urbs_intertemporal_2050'  # for single year file name, for intertemporal folder name
input_dir = 'Input'
input_path = os.path.join(input_dir, input_files)

result_name = 'urbs-rerun'
result_dir = urbs.prepare_result_directory(result_name)  # name + time stamp

#get year
year = date.today().year

# copy input file to result directory
try:
    shutil.copytree(input_path, os.path.join(result_dir, input_dir))
except NotADirectoryError:
    shutil.copyfile(input_path, os.path.join(result_dir, input_files))
# copy run file to result directory
shutil.copy(__file__, result_dir)

# objective function
objective = 'cost'  # set either 'cost' or 'CO2' as objective

# Choose Solver (cplex, glpk, gurobi, ...)
solver = 'gurobi'

# simulation timesteps
(offset, length) = (0, 1)  # time step selection
timesteps = range(offset, offset+length+1)
dt = 8760  # length of each time step (unit: hours)

# detailed reporting commodity/sites
report_tuples = []

# optional: define names for sites in report_tuples
report_sites_name = {('EU27'): 'All'}

# plotting commodities/sites
plot_tuples = []

# optional: define names for sites in plot_tuples
plot_sites_name = {('EU27'): 'All'}

# plotting timesteps
plot_periods = {
    'all': timesteps[1:]
}

# add or change plot colors
my_colors = {'EU27': (200, 230, 200)

}
for country, color in my_colors.items():
    urbs.COLORS[country] = color

# select scenarios to be run
scenarios = [
    urbs.scenario_base
    #urbs.scenario_base_minstock,
    #urbs.scenario_1,
    #urbs.scenario_2,
    #urbs.scenario_3,
    #urbs.scenario_4,
    #urbs.scenario_6,
    #urbs.scenario_7,
    #urbs.scenario_8,
    #urbs.scenario_10,
    #urbs.scenario_11,
    #urbs.scenario_12,
    #urbs.scenario_13,
    #urbs.scenario_14,
    #urbs.scenario_15,
    #urbs.scenario_16,
    #urbs.scenario_17,
    #urbs.scenario_18,
    #urbs.scenario_19,
    #urbs.scenario_20,
    ##urbs.scenario_21,
    #urbs.scenario_25,
    #urbs.scenario_26,
    #urbs.scenario_27,
    #urbs.scenario_28,
    #urbs.scenario_29,
    #urbs.scenario_30,
    #urbs.scenario_31,
    #urbs.scenario_32,
    #urbs.scenario_33,
    #urbs.scenario_34
    #urbs.scenario_35
    #urbs.scenario_36,
    #urbs.scenario_37
    #urbs.scenario_38
    #urbs.scenario_39
    #urbs.scenario_40

]



for scenario in scenarios:
    prob = urbs.run_scenario(input_path, solver, timesteps, scenario,
                             result_dir, dt, objective,
                             plot_tuples=plot_tuples,
                             plot_sites_name=plot_sites_name,
                             plot_periods=plot_periods,
                             report_tuples=report_tuples,
                             report_sites_name=report_sites_name)
