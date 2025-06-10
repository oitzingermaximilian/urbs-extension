from abc import ABC, abstractmethod
import pyomo.core as pyomo
from pyomo.environ import value


class AbstractConstraint(ABC):
    @abstractmethod
    def apply_rule(self, m, stf, location, tech):
        pass


DEBUG = False  # Set to False to disable all debug prints


def debug_print(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)


class CapacityExtGrowthRule(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        if stf == value(m.y0):
            debug_print(
                f"Running constraint CapacityExtGrowthRule for stf={stf} (start year)"
            )
            return (
                m.capacity_ext[stf, location, tech]
                == m.Installed_Capacity_Q_s[location, tech]
                + m.capacity_ext_new[stf, location, tech]
                - m.capacity_dec[stf, location, tech]
            )
        else:
            debug_print(
                f"Running constraint CapacityExtGrowthRule for stf={stf} (inside intervall)"
            )
            return (
                m.capacity_ext[stf, location, tech]
                == m.capacity_ext[stf - 1, location, tech]
                + m.capacity_ext_new[stf, location, tech]
                - m.capacity_dec[stf, location, tech]
            )


class CapacityExtNewRule(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        debug_print(f"Running constraint CapacityExtNewRule for stf={stf}")

        return m.capacity_ext_new[stf, location, tech] == (
            m.capacity_ext_imported[stf, location, tech]
            + m.capacity_ext_stockout[stf, location, tech]
            + m.capacity_ext_euprimary[stf, location, tech]
            + m.capacity_ext_eusecondary[stf, location, tech]
        )


class CapacityExtStockRule(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        if stf == value(m.y0):
            debug_print(
                f"Running constraint CapacityExtStockRule for stf={stf} (start year)"
            )
            return m.capacity_ext_stock[stf, location, tech] == (
                m.Existing_Stock_Q_stock[location, tech]
                + m.capacity_ext_stock_imported[stf, location, tech]
                - m.capacity_ext_stockout[stf, location, tech]
            )
        else:
            # debug_print(f"Running constraint CapacityExtStockRule for stf={stf}")
            return m.capacity_ext_stock[stf, location, tech] == (
                m.capacity_ext_stock[stf - 1, location, tech]
                + m.capacity_ext_stock_imported[stf, location, tech]
                - m.capacity_ext_stockout[stf, location, tech]
            )


class StockTurnoverRule(AbstractConstraint):  # NOTE disabled atm
    def apply_rule(self, m, stf, location, tech):
        valid_years = [2025, 2030, 2035, 2040, 2045]

        if stf in valid_years:
            lhs = sum(
                m.capacity_ext_stockout[j, location, tech]
                for j in range(stf, stf + m.n)
                if j in m.capacity_ext_stockout
            )
            debug_print(f"LHS for {tech} at {location} in year {stf}: {lhs}")

            rhs = (
                m.FT
                * (1 / m.n)
                * sum(
                    m.capacity_ext_stock[j, location, tech]
                    for j in range(stf, stf + m.n)
                    if j in m.capacity_ext_stock
                )
            )
            debug_print(f"RHS for {tech} at {location} in year {stf}: {rhs}")

            return lhs >= rhs
        else:
            return pyomo.Constraint.Skip


class AntiDumpingMeasuresRule(AbstractConstraint):  # NOTE disabled atm
    def apply_rule(self, m, stf, location, tech):
        rhs = m.anti_dumping_index[location, tech] * (
            m.capacity_ext_imported[stf, location, tech]
            + m.capacity_ext_stock_imported[stf, location, tech]
        )

        debug_print(
            f"Anti-Dumping Measure for {tech} at {location} in year {stf}: "
            f"{m.anti_dumping_measures[stf, location, tech]} = {rhs}"
        )

        return m.anti_dumping_measures[stf, location, tech] == rhs


class CapacityExtNewLimitRule(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        if stf == value(m.y0):
            debug_print(
                f"Running constraint CapacityExtNewLimitRule for stf={stf} (start year)"
            )
            cap_val = m.capacity_ext_new[stf, location, tech]
            ext_val = (
                m.Q_ext_new[
                    stf, location, tech
                ]  # + m.capacity_dec_start[location, tech]
            )
            return cap_val <= ext_val
        else:
            debug_print(f"Running constraint CapacityExtNewLimitRule for stf={stf}")
            capacity_value = m.capacity_ext_new[stf, location, tech]
            ext_new_value = (
                m.Q_ext_new[stf, location, tech]
                + m.capacity_dec[stf - 1, location, tech]
            )
            debug_print(
                f"Debug: STF = {stf}, Location = {location}, Tech = {tech}, LHS = {capacity_value}, RHS = {ext_new_value}"
            )
            return capacity_value <= ext_new_value


class TimedelayEUPrimaryProductionRule(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        if stf == 2024:
            debug_print(
                f"Skipping TimedelayEUPrimaryProductionRule constraint for stf={stf} (global start year)"
            )
            return pyomo.Constraint.Skip

        elif stf == value(m.y0):
            debug_print(
                f"Running constraint TimedelayEUPrimaryProductionRule for stf={stf} (start year)"
            )
            lhs = (
                m.capacity_ext_euprimary[stf, location, tech]
                - m.cap_prim_prior[location, tech]
            )
            rhs = (
                m.deltaQ_EUprimary[location, tech]
                + m.IR_EU_primary[location, tech] * m.cap_prim_prior[location, tech]
            )
            debug_print(
                f"Debug: STF = {stf}, Location = {location}, Tech = {tech}, LHS = {lhs}, RHS = {rhs}"
            )
            return lhs <= rhs

        else:
            lhs = (
                m.capacity_ext_euprimary[stf, location, tech]
                - m.capacity_ext_euprimary[stf - 1, location, tech]
            )
            rhs = (
                m.deltaQ_EUprimary[location, tech]
                + m.IR_EU_primary[location, tech]
                * m.capacity_ext_euprimary[stf - 1, location, tech]
            )

            debug_print(
                f"Debug: STF = {stf}, Location = {location}, Tech = {tech}, LHS = {lhs}, RHS = {rhs}"
            )

            return lhs <= rhs


class TimedelayEUSecondaryProductionRule(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        if stf == 2024:
            debug_print(
                f"Skipping TimedelayEUSecondaryProductionRule constraint for stf={stf} (global start year)"
            )
            return pyomo.Constraint.Skip

        elif stf == value(m.y0):
            debug_print(
                f"Running constraint TimedelayEUSecondaryProductionRule for stf={stf} (start year)"
            )
            lhs = (
                m.capacity_ext_eusecondary[stf, location, tech]
                - m.cap_sec_prior[location, tech]
            )
            rhs = (
                m.deltaQ_EUsecondary[location, tech]
                + m.IR_EU_secondary[location, tech] * m.cap_sec_prior[location, tech]
            )
            return lhs <= rhs

        else:
            lhs = (
                m.capacity_ext_eusecondary[stf, location, tech]
                - m.capacity_ext_eusecondary[stf - 1, location, tech]
            )
            rhs = (
                m.deltaQ_EUsecondary[location, tech]
                + m.IR_EU_secondary[location, tech]
                * m.capacity_ext_eusecondary[stf - 1, location, tech]
            )

            debug_print(
                f"Debug: STF = {stf}, Location = {location}, Tech = {tech}, LHS = {lhs}, RHS = {rhs}"
            )

            return lhs <= rhs


class Constraint1EUSecondaryToTotalRule(AbstractConstraint):  # NOTE disabled atm
    def apply_rule(self, m, stf, location, tech):
        l_value = m.l[location, tech]
        if value(m.y0) <= stf - l_value:
            lhs = m.capacity_ext_eusecondary[stf, location, tech]
            rhs = m.capacity_ext_new[stf - l_value, location, tech]

            debug_print(
                f"Debug: STF = {stf}, Location = {location}, Tech = {tech}, LHS = {lhs}, RHS = {rhs}"
            )

            return lhs <= rhs
        else:
            return pyomo.Constraint.Skip


class Constraint2EUSecondaryToTotalRule(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        l_value = m.l[location, tech]
        if value(m.y0) >= stf - l_value:
            lhs = m.capacity_ext_eusecondary[stf, location, tech]
            rhs = m.DCR_solar[stf, location, tech] * m.capacity_ext[stf, location, tech]

            debug_print(
                f"Debug: STF = {stf}, Location = {location}, Tech = {tech}, LHS = {lhs}, RHS = {rhs}"
            )

            return lhs <= rhs
        else:
            return pyomo.Constraint.Skip


class ConstraintEUPrimaryToTotalRule(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        if stf == 2024:
            debug_print(
                f"Skipping ConstraintEUPrimaryToTotalRule constraint for stf={stf} (global start year)"
            )
            return pyomo.Constraint.Skip

        if stf == value(m.y0):
            lhs = m.capacity_ext_euprimary[stf, location, tech]
            rhs = m.DR_primary[location, tech] * m.cap_prim_prior[location, tech]
            return lhs >= rhs

        else:
            lhs = m.capacity_ext_euprimary[stf, location, tech]
            rhs = (
                m.DR_primary[location, tech]
                * m.capacity_ext_euprimary[stf - 1, location, tech]
            )

            debug_print(
                f"Debug: STF = {stf}, Location = {location}, Tech = {tech}, LHS = {lhs}, RHS = {rhs}"
            )

            return lhs >= rhs


class ConstraintEUSecondaryToSecondaryRule(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        if stf == 2024:
            debug_print(
                f"Skipping ConstraintEUSecondaryToSecondaryRule constraint for stf={stf} (global start year)"
            )
            return pyomo.Constraint.Skip

        if stf == value(m.y0):
            lhs = m.capacity_ext_eusecondary[stf, location, tech]
            rhs = m.DR_secondary[location, tech] * m.cap_sec_prior[location, tech]

            return lhs >= rhs
        else:
            lhs = m.capacity_ext_eusecondary[stf, location, tech]
            rhs = (
                m.DR_secondary[location, tech]
                * m.capacity_ext_eusecondary[stf - 1, location, tech]
            )

            debug_print(
                f"Debug: STF = {stf}, Location = {location}, Tech = {tech}, LHS = {lhs}, RHS = {rhs}"
            )

            return lhs >= rhs


class ConstraintMaxIntoStockRule(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        # Calculate the left-hand side (LHS) and right-hand side (RHS)
        lhs = m.capacity_ext_stock_imported[stf, location, tech]
        rhs = 0.5 * m.capacity_ext_imported[stf, location, tech]

        # Debugging: Print the LHS and RHS values
        debug_print(
            f"Debug: STF = {stf}, Location = {location}, Tech = {tech}, LHS = {lhs}, RHS = {rhs}"
        )

        return lhs <= rhs


class ConstraintBatteryDemandRule(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        lhs = m.demand_bess[stf, location]
        rhs = sum(
            m.factor_bess[location, t] * m.capacity_ext_new[stf, location, t]
            for t in m.tech
            if t != "Batteries"
        )
        debug_print(f"Caluclating battery demand for {stf}: demand = {rhs}")
        return lhs == rhs


class ConstraintBatteryCapRule(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        lhs = m.demand_bess[stf, location]
        rhs = m.capacity_ext_new[stf, location, "Batteries"]

        debug_print(
            f"Battery cap constraint for {stf}, {location}: lhs demand = {lhs}, rhs battery cap = {rhs}"
        )
        return lhs <= rhs


class ConstraintCarryoverSecondary(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        return m.capacity_secondary_cumulative[
            stf, location, tech
        ] == m.total_secondary_cap_inital[location, tech] + sum(
            m.capacity_ext_eusecondary[t, location, tech] for t in m.stf if t <= stf
        )


def apply_stockpiling_constraints(m):
    constraints = [
        CapacityExtGrowthRule(),
        CapacityExtNewRule(),
        CapacityExtStockRule(),
        # StockTurnoverRule(),
        # AntiDumpingMeasuresRule(),
        CapacityExtNewLimitRule(),
        TimedelayEUPrimaryProductionRule(),
        TimedelayEUSecondaryProductionRule(),
        # Constraint1EUSecondaryToTotalRule(), #ToDo fix this constraint
        Constraint2EUSecondaryToTotalRule(),
        ConstraintEUPrimaryToTotalRule(),
        ConstraintEUSecondaryToSecondaryRule(),
        ConstraintMaxIntoStockRule(),
        ConstraintBatteryDemandRule(),
        ConstraintBatteryCapRule(),
        ConstraintCarryoverSecondary(),
    ]

    for i, constraint in enumerate(constraints):
        constraint_name = f"constraint_{i + 1}"
        setattr(
            m,
            constraint_name,
            pyomo.Constraint(
                m.stf,
                m.location,
                m.tech,
                rule=lambda m, stf, loc, tech: constraint.apply_rule(m, stf, loc, tech),
            ),
        )
